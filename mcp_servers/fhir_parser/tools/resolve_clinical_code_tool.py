from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import get_fhir_context
from mcp_utilities import create_text_response

_SYSTEM_ALIASES: dict[str, str] = {
    "snomed": "http://snomed.info/sct",
    "loinc": "http://loinc.org",
    "rxnorm": "http://www.nlm.nih.gov/research/umls/rxnorm",
}

_CACHE: dict[tuple[str, str], str] = {}


def _resolve_system(system: str) -> str:
    return _SYSTEM_ALIASES.get(system.lower(), system)


def _extract_display(parameters: dict | None) -> str | None:
    if not parameters:
        return None
    for param in parameters.get("parameter") or []:
        if param.get("name") == "display":
            value = param.get("valueString")
            if value:
                return value
    return None


def _extract_display_from_expansion(expansion: dict | None, code: str) -> str | None:
    if not expansion:
        return None
    contains = (expansion.get("expansion") or {}).get("contains") or []
    for item in contains:
        if item.get("code") == code and item.get("display"):
            return item["display"]
    return None


async def resolve_clinical_code(
    code: Annotated[str, Field(description="The clinical code to resolve.")],
    system: Annotated[
        str,
        Field(description="The code system: 'snomed', 'loinc', 'rxnorm', or a full system URI."),
    ],
    language: Annotated[  # noqa: N803
        str | None,
        Field(description="Optional language for the display (e.g. 'en')."),
    ] = "en",
    ctx: Context = None,
) -> str:
    # print("[TOOL]: resolve_clinical_code")
    fhir_context = get_fhir_context(ctx)
    if not fhir_context:
        raise ValueError("The fhir context could not be retrieved")

    system_uri = _resolve_system(system)
    cache_key = (system_uri, code)
    cached = _CACHE.get(cache_key)
    if cached:
        return create_text_response(cached)

    fhir_client = FhirClient(base_url=fhir_context.url, token=fhir_context.token)

    lookup_path = f"CodeSystem/$lookup?system={system_uri}&code={code}"
    if language:
        lookup_path = f"{lookup_path}&displayLanguage={language}"

    parameters = await fhir_client.read(lookup_path)
    display = _extract_display(parameters)

    if not display:
        expand_path = f"ValueSet/$expand?system={system_uri}&filter={code}"
        expansion = await fhir_client.read(expand_path)
        display = _extract_display_from_expansion(expansion, code)

    if not display:
        return create_text_response(
            f"Could not resolve code {code} in system {system_uri}.",
            is_error=True,
        )

    _CACHE[cache_key] = display
    return create_text_response(display)
