# NutriPlan — MCP Servers

Five Model Context Protocol (MCP) servers powering NutriPlan, a multi-agent clinical AI system for personalized, evidence-based meal planning grounded in real patient data, real food data, and real drug-food interaction safety.

---

## Overview

NutriPlan exposes five domain-focused MCP servers that any clinical AI agent can call:

| Server | Role | Auth Required |
|---|---|---|
| FHIR Parser MCP | Pulls structured patient data from any FHIR R4 server | Yes (bearer token via header) |
| Clinical Knowledge Base MCP | Evidence-based dietary guidelines (AHA, ADA, ACC, AAN) | No |
| User Context MCP | Dietary preferences and cultural food patterns | No |
| Nutrition Database MCP | USDA FoodData Central integration | Yes (USDA API key via header) |
| Drug-Nutrient Interaction MCP | Curated drug-food interaction database | No |

Each server is independently deployable and exposes typed tools via the streamable-HTTP MCP transport.

---

## Architecture

Each MCP server is a Python service built on FastMCP, with tools defined as typed Pydantic functions exposed over the Model Context Protocol. The starting point for every server was the official Python MCP template  provided by the Prompt Opinion community (https://github.com/prompt-opinion/po-community-mcp.git) — a clean FastMCP scaffold handling streamable-HTTP transport, request context, and tool registration.

---

## Requirements

### System

- Python 3.11 or higher
- A Linux, macOS, or Windows host (Linux recommended for production)
- Outbound internet access to FHIR servers and USDA FoodData Central (for the relevant servers)

### Python Dependencies
The following are required across all five servers:
```
fastapi>=0.115.0
uvicorn>=0.32.0
mcp>=1.9.0
httpx>=0.28.0
PyJWT>=2.10.0
```
A consolidated `requirements.txt` is provided at the root for installing all dependencies in one step.

---

## Authentication

Two of the five servers require authentication via HTTP request headers:

### FHIR Parser MCP

The MCP request must include:

- `x-fhir-server-url` — the FHIR R4 endpoint URL (e.g., `https://fhir.example.com/r4`)
- `x-fhir-access-token` — a bearer token authorized for the patient's data

The server decodes the JWT to extract the patient claim and uses the token for all downstream FHIR API calls.

### Nutrition Database MCP

The MCP request should include:

- `x-usda-api-key` — a registered USDA API key (rate limit: 1000 requests/hour)

If absent, the server falls back to the public ***DEMO_KEY*** (rate limit: 50 requests/hour) for prototyping. Register a free key at https://fdc.nal.usda.gov/api-key-signup.html.

---

## Deployment

All five servers in this repo are designed to run independently on dedicated ports. A typical deployment runs each server in its own process or container. For production, consider:

- Process supervision (systemd, supervisord, or similar)
- Reverse proxy (nginx, Caddy) for HTTPS termination
- Per-server environment configuration via `.env` files

---

## Disclaimer

This software is provided for research, educational, and demonstration purposes. It is not a medical device, has not been clinically validated, and must not be used as the sole basis for clinical decisions. Healthcare professionals should always exercise independent clinical judgment. The authors disclaim all liability for use in clinical settings.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---
