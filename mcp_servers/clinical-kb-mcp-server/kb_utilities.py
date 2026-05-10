from kb_constants import DRI_VALUE_KEYS


def format_guideline(guideline: dict) -> str:
    condition = str(guideline.get("condition") or "(unknown condition)")
    issuing_body = str(guideline.get("issuing_body") or "")
    year = guideline.get("guideline_year")
    summary = str(guideline.get("summary") or "(no summary on file)")
    monitoring = guideline.get("monitoring") or []
    source = str(guideline.get("evidence_source") or "(no source on file)")
    url = str(guideline.get("url") or "").strip()

    header_parts = [f"Condition: {condition}"]
    if issuing_body or year:
        body_label = issuing_body or "Unknown"
        year_label = f" ({year})" if year else ""
        header_parts.append(f"Issuing body: {body_label}{year_label}")

    lines: list[str] = list(header_parts)
    lines.append(f"Summary: {summary}")

    targets = guideline.get("key_targets") or {}
    if isinstance(targets, dict) and targets:
        lines.append("Key targets:")
        for k, v in targets.items():
            lines.append(f"  - {k}: {v}")

    if isinstance(monitoring, list) and monitoring:
        lines.append("Monitoring:")
        for item in monitoring:
            lines.append(f"  - {item}")

    lines.append(f"Source: {source}")
    if url:
        lines.append(f"URL: {url}")

    return "\n".join(lines)


def format_dri_row(group: dict, nutrient: str, unit: str) -> str:
    parts: list[str] = []
    for key in DRI_VALUE_KEYS:
        value = group.get(key)
        if value is None:
            continue
        parts.append(f"{key.upper()} {value} {unit}")

    amdr_min = group.get("amdr_pct_kcal_min")
    amdr_max = group.get("amdr_pct_kcal_max")
    if amdr_min is not None and amdr_max is not None:
        parts.append(f"AMDR {amdr_min}-{amdr_max}% kcal")

    crl = group.get("crl")
    if crl is not None:
        parts.append(f"CRL {crl} {unit}")

    if not parts:
        return f"{nutrient}: no DRI values populated"

    return f"{nutrient}: " + "; ".join(parts)


def mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    sex_norm = (sex or "").strip().lower()
    if sex_norm == "male":
        return 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age + 5.0
    return 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age - 161.0
