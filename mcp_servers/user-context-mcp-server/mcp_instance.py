from mcp.server.fastmcp import FastMCP

from tools.build_preference_profile_tool import build_preference_profile
from tools.get_cultural_food_patterns_tool import get_cultural_food_patterns
# from tools.get_preference_questions_tool import get_preference_questions

mcp = FastMCP("NutriPlan User Context MCP Server", stateless_http=True, host="0.0.0.0", port=8004)

_original_get_capabilities = mcp._mcp_server.get_capabilities


def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/user-context": {
            "scopes": []
        }
    }
    return caps


mcp._mcp_server.get_capabilities = _patched_get_capabilities


mcp.tool(
    name="BuildPreferenceProfile",
    description="Builds a structured Preference Profile block from supplied patient preferences for the Meal Planning Agent to consume verbatim.",
)(build_preference_profile)

# mcp.tool(
#     name="GetPreferenceQuestions",
#     description="Returns the suggested questions the Dietary Preference Agent should ask the patient, optionally filtered to specific missing fields.",
# )(get_preference_questions)

mcp.tool(
    name="GetCulturalFoodPatterns",
    description="Returns the curated staples, proteins, spices, cooking methods, and fasting traditions for a cultural food pattern (lookup by key or alias).",
)(get_cultural_food_patterns)
