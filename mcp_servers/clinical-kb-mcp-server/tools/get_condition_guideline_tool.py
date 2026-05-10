from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_repository import repository
from kb_utilities import format_guideline
from mcp_utilities import create_text_response


async def get_condition_guideline(
    condition: Annotated[
        str,
        Field(
            description=(
                "Condition name, alias, ICD-10 code, or SNOMED code (e.g. 'type 2 diabetes', "
                "'t2dm', 'E11', '44054006')."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not condition or not condition.strip():
        return create_text_response("A non-empty 'condition' is required.", is_error=True)

    guideline = repository.find_guideline(condition)
    if guideline is None:
        return create_text_response(f"No guideline found for {condition}.")

    return create_text_response(format_guideline(guideline))
