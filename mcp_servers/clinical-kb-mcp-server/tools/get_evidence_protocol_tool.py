from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_repository import repository
from mcp_utilities import create_text_response


def _format_range(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list) and len(value) == 2:
        return f"{value[0]}-{value[1]}%"
    return str(value)


async def get_evidence_protocol(
    name: Annotated[
        str,
        Field(
            description=(
                "Protocol name (e.g. 'Mediterranean', 'DASH', 'low-FODMAP', 'renal-friendly', "
                "'gluten-free', 'low-sodium', 'low-glycaemic', 'ketogenic', 'MIND', 'plant-based')."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not name or not name.strip():
        return create_text_response("A non-empty 'name' is required.", is_error=True)

    protocol = repository.find_protocol(name)
    if protocol is None:
        available = [str(p.get("name") or "") for p in repository.all_protocols()]
        available_label = ", ".join(a for a in available if a)
        return create_text_response(
            f"No evidence protocol named {name}. Available: {available_label}."
        )

    label = str(protocol.get("name") or name)
    description = str(protocol.get("description") or "(no description on file)")
    indications = protocol.get("indications") or []
    components = protocol.get("core_components") or []
    macro = protocol.get("macro_ratio") or {}
    grade = str(protocol.get("evidence_grade") or "(ungraded)")
    trials = protocol.get("key_trials") or []
    source = str(protocol.get("source") or "(no source on file)")

    lines: list[str] = [f"{label} diet"]
    lines.append(f"  Description: {description}")

    if isinstance(indications, list) and indications:
        lines.append("  Indications: " + ", ".join(str(i) for i in indications))

    if isinstance(components, list) and components:
        lines.append("  Core components:")
        for component in components:
            lines.append(f"    - {component}")

    if isinstance(macro, dict) and macro:
        carbs = _format_range(macro.get("carb_pct"))
        protein = _format_range(macro.get("protein_pct"))
        fat = _format_range(macro.get("fat_pct"))
        macro_parts: list[str] = []
        if carbs:
            macro_parts.append(f"carbs {carbs}")
        if protein:
            macro_parts.append(f"protein {protein}")
        if fat:
            macro_parts.append(f"fat {fat}")
        if macro_parts:
            lines.append("  Macro ratio: " + ", ".join(macro_parts))

    lines.append(f"  Evidence grade: {grade}")

    if isinstance(trials, list) and trials:
        lines.append("  Key trials: " + ", ".join(str(t) for t in trials))

    lines.append(f"  Source: {source}")

    return create_text_response("\n".join(lines))
