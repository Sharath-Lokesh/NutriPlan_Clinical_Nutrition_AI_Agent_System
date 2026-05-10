NUTRIENT_ENERGY_KCAL = 1008
NUTRIENT_PROTEIN = 1003
NUTRIENT_FAT = 1004
NUTRIENT_CARBS = 1005
NUTRIENT_FIBER = 1079
NUTRIENT_SUGARS = 2000
NUTRIENT_SODIUM = 1093
NUTRIENT_POTASSIUM = 1092
NUTRIENT_CALCIUM = 1087
NUTRIENT_IRON = 1089
NUTRIENT_MAGNESIUM = 1090
NUTRIENT_PHOSPHORUS = 1091
NUTRIENT_ZINC = 1095
NUTRIENT_VITAMIN_A_RAE = 1106
NUTRIENT_VITAMIN_D = 1114
NUTRIENT_VITAMIN_E = 1109
NUTRIENT_VITAMIN_K = 1185
NUTRIENT_VITAMIN_C = 1162
NUTRIENT_THIAMIN = 1165
NUTRIENT_RIBOFLAVIN = 1166
NUTRIENT_NIACIN = 1167
NUTRIENT_VITAMIN_B6 = 1175
NUTRIENT_VITAMIN_B12 = 1178
NUTRIENT_FOLATE = 1177
NUTRIENT_SAT_FAT = 1258
NUTRIENT_TRANS_FAT = 1257
NUTRIENT_MONO_FAT = 1292
NUTRIENT_POLY_FAT = 1293
NUTRIENT_CHOLESTEROL = 1253
NUTRIENT_WATER = 1051
NUTRIENT_CAFFEINE = 1057


CURATED_NUTRIENT_PANEL: list[int] = [
    NUTRIENT_ENERGY_KCAL,
    NUTRIENT_PROTEIN,
    NUTRIENT_FAT,
    NUTRIENT_SAT_FAT,
    NUTRIENT_TRANS_FAT,
    NUTRIENT_CHOLESTEROL,
    NUTRIENT_CARBS,
    NUTRIENT_FIBER,
    NUTRIENT_SUGARS,
    NUTRIENT_SODIUM,
    NUTRIENT_POTASSIUM,
    NUTRIENT_CALCIUM,
    NUTRIENT_IRON,
    NUTRIENT_MAGNESIUM,
    NUTRIENT_VITAMIN_D,
    NUTRIENT_VITAMIN_C,
    NUTRIENT_VITAMIN_B12,
    NUTRIENT_FOLATE,
]


USDA_DATA_TYPES: list[str] = ["Foundation", "SR Legacy", "Survey (FNDDS)", "Branded"]


ALLERGEN_KEYWORDS: dict[str, list[str]] = {
    "milk": ["milk", "butter", "cheese", "cream", "whey", "casein", "lactose", "yogurt"],
    "eggs": ["egg", "albumin"],
    "fish": ["fish", "anchovy", "salmon", "tuna", "cod", "tilapia"],
    "shellfish": ["shrimp", "crab", "lobster", "prawn", "crayfish"],
    "tree_nuts": [
        "almond",
        "walnut",
        "cashew",
        "pecan",
        "pistachio",
        "hazelnut",
        "macadamia",
        "brazil nut",
    ],
    "peanuts": ["peanut"],
    "wheat": ["wheat", "flour", "bread", "pasta", "semolina"],
    "soy": ["soy", "soybean", "tofu", "edamame", "tempeh"],
}
