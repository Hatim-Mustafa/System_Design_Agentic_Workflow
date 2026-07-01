from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from typing import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Annotated


# ---------------------------------------------------------------------------
# Clarified Requirements
# ---------------------------------------------------------------------------

class ClarifiedRequirements(BaseModel):
    project_name: str = Field(
        description="Short, canonical name for the project (e.g. 'TaskFlow', 'MediBook')."
    )
    problem_statement: str = Field(
        description="One-to-two sentence description of the core problem this project solves."
    )
    target_users: list[str] = Field(
        description="Distinct user personas or roles who will use this system (e.g. 'admin', 'end user', 'third-party integrator')."
    )
    core_features: list[str] = Field(
        description="High-level capabilities the system must provide to satisfy the problem statement."
    )
    out_of_scope: list[str] = Field(
        description="Features or concerns explicitly excluded from this project to keep scope bounded."
    )
    constraints: list[str] = Field(
        description="Hard technical, business, or regulatory constraints (e.g. 'must use PostgreSQL', 'GDPR compliance required')."
    )
    assumptions: list[str] = Field(
        description="Assumptions made about the environment, users, or system that have not been explicitly confirmed."
    )


class ClarifyingQuestions(BaseModel):
    questions: list[str] = Field(
        description="A batch of short, non-technical clarifying questions to ask the user, ordered from most important to least important."
    )


# ---------------------------------------------------------------------------
# PRD & Feature Manifest
# ---------------------------------------------------------------------------

class Stakeholder(BaseModel):
    role: str = Field(
        description="The stakeholder's role or title (e.g. 'Product Owner', 'End User', 'Compliance Officer')."
    )
    goals: list[str] = Field(
        description="What this stakeholder wants to achieve or get out of the system."
    )


class AcceptanceCriterion(BaseModel):
    criterion: str = Field(
        description="A single, verifiable condition that must be true for this feature to be considered complete."
    )


class Feature(BaseModel):
    id: str = Field(
        description="Unique feature identifier in the format 'F-NNN' (e.g. 'F-001'). Used as a reference key across all documents."
    )
    name: str = Field(
        description="Short, human-readable name for the feature (e.g. 'User Authentication', 'Export to CSV')."
    )
    description: str = Field(
        description="A clear explanation of what this feature does and why it is needed."
    )
    priority: Literal["must-have", "should-have", "nice-to-have"] = Field(
        description="MoSCoW priority: 'must-have' = required for launch, 'should-have' = important but not blocking, 'nice-to-have' = optional enhancement."
    )
    stakeholders: list[str] = Field(
        description="List of stakeholder roles (matching Stakeholder.role) who care about or own this feature."
    )
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        description="Verifiable conditions that define when this feature is done. Should map 1-to-1 to Gherkin scenarios."
    )


class PRD(BaseModel):
    project_name: str = Field(
        description="Canonical project name, must match ClarifiedRequirements.project_name."
    )
    problem_statement: str = Field(
        description="The core problem this product addresses, derived from ClarifiedRequirements."
    )
    goals: list[str] = Field(
        description="Measurable outcomes the product aims to achieve (e.g. 'reduce booking time by 50%')."
    )
    non_goals: list[str] = Field(
        description="Explicit statements of what this product will NOT do, to prevent scope creep."
    )
    stakeholders: list[Stakeholder] = Field(
        description="All stakeholders involved in or affected by this product."
    )
    features: list[Feature] = Field(
        description="Full prioritized list of features. Each feature must have a unique id for cross-document traceability."
    )
    open_questions: list[str] = Field(
        description="Unresolved questions or decisions that need clarification before or during development."
    )


# ---------------------------------------------------------------------------
# Gherkin Acceptance Criteria
# ---------------------------------------------------------------------------

class GherkinStep(BaseModel):
    keyword: Literal["Given", "When", "Then", "And", "But"] = Field(
        description="BDD step keyword: 'Given' = precondition, 'When' = action, 'Then' = expected outcome, 'And'/'But' = continuation."
    )
    text: str = Field(
        description="The step text in plain English, written from the user's perspective (e.g. 'the user is logged in')."
    )


class GherkinScenario(BaseModel):
    title: str = Field(
        description="Short title describing the scenario (e.g. 'Successful login with valid credentials')."
    )
    tags: list[str] = Field(
        description="Labels for filtering or grouping scenarios (e.g. '@smoke', '@auth', '@regression')."
    )
    steps: list[GherkinStep] = Field(
        description="Ordered list of Given/When/Then steps that define the full scenario flow."
    )
    feature_ref: str = Field(
        description="The Feature.id this scenario validates (e.g. 'F-001'). Ensures traceability back to the PRD."
    )


