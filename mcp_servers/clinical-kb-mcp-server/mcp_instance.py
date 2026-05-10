from mcp.server.fastmcp import FastMCP

from tools.calculate_caloric_target_tool import calculate_caloric_target
from tools.get_condition_guideline_tool import get_condition_guideline
from tools.get_dri_tool import get_dri
from tools.get_evidence_protocol_tool import get_evidence_protocol
from tools.get_hard_exclusions_tool import get_hard_exclusions
from tools.get_macronutrient_ratios_tool import get_macronutrient_ratios
from tools.get_micronutrient_priorities_tool import get_micronutrient_priorities
from tools.get_rda_tool import get_rda

mcp = FastMCP("NutriPlan Clinical Knowledge Base", stateless_http=True, host="0.0.0.0", port=8000)

_original_get_capabilities = mcp._mcp_server.get_capabilities


def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/clinical-kb-context": {
            "scopes": []
        }
    }
    return caps


mcp._mcp_server.get_capabilities = _patched_get_capabilities


mcp.tool(
    name="GetConditionGuideline",
    description="Returns the curated evidence-based clinical nutrition guideline for a condition (lookup by name, alias, ICD-10, or SNOMED).",
)(get_condition_guideline)

mcp.tool(
    name="GetRDA",
    description="Returns the Recommended Dietary Allowance (or Adequate Intake when no RDA exists) for a nutrient given sex, age, and pregnancy/lactation status.",
)(get_rda)

mcp.tool(
    name="GetDRI",
    description="Returns the full Dietary Reference Intake row (RDA, AI, UL, EAR) for a nutrient given sex, age, and pregnancy/lactation status.",
)(get_dri)

mcp.tool(
    name="CalculateCaloricTarget",
    description="Calculates BMR (Mifflin-St Jeor), TDEE (using activity factor), and goal-adjusted caloric target for an adult.",
)(calculate_caloric_target)

mcp.tool(
    name="GetMacronutrientRatios",
    description="Returns curated macronutrient distribution (carb/protein/fat percentages) for a clinical condition or goal.",
)(get_macronutrient_ratios)

mcp.tool(
    name="GetMicronutrientPriorities",
    description="Returns the curated list of micronutrients to emphasise and to limit for a clinical condition.",
)(get_micronutrient_priorities)

mcp.tool(
    name="GetHardExclusions",
    description="Returns the curated list of foods, ingredients, and food categories that must be excluded (or strongly avoided) for a clinical condition.",
)(get_hard_exclusions)

mcp.tool(
    name="GetEvidenceProtocol",
    description="Returns the curated definition, indications, components, macro ratio, and key trials for a named evidence-based dietary protocol.",
)(get_evidence_protocol)
