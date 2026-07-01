from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from models import ClarifiedRequirements, DesignState, PRD
from .helpers import (
    _coerce_clarified_requirements,
    _coerce_prd,
    format_clarified_requirements,
    format_prd,
)
from .prompts import PRD_SYSTEM_PROMPT

from .llm import get_chat_model


def _build_prd_messages(state: DesignState) -> list[SystemMessage | HumanMessage]:
    clarified_requirements = _coerce_clarified_requirements(state.get("clarified_requirements"))
    if clarified_requirements is None:
        raise ValueError("clarified_requirements is required before generating a PRD.")

    existing_prd = _coerce_prd(state.get("prd"))
    mode = "revise" if existing_prd is not None else "create"

    messages: list[SystemMessage | HumanMessage] = [SystemMessage(content=PRD_SYSTEM_PROMPT)]
    messages.append(
        HumanMessage(
            content=(
                f"Mode: {mode}\n\n"
                f"Clarified requirements:\n{format_clarified_requirements(clarified_requirements)}"
            )
        )
    )

    if existing_prd is not None:
        messages.append(
            HumanMessage(
                content=(
                    "Existing PRD to revise:\n"
                    f"{format_prd(existing_prd)}"
                )
            )
        )

    intake_messages = state.get("intake_messages", [])
    if intake_messages:
        messages.append(
            HumanMessage(
                content=(
                    "Intake conversation history:\n"
                    "Use the following conversation for additional context and wording cues.\n"
                    f"{intake_messages}"
                )
            )
        )

    return messages


async def run_prd_agent(state: DesignState) -> dict[str, Any]:
    model = get_chat_model().with_structured_output(PRD)
    messages = _build_prd_messages(state)
    prd = await model.ainvoke(messages)
    return {"prd": prd.model_dump()}


async def prd_node(state: DesignState) -> dict[str, Any]:
    return await run_prd_agent(state)