class GherkinFeature(BaseModel):
    title: str = Field(
        description="The feature name as it appears in the Gherkin file (e.g. 'User Authentication')."
    )
    description: str = Field(
        description="Brief narrative description of the feature from the user's perspective (the 'In order to / As a / I want' block)."
    )
    scenarios: list[GherkinScenario] = Field(
        description="All test scenarios that cover this feature, including happy paths and edge cases."
    )


class AcceptanceCriteria(BaseModel):
    features: list[GherkinFeature] = Field(
        description="Complete set of Gherkin features, one per PRD Feature (matched via scenario feature_ref)."
    )


# ---------------------------------------------------------------------------
# OpenAPI Schema Specifications
# ---------------------------------------------------------------------------

class SchemaProperty(BaseModel):
    name: str = Field(
        description="The field name as it appears in the JSON body (e.g. 'email', 'created_at')."
    )
    type: str = Field(
        description="JSON Schema type (e.g. 'string', 'integer', 'boolean', 'array', 'object')."
    )
    required: bool = Field(
        description="Whether this property must be present in the request or response payload."
    )
    description: str = Field(
        description="Human-readable explanation of what this field represents and any constraints (e.g. 'ISO 8601 timestamp')."
    )
    example: Optional[Any] = Field(
        default=None,
        description="A concrete example value to aid code generation and documentation (e.g. 'john@example.com')."
    )


class RequestBody(BaseModel):
    content_type: str = Field(
        description="MIME type of the request body (e.g. 'application/json', 'multipart/form-data')."
    )
    properties: list[SchemaProperty] = Field(
        description="Fields expected in the request body payload."
    )
    required: bool = Field(
        description="Whether a request body must be provided for this endpoint to function."
    )


class Response(BaseModel):
    status_code: int = Field(
        description="HTTP status code for this response (e.g. 200, 201, 400, 404, 422, 500)."
    )
    description: str = Field(
        description="Plain-English explanation of when this response is returned (e.g. 'Returned when the resource is not found')."
    )
    properties: list[SchemaProperty] = Field(
        description="Fields present in the response body for this status code."
    )


class Parameter(BaseModel):
    name: str = Field(
        description="Parameter name as it appears in the URL or header (e.g. 'user_id', 'Authorization')."
    )
    location: Literal["path", "query", "header", "cookie"] = Field(
        description="Where the parameter is passed: 'path' = URL segment, 'query' = URL query string, 'header' = HTTP header, 'cookie' = cookie."
    )
    required: bool = Field(
        description="Whether this parameter must be provided for the request to be valid."
    )
    type: str = Field(
        description="JSON Schema type of the parameter value (e.g. 'string', 'integer')."
    )
    description: str = Field(
        description="What this parameter controls or filters (e.g. 'The unique ID of the user to retrieve')."
    )


class AuthRequirement(BaseModel):
    required: bool = Field(
        description="Whether the caller must be authenticated to access this endpoint."
    )
    scheme: Optional[Literal["bearer", "api_key", "basic", "oauth2"]] = Field(
        default=None,
        description="Authentication scheme required: 'bearer' = JWT/token in Authorization header, 'api_key' = key in header or query, 'basic' = username/password, 'oauth2' = OAuth 2.0 flow. Null if authentication is not required."
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="OAuth2 scopes or permission levels required (e.g. ['read:users', 'write:orders']). Empty list if not applicable."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Any additional auth context (e.g. 'Admin role required', 'Token must belong to the resource owner')."
    )


class Endpoint(BaseModel):
    path: str = Field(
        description="The URL path for this endpoint, using path parameter notation (e.g. '/users/{user_id}/orders')."
    )
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(
        description="HTTP method: GET = read, POST = create, PUT = full replace, PATCH = partial update, DELETE = remove."
    )
    summary: str = Field(
        description="One-line description of what this endpoint does (e.g. 'Retrieve a user by ID')."
    )
    tags: list[str] = Field(
        description="Grouping labels for API documentation and code generation (e.g. ['users', 'admin'])."
    )
    parameters: list[Parameter] = Field(
        description="Path, query, header, or cookie parameters this endpoint accepts."
    )
    request_body: Optional[RequestBody] = Field(
        default=None,
        description="The request body schema. Present for POST, PUT, PATCH. Null for GET and DELETE."
    )
    responses: list[Response] = Field(
        description="All possible HTTP responses this endpoint can return, including error cases."
    )
    auth: AuthRequirement = Field(
        description="Authentication and authorization requirements for this endpoint."
    )
    feature_ref: str = Field(
        description="The Feature.id this endpoint implements (e.g. 'F-003'). Ensures traceability back to the PRD."
    )


