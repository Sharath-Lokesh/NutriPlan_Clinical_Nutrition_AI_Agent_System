from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_constants import CURATED_NUTRIENT_PANEL
from nutrition_utilities import (
    format_nutrient_panel,
    get_usda_context,
    iter_food_nutrients,
)
from usda_client import UsdaClient


async def get_food_nutrients(
    fdcId: Annotated[  # noqa: N803
        int,
        Field(description="USDA FoodData Central FDC ID."),
    ],
    nutrientIds: Annotated[  # noqa: N803
        list[int] | None,
        Field(
            description=(
                "Optional list of USDA nutrient IDs to return. If omitted, a curated "
                "macro+micro panel is returned."
            )
        ),
    ] = None,
    ctx: Context = None,
) -> str:
    if not fdcId or fdcId <= 0:
        return create_text_response("A positive 'fdcId' is required.", is_error=True)

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)

    food = await client.get_food(int(fdcId), format="full")
    if not food:
        return create_text_response("Food not found.", is_error=True)

    food_nutrients = iter_food_nutrients(food)

    if nutrientIds:
        wanted = {int(n) for n in nutrientIds}
        parts: list[str] = []
        for entry in food_nutrients:
            if not isinstance(entry, dict):
                continue
            nutrient = entry.get("nutrient") or {}
            nid = nutrient.get("id") or entry.get("nutrientId")
            try:
                nid_int = int(nid) if nid is not None else None
            except (TypeError, ValueError):
                nid_int = None
            if nid_int is None or nid_int not in wanted:
                continue
            name = nutrient.get("name") or entry.get("nutrientName") or f"Nutrient {nid_int}"
            unit = nutrient.get("unitName") or entry.get("unitName") or ""
            amount = entry.get("amount")
            if amount is None:
                amount = entry.get("value")
            if amount is None:
                continue
            parts.append(f"{name}: {amount} {unit}".rstrip())
        if not parts:
            return create_text_response(
                "None of the requested nutrient IDs are present on this food."
            )
        return create_text_response("; ".join(parts))

    description = food.get("description") or f"FDC {fdcId}"
    panel = format_nutrient_panel(food_nutrients)
    _ = CURATED_NUTRIENT_PANEL  # intentional reference to silence unused-import warnings
    return create_text_response(f"{description} (per 100 g) — {panel}")
