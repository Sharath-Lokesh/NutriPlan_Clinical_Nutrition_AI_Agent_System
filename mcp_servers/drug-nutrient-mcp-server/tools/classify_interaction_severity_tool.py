from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from interaction_repository import repository
from interaction_utilities import highest_severity
from mcp_utilities import create_text_response


def _brief(text: str, max_len: int = 200) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return f"{truncated}..."


async def classify_interaction_severity(
    drug: Annotated[
        str,
        Field(description="Drug name, alias, RxNorm code, or drug class."),
    ],
    food: Annotated[
        str,
        Field(description="Food or nutrient to assess."),
    ],
    ctx: Context = None,
) -> str:
    if not drug or not drug.strip():
        return create_text_response("A non-empty 'drug' is required.", is_error=True)
    if not food or not food.strip():
        return create_text_response("A non-empty 'food' is required.", is_error=True)

    matches = repository.find_by_drug_and_food(drug, food)
    if not matches:
        return create_text_response("No known interaction; severity: none.")

    top_severity = highest_severity(matches)
    chosen: dict = matches[0]
    if top_severity is not None:
        for interaction in matches:
            if str(interaction.get("severity") or "") == top_severity:
                chosen = interaction
                break

    severity = str(chosen.get("severity") or "unspecified")
    mechanism_brief = _brief(str(chosen.get("mechanism") or ""))
    source = str(chosen.get("evidence_source") or "(no source on file)")

    return create_text_response(f"{severity}: {mechanism_brief} Source: {source}")
