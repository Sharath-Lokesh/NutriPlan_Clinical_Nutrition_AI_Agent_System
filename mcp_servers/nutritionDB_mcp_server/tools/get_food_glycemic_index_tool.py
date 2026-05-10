import json
import os
from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_utilities import get_usda_context
from usda_client import UsdaClient


_GI_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "glycemic_index.json",
)


def _load_gi_table() -> tuple[list[dict], str]:
    try:
        with open(_GI_DATA_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return [], ""
    entries = data.get("entries") or []
    source = data.get("_source") or ""
    return entries, source


def _fuzzy_match(name: str, entries: list[dict]) -> dict | None:
    if not name:
        return None
    needle = name.lower()
    best: tuple[int, dict] | None = None
    for entry in entries:
        candidate = str(entry.get("name") or "").lower()
        if not candidate:
            continue
        score = 0
        if candidate == needle:
            score = 1000
        elif candidate in needle:
            score = 100 + len(candidate)
        elif needle in candidate:
            score = 80 + len(needle)
        else:
            tokens = [t for t in needle.replace(",", " ").split() if t]
            overlap = sum(1 for t in tokens if t in candidate)
            if overlap:
                score = 10 * overlap
        if score and (best is None or score > best[0]):
            best = (score, entry)
    return best[1] if best else None


async def get_food_glycemic_index(
    fdcId: Annotated[  # noqa: N803
        int | None,
        Field(description="USDA FDC ID. Optional if 'foodName' is provided."),
    ] = None,
    foodName: Annotated[  # noqa: N803
        str | None,
        Field(description="Plain-text food name. Optional if 'fdcId' is provided."),
    ] = None,
    ctx: Context = None,
) -> str:
    if not fdcId and not foodName:
        return create_text_response(
            "Either 'fdcId' or 'foodName' must be provided.", is_error=True
        )

    entries, source = _load_gi_table()
    if not entries:
        return create_text_response(
            "Glycemic index reference data is unavailable.", is_error=True
        )

    name_for_match = (foodName or "").strip()
    if fdcId and not name_for_match:
        usda_context = get_usda_context(ctx)
        client = UsdaClient(api_key=usda_context.api_key)
        food = await client.get_food(int(fdcId), format="abridged")
        if not food:
            return create_text_response("Food not found.", is_error=True)
        name_for_match = str(food.get("description") or "")

    match = _fuzzy_match(name_for_match, entries)
    if not match:
        return create_text_response("No glycemic index data available for this food.")

    gi = match.get("gi")
    gl = match.get("gl")
    category = match.get("category") or ""
    matched_name = match.get("name") or "(unknown)"
    pieces = [f"GI: {gi} ({category})" if category else f"GI: {gi}"]
    if gl is not None:
        pieces.append(f"GL: {gl}")
    pieces.append(f"matched: {matched_name}")
    if source:
        pieces.append(f"source: {source}")
    return create_text_response("; ".join(pieces))
