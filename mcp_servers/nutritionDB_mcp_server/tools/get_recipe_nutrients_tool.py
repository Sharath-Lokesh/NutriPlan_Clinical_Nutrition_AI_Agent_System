from typing import Annotated

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_utilities import create_text_response
from nutrition_constants import CURATED_NUTRIENT_PANEL
from nutrition_utilities import get_usda_context, iter_food_nutrients
from usda_client import UsdaClient


_LABELS: dict[int, str] = {
    1008: "Energy",
    1003: "Protein",
    1004: "Fat",
    1258: "Saturated Fat",
    1257: "Trans Fat",
    1253: "Cholesterol",
    1005: "Carbs",
    1079: "Fiber",
    2000: "Sugars",
    1093: "Sodium",
    1092: "Potassium",
    1087: "Calcium",
    1089: "Iron",
    1090: "Magnesium",
    1114: "Vitamin D",
    1162: "Vitamin C",
    1178: "Vitamin B12",
    1177: "Folate",
}


def _format_amount(amount: float) -> str:
    if abs(amount) >= 100:
        return f"{amount:.0f}"
    if abs(amount) >= 1:
        return f"{amount:.1f}"
    return f"{amount:.2f}"


async def get_recipe_nutrients(
    ingredients: Annotated[
        list[dict],
        Field(
            description=(
                "List of ingredient dicts, each with keys 'fdcId' (int) and 'grams' (float). "
                "Example: [{'fdcId': 171688, 'grams': 150}, {'fdcId': 168409, 'grams': 50}]."
            )
        ),
    ],
    ctx: Context = None,
) -> str:
    if not ingredients:
        return create_text_response("'ingredients' must be a non-empty list.", is_error=True)

    parsed: list[tuple[int, float]] = []
    for entry in ingredients:
        if not isinstance(entry, dict):
            return create_text_response(
                "Each ingredient must be a dict with 'fdcId' and 'grams'.", is_error=True
            )
        fdc_id = entry.get("fdcId")
        grams = entry.get("grams")
        if fdc_id is None or grams is None:
            return create_text_response(
                "Each ingredient requires both 'fdcId' and 'grams'.", is_error=True
            )
        try:
            parsed.append((int(fdc_id), float(grams)))
        except (TypeError, ValueError):
            return create_text_response(
                "'fdcId' must be int and 'grams' must be numeric.", is_error=True
            )

    fdc_ids = [pair[0] for pair in parsed]

    usda_context = get_usda_context(ctx)
    client = UsdaClient(api_key=usda_context.api_key)

    # Fetch foods from USDA. If the bulk call fails entirely, return an error.
    try:
        foods = await client.get_foods(fdc_ids, format="full")
    except Exception as e:
        return create_text_response(
            f"USDA bulk fetch failed for FDC IDs {fdc_ids}: {type(e).__name__}: {str(e)}",
            is_error=True,
        )

    by_id: dict[int, dict] = {}
    if foods:
        for food in foods:
            if not isinstance(food, dict):
                continue
            fid = food.get("fdcId")
            if fid is not None:
                try:
                    by_id[int(fid)] = food
                except (TypeError, ValueError):
                    continue

    # Identify which FDC IDs were retrieved vs missing.
    successful_ids = [fid for fid in fdc_ids if fid in by_id]
    missing_ids = [fid for fid in fdc_ids if fid not in by_id]

    # If everything failed, surface a clear error so the agent knows to pick different IDs.
    if not successful_ids:
        return create_text_response(
            f"USDA returned no data for any of the supplied FDC IDs: {missing_ids}. "
            f"All IDs may be retired or invalid. Pick different ingredients.",
            is_error=True,
        )

    # Aggregate nutrients only for successfully-fetched ingredients.
    totals: dict[int, float] = {}
    units: dict[int, str] = {}
    names: dict[int, str] = {}
    successful_grams = 0.0
    successful_count = 0

    for fid, grams in parsed:
        if fid not in by_id:
            continue  # skip missing IDs; they're reported separately below
        food = by_id[fid]
        scale = grams / 100.0
        successful_grams += grams
        successful_count += 1

        for entry in iter_food_nutrients(food):
            if not isinstance(entry, dict):
                continue
            nutrient = entry.get("nutrient") or {}
            nid = nutrient.get("id") or entry.get("nutrientId")
            try:
                nid_int = int(nid) if nid is not None else None
            except (TypeError, ValueError):
                nid_int = None
            if nid_int is None:
                continue
            amount = entry.get("amount")
            if amount is None:
                amount = entry.get("value")
            if amount is None:
                continue
            try:
                amount_f = float(amount)
            except (TypeError, ValueError):
                continue
            totals[nid_int] = totals.get(nid_int, 0.0) + amount_f * scale
            if nid_int not in units:
                unit = nutrient.get("unitName") or entry.get("unitName") or ""
                units[nid_int] = str(unit).lower() if unit else ""
            if nid_int not in names:
                names[nid_int] = str(nutrient.get("name") or entry.get("nutrientName") or "")

    parts: list[str] = []
    for nid in CURATED_NUTRIENT_PANEL:
        if nid not in totals:
            continue
        label = _LABELS.get(nid, names.get(nid) or f"Nutrient {nid}")
        unit = units.get(nid, "")
        parts.append(f"{label}: {_format_amount(totals[nid])} {unit}".rstrip())

    # Build the response with optional missing-IDs warning.
    response = (
        f"Recipe total ({successful_grams:.0f} g across {successful_count} ingredients) — "
        + ("; ".join(parts) if parts else "no curated nutrients aggregated")
    )

    if missing_ids:
        response += (
            f". WARNING: skipped {len(missing_ids)} ingredient(s) — FDC IDs not found in USDA: "
            f"{missing_ids}. Aggregate values exclude these ingredients."
        )

    return create_text_response(response)