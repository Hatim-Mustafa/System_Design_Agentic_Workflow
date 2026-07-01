from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from models import ClarifiedRequirements, DesignState, OpenAPISpec, PRD
from .helpers import (
    _coerce_clarified_requirements,
    _coerce_prd,
    _coerce_openapi,
    format_clarified_requirements,
    format_prd,
    format_openapi,
    _coerce_gherkin,
    format_gherkin
)
from .prompts import OPENAPI_SYSTEM_PROMPT

from .llm import get_chat_model


def _build_openapi_messages(state: DesignState) -> list[SystemMessage | HumanMessage]:
    clarified_requirements = _coerce_clarified_requirements(state.get("clarified_requirements"))
    prd = _coerce_prd(state.get("prd"))
    gherkin = _coerce_gherkin(state.get("acceptance_criteria"))
    existing_openapi = _coerce_openapi(state.get("openapi_schema"))

    if clarified_requirements is None:
        raise ValueError("clarified_requirements is required before generating OpenAPI.")
    if prd is None:
        raise ValueError("prd is required before generating OpenAPI.")
    if gherkin is None:
        raise ValueError("acceptance_criteria is required before generating OpenAPI.")

    mode = "revise" if existing_openapi is not None else "create"

    messages: list[SystemMessage | HumanMessage] = [SystemMessage(content=OPENAPI_SYSTEM_PROMPT)]
    messages.append(
        HumanMessage(
            content=(
                f"Mode: {mode}\n\n"
                f"Clarified requirements:\n{format_clarified_requirements(clarified_requirements)}\n\n"
                f"PRD:\n{format_prd(prd)}\n\n"
                f"Gherkin scenarios:\n{format_gherkin(gherkin)}"
            )
        )
    )

    if existing_openapi is not None:
        messages.append(
            HumanMessage(
                content=(
                    "Existing OpenAPI spec to revise:\n"
                    f"{format_openapi(existing_openapi)}"
                )
            )
        )

    return messages


async def run_openapi_agent(state: DesignState) -> dict[str, Any]:
    model = get_chat_model().with_structured_output(OpenAPISpec)
    messages = _build_openapi_messages(state)
    openapi_schema = await model.ainvoke(messages)
    return {"openapi_schema": openapi_schema.model_dump()}


async def openapi_node(state: DesignState) -> dict[str, Any]:
    return await run_openapi_agent(state)
