from mcp.server.fastmcp import FastMCP

from tools.patient_age_tool import get_patient_age
from tools.patient_allergies_tool import get_patient_allergies
from tools.patient_id_tool import find_patient_id
from tools.patient_conditions_tool import get_patient_conditions
from tools.patient_demographics_tool import get_patient_demographics
from tools.patient_medications_tool import get_patient_medications
from tools.patient_observations_tool import get_patient_observations
from tools.patient_procedures_tool import get_patient_procedures
# from tools.patient_sdoh_tool import get_patient_sdoh
from tools.patient_vitals_tool import get_patient_vitals
from tools.resolve_clinical_code_tool import resolve_clinical_code

mcp = FastMCP("NutriPlan FHIR Parser MCP Server", stateless_http=True, host="0.0.0.0", port =8002)

_original_get_capabilities = mcp._mcp_server.get_capabilities

def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/fhir-context": {
            "scopes": [
                {"name": "patient/Patient.rs", "required": True},
                {"name": "patient/Observation.rs"},
                {"name": "patient/Condition.rs"},
                {"name": "patient/AllergyIntolerance.rs"},
                {"name": "patient/MedicationRequest.rs"},
                {"name": "patient/MedicationStatement.rs"},
                {"name": "patient/Procedure.rs"},
            ]
        }
    }
    # print(f"[CAPABILITIES] Returning extensions: {caps.model_extra.get('extensions')}")
    return caps

mcp._mcp_server.get_capabilities = _patched_get_capabilities

mcp.tool(
    name="GetPatientAge",
    description="Gets the age of a patient.",
)(get_patient_age)

mcp.tool(
    name="GetPatientAllergies",
    description="Gets the known allergies of a patient.",
)(get_patient_allergies)

mcp.tool(
    name="FindPatientId",
    description="Finds a patient id given a first name and last name.",
)(find_patient_id)

mcp.tool(
    name="GetPatientConditions",
    description="Gets the active (or filtered) clinical conditions of a patient.",
)(get_patient_conditions)

mcp.tool(
    name="GetPatientMedications",
    description="Gets the active medications of a patient from MedicationStatement and optionally MedicationRequest.",
)(get_patient_medications)

mcp.tool(
    name="GetPatientObservations",
    description="Gets recent laboratory or other observations for a patient, returning the latest value per LOINC code.",
)(get_patient_observations)

mcp.tool(
    name="GetPatientVitals",
    description="Gets the latest vital signs (height, weight, BMI, BP, waist) for a patient.",
)(get_patient_vitals)

mcp.tool(
    name="GetPatientDemographics",
    description="Gets the patient demographics including sex, age, race, and ethnicity.",
)(get_patient_demographics)

# mcp.tool(
#     name="GetPatientSDOH",
#     description="Gets the patient's social determinants of health (food insecurity, housing instability, income).",
# )(get_patient_sdoh)

mcp.tool(
    name="GetPatientProcedures",
    description="Gets the patient's nutrition-relevant past procedures (bariatric, bowel resection, cholecystectomy, etc.).",
)(get_patient_procedures)

mcp.tool(
    name="ResolveClinicalCode",
    description="Resolves a clinical code (SNOMED, LOINC, RxNorm, or full system URI) to its display name via FHIR terminology lookup.",
)(resolve_clinical_code)
