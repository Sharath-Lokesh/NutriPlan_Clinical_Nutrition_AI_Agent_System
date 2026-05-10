from datetime import date
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

_SNOMED_SYSTEM = "http://snomed.info/sct"
_CPT_SYSTEM = "http://www.ama-assn.org/go/cpt"

NUTRITION_RELEVANT_CODES: set[str] = {
    "13190005",
    "26390003",
    "237782008",
    "266717002",
    "287614003",
    "359570006",
    "442338001",
    "443573004",
    "44124007",
    "45595009",
    "47114000",
    "60815008",
    "67466004",
    "73893000",
    "80146002",
    "82918005",
    "43644",
    "43645",
    "43770",
    "43775",
    "43846",
    "43847",
    "44120",
    "44204",
    "44970",
    "47562",
    "47563",
    "47600",
    "47605",
    "44150",
    "44155",
    "44160",
}

NUTRITION_KEYWORDS: tuple[str, ...] = (
    "bariatric",
    "gastric bypass",
    "sleeve gastrectomy",
    "roux-en-y",
    "bowel resection",
    "colectomy",
    "cholecystectomy",
    "gastrectomy",
    "appendectomy",
    "ileostomy",
    "colostomy",
    "whipple",
)


def _is_nutrition_relevant(code_block: dict | None) -> bool:
    if not code_block:
        return False
    for coding in code_block.get("coding") or []:
        system = coding.get("system")
        code = coding.get("code")
        if not code:
            continue
        if system in (_SNOMED_SYSTEM, _CPT_SYSTEM) and code in NUTRITION_RELEVANT_CODES:
            return True
        if code in NUTRITION_RELEVANT_CODES:
            return True
        display = (coding.get("display") or "").lower()
        if any(keyword in display for keyword in NUTRITION_KEYWORDS):
            return True
    text = (code_block.get("text") or "").lower()
    if any(keyword in text for keyword in NUTRITION_KEYWORDS):
        return True
    return False


def _five_years_ago_iso() -> str:
    today = date.today()
    try:
        return today.replace(year=today.year - 5).isoformat()
    except ValueError:
        return today.replace(year=today.year - 5, day=28).isoformat()


async def get_patient_procedures(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(description="The id of the patient. This is optional if patient context already exists"),
    ] = None,
    dateFrom: Annotated[  # noqa: N803
        str | None,
        Field(description="Optional ISO date (YYYY-MM-DD); only procedures on/after this date. Defaults to 5 years ago."),
    ] = None,
    category: Annotated[  # noqa: N803
        str | None,
        Field(description="Optional procedure category filter."),
    ] = None,
    ctx: Context = None,
) -> str:
    # print("[TOOL]: get_patient_procedures")
    if not patientId:
        patientId = get_patient_id_if_context_exists(ctx)
        if not patientId:
            raise ValueError("No patient context found")

    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    if not dateFrom:
        dateFrom = _five_years_ago_iso()

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

    params: dict[str, str] = {
        "patient": patientId,
        "date": f"ge{dateFrom}",
        "status": "completed",
    }
    if category:
        params["category"] = category

    bundle = await fhir_client.search("Procedure", params)
    if not bundle or not bundle.get("entry"):
        return create_text_response("No nutrition-relevant procedures.")

    lines: list[str] = []
    for resource in iter_bundle_resources(bundle):
        code_block = resource.get("code") or {}
        if not _is_nutrition_relevant(code_block):
            continue
        name = extract_codeable_display(code_block)
        if not name:
            continue
        performed = resource.get("performedDateTime") or (resource.get("performedPeriod") or {}).get("start")
        if performed:
            lines.append(f"{name} ({performed})")
        else:
            lines.append(name)

    if not lines:
        return create_text_response("No nutrition-relevant procedures.")

    return create_text_response("\n".join(lines))
