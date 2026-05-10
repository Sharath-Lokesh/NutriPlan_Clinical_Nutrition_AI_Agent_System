from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from interaction_constants import SEVERITY_LEVELS, SEVERITY_RANK
from interaction_repository import repository
from interaction_utilities import format_interaction, sort_by_severity
from mcp_utilities import create_text_response


async def get_interactions_for_drug(
    drug: Annotated[
        str,
        Field(
            description=(
                "Drug name, brand alias, RxNorm code, or drug class to fetch interactions for."
            )
        ),
    ],
    minSeverity: Annotated[  # noqa: N803
        str,
        Field(
            description=(
                "Minimum severity to include. One of: contraindicated, significant, "
                "moderate, advisory. Defaults to 'advisory' (returns everything)."
            )
        ),
    ] = "advisory",
    ctx: Context = None,
) -> str:
    if not drug or not drug.strip():
        return create_text_response("A non-empty 'drug' is required.", is_error=True)

    threshold_label = (minSeverity or "advisory").strip().lower()
    if threshold_label not in SEVERITY_LEVELS:
        return create_text_response(
            f"'minSeverity' must be one of: {SEVERITY_LEVELS}.", is_error=True
        )
    threshold_rank = SEVERITY_RANK[threshold_label]

    matches = repository.find_by_drug(drug)
    filtered = [
        i
        for i in matches
        if SEVERITY_RANK.get(str(i.get("severity") or ""), 0) >= threshold_rank
    ]

    if not filtered:
        return create_text_response(
            f"No known food or nutrient interactions for {drug}."
        )

    ordered = sort_by_severity(filtered)
    blocks = [format_interaction(item) for item in ordered]
    return create_text_response("\n---\n".join(blocks))
