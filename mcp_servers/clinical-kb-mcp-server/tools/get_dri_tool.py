from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from kb_repository import repository
from kb_utilities import format_dri_row
from mcp_utilities import create_text_response


async def get_dri(
    nutrient: Annotated[
        str,
        Field(description="Nutrient name (e.g. 'vitamin D', 'iron', 'protein', 'calcium')."),
    ],
    sex: Annotated[
        str,
        Field(description="Biological sex: 'male' or 'female'."),
    ],
    age: Annotated[
        int,
        Field(description="Age in years (integer)."),
    ],
    pregnant: Annotated[
        bool,
        Field(description="Whether the subject is pregnant. Defaults to false."),
    ] = False,
    lactating: Annotated[
        bool,
        Field(description="Whether the subject is lactating. Defaults to false."),
    ] = False,
    ctx: Context = None,
) -> str:
    if not nutrient or not nutrient.strip():
        return create_text_response("A non-empty 'nutrient' is required.", is_error=True)

    sex_norm = (sex or "").strip().lower()
    if sex_norm not in {"male", "female"}:
        return create_text_response(
            "'sex' must be either 'male' or 'female'.", is_error=True
        )

    if not isinstance(age, int) or age < 0 or age > 120:
        return create_text_response(
            "'age' must be an integer between 0 and 120.", is_error=True
        )

    result = repository.find_dri(nutrient, sex_norm, age, pregnant=pregnant, lactating=lactating)
    if result is None:
        return create_text_response(
            f"No DRI values available for {nutrient} for the specified group.",
            is_error=True,
        )

    group = result.get("group") or {}
    unit = result.get("unit") or ""
    source = result.get("source") or "(no source on file)"
    nutrient_label = result.get("nutrient") or nutrient

    row = format_dri_row(group, nutrient_label, unit)
    return create_text_response(f"{row}\nSource: {source}")
