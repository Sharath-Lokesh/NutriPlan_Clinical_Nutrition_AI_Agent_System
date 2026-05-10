from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_repository import repository
from mcp_utilities import create_text_response


def _format_range(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list) and len(value) == 2:
        return f"{value[0]}-{value[1]}"
    return str(value)


async def get_macronutrient_ratios(
    key: Annotated[
        str,
        Field(
            description=(
                "Condition name or goal key (e.g. 'type 2 diabetes', 'weight_loss', "
                "'muscle_gain', 'endurance', 'maintenance', 'general_healthy')."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not key or not key.strip():
        return create_text_response("A non-empty 'key' is required.", is_error=True)

    ratio = repository.find_macro_ratios(key)
    if ratio is None:
        return create_text_response(f"No macronutrient guidance for {key}.")

    label = str(ratio.get("key") or key)
    lines: list[str] = [f"Macronutrient ratios for {label}:"]

    carbs = _format_range(ratio.get("carb_pct"))
    protein = _format_range(ratio.get("protein_pct"))
    fat = _format_range(ratio.get("fat_pct"))

    if carbs:
        lines.append(f"  Carbs: {carbs}% kcal")
    if protein:
        lines.append(f"  Protein: {protein}% kcal")
    if fat:
        lines.append(f"  Fat: {fat}% kcal")

    sat_max = ratio.get("saturated_fat_pct_max")
    if sat_max is not None:
        lines.append(f"  Saturated fat: <{sat_max}% kcal")

    fibre_min = ratio.get("fibre_g_per_1000_kcal_min")
    if fibre_min is not None:
        lines.append(f"  Fibre: >={fibre_min} g/1000 kcal")

    rationale = ratio.get("rationale")
    if rationale:
        lines.append(f"Rationale: {rationale}")

    source = ratio.get("source") or "(no source on file)"
    lines.append(f"Source: {source}")

    return create_text_response("\n".join(lines))
