from datetime import date, timedelta
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


def _loinc_code(code_block: dict | None) -> str | None:
    if not code_block:
        return None
    for coding in code_block.get("coding") or []:
        if coding.get("system") == _LOINC_SYSTEM and coding.get("code"):
            return coding["code"]
    return None


def _format_value(resource: dict) -> str | None:
    qty = resource.get("valueQuantity")
    if qty and qty.get("value") is not None:
        unit = qty.get("unit") or qty.get("code") or ""
        return f"{qty['value']} {unit}".strip()
    if resource.get("valueString"):
        return resource["valueString"]
    coded = extract_codeable_display(resource.get("valueCodeableConcept"))
    if coded:
        return coded
    return None


async def get_patient_observations(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    loincCodes: Annotated[  # noqa: N803
        list[str] | None,
        Field(description="Optional list of LOINC codes to filter observations by."),
    ] = None,
    category: Annotated[  # noqa: N803
        str | None,
        Field(description="The observation category. Defaults to 'laboratory'."),
    ] = "laboratory",
    dateFrom: Annotated[  # noqa: N803
        str | None,
        Field(description="Optional ISO date (YYYY-MM-DD); only observations on/after this date are returned. Defaults to 12 months ago."),
    ] = None,
    ctx: Context = None,
) -> str:
    # print("[TOOL]:get_patient_observations")
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    if not dateFrom:
        dateFrom = (date.today() - timedelta(days=365)).isoformat()

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

    params: dict[str, str] = {
        "patient": patientId,
        "date": f"ge{dateFrom}",
    }
    # Hardcode - as the agent was failing to pass this parameter
    if category is None:
        category = "laboratory"
    if category:
        params["category"] = category
    if loincCodes:
        params["code"] = ",".join(loincCodes)

    bundle = await fhir_client.search("Observation", params)
    if not bundle or not bundle.get("entry"):
        return create_text_response("No relevant laboratory observations found.")

    latest: dict[str, tuple[date | None, str, str | None, str | None]] = {}
    for resource in iter_bundle_resources(bundle):
        code_block = resource.get("code") or {}
        loinc = _loinc_code(code_block) or extract_codeable_display(code_block) or "unknown"
        name = extract_codeable_display(code_block) or loinc
        value = _format_value(resource)
        if not value:
            continue
        effective = resource.get("effectiveDateTime") or (resource.get("effectivePeriod") or {}).get("issued")
        eff_date = parse_fhir_date(effective)
        existing = latest.get(loinc)
        if existing is None or (eff_date and (existing[0] is None or eff_date > existing[0])):
            latest[loinc] = (eff_date, name, value, effective)

    if not latest:
        return create_text_response("No relevant laboratory observations found.")

    lines: list[str] = []
    for _, (_, name, value, effective) in latest.items():
        if effective:
            lines.append(f"{name}: {value} ({effective})")
        else:
            lines.append(f"{name}: {value}")

    return create_text_response("\n".join(lines))
