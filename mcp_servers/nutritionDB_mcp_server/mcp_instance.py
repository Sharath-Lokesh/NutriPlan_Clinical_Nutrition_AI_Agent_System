from mcp.server.fastmcp import FastMCP

from tools.filter_foods_by_diet_tool import filter_foods_by_diet
from tools.find_foods_by_nutrient_tool import find_foods_by_nutrient
from tools.get_food_allergens_tool import get_food_allergens
from tools.get_food_glycemic_index_tool import get_food_glycemic_index
from tools.get_food_nutrients_tool import get_food_nutrients
from tools.get_recipe_nutrients_tool import get_recipe_nutrients
from tools.get_serving_sizes_tool import get_serving_sizes
from tools.search_food_tool import search_food
from tools.suggest_food_substitute_tool import suggest_food_substitute

mcp = FastMCP("NutriPlan Nutrition MCP Server", stateless_http=True, host="0.0.0.0", port=8003)

_original_get_capabilities = mcp._mcp_server.get_capabilities


def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/nutrition-context": {
            "scopes": []
        }
    }
    return caps


mcp._mcp_server.get_capabilities = _patched_get_capabilities


mcp.tool(
    name="SearchFood",
    description="Searches USDA FoodData Central for foods matching a query, returning FDC IDs and descriptions.",
)(search_food)

mcp.tool(
    name="GetFoodNutrients",
    description="Gets the nutrient panel (energy, macros, key micros) for a food by FDC ID, or specific nutrients if requested.",
)(get_food_nutrients)

mcp.tool(
    name="GetFoodGlycemicIndex",
    description="Looks up the glycemic index and glycemic load for a food using a curated reference table.",
)(get_food_glycemic_index)

mcp.tool(
    name="GetFoodAllergens",
    description="Detects Big-8 allergens (milk, eggs, fish, shellfish, tree nuts, peanuts, wheat, soy) in a USDA food entry.",
)(get_food_allergens)

mcp.tool(
    name="GetServingSizes",
    description="Returns the available household serving sizes and their gram weights for a food.",
)(get_serving_sizes)

mcp.tool(
    name="GetRecipeNutrients",
    description="Aggregates nutrients across a list of ingredients (each with FDC ID and grams) into a single nutrition panel.",
)(get_recipe_nutrients)

mcp.tool(
    name="FindFoodsByNutrient",
    description="Finds foods within an optional category whose amount of a given nutrient falls inside an optional min/max range.",
)(find_foods_by_nutrient)

mcp.tool(
    name="FilterFoodsByDiet",
    description="Filters a list of foods by a diet (vegan, vegetarian, gluten-free, halal, kosher, low-fodmap, dairy-free), reporting pass/fail per food.",
)(filter_foods_by_diet)

mcp.tool(
    name="SuggestFoodSubstitute",
    description="Suggests substitute foods within the same category, optionally matching a target nutrient amount within ±20% and excluding given keywords.",
)(suggest_food_substitute)
