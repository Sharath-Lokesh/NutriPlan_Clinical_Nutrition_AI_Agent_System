from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from interaction_repository import repository
from interaction_utilities import format_interaction, sort_by_severity
from mcp_utilities import create_text_response


async def check_drug_food_interaction(
    drug: Annotated[
        str,
        Field(
            description=(
                "Drug name, brand alias, RxNorm code, or drug class to check (e.g. "
                "'warfarin', 'coumadin', '11289', 'statin')."
            )
        ),
    ],
    food: Annotated[
        str,
        Field(
            description=(
                "Food name or nutrient to check (e.g. 'kale', 'grapefruit', 'vitamin K', "
                "'tyramine')."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not drug or not drug.strip():
        return create_text_response("A non-empty 'drug' is required.", is_error=True)
    if not food or not food.strip():
        return create_text_response("A non-empty 'food' is required.", is_error=True)

    matches = repository.find_by_drug_and_food(drug, food)
    if not matches:
        return create_text_response(
            f"No known interaction between {drug} and {food}."
        )

    ordered = sort_by_severity(matches)
    blocks = [format_interaction(item) for item in ordered]
    return create_text_response("\n---\n".join(blocks))
