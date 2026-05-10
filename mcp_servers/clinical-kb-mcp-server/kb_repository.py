import json
import os


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh) or {}


def _norm(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", " ")


class KbRepository:
    def __init__(self, data_dir: str) -> None:
        if not os.path.isabs(data_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, data_dir)
        self._data_dir: str = data_dir

        self._guidelines: list[dict] = self._load_list("condition_guidelines.json", "guidelines")
        self._dri_nutrients: list[dict] = self._load_list("dri_tables.json", "nutrients")
        self._macro_ratios: list[dict] = self._load_list("macronutrient_ratios.json", "ratios")
        self._micro_priorities: list[dict] = self._load_list("micronutrient_priorities.json", "priorities")
        self._hard_exclusions: list[dict] = self._load_list("hard_exclusions.json", "exclusions")
        self._protocols: list[dict] = self._load_list("evidence_protocols.json", "protocols")

    def _load_list(self, filename: str, key: str) -> list[dict]:
        payload = _load_json(os.path.join(self._data_dir, filename))
        items = payload.get(key) or []
        return [item for item in items if isinstance(item, dict)]

    def counts(self) -> dict[str, int]:
        return {
            "condition_guidelines": len(self._guidelines),
            "dri_nutrients": len(self._dri_nutrients),
            "macronutrient_ratios": len(self._macro_ratios),
            "micronutrient_priorities": len(self._micro_priorities),
            "hard_exclusions": len(self._hard_exclusions),
            "evidence_protocols": len(self._protocols),
        }

    @staticmethod
    def _condition_matches(entry: dict, query: str, condition_field: str = "condition") -> bool:
        q = _norm(query)
        if not q:
            return False

        condition = _norm(entry.get(condition_field))
        if condition and (q == condition or q in condition or condition in q):
            return True

        aliases = entry.get("aliases") or []
        for alias in aliases:
            a = _norm(alias)
            if a and (q == a or q in a or a in q):
                return True

        icd10_codes = entry.get("icd10_codes") or []
        for code in icd10_codes:
            c = _norm(code)
            if c and (q == c or q.startswith(c) or c.startswith(q)):
                return True

        snomed_codes = entry.get("snomed_codes") or []
        for code in snomed_codes:
            c = _norm(code)
            if c and q == c:
                return True

        return False

    def find_guideline(self, condition_query: str) -> dict | None:
        for guideline in self._guidelines:
            if self._condition_matches(guideline, condition_query):
                return guideline
        return None

    def find_dri(
        self,
        nutrient: str,
        sex: str,
        age: int,
        pregnant: bool = False,
        lactating: bool = False,
    ) -> dict | None:
        n = _norm(nutrient)
        s = _norm(sex)
        if not n or not s:
            return None

        nutrient_entry: dict | None = None
        for item in self._dri_nutrients:
            if _norm(item.get("nutrient")) == n:
                nutrient_entry = item
                break
        if nutrient_entry is None:
            return None

        groups = nutrient_entry.get("groups") or []
        if not isinstance(groups, list):
            return None

        candidates: list[dict] = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            if _norm(group.get("sex")) != s:
                continue
            age_min = group.get("age_min")
            age_max = group.get("age_max")
            if age_min is None or age_max is None:
                continue
            if not (age_min <= age <= age_max):
                continue
            candidates.append(group)

        if not candidates:
            return None

        def match_score(g: dict) -> int:
            g_pregnant = bool(g.get("pregnant"))
            g_lactating = bool(g.get("lactating"))
            score = 0
            if pregnant and g_pregnant:
                score += 2
            if lactating and g_lactating:
                score += 2
            if not pregnant and not g_pregnant:
                score += 1
            if not lactating and not g_lactating:
                score += 1
            return score

        if pregnant or lactating:
            specific = [g for g in candidates if (pregnant and g.get("pregnant")) or (lactating and g.get("lactating"))]
            chosen = max(specific, key=match_score) if specific else None
        else:
            generic = [g for g in candidates if not g.get("pregnant") and not g.get("lactating")]
            chosen = generic[0] if generic else candidates[0]

        if chosen is None:
            return None

        return {
            "nutrient": nutrient_entry.get("nutrient"),
            "unit": nutrient_entry.get("unit"),
            "source": nutrient_entry.get("source"),
            "group": chosen,
        }

    def find_macro_ratios(self, key: str) -> dict | None:
        q = _norm(key)
        if not q:
            return None
        for ratio in self._macro_ratios:
            r_key = _norm(ratio.get("key"))
            if r_key and (r_key == q or q in r_key or r_key in q):
                return ratio
        return None

    def find_micro_priorities(self, condition_query: str) -> dict | None:
        for entry in self._micro_priorities:
            if self._condition_matches(entry, condition_query):
                return entry
        return None

    def find_hard_exclusions(self, condition_query: str) -> dict | None:
        for entry in self._hard_exclusions:
            if self._condition_matches(entry, condition_query):
                return entry
        return None

    def find_protocol(self, name: str) -> dict | None:
        q = _norm(name)
        if not q:
            return None
        for protocol in self._protocols:
            if _norm(protocol.get("name")) == q:
                return protocol
        return None

    def all_protocols(self) -> list[dict]:
        return list(self._protocols)


repository = KbRepository("data")
