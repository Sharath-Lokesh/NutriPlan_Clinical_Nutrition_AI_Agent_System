from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_utilities import extract_nutrient_value, get_usda_context, iter_food_nutrients
from usda_client import UsdaClient


def _category_string(food: dict) -> str:
    food_category = food.get("foodCategory")
    if isinstance(food_category, dict):
        return str(food_category.get("description") or "")
    if isinstance(food_category, str):
        return food_category
    return ""


def _haystack(food: dict) -> str:
    parts: list[str] = []
    if food.get("description"):
        parts.append(str(food["description"]))
    if food.get("ingredients"):
        parts.append(str(food["ingredients"]))
    parts.append(_category_string(food))
    return " ".join(parts).lower()


def _unit_for_nutrient(food_nutrients: list[dict], nutrient_id: int) -> str:
    for entry in food_nutrients:
        if not isinstance(entry, dict):
            continue
        nutrient = entry.get("nutrient") or {}
        nid = nutrient.get("id") or entry.get("nutrientId")
        try:
            nid_int = int(nid) if nid is not None else None
        except (TypeError, ValueError):
            nid_int = None
        if nid_int == nutrient_id:
            return str(nutrient.get("unitName") or entry.get("unitName") or "").lower()
    return ""


def _nutrient_name(food_nutrients: list[dict], nutrient_id: int) -> str:
    for entry in food_nutrients:
        if not isinstance(entry, dict):
            continue
        nutrient = entry.get("nutrient") or {}
        nid = nutrient.get("id") or entry.get("nutrientId")
        try:
            nid_int = int(nid) if nid is not None else None
        except (TypeError, ValueError):
            nid_int = None
        if nid_int == nutrient_id:
            return str(nutrient.get("name") or entry.get("nutrientName") or f"Nutrient {nutrient_id}")
    return f"Nutrient {nutrient_id}"


async def suggest_food_substitute(
    fdcId: Annotated[  # noqa: N803
        int,
        Field(description="USDA FDC ID of the food to substitute."),
    ],
    targetNutrientId: Annotated[  # noqa: N803
        int | None,
        Field(
            description=(
                "Optional USDA nutrient ID to match. Substitutes are ranked by closeness "
                "to the original food's amount of this nutrient (within ±20%)."
            )
        ),
    ] = None,
    excludeKeywords: Annotated[  # noqa: N803
        list[str] | None,
        Field(description="Optional list of keywords; substitutes containing any are excluded."),
    ] = None,
    pageSize: Annotated[  # noqa: N803
        int,
        Field(description="Max candidate foods to scan from USDA search (capped at 50)."),
    ] = 10,
    ctx: Context = None,
) -> str:
    if not fdcId or fdcId <= 0:
        return create_text_response("A positive 'fdcId' is required.", is_error=True)
    # Hardcode - as the agent was failing to pass this parameter
    if pageSize is None:
        pageSize = 10
    page_size = max(1, min(int(pageSize or 10), 50))
    excludes = [str(k).lower() for k in (excludeKeywords or []) if k]

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)

    original = await client.get_food(int(fdcId), format="full")
    if not original:
        return create_text_response("Original food not found.", is_error=True)

    original_category = _category_string(original)
    original_description = str(original.get("description") or "")
    target_amount: float | None = None
    if targetNutrientId is not None:
        target_amount = extract_nutrient_value(
            iter_food_nutrients(original), int(targetNutrientId)
        )

    search_term = original_category or original_description.split(",")[0] or "food"
    search_response = await client.search(
        search_term,
        page_size=page_size,
        data_type=["Foundation", "SR Legacy"],
    )
    candidates = (search_response or {}).get("foods") or []
    candidate_ids: list[int] = []
    for food in candidates:
        if not isinstance(food, dict):
            continue
        cid = food.get("fdcId")
        if cid is None:
            continue
        try:
            cid_int = int(cid)
        except (TypeError, ValueError):
            continue
        if cid_int == int(fdcId):
            continue
        candidate_ids.append(cid_int)

    if not candidate_ids:
        return create_text_response("No suitable substitute found.")

    full_candidates = await client.get_foods(candidate_ids, format="full") or []

    ranked: list[tuple[float, str, int, float | None, str]] = []
    for food in full_candidates:
        if not isinstance(food, dict):
            continue
        haystack = _haystack(food)
        if any(kw in haystack for kw in excludes):
            continue
        if original_category:
            cand_category = _category_string(food).lower()
            if original_category.lower() not in cand_category and cand_category not in original_category.lower():
                continue
        food_nutrients = iter_food_nutrients(food)
        amount: float | None = None
        unit = ""
        diff_score = 0.0
        if targetNutrientId is not None:
            amount = extract_nutrient_value(food_nutrients, int(targetNutrientId))
            if amount is None:
                continue
            unit = _unit_for_nutrient(food_nutrients, int(targetNutrientId))
            if target_amount is not None and target_amount > 0:
                pct_diff = abs(amount - target_amount) / target_amount
                if pct_diff > 0.20:
                    continue
                diff_score = pct_diff
            else:
                diff_score = abs(amount)
        try:
            cand_fid = int(food.get("fdcId"))
        except (TypeError, ValueError):
            continue
        cand_desc = str(food.get("description") or "(no description)")
        ranked.append((diff_score, cand_desc, cand_fid, amount, unit))

    if not ranked:
        return create_text_response("No suitable substitute found.")

    ranked.sort(key=lambda r: r[0])

    nutrient_label = ""
    if targetNutrientId is not None:
        nutrient_label = _nutrient_name(
            iter_food_nutrients(original), int(targetNutrientId)
        )

    lines: list[str] = []
    for diff_score, description, cand_fid, amount, unit in ranked:
        if targetNutrientId is not None and amount is not None:
            if target_amount and target_amount > 0:
                pct = (amount - target_amount) / target_amount * 100.0
                pct_str = f"{pct:+.1f}%"
            else:
                pct_str = "n/a"
            lines.append(
                f"{cand_fid}: {description} ({nutrient_label}: {amount} {unit}, {pct_str})".rstrip()
            )
        else:
            lines.append(f"{cand_fid}: {description}")

    return create_text_response("\n".join(lines))
