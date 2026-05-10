from interaction_constants import SEVERITY_RANK


def format_interaction(interaction: dict) -> str:
    drug = interaction.get("drug") or {}
    food = interaction.get("food_or_nutrient") or {}

    drug_name = str(drug.get("name") or "(unknown drug)")
    drug_class = str(drug.get("drug_class") or "")
    food_name = str(food.get("name") or "(unknown food/nutrient)")
    food_type = str(food.get("type") or "")
    severity = str(interaction.get("severity") or "unspecified")
    mechanism = str(interaction.get("mechanism") or "(no mechanism on file)")
    clinical_effect = str(interaction.get("clinical_effect") or "(no clinical effect on file)")
    recommendation = str(interaction.get("recommendation") or "(no recommendation on file)")
    evidence_source = str(interaction.get("evidence_source") or "(no source on file)")

    drug_label = f"{drug_name}"
    if drug_class:
        drug_label += f" ({drug_class})"

    food_label = f"{food_name}"
    if food_type:
        food_label += f" [{food_type}]"

    return (
        f"[{severity.upper()}] {drug_label} x {food_label}\n"
        f"  Mechanism: {mechanism}\n"
        f"  Clinical effect: {clinical_effect}\n"
        f"  Recommendation: {recommendation}\n"
        f"  Source: {evidence_source}"
    )


def highest_severity(interactions: list[dict]) -> str | None:
    if not interactions:
        return None
    best_label: str | None = None
    best_rank = -1
    for interaction in interactions:
        label = str(interaction.get("severity") or "")
        rank = SEVERITY_RANK.get(label, 0)
        if rank > best_rank:
            best_rank = rank
            best_label = label
    return best_label


def sort_by_severity(interactions: list[dict]) -> list[dict]:
    return sorted(
        interactions,
        key=lambda i: SEVERITY_RANK.get(str(i.get("severity") or ""), 0),
        reverse=True,
    )
