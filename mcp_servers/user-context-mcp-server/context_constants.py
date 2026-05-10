COOKING_SKILLS = ["novice", "intermediate", "advanced"]
DIET_PATTERNS = ["vegan", "vegetarian", "omnivore", "pescatarian", "halal", "kosher", "none"]
TASTE_DIMENSIONS = ["sweet", "salty", "spicy", "umami", "bitter", "sour"]
TASTE_LEVELS = ["low", "medium", "high"]
COMMON_EQUIPMENT = [
    "oven",
    "stovetop",
    "microwave",
    "blender",
    "instant pot",
    "air fryer",
    "slow cooker",
    "grill",
]

PREFERENCE_QUESTIONS = [
    {
        "field": "cuisines",
        "question": "Which cuisines do you most enjoy? (e.g. italian, japanese, mexican, indian)",
        "type": "list",
    },
    {
        "field": "dislikes",
        "question": "Are there any foods or ingredients you dislike or want to avoid?",
        "type": "list",
    },
    {
        "field": "dietPattern",
        "question": "Do you follow a particular diet pattern?",
        "type": "single_select",
        "options": DIET_PATTERNS,
    },
    {
        "field": "cookingSkill",
        "question": "How would you describe your cooking skill?",
        "type": "single_select",
        "options": COOKING_SKILLS,
    },
    {
        "field": "equipment",
        "question": "What kitchen equipment do you have available?",
        "type": "multi_select",
        "options": COMMON_EQUIPMENT,
    },
    {
        "field": "tasteProfile",
        "question": "How do you feel about each taste? (sweet/salty/spicy/umami/bitter/sour — low, medium, or high)",
        "type": "taste_map",
    },
    {
        "field": "budgetNote",
        "question": "Any budget constraints we should consider?",
        "type": "free_text",
    },
    {
        "field": "scheduleNote",
        "question": "Any schedule constraints? (e.g. limited weekday cooking time, shift work)",
        "type": "free_text",
    },
    {
        "field": "fastingNote",
        "question": "Do you observe any fasting practices we should respect?",
        "type": "free_text",
    },
]
