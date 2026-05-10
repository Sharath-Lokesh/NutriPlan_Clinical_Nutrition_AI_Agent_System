from datetime import date
from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import get_fhir_context, get_patient_id_if_context_exists, parse_fhir_date
from mcp_utilities import create_text_response

_RACE_URL = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
_ETHNICITY_URL = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
_OMB_SYSTEM = "urn:oid:2.16.840.1.113883.6.238"


def _us_core_value(extensions: list[dict] | None, url: str) -> str | None:
    for ext in extensions or []:
        if ext.get("url") != url:
            continue
        for sub in ext.get("extension") or []:
            if sub.get("url") == "text" and sub.get("valueString"):
                return sub["valueString"]
        for sub in ext.get("extension") or []:
            if sub.get("url") == "ombCategory":
                coding = sub.get("valueCoding") or {}
                if coding.get("system") == _OMB_SYSTEM and (coding.get("display") or coding.get("code")):
                    return coding.get("display") or coding.get("code")
    return None


def _compute_age(birth_str: str | None) -> int | None:
    bd = parse_fhir_date(birth_str)
    if not bd:
        return None
    today = date.today()
    return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))

def _pick_first_given(name_entry: dict) -> str | None:
    given = name_entry.get("given") or []
    for part in given:
        if isinstance(part, str) and part.strip():
            return part.strip()
    return None


def _extract_names(names: list[dict]) -> tuple[str | None, str | None, str | None]:
    """
    Walk Patient.name[] and return (first_name, last_name, preferred_name).

    FHIR R4 conventions:
      - 'official' use is the legal name (preferred for first/last fallback).
      - 'usual' use is what the person prefers to be called day-to-day.
      - If no 'use' is set, treat the first entry as the canonical name.
    """
    if not names:
        return None, None, None

    official: dict | None = None
    usual: dict | None = None
    fallback: dict | None = None

    for entry in names:
        if not isinstance(entry, dict):
            continue
        use = (entry.get("use") or "").lower()
        if use == "official" and official is None:
            official = entry
        elif use == "usual" and usual is None:
            usual = entry
        elif fallback is None:
            fallback = entry

    canonical = official or fallback or usual
    first_name = _pick_first_given(canonical) if canonical else None
    last_name = canonical.get("family") if canonical else None
    if isinstance(last_name, str):
        last_name = last_name.strip() or None

    preferred_name = _pick_first_given(usual) if usual else first_name

    return first_name, last_name, preferred_name

async def get_patient_demographics(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    ctx: Context = None,
) -> str:
    # print("[TOOL]: get_patient_demographics")
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)
    patient = await fhir_client.read(f"Patient/{patientId}")
    if not patient:
        return create_text_response("The patient could not be found.", is_error=True)

    parts: list[str] = []
    names = patient.get("name") or []
    first_name, last_name, preferred_name = _extract_names(names)
    if first_name:
        parts.append(f"First name: {first_name}")
    if last_name:
        parts.append(f"Last name: {last_name}")
    if preferred_name and preferred_name != first_name:
        parts.append(f"Preferred name: {preferred_name}")
    
    gender = patient.get("gender")
    if gender:
        parts.append(f"Sex: {gender}")

    age = _compute_age(patient.get("birthDate"))
    if age is not None:
        parts.append(f"Age: {age}")

    extensions = patient.get("extension") or []
    race = _us_core_value(extensions, _RACE_URL)
    if race:
        parts.append(f"Race: {race}")
    ethnicity = _us_core_value(extensions, _ETHNICITY_URL)
    if ethnicity:
        parts.append(f"Ethnicity: {ethnicity}")

    if not parts:
        return create_text_response("No demographic information available.")

    return create_text_response("; ".join(parts))
