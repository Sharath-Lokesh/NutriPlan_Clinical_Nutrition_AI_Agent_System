from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import (
    extract_codeable_display,
    get_fhir_context,
    get_patient_id_if_context_exists,
    iter_bundle_resources,
)
from mcp_utilities import create_text_response

_RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"


def _rxnorm_code(med_codeable: dict | None) -> str | None:
    if not med_codeable:
        return None
    for coding in med_codeable.get("coding") or []:
        if coding.get("system") == _RXNORM_SYSTEM and coding.get("code"):
            return coding["code"]
    return None


def _dosage_text(resource: dict, key: str) -> str | None:
    dosage = resource.get(key) or []
    if not dosage:
        return None
    first = dosage[0] or {}
    text = first.get("text")
    if text:
        return text
    return None


async def get_patient_medications(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    status: Annotated[  # noqa: N803
        str | None,
        Field(description="Medication status filter (e.g. active, completed). Defaults to active."),
    ] = "active",
    includeRequested: Annotated[  # noqa: N803
        bool,
        Field(description="Whether to also include MedicationRequest results."),
    ] = True,
    ctx: Context = None,
) -> str:
    # print("[TOOL]: get_patient_medications")
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

    seen_codes: set[str] = set()
    seen_names: set[str] = set()
    medications: list[str] = []

	# Hardcode - as the agent was failing to pass this parameter
    if status is None:
        status = "active"

    statement_bundle = await fhir_client.search(
        "MedicationStatement",
        {"patient": patientId, "status": status} if status else {"patient": patientId},
    )
    for resource in iter_bundle_resources(statement_bundle):
        med = resource.get("medicationCodeableConcept")
        name = extract_codeable_display(med)
        if not name:
            continue
        code = _rxnorm_code(med)
        if code and code in seen_codes:
            continue
        if not code and name in seen_names:
            continue
        if code:
            seen_codes.add(code)
        seen_names.add(name)
        dose = _dosage_text(resource, "dosage")
        medications.append(f"{name} — {dose}" if dose else name)

    if includeRequested:
        request_status = "active" if status == "active" else status
        params = {"patient": patientId}
        if request_status:
            params["status"] = request_status
        request_bundle = await fhir_client.search("MedicationRequest", params)
        for resource in iter_bundle_resources(request_bundle):
            med = resource.get("medicationCodeableConcept")
            name = extract_codeable_display(med)
            if not name:
                continue
            code = _rxnorm_code(med)
            if code and code in seen_codes:
                continue
            if not code and name in seen_names:
                continue
            if code:
                seen_codes.add(code)
            seen_names.add(name)
            dose = _dosage_text(resource, "dosageInstruction")
            medications.append(f"{name} — {dose}" if dose else name)

    if not medications:
        return create_text_response("No active medications found.")

    return create_text_response("\n".join(medications))
