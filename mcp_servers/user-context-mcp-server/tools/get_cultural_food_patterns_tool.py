from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from context_utilities import all_pattern_keys, find_cultural_pattern
from mcp_utilities import create_text_response


def _format_list(values: list[str]) -> str:
    return ", ".join(v for v in values if v)


async def get_cultural_food_patterns(
    culturalKey: Annotated[  # noqa: N803
        str,
        Field(
            description=(
                "Cultural pattern key or alias (e.g. 'south_asian', 'indian', 'mediterranean', "
                "'east_asian'). Matching is case-insensitive."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not culturalKey or not culturalKey.strip():
        return create_text_response("A non-empty 'culturalKey' is required.", is_error=True)

    pattern = find_cultural_pattern(culturalKey)
    if pattern is None:
        keys = ", ".join(all_pattern_keys())
        return create_text_response(
            f"No cultural pattern matches '{culturalKey}'. Available: {keys}."
        )

    key = pattern.get("key", "")
    staples = pattern.get("staples") or []
    proteins = pattern.get("common_proteins") or []
    spices = pattern.get("common_spices") or []
    methods = pattern.get("typical_cooking_methods") or []
    fasting = pattern.get("fasting_traditions") or []

    lines = [f"Pattern: {key}"]
    if staples:
        lines.append(f"  Staples: {_format_list(staples)}")
    if proteins:
        lines.append(f"  Common proteins: {_format_list(proteins)}")
    if spices:
        lines.append(f"  Common spices: {_format_list(spices)}")
    if methods:
        lines.append(f"  Cooking methods: {_format_list(methods)}")
    if fasting:
        lines.append(f"  Fasting traditions: {_format_list(fasting)}")

    return create_text_response("\n".join(lines))
