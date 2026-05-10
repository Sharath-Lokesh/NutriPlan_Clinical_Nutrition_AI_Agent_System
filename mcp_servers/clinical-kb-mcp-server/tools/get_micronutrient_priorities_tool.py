from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_repository import repository
from mcp_utilities import create_text_response


def _format_emphasise(item: dict) -> str:
    nutrient = str(item.get("nutrient") or "(unknown nutrient)")
    rationale = str(item.get("rationale") or "")
    return f"  - {nutrient} - {rationale}" if rationale else f"  - {nutrient}"


def _format_limit(item: dict) -> str:
    nutrient = str(item.get("nutrient") or "(unknown nutrient)")
    rationale = str(item.get("rationale") or "")

    parts: list[str] = []
    max_mg = item.get("max_mg_per_day")
    max_mcg = item.get("max_mcg_per_day")
    max_pct = item.get("max_pct_kcal")

    if max_mg is not None:
        parts.append(f"max {max_mg} mg/day")
    if max_mcg is not None:
        parts.append(f"max {max_mcg} mcg/day")
    if max_pct is not None:
        parts.append(f"max {max_pct}% kcal")

    cap = ": " + ", ".join(parts) if parts else ""
    suffix = f" - {rationale}" if rationale else ""
    return f"  - {nutrient}{cap}{suffix}"


async def get_micronutrient_priorities(
    condition: Annotated[
        str,
        Field(description="Condition name or alias (e.g. 'CKD stage 4-5', 'pregnancy', 'coeliac disease')."),
    ],
    ctx: Context = None,
) -> str:
    if not condition or not condition.strip():
        return create_text_response("A non-empty 'condition' is required.", is_error=True)

    entry = repository.find_micro_priorities(condition)
    if entry is None:
        return create_text_response(f"No micronutrient priorities defined for {condition}.")

    emphasise = entry.get("emphasise") or []
    limit = entry.get("limit") or []
    source = entry.get("source") or "(no source on file)"

    lines: list[str] = []
    lines.append("Emphasise:")
    if isinstance(emphasise, list) and emphasise:
        for item in emphasise:
            if isinstance(item, dict):
                lines.append(_format_emphasise(item))
    else:
        lines.append("  (none specified)")

    lines.append("Limit:")
    if isinstance(limit, list) and limit:
        for item in limit:
            if isinstance(item, dict):
                lines.append(_format_limit(item))
    else:
        lines.append("  (none specified)")

    lines.append(f"Source: {source}")
    return create_text_response("\n".join(lines))
