from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_constants import ACTIVITY_FACTORS, GOAL_ADJUSTMENTS
from kb_utilities import mifflin_st_jeor
from mcp_utilities import create_text_response


def _round_to_50(value: float) -> int:
    return int(round(value / 50.0) * 50)


async def calculate_caloric_target(
    sex: Annotated[
        str,
        Field(description="Biological sex: 'male' or 'female'."),
    ],
    weightKg: Annotated[  # noqa: N803
        float,
        Field(description="Body weight in kilograms."),
    ],
    heightCm: Annotated[  # noqa: N803
        float,
        Field(description="Height in centimetres."),
    ],
    age: Annotated[
        int,
        Field(description="Age in years (integer)."),
    ],
    activityLevel: Annotated[  # noqa: N803
        str,
        Field(
            description=(
                "Activity level. One of: sedentary, light, moderate, active, very_active."
            )
        ),
    ],
    goal: Annotated[
        str,
        Field(
            description=(
                "Goal for caloric adjustment. One of: weight_loss, mild_weight_loss, "
                "maintenance, mild_weight_gain, weight_gain. Defaults to 'maintenance'."
            )
        ),
    ] = "maintenance",
    ctx: Context = None,
) -> str:
    sex_norm = (sex or "").strip().lower()
    if sex_norm not in {"male", "female"}:
        return create_text_response(
            "'sex' must be either 'male' or 'female'.", is_error=True
        )

    try:
        weight_kg = float(weightKg)
        height_cm = float(heightCm)
    except (TypeError, ValueError):
        return create_text_response(
            "'weightKg' and 'heightCm' must be numeric.", is_error=True
        )

    if weight_kg <= 0 or height_cm <= 0:
        return create_text_response(
            "'weightKg' and 'heightCm' must be positive.", is_error=True
        )

    if not isinstance(age, int) or age < 0 or age > 120:
        return create_text_response(
            "'age' must be an integer between 0 and 120.", is_error=True
        )

    activity_norm = (activityLevel or "").strip().lower()
    if activity_norm not in ACTIVITY_FACTORS:
        return create_text_response(
            f"'activityLevel' must be one of: {sorted(ACTIVITY_FACTORS.keys())}.",
            is_error=True,
        )

    goal_norm = (goal or "maintenance").strip().lower()
    if goal_norm not in GOAL_ADJUSTMENTS:
        return create_text_response(
            f"'goal' must be one of: {sorted(GOAL_ADJUSTMENTS.keys())}.",
            is_error=True,
        )

    bmr = mifflin_st_jeor(sex_norm, weight_kg, height_cm, age)
    tdee = bmr * ACTIVITY_FACTORS[activity_norm]
    target = tdee + GOAL_ADJUSTMENTS[goal_norm]

    bmr_rounded = _round_to_50(bmr)
    tdee_rounded = _round_to_50(tdee)
    target_rounded = _round_to_50(target)

    return create_text_response(
        f"BMR: {bmr_rounded} kcal/day; TDEE: {tdee_rounded} kcal/day; "
        f"Target ({goal_norm}): {target_rounded} kcal/day (Mifflin-St Jeor)"
    )
