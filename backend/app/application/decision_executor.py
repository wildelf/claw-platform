"""Decision tree executor for running SKILL.md workflows."""

import logging
from typing import Any

from app.domain.skill_decision import (
    DecisionNode,
    DecisionNodeType,
    ExecutionStep,
    ExecutionTrace,
    SkillMetadata,
)
from app.domain.log import LogActionType, LogEntry
from app.application.log_service import LogService
from app.infrastructure.storage.base import StorageAdapter
from app.infrastructure.mcp.adapter import MCPAdapter
from app.domain.tool import Tool, ToolType

logger = logging.getLogger(__name__)


class DecisionTreeExecutor:
    """Executes a parsed SKILL.md decision tree.

    Walks the decision tree node by node, evaluates branch conditions
    using the LLM, calls MCP tools for data_query nodes, and emits
    logs for each step.
    """

    def __init__(
        self,
        skill_metadata: SkillMetadata,
        agent_id: str,
        session_id: str,
        storage: StorageAdapter,
        log_service: LogService,
        mcp_adapters: dict[str, MCPAdapter],
        llm_evaluator: "LLMEvaluator | None" = None,
    ):
        """Initialize executor.

        Args:
            skill_metadata: Parsed SKILL.md with decision tree.
            agent_id: ID of the agent running this skill.
            session_id: Current session ID.
            storage: Storage adapter for fetching tools and configs.
            log_service: LogService for emitting audit events.
            mcp_adapters: Map of tool_id -> MCPAdapter for MCP tool calls.
            llm_evaluator: Optional LLM for evaluating branch conditions.
        """
        self._skill = skill_metadata
        self._agent_id = agent_id
        self._session_id = session_id
        self._storage = storage
        self._log_service = log_service
        self._mcp_adapters = mcp_adapters
        self._llm_evaluator = llm_evaluator
        self._trace = ExecutionTrace(
            skill_id=getattr(skill_metadata, "name", ""),
            session_id=session_id,
        )

    async def execute(self, initial_context: dict[str, Any] | None = None) -> ExecutionTrace:
        """Execute the decision tree from root.

        Args:
            initial_context: Initial context data (e.g., user input异常).

        Returns:
            ExecutionTrace with all steps and final outcome.
        """
        context = initial_context or {}
        current_node_id = self._skill.decision_tree.root

        while current_node_id:
            node = self._skill.decision_tree.get_node(current_node_id)
            if not node:
                await self._emit_error(
                    node_id=current_node_id,
                    error=f"Node '{current_node_id}' not found in decision tree",
                )
                break

            step = await self._execute_node(node, context)
            self._trace.steps.append(step)

            # Log the step
            await self._log_step(step)

            if step.error:
                self._trace.outcome = f"Error at node '{current_node_id}': {step.error}"
                break

            # Determine next node
            if node.type == DecisionNodeType.DECISION_BRANCH:
                # Branch selection happens inside _execute_node via LLM
                # step.decision_context holds the chosen branch condition
                if step.decision_context:
                    # Find which branch was taken
                    for branch in node.branches:
                        if branch.condition == step.decision_context:
                            current_node_id = branch.next
                            break
                    else:
                        # No matching branch found — escalate
                        self._trace.outcome = f"No matching branch at '{current_node_id}', escalating"
                        self._trace.escalated = True
                        break
                else:
                    break
            elif node.type == DecisionNodeType.NOTIFICATION:
                # Notification nodes always escalate
                self._trace.outcome = f"Notification sent: {node.message}"
                self._trace.escalated = True
                break
            elif node.type == DecisionNodeType.REPORT_GENERATION:
                # End of path
                self._trace.outcome = "Report generated successfully"
                break
            else:
                current_node_id = node.next

        return self._trace

    async def _execute_node(
        self, node: DecisionNode, context: dict[str, Any]
    ) -> ExecutionStep:
        """Execute a single decision tree node.

        Returns:
            ExecutionStep with result or error.
        """
        if node.type == DecisionNodeType.DATA_QUERY:
            return await self._execute_data_query(node, context)
        elif node.type == DecisionNodeType.DECISION_BRANCH:
            return await self._execute_decision_branch(node, context)
        elif node.type == DecisionNodeType.REPORT_GENERATION:
            return await self._execute_report_generation(node, context)
        elif node.type == DecisionNodeType.NOTIFICATION:
            return await self._execute_notification(node, context)
        else:
            return ExecutionStep(
                node_id=node.id,
                node_type=node.type,
                error=f"Unknown node type: {node.type}",
            )

    async def _execute_data_query(
        self, node: DecisionNode, context: dict[str, Any]
    ) -> ExecutionStep:
        """Execute a data_query node by calling an MCP tool."""
        tool_name = node.tool or ""
        params = node.params or {}

        # Merge params with context
        merged_params = self._resolve_params(params, context)

        try:
            result = await self._call_mcp_tool(tool_name, merged_params)
            context[node.id] = result
            return ExecutionStep(
                node_id=node.id,
                node_type=node.type,
                tool_name=tool_name,
                params=merged_params,
                result=result,
            )
        except Exception as e:
            logger.warning(f"Data query failed for tool '{tool_name}': {e}")
            return ExecutionStep(
                node_id=node.id,
                node_type=node.type,
                tool_name=tool_name,
                params=merged_params,
                error=str(e),
            )

    async def _execute_decision_branch(
        self, node: DecisionNode, context: dict[str, Any]
    ) -> ExecutionStep:
        """Evaluate branch conditions and select next node."""
        if not node.branches:
            return ExecutionStep(
                node_id=node.id,
                node_type=node.type,
                error="Decision branch node has no branches",
            )

        # Use LLM to evaluate which branch condition is true
        if self._llm_evaluator:
            chosen_condition, reasoning = await self._llm_evaluator.evaluate_branch(
                context=context,
                conditions=[b.condition for b in node.branches],
            )
            logger.info(f"Decision branch '{node.id}': selected '{chosen_condition}' — {reasoning}")
        else:
            # No LLM evaluator — cannot proceed, escalate
            chosen_condition = ""
            reasoning = "No LLM evaluator configured"

        return ExecutionStep(
            node_id=node.id,
            node_type=node.type,
            result={"reasoning": reasoning},
            decision_context=chosen_condition,
        )

    async def _execute_report_generation(
        self, node: DecisionNode, context: dict[str, Any]
    ) -> ExecutionStep:
        """Generate a report using a template."""
        template_name = node.template or ""
        return ExecutionStep(
            node_id=node.id,
            node_type=node.type,
            result={"template": template_name, "context_summary": list(context.keys())},
        )

    async def _execute_notification(
        self, node: DecisionNode, context: dict[str, Any]
    ) -> ExecutionStep:
        """Send a notification (human escalation)."""
        return ExecutionStep(
            node_id=node.id,
            node_type=node.type,
            result={
                "notify": node.notify,
                "message": node.message,
                "escalation": True,
            },
        )

    async def _call_mcp_tool(
        self, tool_name: str, params: dict[str, Any]
    ) -> Any:
        """Call an MCP tool via registered adapter."""
        # Find adapter by tool_name
        for tool_id, adapter in self._mcp_adapters.items():
            if adapter.tool.name == tool_name:
                return await adapter.call_tool(tool_name, params)

        # Fallback: try calling via storage tool lookup
        # (This path used when tools are registered via Tool model)
        raise RuntimeError(f"No MCP adapter registered for tool '{tool_name}'")

    def _resolve_params(
        self, params: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve parameter references in context.

        Supports {{context.key}} substitution in param values.
        """
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str):
                # Replace {{context.key}} placeholders
                for ctx_key, ctx_val in context.items():
                    placeholder = f"{{{{{ctx_key}}}}}"
                    if placeholder in v:
                        v = v.replace(placeholder, str(ctx_val))
            resolved[k] = v
        return resolved

    async def _log_step(self, step: ExecutionStep) -> None:
        """Emit a log entry for an execution step."""
        await self._log_service.emit(
            agent_id=self._agent_id,
            session_id=self._session_id,
            action_type=LogActionType.DECISION_BRANCH if step.decision_context else LogActionType.MCP_CALL,
            tool_name=step.tool_name,
            input_json=str(step.params) if step.params else None,
            output_json=str(step.result) if step.result else None,
            decision_context=step.node_id,
            error=step.error,
        )

    async def _emit_error(self, node_id: str, error: str) -> None:
        """Emit an error log entry."""
        await self._log_service.emit(
            agent_id=self._agent_id,
            session_id=self._session_id,
            action_type=LogActionType.MCP_CALL,
            decision_context=node_id,
            error=error,
        )


# Type for LLM-based branch evaluation
class LLMEvaluator:
    """LLM-based evaluator for decision branch conditions."""

    async def evaluate_branch(
        self,
        context: dict[str, Any],
        conditions: list[str],
    ) -> tuple[str, str]:
        """Evaluate which branch condition is true given the context.

        Args:
            context: Current execution context (data collected so far).
            conditions: List of condition expressions.

        Returns:
            Tuple of (chosen_condition, reasoning).
        """
        raise NotImplementedError
