from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_utilities import extract_nutrient_value, get_usda_context, iter_food_nutrients
from usda_client import UsdaClient


async def find_foods_by_nutrient(
    nutrientId: Annotated[  # noqa: N803
        int,
        Field(description="USDA nutrient ID, e.g. 1003 for Protein, 1079 for Fiber."),
    ],
    minAmount: Annotated[  # noqa: N803
        float | None,
        Field(description="Optional minimum nutrient amount per 100 g (inclusive)."),
    ] = None,
    maxAmount: Annotated[  # noqa: N803
        float | None,
        Field(description="Optional maximum nutrient amount per 100 g (inclusive)."),
    ] = None,
    query: Annotated[
        str | None,
        Field(description="Optional search term to scope results, e.g. 'vegetables' or 'beans'."),
    ] = None,
    pageSize: Annotated[  # noqa: N803
        int,
        Field(description="Max foods to scan from USDA search (capped at 50)."),
    ] = 20,
    ctx: Context = None,
) -> str:
    if not nutrientId or nutrientId <= 0:
        return create_text_response("A positive 'nutrientId' is required.", is_error=True)

    page_size = max(1, min(int(pageSize or 20), 50))
    search_query = (query or "").strip() or "food"

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)

	# Hardcode - as the agent was failing to pass this parameter
    if pageSize is None:
        pageSize = 20

    search_response = await client.search(
        search_query,
        page_size=page_size,
        data_type=["Foundation", "SR Legacy"],
    )
    foods = (search_response or {}).get("foods") or []
    fdc_ids: list[int] = []
    for food in foods:
        if not isinstance(food, dict):
            continue
        fid = food.get("fdcId")
        if fid is None:
            continue
        try:
            fdc_ids.append(int(fid))
        except (TypeError, ValueError):
            continue

    if not fdc_ids:
        return create_text_response("No foods match the nutrient criteria.")

    full_foods = await client.get_foods(fdc_ids, format="full") or []

    matches: list[tuple[float, str, str, int]] = []
    for food in full_foods:
        if not isinstance(food, dict):
            continue
        food_nutrients = iter_food_nutrients(food)
        amount = extract_nutrient_value(food_nutrients, int(nutrientId))
        if amount is None:
            continue
        if minAmount is not None and amount < float(minAmount):
            continue
        if maxAmount is not None and amount > float(maxAmount):
            continue
        unit = ""
        for entry in food_nutrients:
            if not isinstance(entry, dict):
                continue
            nutrient = entry.get("nutrient") or {}
            nid = nutrient.get("id") or entry.get("nutrientId")
            try:
                nid_int = int(nid) if nid is not None else None
            except (TypeError, ValueError):
                nid_int = None
            if nid_int == int(nutrientId):
                unit = str(nutrient.get("unitName") or entry.get("unitName") or "").lower()
                break
        description = str(food.get("description") or "(no description)")
        try:
            fid = int(food.get("fdcId"))
        except (TypeError, ValueError):
            continue
        matches.append((amount, description, unit, fid))

    if not matches:
        return create_text_response("No foods match the nutrient criteria.")

    matches.sort(key=lambda m: m[0], reverse=True)
    lines = [
        f"{description}: {amount} {unit} (fdcId: {fid})".rstrip()
        for amount, description, unit, fid in matches
    ]
    return create_text_response("\n".join(lines))
