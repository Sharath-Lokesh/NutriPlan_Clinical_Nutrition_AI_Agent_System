from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from interaction_constants import SEVERITY_RANK
from interaction_repository import repository
from mcp_utilities import create_text_response


def _pick_substitution(interaction: dict, ingredient: str) -> str:
    substitutions = interaction.get("substitutions") or []
    if not isinstance(substitutions, list):
        return "None available"

    target = (ingredient or "").lower()
    for sub in substitutions:
        if not isinstance(sub, dict):
            continue
        replace = str(sub.get("replace") or "").strip().lower()
        with_ = str(sub.get("with") or "").strip()
        if with_ and replace and (target in replace or replace in target):
            return with_

    for sub in substitutions:
        if not isinstance(sub, dict):
            continue
        with_ = str(sub.get("with") or "").strip()
        if with_:
            return with_

    return "None available"


def _format_pair(medication: str, ingredient: str, interaction: dict) -> str:
    severity = str(interaction.get("severity") or "unspecified").upper()
    mechanism = str(interaction.get("mechanism") or "(no mechanism on file)")
    recommendation = str(interaction.get("recommendation") or "(no recommendation on file)")
    substitution_text = _pick_substitution(interaction, ingredient)

    return (
        f"[{severity}] {medication} x {ingredient}\n"
        f"  Mechanism: {mechanism}\n"
        f"  Recommendation: {recommendation}\n"
        f"  Suggested substitution: {substitution_text}"
    )


async def check_meal_plan_interactions(
    medications: Annotated[
        list[str],
        Field(description="List of medication names, aliases, RxNorm codes, or drug classes."),
    ],
    ingredients: Annotated[
        list[str],
        Field(description="List of foods or nutrients in the meal plan."),
    ],
    ctx: Context = None,
) -> str:
    if not medications:
        return create_text_response(
            "'medications' must be a non-empty list.", is_error=True
        )
    if not ingredients:
        return create_text_response(
            "'ingredients' must be a non-empty list.", is_error=True
        )

    flagged: list[tuple[str, str, dict]] = []
    seen: set[str] = set()
    for medication in medications:
        if not isinstance(medication, str) or not medication.strip():
            continue
        for ingredient in ingredients:
            if not isinstance(ingredient, str) or not ingredient.strip():
                continue
            matches = repository.find_by_drug_and_food(medication, ingredient)
            for match in matches:
                key = f"{medication.lower()}|{ingredient.lower()}|{match.get('id', '')}"
                if key in seen:
                    continue
                seen.add(key)
                flagged.append((medication, ingredient, match))

    if not flagged:
        return create_text_response("No interactions detected across the meal plan.")

    flagged.sort(
        key=lambda triple: SEVERITY_RANK.get(str(triple[2].get("severity") or ""), 0),
        reverse=True,
    )

    blocks = [_format_pair(med, ing, interaction) for med, ing, interaction in flagged]
    return create_text_response("\n---\n".join(blocks))
