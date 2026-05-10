import json
import os

from context_constants import TASTE_DIMENSIONS, TASTE_LEVELS


def _norm(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", " ")


def _load_patterns() -> list[dict]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "cultural_patterns.json")
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh) or {}
    items = payload.get("patterns") or []
    return [item for item in items if isinstance(item, dict)]


_PATTERNS: list[dict] = _load_patterns()


def all_pattern_keys() -> list[str]:
    return [p.get("key", "") for p in _PATTERNS if p.get("key")]


def find_cultural_pattern(query: str) -> dict | None:
    q = _norm(query)
    if not q:
        return None
    for pattern in _PATTERNS:
        key = _norm(pattern.get("key"))
        if key and (q == key or q == key.replace(" ", "_")):
            return pattern
        for alias in pattern.get("aliases") or []:
            if _norm(alias) == q:
                return pattern
    for pattern in _PATTERNS:
        key = _norm(pattern.get("key"))
        if key and (q in key or key in q):
            return pattern
        for alias in pattern.get("aliases") or []:
            a = _norm(alias)
            if a and (q in a or a in q):
                return pattern
    return None


def validate_choice(value: str, allowed: list[str], field_name: str) -> None:
    if value not in allowed:
        raise ValueError(
            f"Invalid value '{value}' for '{field_name}'. Valid values: {', '.join(allowed)}."
        )


def validate_taste_profile(profile: dict[str, str]) -> None:
    for dim, level in profile.items():
        if dim not in TASTE_DIMENSIONS:
            raise ValueError(
                f"Invalid taste dimension '{dim}'. Valid dimensions: {', '.join(TASTE_DIMENSIONS)}."
            )
        if level not in TASTE_LEVELS:
            raise ValueError(
                f"Invalid taste level '{level}' for '{dim}'. Valid levels: {', '.join(TASTE_LEVELS)}."
            )
