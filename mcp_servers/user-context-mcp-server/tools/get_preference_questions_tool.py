from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from context_constants import PREFERENCE_QUESTIONS
from mcp_utilities import create_text_response


_VALID_FIELDS: list[str] = [q["field"] for q in PREFERENCE_QUESTIONS]


def _format_question(idx: int, entry: dict) -> str:
    line = f"  {idx}. [{entry['field']}] {entry['question']}"
    options = entry.get("options")
    if options:
        line += f"\n       Options: {', '.join(options)}"
    return line


async def get_preference_questions(
    missingFields: Annotated[  # noqa: N803
        list[str] | None,
        Field(
            description=(
                "Optional list of preference field names to filter on (e.g. ['cuisines', "
                "'dietPattern']). If omitted or empty, all questions are returned. Valid fields: "
                + ", ".join(_VALID_FIELDS)
                + "."
            )
        ),
    ] = None,
    ctx: Context = None,
) -> str:
    cleaned = [f.strip() for f in (missingFields or []) if f and f.strip()]

    if cleaned:
        unknown = [f for f in cleaned if f not in _VALID_FIELDS]
        if unknown:
            return create_text_response(
                f"Unknown preference field(s): {', '.join(unknown)}. "
                f"Valid fields: {', '.join(_VALID_FIELDS)}.",
                is_error=True,
            )
        wanted = set(cleaned)
        selected = [q for q in PREFERENCE_QUESTIONS if q["field"] in wanted]
    else:
        selected = list(PREFERENCE_QUESTIONS)

    if not selected:
        return create_text_response("No matching preference questions for the requested fields.")

    lines = [_format_question(i + 1, entry) for i, entry in enumerate(selected)]
    return create_text_response("\n".join(lines))
