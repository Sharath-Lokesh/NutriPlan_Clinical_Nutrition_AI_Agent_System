from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from context_constants import (
    COOKING_SKILLS,
    DIET_PATTERNS,
)
from context_utilities import (
    find_cultural_pattern,
    validate_choice,
    validate_taste_profile,
)
from mcp_utilities import create_text_response


def _format_taste_profile(profile: dict[str, str]) -> str:
    return ", ".join(f"{dim}={level}" for dim, level in profile.items())


def _format_list(values: list[str]) -> str:
    return ", ".join(v.strip() for v in values if v and v.strip())


async def build_preference_profile(
    cuisines: Annotated[  # noqa: N803
        list[str] | None,
        Field(description="Cuisines the patient enjoys (e.g. ['italian', 'japanese', 'mexican'])."),
    ] = None,
    dislikes: Annotated[  # noqa: N803
        list[str] | None,
        Field(description="Foods or ingredients the patient dislikes or wants to avoid."),
    ] = None,
    tasteProfile: Annotated[  # noqa: N803
        dict[str, str] | None,
        Field(
            description=(
                "Taste preferences as a map. Keys must be in "
                "[sweet, salty, spicy, umami, bitter, sour]; values must be in [low, medium, high]."
            )
        ),
    ] = None,
    cookingSkill: Annotated[  # noqa: N803
        str | None,
        Field(description="Cooking skill level: novice, intermediate, or advanced."),
    ] = None,
    equipment: Annotated[  # noqa: N803
        list[str] | None,
        Field(description="Kitchen equipment available (e.g. ['oven', 'blender', 'instant pot'])."),
    ] = None,
    dietPattern: Annotated[  # noqa: N803
        str | None,
        Field(
            description=(
                "Diet pattern: vegan, vegetarian, omnivore, pescatarian, halal, kosher, or none."
            )
        ),
    ] = None,
    culturalKey: Annotated[  # noqa: N803
        str | None,
        Field(
            description=(
                "Cultural pattern key or alias to fold staples + spices into the profile "
                "(e.g. 'south_asian', 'indian', 'mediterranean')."
            )
        ),
    ] = None,
    budgetNote: Annotated[  # noqa: N803
        str | None,
        Field(description="Free-text budget constraints (e.g. 'groceries under $80/week')."),
    ] = None,
    scheduleNote: Annotated[  # noqa: N803
        str | None,
        Field(description="Free-text schedule constraints (e.g. 'limited weekday cooking')."),
    ] = None,
    fastingNote: Annotated[  # noqa: N803
        str | None,
        Field(description="Free-text fasting practices to respect (e.g. 'Ramadan', 'Lent')."),
    ] = None,
    ctx: Context = None,
) -> str:
    if cookingSkill is not None and cookingSkill != "":
        try:
            validate_choice(cookingSkill, COOKING_SKILLS, "cookingSkill")
        except ValueError as exc:
            return create_text_response(str(exc), is_error=True)

    if dietPattern is not None and dietPattern != "":
        try:
            validate_choice(dietPattern, DIET_PATTERNS, "dietPattern")
        except ValueError as exc:
            return create_text_response(str(exc), is_error=True)

    if tasteProfile:
        try:
            validate_taste_profile(tasteProfile)
        except ValueError as exc:
            return create_text_response(str(exc), is_error=True)

    cleaned_cuisines = [c for c in (cuisines or []) if c and c.strip()]
    cleaned_dislikes = [d for d in (dislikes or []) if d and d.strip()]
    cleaned_equipment = [e for e in (equipment or []) if e and e.strip()]
    cleaned_taste = {k: v for k, v in (tasteProfile or {}).items() if k and v}
    cleaned_cooking = (cookingSkill or "").strip()
    cleaned_diet = (dietPattern or "").strip()
    cleaned_budget = (budgetNote or "").strip()
    cleaned_schedule = (scheduleNote or "").strip()
    cleaned_fasting = (fastingNote or "").strip()
    cleaned_cultural_key = (culturalKey or "").strip()

    cultural_pattern: dict | None = None
    if cleaned_cultural_key:
        cultural_pattern = find_cultural_pattern(cleaned_cultural_key)

    has_any = any(
        [
            cleaned_cuisines,
            cleaned_dislikes,
            cleaned_taste,
            cleaned_cooking,
            cleaned_equipment,
            cleaned_diet,
            cultural_pattern,
            cleaned_budget,
            cleaned_schedule,
            cleaned_fasting,
        ]
    )

    if not has_any:
        return create_text_response(
            "Preference Profile: no preferences supplied. Call GetPreferenceQuestions to gather them."
        )

    lines: list[str] = ["Preference Profile"]

    if cleaned_cuisines:
        lines.append(f"  Cuisines: {_format_list(cleaned_cuisines)}")
    if cleaned_dislikes:
        lines.append(f"  Dislikes: {_format_list(cleaned_dislikes)}")
    if cleaned_taste:
        lines.append(f"  Taste profile: {_format_taste_profile(cleaned_taste)}")
    if cleaned_diet:
        lines.append(f"  Diet pattern: {cleaned_diet}")
    if cleaned_cooking:
        lines.append(f"  Cooking skill: {cleaned_cooking}")
    if cleaned_equipment:
        lines.append(f"  Equipment: {_format_list(cleaned_equipment)}")
    if cultural_pattern:
        key = cultural_pattern.get("key", cleaned_cultural_key)
        lines.append(f"  Cultural context ({key}):")
        staples = cultural_pattern.get("staples") or []
        spices = cultural_pattern.get("common_spices") or []
        if staples:
            lines.append(f"    Staples: {_format_list(staples)}")
        if spices:
            lines.append(f"    Common spices: {_format_list(spices)}")
    if cleaned_budget:
        lines.append(f"  Budget: {cleaned_budget}")
    if cleaned_schedule:
        lines.append(f"  Schedule: {cleaned_schedule}")
    if cleaned_fasting:
        lines.append(f"  Fasting: {cleaned_fasting}")

    return create_text_response("\n".join(lines))
