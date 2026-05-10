from mcp.server.fastmcp import FastMCP

from tools.check_drug_food_interaction_tool import check_drug_food_interaction
from tools.check_meal_plan_interactions_tool import check_meal_plan_interactions
from tools.classify_interaction_severity_tool import classify_interaction_severity
from tools.get_interactions_for_drug_tool import get_interactions_for_drug
from tools.get_interactions_for_food_tool import get_interactions_for_food
from tools.get_substitution_for_interaction_tool import get_substitution_for_interaction

mcp = FastMCP("NutriPlan Drug Nutrient MCP Server", stateless_http=True, host="0.0.0.0", port=8001)

_original_get_capabilities = mcp._mcp_server.get_capabilities


def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/drug-nutrient-context": {
            "scopes": []
        }
    }
    return caps


mcp._mcp_server.get_capabilities = _patched_get_capabilities


mcp.tool(
    name="CheckDrugFoodInteraction",
    description="Checks whether a specific drug and a specific food or nutrient have a curated interaction, returning severity, mechanism, and recommendation.",
)(check_drug_food_interaction)

mcp.tool(
    name="CheckMealPlanInteractions",
    description="Cross-checks a list of medications against a list of meal-plan ingredients and reports every flagged drug-food pair, sorted by severity.",
)(check_meal_plan_interactions)

mcp.tool(
    name="GetInteractionsForDrug",
    description="Lists all curated food and nutrient interactions for a given drug, optionally filtered by minimum severity.",
)(get_interactions_for_drug)

mcp.tool(
    name="GetInteractionsForFood",
    description="Lists all curated drug interactions for a given food or nutrient, grouped by drug class and optionally filtered by minimum severity.",
)(get_interactions_for_food)

mcp.tool(
    name="GetSubstitutionForInteraction",
    description="Returns curated food substitutions to avoid a specific drug-food interaction while preserving culinary intent.",
)(get_substitution_for_interaction)

mcp.tool(
    name="ClassifyInteractionSeverity",
    description="Returns a one-line classification of the severity of a drug-food interaction, with a brief mechanism and the evidence source.",
)(classify_interaction_severity)
