"""Claw-platform poller — fetches tool registrations from claw-platform REST API.

Gateway polls /api/tools every N seconds (configurable via POLL_INTERVAL env).
On new or changed tools, dynamically registers FastMCP routes via RouteGenerator.
"""

import asyncio
import logging
import httpx
from typing import Optional

from gateway.core.tool_registry import ToolRegistry
from gateway.core.route_generator import RouteGenerator

logger = logging.getLogger(__name__)


class ClawPoller:
    """Background poller that syncs tool registrations from claw-platform."""

    def __init__(
        self,
        claw_url: str,
        gateway_token: str,
        tool_registry: ToolRegistry,
        route_generator: RouteGenerator,
        poll_interval: int = 30,
    ):
        self.claw_url = claw_url.rstrip("/")
        self.gateway_token = gateway_token
        self.tool_registry = tool_registry
        self.route_generator = route_generator
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def run(self):
        """Start the polling loop."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Claw poller started, polling every {self.poll_interval}s")

    async def stop(self):
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Claw poller stopped")

    async def fetch_once(self):
        """Fetch tools from claw-platform once (used for initial sync)."""
        await self._fetch_and_register()

    async def _poll_loop(self):
        """Poll loop."""
        while self._running:
            try:
                await asyncio.sleep(self.poll_interval)
                await self._fetch_and_register()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")

    async def _fetch_and_register(self):
        """Fetch tools from claw-platform and register new routes."""
        headers = {
            "Authorization": f"Bearer {self.gateway_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.claw_url}/api/tools",
                    headers=headers,
                )
                response.raise_for_status()
                tools = response.json()

            # Update registry
            previous_ids = {t.id for t in self.tool_registry.list_tools()}
            self.tool_registry.update_tools(tools)

            # Register new tools
            for tool in tools:
                if tool.get("type", "").lower() == "mcp" and tool.get("mcp_config"):
                    # Use the tool's mcp_config to build a ToolConfig
                    from gateway.core.tool_registry import ToolConfig
                    mcp_cfg = tool["mcp_config"]
                    auth_cfg = mcp_cfg.get("auth", {})
                    cfg = ToolConfig(
                        id=tool["id"],
                        name=tool["name"],
                        description=tool.get("description", ""),
                        type=tool.get("type", "mcp"),
                        server_name=tool.get("server_name"),
                        endpoint=mcp_cfg.get("endpoint", ""),
                        method=mcp_cfg.get("method", "POST"),
                        auth={
                            "type": auth_cfg.get("type", "none"),
                            "token": auth_cfg.get("token"),
                            "header_name": auth_cfg.get("header_name", "X-API-Key"),
                        },
                        headers=mcp_cfg.get("headers", {}),
                        args=tool.get("args", []),
                        request_template=mcp_cfg.get("request_template"),
                        response_template=mcp_cfg.get("response_template"),
                        updated_at=tool.get("updated_at", ""),
                    )
                    self.route_generator.register_tool(cfg)

            logger.info(f"Tool sync complete: {len(tools)} tools registered")

        except httpx.HTTPStatusError as e:
            logger.warning(f"Claw API returned {e.response.status_code}: {e.response.text[:200]}")
        except httpx.RequestError as e:
            logger.warning(f"Failed to fetch tools from claw-platform: {e}")