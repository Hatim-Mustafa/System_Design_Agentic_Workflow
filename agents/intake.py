from __future__ import annotations

import asyncio
from typing import Any, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from models import ClarifiedRequirements, ClarifyingQuestions, DesignState

from .llm import get_chat_model
from .helpers import _coerce_clarified_requirements, format_clarified_requirements

INTAKE_SYSTEM_PROMPT = """You are the intake agent for a design-workflow system.
Your job is to turn a rough product idea and any prior clarification into a complete ClarifiedRequirements object.

Rules:
- Be concise and concrete.
- Prefer grounded assumptions over inventing requirements.
- Put uncertain items into assumptions.
- Keep the output aligned with the schema exactly.
- Do not mention implementation details or downstream agent stages.
- If the idea is too vague, infer the most likely interpretation and capture uncertainty in assumptions.
"""

QUESTION_SYSTEM_PROMPT = """You are analyzing a rough product idea and need to ask a single clarifying question for a non-technical user.
The user is a business person, not a developer. Ask ONLY business and user-focused questions—never ask about technology, architecture, or implementation.
Return a small batch of short questions that you want answered before you can confidently design the product.
Ask as many questions as you want, but keep them short, direct, and business-focused."""


def _is_requirements_complete(req: ClarifiedRequirements | None) -> bool:
    """Check if ClarifiedRequirements object has sufficient content to proceed."""
    req = _coerce_clarified_requirements(req)
    if req is None:
        return False

    # All fields must be populated and non-empty
    return bool(
        req.project_name
        and req.problem_statement
        and req.target_users
        and req.core_features
        and req.out_of_scope
        and req.constraints
        and req.assumptions
    )


def _format_conversation_summary(state: DesignState) -> str:
    parts: list[str] = [f"Raw idea: {state['raw_idea']}"]

    clarified = _coerce_clarified_requirements(state.get("clarified_requirements"))
    if clarified is not None:
        parts.append(
            "Existing clarified requirements were already captured; refine them rather than restarting from scratch."
        )

    return "\n".join(parts)


def build_intake_messages(state: DesignState) -> list[BaseMessage]:
    messages: list[BaseMessage] = [SystemMessage(content=INTAKE_SYSTEM_PROMPT)]

    prior_messages: Sequence[BaseMessage] = state.get("intake_messages", [])
    if prior_messages:
        messages.extend(prior_messages)

    messages.append(HumanMessage(content=_format_conversation_summary(state)))
    return messages


async def _generate_next_questions(state: DesignState) -> list[str]:
    """Generate a batch of clarifying questions based on the current state."""
    model = get_chat_model()
    
    prompt = f"""Based on this product idea "{state['raw_idea']}", generate the smallest useful batch of clarifying questions that would help you confidently understand the product.

Questions should be:
- short
- non-technical
- focused on business goals, users, workflows, priorities, and scope
- ordered from most important to least important
- returned as a list

Return the result as a structured list of questions only."""

    messages = [
        SystemMessage(content=QUESTION_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    
    response = await model.with_structured_output(ClarifyingQuestions).ainvoke(messages)
    return response.questions


async def run_intake_agent(state: DesignState) -> dict[str, Any]:
    """Run the intake agent with a batch of clarifying questions followed by one synthesis pass."""
    model = get_chat_model().with_structured_output(ClarifiedRequirements)

    questions = await _generate_next_questions(state)

    new_messages = list(state.get("intake_messages", []))
    for question in questions:
        user_response = await asyncio.to_thread(input, f"\n{question}\nYour response: ")
        new_messages.append(AIMessage(content=question))
        new_messages.append(HumanMessage(content=f"User answer: {user_response}"))

    messages: list[BaseMessage] = [SystemMessage(content=INTAKE_SYSTEM_PROMPT)]
    messages.extend(new_messages)

    clarified_requirements = await model.ainvoke(messages)

    # Check if we have enough information
    if _is_requirements_complete(clarified_requirements):
        return {
            "clarifying_questions": questions,
            "clarified_requirements": clarified_requirements.model_dump(),
        }
    return {
        "clarifying_questions": questions,
        "intake_messages": new_messages,
        "clarified_requirements": clarified_requirements.model_dump(),  # Keep partial progress as plain data
    }


async def intake_node(state: DesignState) -> dict[str, Any]:
    """LangGraph node wrapper for the intake agent."""
    return await run_intake_agent(state)
