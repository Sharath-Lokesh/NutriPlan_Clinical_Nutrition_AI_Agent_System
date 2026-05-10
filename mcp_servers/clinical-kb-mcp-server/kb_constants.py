ACTIVITY_FACTORS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS: dict[str, int] = {
    "weight_loss": -500,
    "mild_weight_loss": -250,
    "maintenance": 0,
    "mild_weight_gain": 250,
    "weight_gain": 500,
}

DRI_VALUE_KEYS: list[str] = ["rda", "ai", "ul", "ear"]
