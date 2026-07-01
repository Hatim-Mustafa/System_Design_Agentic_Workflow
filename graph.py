from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
from langgraph.constants import START, END

from agents import intake_node, prd_node, openapi_node, er_node, _is_requirements_complete, gherkin_node
from models import DesignState


def _intake_router(state: DesignState) -> str:
    """Route based on whether intake requirements are complete."""
    if _is_requirements_complete(state.get("clarified_requirements")):
        return "done"
    return "continue"


def build_graph() -> StateGraph:
    """Build the full LangGraph workflow."""
    graph = StateGraph(DesignState)
    
    # Add the intake node
    graph.add_node("intake", intake_node)
    graph.add_node("prd", prd_node)
    graph.add_node("gherkin", gherkin_node)
    graph.add_node("openapi", openapi_node)
    graph.add_node("er", er_node)
    
    graph.add_edge(START, "intake")  # Start to intake
    
    # Conditional edge: if intake is complete, end; otherwise loop back
    graph.add_conditional_edges(
        "intake",
        _intake_router,
        {
            "continue": "intake",
            "done": "prd",
        },
    )

    graph.add_edge("prd", "gherkin")
    graph.add_edge("gherkin", "openapi")
    graph.add_edge("openapi", "er")
    graph.add_edge("er", END)
    
    return graph.compile(checkpointer=InMemorySaver())


def get_graph() -> StateGraph:
    """Get the compiled graph."""
    return build_graph()
