"""Decision tree schema for SKILL.md parsing and execution."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DecisionNodeType(str, Enum):
    """Types of nodes in a decision tree."""

    DATA_QUERY = "data_query"         # Query data from an MCP tool
    DECISION_BRANCH = "decision_branch"  # Conditional branch based on LLM evaluation
    REPORT_GENERATION = "report_generation"  # Generate a report from collected data
    NOTIFICATION = "notification"     # Send a notification or escalation


class DecisionBranch(BaseModel):
    """A single branch within a decision node."""

    condition: str = Field(description="Condition expression (LLM-evaluable)")
    next: str = Field(description="ID of the next node to execute if condition is true")


class DecisionNode(BaseModel):
    """A single node in the decision tree."""

    id: str = Field(description="Unique node identifier")
    type: DecisionNodeType = Field(description="Type of this node")
    tool: str | None = Field(default=None, description="MCP tool name (for data_query)")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    branches: list[DecisionBranch] = Field(
        default_factory=list,
        description="Branches for decision_branch nodes"
    )
    template: str | None = Field(default=None, description="Template path (for report_generation)")
    next: str | None = Field(default=None, description="Next node ID (for non-branch nodes)")
    notify: str | None = Field(default=None, description="Target group (for notification)")
    message: str | None = Field(default=None, description="Notification message")
    description: str | None = Field(default=None, description="Human-readable description")


class DecisionTree(BaseModel):
    """Parsed decision tree from SKILL.md."""

    root: str = Field(description="ID of the root node")
    nodes: list[DecisionNode] = Field(description="All decision nodes")

    def get_node(self, node_id: str) -> DecisionNode | None:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None


class SkillMetadata(BaseModel):
    """Metadata section parsed from SKILL.md frontmatter."""

    name: str = Field(description="Skill name")
    version: str = Field(default="1.0", description="Skill version")
    agent_type: str | None = Field(default=None, description="Agent type for this skill")
    description: str = Field(default="", description="Skill description")
    decision_tree: DecisionTree = Field(description="The decision tree")


class ExecutionStep(BaseModel):
    """A single step in the decision tree execution."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_id: str = Field(description="Node that was executed")
    node_type: DecisionNodeType = Field(description="Type of node executed")
    tool_name: str | None = Field(default=None, description="Tool called")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameters passed")
    result: Any | None = Field(default=None, description="Result of this step")
    decision_context: str | None = Field(default=None, description="Branch condition that led here")
    error: str | None = Field(default=None, description="Error if step failed")


class ExecutionTrace(BaseModel):
    """Full execution trace of a decision tree run."""

    skill_id: str = Field(description="Skill that was executed")
    session_id: str = Field(description="Session this ran in")
    steps: list[ExecutionStep] = Field(default_factory=list)
    outcome: str = Field(default="", description="Final outcome")
    escalated: bool = Field(default=False, description="Whether human escalation was triggered")
