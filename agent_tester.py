from __future__ import annotations

import argparse
import asyncio
import json
import pickle
from pathlib import Path
from typing import Any

from agents import intake_node, prd_node, openapi_node, er_node
from main import build_initial_state
from models import DesignState

STATE_SNAPSHOT_PATH = Path("design_state_snapshot.bin")


def load_state_snapshot(snapshot_path: Path = STATE_SNAPSHOT_PATH) -> dict[str, Any]:
    if snapshot_path.exists():
        with snapshot_path.open("rb") as snapshot_file:
            return pickle.load(snapshot_file)
    return {}


def save_state_snapshot(state: dict[str, Any], snapshot_path: Path = STATE_SNAPSHOT_PATH) -> None:
    with snapshot_path.open("wb") as snapshot_file:
        pickle.dump(state, snapshot_file)


def normalize_state_for_agent(agent_name: str, snapshot_state: dict[str, Any]) -> DesignState:
    if agent_name == "intake":
        raw_idea = snapshot_state.get("raw_idea", "") or input("Enter a rough product idea for intake: ").strip()
        if not raw_idea:
            raise SystemExit("A raw idea is required for intake testing.")
        return build_initial_state(raw_idea)

    state: DesignState = build_initial_state(snapshot_state.get("raw_idea", ""))
    state.update(snapshot_state)

    if agent_name == "prd":
        if state.get("clarified_requirements") is None:
            raise SystemExit("PRD testing requires clarified_requirements in the saved state snapshot.")
        state["prd"] = None
    elif agent_name == "openapi":
        if state.get("clarified_requirements") is None or state.get("prd") is None:
            raise SystemExit("OpenAPI testing requires clarified_requirements and prd in the saved state snapshot.")
        state["openapi_schema"] = None
    elif agent_name == "er":
        if state.get("clarified_requirements") is None or state.get("prd") is None or state.get("openapi_schema") is None:
            raise SystemExit("ER testing requires clarified_requirements, prd, and openapi_schema in the saved state snapshot.")
        state["er_schema"] = None

    return state


async def run_selected_agent(agent_name: str, state: DesignState) -> dict[str, Any]:
    if agent_name == "intake":
        return await intake_node(state)
    if agent_name == "prd":
        return await prd_node(state)
    if agent_name == "openapi":
        return await openapi_node(state)
    if agent_name == "er":
        return await er_node(state)
    raise SystemExit(f"Unsupported agent: {agent_name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single agent against the saved DesignState snapshot.")
    parser.add_argument(
        "agent",
        choices=["intake", "prd", "openapi", "er"],
        help="Which agent to run from the saved state snapshot.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_state = load_state_snapshot()
    state = normalize_state_for_agent(args.agent, snapshot_state)

    result = asyncio.run(run_selected_agent(args.agent, state))
    updated_state = dict(state)
    updated_state.update(result)
    save_state_snapshot(updated_state)

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()