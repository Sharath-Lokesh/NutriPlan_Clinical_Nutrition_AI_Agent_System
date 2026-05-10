import json
import os
from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_utilities import get_usda_context
from usda_client import UsdaClient


_DIET_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "diet_filters.json",
)


_ALLOWED_DIETS = {
    "vegan",
    "vegetarian",
    "gluten-free",
    "halal",
    "kosher",
    "low-fodmap",
    "dairy-free",
}


def _load_diet_filters() -> dict:
    try:
        with open(_DIET_DATA_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh) or {}
    except (OSError, ValueError):
        return {}


def _haystack(food: dict) -> str:
    parts: list[str] = []
    if food.get("description"):
        parts.append(str(food["description"]))
    if food.get("ingredients"):
        parts.append(str(food["ingredients"]))
    food_category = food.get("foodCategory")
    if isinstance(food_category, dict):
        if food_category.get("description"):
            parts.append(str(food_category["description"]))
    elif isinstance(food_category, str):
        parts.append(food_category)
    return " ".join(parts).lower()


def _category_string(food: dict) -> str:
    food_category = food.get("foodCategory")
    if isinstance(food_category, dict):
        return str(food_category.get("description") or "")
    if isinstance(food_category, str):
        return food_category
    return ""


async def filter_foods_by_diet(
    fdcIds: Annotated[  # noqa: N803
        list[int],
        Field(description="List of USDA FDC IDs to evaluate."),
    ],
    diet: Annotated[
        str,
        Field(
            description=(
                "Diet to filter against. One of: vegan, vegetarian, gluten-free, halal, "
                "kosher, low-fodmap, dairy-free."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not fdcIds:
        return create_text_response("'fdcIds' must be a non-empty list.", is_error=True)
    diet_key = (diet or "").strip().lower()
    if diet_key not in _ALLOWED_DIETS:
        return create_text_response(
            f"'diet' must be one of: {sorted(_ALLOWED_DIETS)}.", is_error=True
        )

    filters = _load_diet_filters()
    rule = filters.get(diet_key) or {}
    exclude_keywords = [str(k).lower() for k in (rule.get("exclude_keywords") or [])]
    exclude_categories = [str(c).lower() for c in (rule.get("exclude_categories") or [])]

    try:
        ids = [int(i) for i in fdcIds]
    except (TypeError, ValueError):
        return create_text_response("All 'fdcIds' must be integers.", is_error=True)

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)
    foods = await client.get_foods(ids, format="full") or []

    by_id: dict[int, dict] = {}
    for food in foods:
        if not isinstance(food, dict):
            continue
        fid = food.get("fdcId")
        if fid is not None:
            try:
                by_id[int(fid)] = food
            except (TypeError, ValueError):
                continue

    lines: list[str] = []
    for fid in ids:
        food = by_id.get(fid)
        if not food:
            lines.append(f"{fid}: (not found) — fail: food data unavailable")
            continue
        description = str(food.get("description") or "(no description)")
        haystack = _haystack(food)
        category = _category_string(food).lower()

        failure_reason: str | None = None
        for cat in exclude_categories:
            if cat and cat in category:
                failure_reason = f"excluded category '{cat}'"
                break
        if failure_reason is None:
            for keyword in exclude_keywords:
                if keyword and keyword in haystack:
                    failure_reason = f"contains '{keyword}'"
                    break

        if failure_reason:
            lines.append(f"{fid}: {description} — fail: {failure_reason}")
        else:
            lines.append(f"{fid}: {description} — pass")

    return create_text_response("\n".join(lines))
