from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_utilities import get_usda_context
from usda_client import UsdaClient


async def get_serving_sizes(
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

    portions = food.get("foodPortions") or []
    descriptions: list[str] = []
    for portion in portions:
        if not isinstance(portion, dict):
            continue
        amount = portion.get("amount")
        gram_weight = portion.get("gramWeight")
        modifier = portion.get("modifier") or ""
        portion_description = portion.get("portionDescription") or ""
        measure_unit = portion.get("measureUnit") or {}
        unit_name = ""
        if isinstance(measure_unit, dict):
            unit_name = measure_unit.get("name") or ""

        label_parts: list[str] = []
        if portion_description and portion_description.lower() != "undetermined":
            label_parts.append(str(portion_description))
        else:
            if amount is not None:
                label_parts.append(str(amount))
            if unit_name and unit_name.lower() != "undetermined":
                label_parts.append(unit_name)
            if modifier:
                label_parts.append(modifier)
        label = " ".join(p for p in label_parts if p).strip() or "(serving)"
        if gram_weight is not None:
            descriptions.append(f"{label} ({gram_weight} g)")
        else:
            descriptions.append(label)

    descriptions.append("100 g (default reference)")

    if len(descriptions) == 1:
        return create_text_response("Only 100 g reference available.")

    return create_text_response("; ".join(descriptions))
