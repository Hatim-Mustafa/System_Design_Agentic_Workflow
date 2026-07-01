from __future__ import annotations

import asyncio
import json
import pickle
from typing import Any

from langgraph.types import Command

from graph import get_graph
from models import DesignState

STATE_SNAPSHOT_PATH = "design_state_snapshot.bin"


def build_initial_state(raw_idea: str) -> DesignState:
    return {
        "raw_idea": raw_idea,
        "intake_messages": [],
        "clarifying_questions": [],
        "clarified_requirements": None,
        "prd": None,
        "acceptance_criteria": None,
        "openapi_schema": None,
        "er_schema": None,
        "critique_history": [],
        "revision_counts": {},
        "max_revisions": 3,
        "documents_finalized": False,
    }


def save_state_snapshot(state: dict[str, Any], snapshot_path: str = STATE_SNAPSHOT_PATH) -> None:
    with open(snapshot_path, "wb") as snapshot_file:
        pickle.dump(state, snapshot_file)


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


async def run_workflow_with_interrupts(raw_idea: str) -> dict[str, Any]:
    """Run the workflow and handle interrupts interactively."""
    graph = get_graph()
    input_payload: Any = build_initial_state(raw_idea)
    config = {"configurable": {"thread_id": "main"}}

    while True:
        final_state: dict[str, Any] | None = None
        interrupted = False

        async for chunk in graph.astream(input_payload, config, stream_mode="values", version="v2"):
            if isinstance(chunk, dict) and chunk.get("interrupts"):
                interrupt_message = chunk["interrupts"][0].value
                print(f"\n{interrupt_message}")

                user_input = input("\nYour response: ").strip()
                input_payload = Command(resume=user_input)
                interrupted = True
                break

            if isinstance(chunk, dict) and "data" in chunk:
                final_state = chunk["data"]

        if interrupted:
            continue

        if final_state is not None:
            return final_state

        return {}


def main() -> None:
    raw_idea = input("Enter a rough product idea: ").strip()

    if not raw_idea:
        raise SystemExit("A raw idea is required to run the workflow.")

    try:
        final_state = asyncio.run(run_workflow_with_interrupts(raw_idea))
        save_state_snapshot(final_state)

        clarified_requirements = final_state.get("clarified_requirements")
        prd = final_state.get("prd")

        if clarified_requirements or prd:
            print("\n✓ Workflow complete! Here's what was produced:")

            if clarified_requirements:
                print("\nClarified requirements:")
                print(json.dumps(_serialize_value(clarified_requirements), indent=2))

            if prd:
                print("\nPRD:")
                print(json.dumps(_serialize_value(prd), indent=2))
        else:
            print("\nWorkflow ended without complete requirements. Check the output above.")

    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")


if __name__ == "__main__":
    main()
