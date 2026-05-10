from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_constants import ALLERGEN_KEYWORDS
from nutrition_utilities import get_usda_context
from usda_client import UsdaClient


def _haystack(food: dict) -> str:
    parts: list[str] = []
    description = food.get("description")
    if description:
        parts.append(str(description))
    ingredients = food.get("ingredients")
    if ingredients:
        parts.append(str(ingredients))
    food_category = food.get("foodCategory")
    if isinstance(food_category, dict):
        cat_desc = food_category.get("description")
        if cat_desc:
            parts.append(str(cat_desc))
    elif isinstance(food_category, str):
        parts.append(food_category)
    food_attributes = food.get("foodAttributes") or []
    for attr in food_attributes:
        if not isinstance(attr, dict):
            continue
        value = attr.get("value")
        if value:
            parts.append(str(value))
        name = attr.get("name")
        if name:
            parts.append(str(name))
    label_nutrients = food.get("labelNutrients")
    if isinstance(label_nutrients, dict):
        parts.append(" ".join(label_nutrients.keys()))
    return " ".join(parts).lower()


async def get_food_allergens(
    fdcId: Annotated[  # noqa: N803
        int,
        Field(description="USDA FoodData Central FDC ID."),
    ],
    ctx: Context = None,
) -> str:
    if not fdcId or fdcId <= 0:
        return create_text_response("A positive 'fdcId' is required.", is_error=True)

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)

    food = await client.get_food(int(fdcId), format="full")
    if not food:
        return create_text_response("Food not found.", is_error=True)

    haystack = _haystack(food)
    detected: list[str] = []
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in haystack:
                detected.append(allergen)
                break

    if not detected:
        return create_text_response(
            "No Big-8 allergens detected (note: ingredient list may be incomplete for non-branded foods)."
        )

    return create_text_response("Contains: " + ", ".join(sorted(set(detected))))
