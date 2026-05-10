from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import (
    extract_codeable_display,
    get_fhir_context,
    get_patient_id_if_context_exists,
    iter_bundle_resources,
    parse_fhir_date,
)
from mcp_utilities import create_text_response

_LOINC_SYSTEM = "http://loinc.org"

_SDOH_LABELS: dict[str, str] = {
    "88122-7": "Food insecurity (worry food would run out)",
    "88123-5": "Food ran out",
    "93030-5": "Housing instability",
    "76437-3": "Income tier",
}


def _loinc_code(code_block: dict | None) -> str | None:
    if not code_block:
        return None
    for coding in code_block.get("coding") or []:
        if coding.get("system") == _LOINC_SYSTEM and coding.get("code"):
            return coding["code"]
    return None


def _value(resource: dict) -> str | None:
    coded = extract_codeable_display(resource.get("valueCodeableConcept"))
    if coded:
        return coded
    if resource.get("valueString"):
        return resource["valueString"]
    qty = resource.get("valueQuantity") or {}
    if qty.get("value") is not None:
        unit = qty.get("unit") or qty.get("code") or ""
        return f"{qty['value']} {unit}".strip()
    return None


async def get_patient_sdoh(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    ctx: Context = None,
) -> str:
    # print("[TOOL]: get_patient_sdoh")
    try:
        if not patientId:
            patientId = get_patient_id_if_context_exists(ctx)
            if not patientId:
                raise ValueError("No patient context found")

        fhir_context = get_fhir_context(ctx)
        if not fhir_context:
            raise ValueError("The fhir context could not be retrieved")

        fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

        latest: dict[str, tuple] = {}
        for category in ("social-history", "survey"):
            bundle = await fhir_client.search(
                "Observation",
                {"patient": patientId, "category": category},
            )
            for resource in iter_bundle_resources(bundle):
                code = _loinc_code(resource.get("code"))
                if code not in _SDOH_LABELS:
                    continue
                value = _value(resource)
                if not value:
                    continue
                effective = resource.get("effectiveDateTime") or (resource.get("effectivePeriod") or {}).get("issued")
                eff_date = parse_fhir_date(effective)
                existing = latest.get(code)
                if existing is None or (eff_date and (existing[0] is None or eff_date > existing[0])):
                    latest[code] = (eff_date, value)

        if not latest:
            return create_text_response("No SDOH data available.")

        parts = [f"{_SDOH_LABELS[code]}: {value}" for code, (_, value) in latest.items()]
        return create_text_response("; ".join(parts))
    except Exception as e:
        # print(f"[SDOH ERROR] {type(e).__name__}: {e}")
        raise
