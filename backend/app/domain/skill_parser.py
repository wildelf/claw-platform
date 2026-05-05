"""SKILL.md parser for extracting decision tree structure."""

import logging
import re
from typing import Any

import yaml

from app.domain.skill_decision import (
    DecisionBranch,
    DecisionNode,
    DecisionNodeType,
    DecisionTree,
    ExecutionTrace,
    ExecutionStep,
    SkillMetadata,
)
from app.deepagents.exceptions import SkillNotFoundError

logger = logging.getLogger(__name__)

# Regex to extract YAML frontmatter from SKILL.md content
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from SKILL.md.

    Args:
        content: Raw SKILL.md file content.

    Returns:
        Parsed YAML as dict.

    Raises:
        SkillNotFoundError: If frontmatter is missing or invalid.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise SkillNotFoundError(
            f"SKILL.md missing YAML frontmatter. Content preview: {content[:200]}"
        )

    try:
        data = yaml.safe_load(match.group(1))
        if not isinstance(data, dict):
            raise SkillNotFoundError("SKILL.md frontmatter must be a YAML dict")
        return data
    except yaml.YAMLError as e:
        raise SkillNotFoundError(f"SKILL.md frontmatter parse error: {e}")


def parse_skill_metadata(content: str) -> SkillMetadata:
    """Parse SKILL.md into SkillMetadata with decision tree.

    Args:
        content: Raw SKILL.md file content.

    Returns:
        SkillMetadata with decision tree.

    Raises:
        SkillNotFoundError: If SKILL.md is malformed.
    """
    data = parse_frontmatter(content)

    # Extract top-level fields
    name = data.get("name", "")
    version = data.get("version", "1.0")
    agent_type = data.get("agent_type")
    description = data.get("description", "")

    # Parse decision tree
    dt_data = data.get("decision_tree", {})
    root = dt_data.get("root", "")
    nodes_data = dt_data.get("nodes", [])

    nodes: list[DecisionNode] = []
    for node_data in nodes_data:
        node_type_str = node_data.get("type", "")
        try:
            node_type = DecisionNodeType(node_type_str)
        except ValueError:
            logger.warning(f"Unknown node type '{node_type_str}' in skill {name}, skipping")
            continue

        branches: list[DecisionBranch] = []
        for branch_data in node_data.get("branches", []):
            branches.append(DecisionBranch(
                condition=branch_data.get("condition", ""),
                next=branch_data.get("next", ""),
            ))

        node = DecisionNode(
            id=node_data.get("id", ""),
            type=node_type,
            tool=node_data.get("tool"),
            params=node_data.get("params", {}),
            branches=branches,
            template=node_data.get("template"),
            next=node_data.get("next"),
            notify=node_data.get("notify"),
            message=node_data.get("message"),
            description=node_data.get("description"),
        )
        nodes.append(node)

    decision_tree = DecisionTree(root=root, nodes=nodes)

    return SkillMetadata(
        name=name,
        version=version,
        agent_type=agent_type,
        description=description,
        decision_tree=decision_tree,
    )


def validate_skill_content(content: str) -> list[str]:
    """Validate SKILL.md content and return list of issues.

    Args:
        content: Raw SKILL.md file content.

    Returns:
        List of validation error messages (empty if valid).
    """
    issues: list[str] = []

    try:
        data = parse_frontmatter(content)
    except SkillNotFoundError as e:
        issues.append(str(e))
        return issues

    # Check required top-level fields
    if not data.get("name"):
        issues.append("Missing required field: name")

    dt = data.get("decision_tree", {})
    if not dt:
        issues.append("Missing required field: decision_tree")
        return issues

    if not dt.get("root"):
        issues.append("Missing required field: decision_tree.root")

    nodes = dt.get("nodes", [])
    if not nodes:
        issues.append("decision_tree.nodes is empty")

    node_ids = set()
    for node_data in nodes:
        node_id = node_data.get("id", "")
        if not node_id:
            issues.append("Node missing required field: id")
        if node_id in node_ids:
            issues.append(f"Duplicate node ID: {node_id}")
        node_ids.add(node_id)

        node_type = node_data.get("type", "")
        valid_types = [t.value for t in DecisionNodeType]
        if node_type not in valid_types:
            issues.append(f"Node '{node_id}' has unknown type '{node_type}'")

        # Type-specific validation
        if node_type == "data_query" and not node_data.get("tool"):
            issues.append(f"Node '{node_id}' (data_query) missing required field: tool")

        if node_type == "report_generation" and not node_data.get("template"):
            issues.append(f"Node '{node_id}' (report_generation) missing required field: template")

        if node_type == "notification" and not node_data.get("notify"):
            issues.append(f"Node '{node_id}' (notification) missing required field: notify")

    # Verify root node exists
    root_id = dt.get("root", "")
    if root_id and root_id not in node_ids:
        issues.append(f"Root node ID '{root_id}' not found in nodes")

    return issues
