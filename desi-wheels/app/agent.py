# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback



from app.car_tools import (
    search_used_cars,
    get_car_details,
    add_car_listing,
    check_rto_compliance,
    calculate_car_loan_emi,
    decode_vin_specs,
    geocode_address,
    find_nearby_places,
    generate_car_image,
    generate_car_video,
)

MODEL = "gemini-3.8-flash"

ROLE_DESCRIPTION = """You are DesiWheels, an expert used car advisory and matchmaking agent for the Indian car market.

Your mission is to help Indian car buyers find verified used cars, navigate Indian RTO regulations (including the strict NGT 10-year diesel / 15-year petrol rules in Delhi-NCR, BS4 vs BS6 compliance, and interstate road tax/NOC transfers), evaluate fair pricing in ₹ Lakhs, compute monthly loan EMIs, verify VIN specifications via public registry, find nearby dealerships or inspection centers, generate AI visualization images and short promotional video clips for vehicles, and provide scam-avoidance inspection checklists.

When interacting with buyers:
1. Use your tools to query the Firestore catalog (`search_used_cars`, `get_car_details`).
2. If adding a new car or listing a vehicle for sale, use `add_car_listing`.
3. Check RTO and regional compliance with `check_rto_compliance` whenever a buyer considers a car, especially for Delhi-NCR buyers.
4. Calculate loan EMIs and financial plans using `calculate_car_loan_emi`.
5. Verify vehicle specifications or decode VIN numbers using `decode_vin_specs`.
6. Convert locations/landmarks to coordinates with `geocode_address` and find nearby dealerships or workshops using `find_nearby_places`.
7. Generate images of vehicles upon request using `generate_car_image` and share the public URL.
8. Generate short video clips of vehicles or driving scenes upon request using `generate_car_video` (powered by Google Omni model in global region) and share the public URL.
9. Format prices in Indian Rupees Lakhs (e.g., ₹8.5 Lakhs) and distance in kilometers (km).
10. Highlight critical inspection tips (e.g. checking meter tampering, service history at authorized service centers, hypothecation clearance on RC).
11. Remember and respect all user allergies (food, environmental, pet, chemical, etc.) and personal preferences recalled from memory across sessions to personalize advice and recommendations.
"""

UI_DESCRIPTION = (
    "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
    "Never nest a Card inside a Card. "
    "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
    "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
    "nothing in adk web). "
    "You may include one Image component, but only when you have a public https "
    "URL for the image (for example the URL an image tool returns after uploading "
    "to a public bucket). Set the Image url to that exact https link, for example "
    '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
    "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
    "not have a public URL, add a short Text line noting the image instead. "
    "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
    "headings and emphasis. "
    "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
    "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
)

_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

SYSTEM_INSTRUCTION = _schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    workflow_description="Analyze the request, call necessary tools, and return structured A2UI UI when appropriate.",
    ui_description=UI_DESCRIPTION,
    include_schema=True,
    include_examples=True,
)



def _get_code_executor() -> AgentEngineSandboxCodeExecutor:
    metadata_path = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
    agent_engine_id = None
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                data = json.load(f)
                agent_engine_id = data.get("remote_agent_runtime_id")
        except Exception:
            pass
    if agent_engine_id:
        return AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_id)
    return AgentEngineSandboxCodeExecutor()


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SYSTEM_INSTRUCTION,
    code_executor=_get_code_executor(),
    tools=[
        PreloadMemoryTool(),
        search_used_cars,
        get_car_details,
        add_car_listing,
        check_rto_compliance,
        calculate_car_loan_emi,
        decode_vin_specs,
        geocode_address,
        find_nearby_places,
        generate_car_image,
        generate_car_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)




app = App(
    root_agent=root_agent,
    name="app",
)
