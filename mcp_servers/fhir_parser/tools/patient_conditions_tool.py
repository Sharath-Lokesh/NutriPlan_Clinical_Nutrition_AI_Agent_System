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


async def get_patient_conditions(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    clinicalStatus: Annotated[  # noqa: N803
        str | None,
        Field(description="The clinical status of the conditions to fetch (e.g. active, resolved). Defaults to active."),
    ] = "active",
    category: Annotated[  # noqa: N803
        str | None,
        Field(description="Optional category filter: 'problem-list-item' or 'encounter-diagnosis'."),
    ] = None,
    ctx: Context = None,
) -> str:
    # print("[TOOL]: get_patient_conditions")
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

    params: dict[str, str] = {"patient": patientId}
    # Hardcode - as the agent was failing to pass this parameter
    if clinicalStatus is None:
        clinicalStatus = "active"
    # if clinicalStatus:
    #     params["clinicalStatus"] = clinicalStatus
    if category:
        params["category"] = category

    bundle = await fhir_client.search("Condition", params)
    if not bundle or not bundle.get("entry"):
        return create_text_response("No active conditions found.")
    
    target_status = (clinicalStatus or "active").lower()

    lines: list[str] = []
    for resource in iter_bundle_resources(bundle):
        if target_status:
            clinical_status = resource.get("clinicalStatus") or {}
            codings = clinical_status.get("coding") or []
            status_code = ""
            if codings:
                status_code = (codings[0].get("code") or "").lower()
            if status_code != target_status:
                continue
        name = extract_codeable_display(resource.get("code"))
        if not name:
            continue
        onset = resource.get("onsetDateTime") or (resource.get("onsetPeriod") or {}).get("recordedDate")
        severity = extract_codeable_display(resource.get("severity"))
        line = name
        if onset:
            line = f"{line} (since {onset})"
        if severity:
            line = f"{line} [severity: {severity}]"
        lines.append(line)

    if not lines:
        return create_text_response("No active conditions found.")

    return create_text_response("\n".join(lines))
