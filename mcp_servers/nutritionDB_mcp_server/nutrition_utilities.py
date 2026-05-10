from mcp.server.fastmcp import Context

from mcp_constants import USDA_API_KEY_HEADER
from nutrition_constants import (
    CURATED_NUTRIENT_PANEL,
    NUTRIENT_CALCIUM,
    NUTRIENT_CARBS,
    NUTRIENT_CHOLESTEROL,
    NUTRIENT_ENERGY_KCAL,
    NUTRIENT_FAT,
    NUTRIENT_FIBER,
    NUTRIENT_FOLATE,
    NUTRIENT_IRON,
    NUTRIENT_MAGNESIUM,
    NUTRIENT_POTASSIUM,
    NUTRIENT_PROTEIN,
    NUTRIENT_SAT_FAT,
    NUTRIENT_SODIUM,
    NUTRIENT_SUGARS,
    NUTRIENT_TRANS_FAT,
    NUTRIENT_VITAMIN_B12,
    NUTRIENT_VITAMIN_C,
    NUTRIENT_VITAMIN_D,
)
from usda_context import UsdaContext


_NUTRIENT_LABELS: dict[int, str] = {
    NUTRIENT_ENERGY_KCAL: "Energy",
    NUTRIENT_PROTEIN: "Protein",
    NUTRIENT_FAT: "Fat",
    NUTRIENT_SAT_FAT: "Saturated Fat",
    NUTRIENT_TRANS_FAT: "Trans Fat",
    NUTRIENT_CHOLESTEROL: "Cholesterol",
    NUTRIENT_CARBS: "Carbs",
    NUTRIENT_FIBER: "Fiber",
    NUTRIENT_SUGARS: "Sugars",
    NUTRIENT_SODIUM: "Sodium",
    NUTRIENT_POTASSIUM: "Potassium",
    NUTRIENT_CALCIUM: "Calcium",
    NUTRIENT_IRON: "Iron",
    NUTRIENT_MAGNESIUM: "Magnesium",
    NUTRIENT_VITAMIN_D: "Vitamin D",
    NUTRIENT_VITAMIN_C: "Vitamin C",
    NUTRIENT_VITAMIN_B12: "Vitamin B12",
    NUTRIENT_FOLATE: "Folate",
}


def get_usda_context(ctx: Context) -> UsdaContext:
    api_key: str | None = None
    try:
        request = ctx.request_context.request
        if request is not None:
            api_key = request.headers.get(USDA_API_KEY_HEADER)
    except (AttributeError, LookupError):
        api_key = None
    if not api_key:
        api_key = "DEMO_KEY"
    return UsdaContext(api_key=api_key)


def _nutrient_id(food_nutrient: dict) -> int | None:
    nutrient = food_nutrient.get("nutrient") or {}
    nutrient_id = nutrient.get("id")
    if nutrient_id is None:
        nutrient_id = food_nutrient.get("nutrientId")
    if nutrient_id is None:
        return None
    try:
        return int(nutrient_id)
    except (TypeError, ValueError):
        return None


def _nutrient_amount(food_nutrient: dict) -> float | None:
    amount = food_nutrient.get("amount")
    if amount is None:
        amount = food_nutrient.get("value")
    if amount is None:
        return None
    try:
        return float(amount)
    except (TypeError, ValueError):
        return None


def _nutrient_unit(food_nutrient: dict) -> str:
    nutrient = food_nutrient.get("nutrient") or {}
    unit = nutrient.get("unitName") or food_nutrient.get("unitName") or ""
    return str(unit).lower() if unit else ""


def _nutrient_name(food_nutrient: dict) -> str:
    nutrient = food_nutrient.get("nutrient") or {}
    name = nutrient.get("name") or food_nutrient.get("nutrientName") or ""
    return str(name)


def extract_nutrient_value(
    food_nutrients: list[dict], nutrient_id: int
) -> float | None:
    if not food_nutrients:
        return None
    for entry in food_nutrients:
        if not isinstance(entry, dict):
            continue
        if _nutrient_id(entry) == nutrient_id:
            return _nutrient_amount(entry)
    return None


def format_nutrient_panel(food_nutrients: list[dict]) -> str:
    if not food_nutrients:
        return "No nutrient data available."
    parts: list[str] = []
    for nutrient_id in CURATED_NUTRIENT_PANEL:
        amount = extract_nutrient_value(food_nutrients, nutrient_id)
        if amount is None:
            continue
        label = _NUTRIENT_LABELS.get(nutrient_id, f"Nutrient {nutrient_id}")
        unit = _lookup_unit(food_nutrients, nutrient_id)
        parts.append(f"{label}: {_format_amount(amount)} {unit}".rstrip())
    if not parts:
        return "No curated panel nutrients available for this food."
    return "; ".join(parts)


def _lookup_unit(food_nutrients: list[dict], nutrient_id: int) -> str:
    for entry in food_nutrients:
        if not isinstance(entry, dict):
            continue
        if _nutrient_id(entry) == nutrient_id:
            return _nutrient_unit(entry)
    return ""


def _format_amount(amount: float) -> str:
    if abs(amount) >= 100:
        return f"{amount:.0f}"
    if abs(amount) >= 1:
        return f"{amount:.1f}"
    return f"{amount:.2f}"


def iter_food_nutrients(food: dict | None) -> list[dict]:
    if not food:
        return []
    return food.get("foodNutrients") or []
