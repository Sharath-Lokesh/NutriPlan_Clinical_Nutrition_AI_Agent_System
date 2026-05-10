import json
import os


class InteractionRepository:
    def __init__(self, data_path: str) -> None:
        if not os.path.isabs(data_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, data_path)
        self._data_path: str = data_path
        self._interactions: list[dict] = self._load()

    def _load(self) -> list[dict]:
        with open(self._data_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh) or {}
        items = payload.get("interactions") or []
        return [item for item in items if isinstance(item, dict)]

    def all(self) -> list[dict]:
        return list(self._interactions)

    @staticmethod
    def _drug_matches(interaction: dict, drug_query: str) -> bool:
        q = (drug_query or "").strip().lower()
        if not q:
            return False
        drug = interaction.get("drug") or {}
        name = str(drug.get("name") or "").lower()
        drug_class = str(drug.get("drug_class") or "").lower()
        rxnorm = str(drug.get("rxnorm") or "").lower()
        aliases = [str(a).lower() for a in (drug.get("aliases") or [])]
        if q == name or q == drug_class or q == rxnorm:
            return True
        if q in aliases:
            return True
        if name and (q in name or name in q):
            return True
        if drug_class and (q in drug_class or drug_class in q):
            return True
        for alias in aliases:
            if alias and (q in alias or alias in q):
                return True
        return False

    @staticmethod
    def _food_matches(interaction: dict, food_query: str) -> bool:
        q = (food_query or "").strip().lower()
        if not q:
            return False
        food = interaction.get("food_or_nutrient") or {}
        name = str(food.get("name") or "").lower()
        keywords = [str(k).lower() for k in (food.get("keywords") or [])]
        if name and (q in name or name in q):
            return True
        for keyword in keywords:
            if keyword and (q in keyword or keyword in q):
                return True
        return False

    def find_by_drug(self, drug_query: str) -> list[dict]:
        return [i for i in self._interactions if self._drug_matches(i, drug_query)]

    def find_by_food(self, food_query: str) -> list[dict]:
        return [i for i in self._interactions if self._food_matches(i, food_query)]

    def find_by_drug_and_food(self, drug_query: str, food_query: str) -> list[dict]:
        return [
            i
            for i in self._interactions
            if self._drug_matches(i, drug_query) and self._food_matches(i, food_query)
        ]

    def find_by_drug_class(self, drug_class: str) -> list[dict]:
        q = (drug_class or "").strip().lower()
        if not q:
            return []
        results: list[dict] = []
        for interaction in self._interactions:
            drug = interaction.get("drug") or {}
            cls = str(drug.get("drug_class") or "").lower()
            if cls and (q == cls or q in cls or cls in q):
                results.append(interaction)
        return results


repository = InteractionRepository("data/interactions.json")
