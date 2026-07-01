from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from models import ClarifiedRequirements, DesignState, ERSchema, OpenAPISpec, PRD
from .helpers import (
    _coerce_clarified_requirements,
    _coerce_prd,
    _coerce_openapi,
    _coerce_er_schema,
    format_clarified_requirements,
    format_prd,
    format_openapi,
    format_er_schema,
)
from .prompts import ER_SYSTEM_PROMPT

from .llm import get_chat_model


def _build_er_messages(state: DesignState) -> list[SystemMessage | HumanMessage]:
    clarified_requirements = _coerce_clarified_requirements(state.get("clarified_requirements"))
    prd = _coerce_prd(state.get("prd"))
    openapi_schema = _coerce_openapi(state.get("openapi_schema"))
    existing_er = _coerce_er_schema(state.get("er_schema"))

    if clarified_requirements is None:
        raise ValueError("clarified_requirements is required before generating an ER schema.")
    if prd is None:
        raise ValueError("prd is required before generating an ER schema.")
    if openapi_schema is None:
        raise ValueError("openapi_schema is required before generating an ER schema.")

    mode = "revise" if existing_er is not None else "create"

    messages: list[SystemMessage | HumanMessage] = [SystemMessage(content=ER_SYSTEM_PROMPT)]
    messages.append(
        HumanMessage(
            content=(
                f"Mode: {mode}\n\n"
                f"Clarified requirements:\n{format_clarified_requirements(clarified_requirements)}\n\n"
                f"PRD:\n{format_prd(prd)}\n\n"
                f"OpenAPI spec:\n{format_openapi(openapi_schema)}"
            )
        )
    )

    if existing_er is not None:
        messages.append(
            HumanMessage(
                content=(
                    "Existing ER schema to revise:\n"
                    f"{format_er_schema(existing_er)}"
                )
            )
        )

    return messages


async def run_er_agent(state: DesignState) -> dict[str, Any]:
    model = get_chat_model().with_structured_output(ERSchema)
    messages = _build_er_messages(state)
    er_schema = await model.ainvoke(messages)
    return {"er_schema": er_schema.model_dump()}


async def er_node(state: DesignState) -> dict[str, Any]:
    return await run_er_agent(state)
