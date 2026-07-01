from __future__ import annotations

from typing import Any

from models import (
    AcceptanceCriteria,
    ClarifiedRequirements,
    ERSchema,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
    OpenAPISpec,
    PRD,
)


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


def _coerce_openapi(openapi_schema: OpenAPISpec | dict[str, Any] | None) -> OpenAPISpec | None:
    if openapi_schema is None:
        return None
    if isinstance(openapi_schema, OpenAPISpec):
        return openapi_schema
    return OpenAPISpec.model_validate(openapi_schema)


def _coerce_er_schema(er_schema: ERSchema | dict[str, Any] | None) -> ERSchema | None:
    if er_schema is None:
        return None
    if isinstance(er_schema, ERSchema):
        return er_schema
    return ERSchema.model_validate(er_schema)


def _coerce_gherkin(
    gherkin: AcceptanceCriteria | dict[str, Any] | None,
) -> AcceptanceCriteria | None:
    if gherkin is None:
        return None
    if isinstance(gherkin, AcceptanceCriteria):
        return gherkin
    return AcceptanceCriteria.model_validate(gherkin)


def format_clarified_requirements(requirements: ClarifiedRequirements | dict[str, Any]) -> str:
    if isinstance(requirements, ClarifiedRequirements):
        data = requirements.model_dump()
    else:
        data = requirements

    def _format_list(value: Any) -> str:
        if not value:
            return "None"
        if isinstance(value, list):
            return "; ".join(str(item) for item in value)
        return str(value)

    project_name = data.get("project_name", "Unknown project")
    problem_statement = data.get("problem_statement", "Not provided")
    target_users = _format_list(data.get("target_users"))
    core_features = _format_list(data.get("core_features"))
    out_of_scope = _format_list(data.get("out_of_scope"))
    constraints = _format_list(data.get("constraints"))
    assumptions = _format_list(data.get("assumptions"))

    return (
        f"Project name: {project_name}\n"
        f"Problem statement: {problem_statement}\n"
        f"Target users: {target_users}\n"
        f"Core features: {core_features}\n"
        f"Out of scope: {out_of_scope}\n"
        f"Constraints: {constraints}\n"
        f"Assumptions: {assumptions}"
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


def format_openapi(openapi_schema: OpenAPISpec | dict[str, Any]) -> str:
    if isinstance(openapi_schema, OpenAPISpec):
        data = openapi_schema.model_dump()
    else:
        data = openapi_schema

    endpoints = data.get("endpoints", [])
    endpoint_text = "\n".join(
        f"- {item.get('method', 'GET')} {item.get('path', '/')} :: {item.get('summary', '')}"
        for item in endpoints
    ) or "None"

    return (
        f"Title: {data.get('title', 'Untitled API')}\n"
        f"Version: {data.get('version', '1.0.0')}\n"
        f"Base URL: {data.get('base_url', 'Not provided')}\n"
        f"Endpoints:\n{endpoint_text}"
    )


def format_er_schema(er_schema: ERSchema | dict[str, Any]) -> str:
    if isinstance(er_schema, ERSchema):
        data = er_schema.model_dump()
    else:
        data = er_schema

    entities = data.get("entities", [])
    relationships = data.get("relationships", [])

    entity_text = "\n".join(
        f"- {item.get('name', 'Unknown entity')}: {item.get('description', '')}"
        for item in entities
    ) or "None"

    relationship_text = "\n".join(
        f"- {item.get('from_entity', 'Unknown')} -> {item.get('to_entity', 'Unknown')} ({item.get('cardinality', 'unknown')}): {item.get('label', '')}"
        for item in relationships
    ) or "None"

    return (
        f"Entities:\n{entity_text}\n"
        f"Relationships:\n{relationship_text}"
    )


def format_gherkin(gherkin: AcceptanceCriteria | dict[str, Any]) -> str:
    if isinstance(gherkin, AcceptanceCriteria):
        data = gherkin.model_dump()
    else:
        data = gherkin

    features = data.get("features", [])

    def _format_steps(steps: list[dict[str, Any]]) -> str:
        if not steps:
            return "None"
        return "\n".join(
            f"    - {step.get('keyword', 'Given')} {step.get('text', '')}"
            for step in steps
        )

    feature_text = []
    for feature in features:
        scenarios = feature.get("scenarios", [])
        scenario_text = []
        for scenario in scenarios:
            tags = scenario.get("tags", [])
            scenario_text.append(
                f"  * {scenario.get('title', 'Untitled scenario')} [{', '.join(tags) or 'no tags'}]\n"
                f"{_format_steps(scenario.get('steps', []))}"
            )

        feature_text.append(
            f"- {feature.get('title', 'Untitled feature')}: {feature.get('description', '')}\n"
            f"{chr(10).join(scenario_text) if scenario_text else '  None'}"
        )

    return "\n".join(feature_text) or "None"