class OpenAPISpec(BaseModel):
    title: str = Field(
        description="Human-readable API title (e.g. 'TaskFlow REST API')."
    )
    version: str = Field(
        description="Semantic version of this API spec (e.g. '1.0.0')."
    )
    base_url: str = Field(
        description="Base URL for all endpoints (e.g. 'https://api.taskflow.com/v1')."
    )
    endpoints: list[Endpoint] = Field(
        description="Complete list of all API endpoints. Every PRD feature with a REST interface should have at least one endpoint."
    )


# ---------------------------------------------------------------------------
# ER Schema
# ---------------------------------------------------------------------------

class AttributeType(BaseModel):
    name: str = Field(
        description="Column or field name in snake_case (e.g. 'user_id', 'created_at')."
    )
    data_type: str = Field(
        description="SQL or conceptual data type (e.g. 'UUID', 'VARCHAR(255)', 'TIMESTAMP', 'BOOLEAN', 'INTEGER')."
    )
    is_primary_key: bool = Field(
        default=False,
        description="True if this attribute is the primary key of the entity."
    )
    is_foreign_key: bool = Field(
        default=False,
        description="True if this attribute references a primary key in another entity."
    )
    nullable: bool = Field(
        default=True,
        description="Whether this field can hold a NULL value. Set to False for required fields."
    )
    unique: bool = Field(
        default=False,
        description="Whether all values for this attribute must be unique across rows (e.g. email, username)."
    )


class Entity(BaseModel):
    name: str = Field(
        description="PascalCase entity name matching the domain concept (e.g. 'User', 'OrderItem', 'PaymentTransaction')."
    )
    description: str = Field(
        description="What real-world concept this entity represents and its role in the system."
    )
    attributes: list[AttributeType] = Field(
        description="All columns/fields for this entity, including primary key, foreign keys, and data attributes."
    )


class Relationship(BaseModel):
    from_entity: str = Field(
        description="The source entity name (must match an Entity.name in this schema)."
    )
    to_entity: str = Field(
        description="The target entity name (must match an Entity.name in this schema)."
    )
    cardinality: Literal["one-to-one", "one-to-many", "many-to-many"] = Field(
        description="Cardinality of the relationship: 'one-to-one', 'one-to-many' (from_entity is the 'one'), or 'many-to-many' (requires a junction table)."
    )
    label: str = Field(
        description="Verb phrase describing the relationship direction (e.g. 'places', 'belongs to', 'is assigned to')."
    )
    via_table: Optional[str] = Field(
        default=None,
        description="Name of the junction/association table for many-to-many relationships (e.g. 'user_roles'). Null for all other cardinalities."
    )


class ERSchema(BaseModel):
    entities: list[Entity] = Field(
        description="All domain entities (tables) in the data model."
    )
    relationships: list[Relationship] = Field(
        description="All relationships between entities, capturing cardinality and foreign key semantics."
    )


# ---------------------------------------------------------------------------
# Critic Models
# ---------------------------------------------------------------------------

class ConsistencyIssue(BaseModel):
    issue: str = Field(
        description="Clear description of the inconsistency or problem found across documents."
    )
    affected_documents: list[Literal["prd", "gherkin", "openapi", "er"]] = Field(
        description="Which documents are involved in or affected by this inconsistency."
    )
    severity: Literal["blocking", "warning"] = Field(
        description="'blocking' = must be fixed before finalization, 'warning' = should be fixed but won't block assembly."
    )
    suggested_fix: str = Field(
        description="Concrete, actionable suggestion for resolving this issue."
    )


class Critique(BaseModel):
    revision_number: int = Field(
        description="Which revision cycle this critique belongs to for the target document (1-indexed)."
    )
    target_document: Literal["prd", "gherkin", "openapi", "er"] = Field(
        description="The single document this critique is evaluating. Critic validates only populated docs in state."
    )
    issues: list[ConsistencyIssue] = Field(
        description="All consistency issues found. Empty list means document passes."
    )
    approved: bool = Field(
        description="True if no blocking issues remain and this document is ready for next stage."
    )


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class DesignState(TypedDict):
    raw_idea: str
    intake_messages: Annotated[list[BaseMessage], add_messages]
    clarifying_questions: list[str]
    clarified_requirements: Optional[ClarifiedRequirements]
    prd: Optional[PRD]
    acceptance_criteria: Optional[AcceptanceCriteria]
    openapi_schema: Optional[OpenAPISpec]
    er_schema: Optional[ERSchema]
    critique_history: list[Critique]
    revision_counts: dict[str, int]
    max_revisions: int
    documents_finalized: bool