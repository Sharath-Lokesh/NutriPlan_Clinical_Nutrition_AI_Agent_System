from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_utilities import get_usda_context
from usda_client import UsdaClient


async def search_food(
    query: Annotated[
        str,
        Field(description="Natural language search term, e.g. 'chicken breast' or 'oat milk'."),
    ],
    dataType: Annotated[  # noqa: N803
        list[str] | None,
        Field(
            description=(
                "USDA data types to search. One or more of 'Foundation', 'SR Legacy', "
                "'Survey (FNDDS)', 'Branded'. Defaults to ['Foundation', 'SR Legacy']."
            )
        ),
    ] = None,
    pageSize: Annotated[  # noqa: N803
        int,
        Field(description="Maximum number of results to return (1-50)."),
    ] = 10,
    ctx: Context = None,
) -> str:
    if not query or not query.strip():
        return create_text_response("A non-empty 'query' is required.", is_error=True)

    if dataType is None:
        dataType = ["Foundation", "SR Legacy"]
    # Hardcode - as the agent was failing to pass this parameter
    if pageSize is None:
        pageSize = 10
    page_size = max(1, min(int(pageSize or 10), 50))

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)

    response = await client.search(query, page_size=page_size, data_type=dataType)
    foods = (response or {}).get("foods") or []
    if not foods:
        return create_text_response("No foods found for query.")

    lines: list[str] = []
    for food in foods:
        if not isinstance(food, dict):
            continue
        fdc_id = food.get("fdcId")
        description = food.get("description") or "(no description)"
        food_data_type = food.get("dataType") or "Unknown"
        brand = food.get("brandOwner")
        suffix = f" — {brand}" if brand else ""
        lines.append(f"{fdc_id}: {description} [{food_data_type}]{suffix}")

    if not lines:
        return create_text_response("No foods found for query.")

    return create_text_response("\n".join(lines))
