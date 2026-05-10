from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import (
    get_fhir_context,
    get_patient_id_if_context_exists,
    iter_bundle_resources,
    parse_fhir_date,
)
from mcp_utilities import create_text_response

_LOINC_SYSTEM = "http://loinc.org"

_HEIGHT = "8302-2"
_WEIGHT = "29463-7"
_BMI = "39156-5"
_BP_PANEL = "85354-9"
_BP_SYSTOLIC = "8480-6"
_BP_DIASTOLIC = "8462-4"
_WAIST = "8280-0"


def _loinc_code(code_block: dict | None) -> str | None:
    if not code_block:
        return None
    for coding in code_block.get("coding") or []:
        if coding.get("system") == _LOINC_SYSTEM and coding.get("code"):
            return coding["code"]
    return None


def _convert_height_to_cm(value: float, unit: str | None) -> float:
    if unit and unit.lower() in {"in", "[in_i]", "inch", "inches"}:
        return round(value * 2.54, 1)
    return round(value, 1)


def _convert_weight_to_kg(value: float, unit: str | None) -> float:
    if unit and unit.lower() in {"lb", "[lb_av]", "lbs", "pound", "pounds"}:
        return round(value * 0.453592, 1)
    return round(value, 1)


def _component_value(components: list[dict], target_code: str) -> float | None:
    for component in components or []:
        code = _loinc_code(component.get("code"))
        if code == target_code:
            qty = component.get("valueQuantity") or {}
            if qty.get("value") is not None:
                return float(qty["value"])
    return None


async def get_patient_vitals(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    latestOnly: Annotated[  # noqa: N803
        bool,
        Field(description="If true, only the most recent value per vital is returned."),
    ] = True,
    ctx: Context = None,
) -> str:
    # print("[TOOL]: get_patient_vitals")
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

	# Hardcode - as the agent was failing to pass this parameter
    if latestOnly is None:
        latestOnly = True
    
    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)
    bundle = await fhir_client.search(
        "Observation",
        {"patient": patientId, "category": "vital-signs"},
    )
    if not bundle or not bundle.get("entry"):
        return create_text_response("No vitals found.")

    latest: dict[str, tuple] = {}
    for resource in iter_bundle_resources(bundle):
        code = _loinc_code(resource.get("code"))
        if not code:
            continue
        effective = resource.get("effectiveDateTime") or (resource.get("effectivePeriod") or {}).get("issued")
        eff_date = parse_fhir_date(effective)

        if code == _BP_PANEL:
            components = resource.get("component") or []
            sys_val = _component_value(components, _BP_SYSTOLIC)
            dia_val = _component_value(components, _BP_DIASTOLIC)
            if sys_val is None or dia_val is None:
                continue
            payload = (sys_val, dia_val)
        else:
            qty = resource.get("valueQuantity") or {}
            if qty.get("value") is None:
                continue
            payload = (float(qty["value"]), qty.get("unit") or qty.get("code"))

        existing = latest.get(code)
        if not latestOnly or existing is None or (eff_date and (existing[0] is None or eff_date > existing[0])):
            latest[code] = (eff_date, payload)

    parts: list[str] = []

    if _HEIGHT in latest:
        value, unit = latest[_HEIGHT][1]
        parts.append(f"Height: {_convert_height_to_cm(value, unit)} cm")
    if _WEIGHT in latest:
        value, unit = latest[_WEIGHT][1]
        parts.append(f"Weight: {_convert_weight_to_kg(value, unit)} kg")
    if _BMI in latest:
        value, _unit = latest[_BMI][1]
        parts.append(f"BMI: {round(value, 1)}")
    if _BP_PANEL in latest:
        sys_val, dia_val = latest[_BP_PANEL][1]
        parts.append(f"BP: {int(sys_val)}/{int(dia_val)} mmHg")
    if _WAIST in latest:
        value, unit = latest[_WAIST][1]
        parts.append(f"Waist: {_convert_height_to_cm(value, unit)} cm")

    if not parts:
        return create_text_response("No vitals found.")

    return create_text_response("; ".join(parts))
