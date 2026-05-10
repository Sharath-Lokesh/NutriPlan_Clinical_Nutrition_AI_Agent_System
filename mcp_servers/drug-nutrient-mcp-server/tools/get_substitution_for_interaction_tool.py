from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from interaction_repository import repository
from mcp_utilities import create_text_response


async def get_substitution_for_interaction(
    drug: Annotated[
        str,
        Field(description="Drug name, alias, RxNorm code, or drug class."),
    ],
    food: Annotated[
        str,
        Field(description="Food or nutrient causing the interaction."),
    ],
    ctx: Context = None,
) -> str:
    if not drug or not drug.strip():
        return create_text_response("A non-empty 'drug' is required.", is_error=True)
    if not food or not food.strip():
        return create_text_response("A non-empty 'food' is required.", is_error=True)

    matches = repository.find_by_drug_and_food(drug, food)
    if not matches:
        return create_text_response("No interaction found; no substitution needed.")

    suggestions: list[str] = []
    seen: set[str] = set()
    for interaction in matches:
        substitutions = interaction.get("substitutions") or []
        if not isinstance(substitutions, list):
            continue
        for sub in substitutions:
            if not isinstance(sub, dict):
                continue
            replace = str(sub.get("replace") or "").strip()
            with_ = str(sub.get("with") or "").strip()
            rationale = str(sub.get("rationale") or "").strip()
            if not replace or not with_:
                continue
            key = f"{replace.lower()}|{with_.lower()}"
            if key in seen:
                continue
            seen.add(key)
            if rationale:
                suggestions.append(f"Replace {replace} with {with_} - {rationale}")
            else:
                suggestions.append(f"Replace {replace} with {with_}")

    if not suggestions:
        return create_text_response(
            "Interaction noted but no curated substitution available. Consult a clinician."
        )

    return create_text_response("\n".join(suggestions))
