from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_repository import repository
from mcp_utilities import create_text_response


async def get_hard_exclusions(
    condition: Annotated[
        str,
        Field(
            description=(
                "Condition or therapy name (e.g. 'coeliac disease', 'PKU', 'pregnancy', "
                "'MAOI therapy', 'shellfish allergy')."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not condition or not condition.strip():
        return create_text_response("A non-empty 'condition' is required.", is_error=True)

    entry = repository.find_hard_exclusions(condition)
    if entry is None:
        return create_text_response(f"No hard exclusions defined for {condition}.")

    label = str(entry.get("condition") or condition)
    is_absolute = bool(entry.get("absolute"))
    severity_label = "absolute" if is_absolute else "strong avoidance"

    keywords = entry.get("exclude_keywords") or []
    categories = entry.get("exclude_categories") or []
    rationale = entry.get("rationale") or ""
    source = entry.get("evidence_source") or "(no source on file)"

    lines: list[str] = [f"Hard exclusions for {label} [{severity_label}]:"]

    if isinstance(keywords, list) and keywords:
        lines.append("  Keywords: " + ", ".join(str(k) for k in keywords))
    else:
        lines.append("  Keywords: (none)")

    if isinstance(categories, list) and categories:
        lines.append("  Categories: " + ", ".join(str(c) for c in categories))
    else:
        lines.append("  Categories: (none)")

    if rationale:
        lines.append(f"Rationale: {rationale}")
    lines.append(f"Source: {source}")

    return create_text_response("\n".join(lines))
