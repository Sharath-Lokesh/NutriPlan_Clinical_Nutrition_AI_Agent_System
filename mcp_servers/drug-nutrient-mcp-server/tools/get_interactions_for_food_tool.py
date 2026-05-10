from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from interaction_constants import SEVERITY_LEVELS, SEVERITY_RANK
from interaction_repository import repository
from interaction_utilities import sort_by_severity
from mcp_utilities import create_text_response


async def get_interactions_for_food(
    food: Annotated[
        str,
        Field(description="Food or nutrient to look up (e.g. 'grapefruit', 'calcium')."),
    ],
    minSeverity: Annotated[  # noqa: N803
        str,
        Field(
            description=(
                "Minimum severity to include. One of: contraindicated, significant, "
                "moderate, advisory. Defaults to 'advisory'."
            )
        ),
    ] = "advisory",
    ctx: Context = None,
) -> str:
    if not food or not food.strip():
        return create_text_response("A non-empty 'food' is required.", is_error=True)

    threshold_label = (minSeverity or "advisory").strip().lower()
    if threshold_label not in SEVERITY_LEVELS:
        return create_text_response(
            f"'minSeverity' must be one of: {SEVERITY_LEVELS}.", is_error=True
        )
    threshold_rank = SEVERITY_RANK[threshold_label]

    matches = repository.find_by_food(food)
    filtered = [
        i
        for i in matches
        if SEVERITY_RANK.get(str(i.get("severity") or ""), 0) >= threshold_rank
    ]

    if not filtered:
        return create_text_response(f"No known drug interactions for {food}.")

    grouped: dict[str, list[dict]] = {}
    for interaction in filtered:
        drug = interaction.get("drug") or {}
        drug_class = str(drug.get("drug_class") or "uncategorized")
        grouped.setdefault(drug_class, []).append(interaction)

    def _class_max_rank(items: list[dict]) -> int:
        return max(
            (SEVERITY_RANK.get(str(i.get("severity") or ""), 0) for i in items),
            default=0,
        )

    ordered_classes = sorted(
        grouped.items(),
        key=lambda kv: _class_max_rank(kv[1]),
        reverse=True,
    )

    lines: list[str] = []
    for drug_class, items in ordered_classes:
        lines.append(f"Drug class: {drug_class}")
        for item in sort_by_severity(items):
            drug = item.get("drug") or {}
            drug_name = str(drug.get("name") or "(unknown)")
            severity = str(item.get("severity") or "unspecified")
            recommendation = str(
                item.get("recommendation") or "(no recommendation on file)"
            )
            lines.append(f"  - {drug_name} [{severity}]: {recommendation}")

    return create_text_response("\n".join(lines))
