from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from models import ClarifiedRequirements, DesignState, PRD

from .llm import get_chat_model

PRD_SYSTEM_PROMPT = """You are the PRD agent for a design-workflow system.
Your job is to produce a grounded product requirements document from clarified requirements.

Rules:
- Use the clarified requirements as the source of truth.
- If an existing PRD is present, revise it rather than starting from scratch.
- If no PRD exists, create a new one.
- Keep the PRD practical, business-focused, and implementation-agnostic.
- Preserve traceability and use the clarified requirements to inform goals, non-goals, stakeholders, features, and open questions.
- Return only a structured PRD.
"""


def _coerce_clarified_requirements(
    requirements: ClarifiedRequirements | dict[str, Any] | None,
) -> ClarifiedRequirements | None:
    if requirements is None:
        return None
    if isinstance(requirements, ClarifiedRequirements):
        return requirements
    return ClarifiedRequirements.model_validate(requirements)


def _coerce_prd(prd: PRD | dict[str, Any] | None) -> PRD | None:
    if prd is None:
        return None
    if isinstance(prd, PRD):
        return prd
    return PRD.model_validate(prd)


def format_clarified_requirements(requirements: ClarifiedRequirements | dict[str, Any]) -> str:
    if isinstance(requirements, ClarifiedRequirements):
        data = requirements.model_dump()
    else:
        data = requirements

    return (
        f"Project name: {data.get('project_name', 'Unknown project')}\n"
        f"Problem statement: {data.get('problem_statement', 'Not provided')}\n"
        f"Target users: {', '.join(data.get('target_users', [])) or 'None'}\n"
        f"Core features: {', '.join(data.get('core_features', [])) or 'None'}\n"
        f"Out of scope: {', '.join(data.get('out_of_scope', [])) or 'None'}\n"
        f"Constraints: {', '.join(data.get('constraints', [])) or 'None'}\n"
        f"Assumptions: {', '.join(data.get('assumptions', [])) or 'None'}"
    )


def format_prd(prd: PRD | dict[str, Any]) -> str:
    if isinstance(prd, PRD):
        data = prd.model_dump()
    else:
        data = prd

    stakeholders = data.get("stakeholders", [])
    features = data.get("features", [])

    stakeholder_text = "\n".join(
        f"- {item.get('role', 'Unknown role')}: {', '.join(item.get('goals', [])) or 'No goals listed'}"
        for item in stakeholders
    ) or "None"

    feature_text = "\n".join(
        f"- {item.get('id', 'F-000')} {item.get('name', 'Unnamed feature')} ({item.get('priority', 'unknown')}): {item.get('description', '')}"
        for item in features
    ) or "None"

    return (
        f"Project name: {data.get('project_name', 'Unknown project')}\n"
        f"Problem statement: {data.get('problem_statement', 'Not provided')}\n"
        f"Goals: {', '.join(data.get('goals', [])) or 'None'}\n"
        f"Non-goals: {', '.join(data.get('non_goals', [])) or 'None'}\n"
        f"Stakeholders:\n{stakeholder_text}\n"
        f"Features:\n{feature_text}\n"
        f"Open questions: {', '.join(data.get('open_questions', [])) or 'None'}"
    )


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
