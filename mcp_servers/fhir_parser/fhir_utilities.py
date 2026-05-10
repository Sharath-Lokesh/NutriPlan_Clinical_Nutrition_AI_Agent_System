import jwt
from mcp.server.fastmcp import Context

from fhir_context import FhirContext
from mcp_constants import FHIR_ACCESS_TOKEN_HEADER, FHIR_SERVER_URL_HEADER, PATIENT_ID_HEADER

from datetime import date, datetime
from typing import Iterator
import json

def get_fhir_context(ctx: Context) -> FhirContext | None:
    req = ctx.request_context.request
    url = req.headers.get(FHIR_SERVER_URL_HEADER)
    if not url:
        return None
    token = req.headers.get(FHIR_ACCESS_TOKEN_HEADER)
    return FhirContext(url=url, token=token)


def get_patient_id_if_context_exists(ctx: Context) -> str | None:
    req = ctx.request_context.request
    fhir_token = req.headers.get(FHIR_ACCESS_TOKEN_HEADER)
    if fhir_token:
        claims = jwt.decode(fhir_token, options={"verify_signature": False})
        # print("=" * 80)
        # print("[JWT DECODE] Full token claims:")
        # print(json.dumps(claims, indent=2, default=str))
        # print("=" * 80)
        patient = claims.get("patient")
        if patient:
            return str(patient)
    return req.headers.get(PATIENT_ID_HEADER)

def extract_codeable_display(codeable: dict | None) -> str | None:
    if not codeable:
        return None
    text = codeable.get("text")
    if text:
        return text
    coding = codeable.get("coding") or []
    if coding:
        first = coding[0] or {}
        return first.get("display") or first.get("code")
    return None


def parse_fhir_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        if len(value) == 4:
            return date(int(value), 1, 1)
        if len(value) == 7:
            return date(int(value[:4]), int(value[5:7]), 1)
        if len(value) == 10:
            return date.fromisoformat(value)
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def iter_bundle_resources(bundle: dict | None) -> Iterator[dict]:
    if not bundle:
        return
    for entry in bundle.get("entry") or []:
        resource = entry.get("resource")
        if resource:
            yield resource