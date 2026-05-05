"""MCP Gateway — FastMCP-based HTTP→MCP gateway service.

Receives MCP calls over SSE/streamable HTTP, translates them to HTTP backend calls
using Jinja2-like template expressions (inspired by Unla's tool config).
Polls claw-platform for tool registration updates.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from fastmcp import FastMCP

from gateway.core.tool_registry import ToolRegistry
from gateway.core.route_generator import RouteGenerator
from gateway.core.transport import setup_transport
from gateway.sync.claw_poller import ClawPoller

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class MCPGateway:
    """MCP Gateway service."""

    def __init__(self, claw_url: str, gateway_token: str, poll_interval: int = 30):
        self.claw_url = claw_url.rstrip("/")
        self.gateway_token = gateway_token
        self.poll_interval = poll_interval

        self.mcp = FastMCP("MCP Gateway")
        self.tool_registry = ToolRegistry()
        self.route_generator = RouteGenerator(self.mcp, self.tool_registry)
        self.poller: Optional[ClawPoller] = None

    async def start(self):
        """Start the gateway."""
        logger.info(f"Starting MCP Gateway, polling claw-platform at {self.claw_url}")

        # Start claw poller
        self.poller = ClawPoller(
            claw_url=self.claw_url,
            gateway_token=self.gateway_token,
            tool_registry=self.tool_registry,
            route_generator=self.route_generator,
            poll_interval=self.poll_interval,
        )
        asyncio.create_task(self.poller.run())

        # Initial fetch
        await self.poller.fetch_once()

        # Setup SSE/streamable HTTP transport
        setup_transport(self.mcp)

        logger.info("MCP Gateway started successfully")

    async def stop(self):
        """Stop the gateway."""
        if self.poller:
            await self.poller.stop()
        logger.info("MCP Gateway stopped")


def create_gateway() -> MCPGateway:
    """Create gateway instance from environment."""
    import os
    claw_url = os.environ.get("CLAW_URL", "http://localhost:8080")
    gateway_token = os.environ.get("GATEWAY_TOKEN", "dev-token")
    poll_interval = int(os.environ.get("POLL_INTERVAL", "30"))
    return MCPGateway(claw_url=claw_url, gateway_token=gateway_token, poll_interval=poll_interval)


async def main():
    gateway = create_gateway()

    # Graceful shutdown
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal")
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    # Start gateway
    await gateway.start()

    # Run until shutdown
    await shutdown_event.wait()
    await gateway.stop()


if __name__ == "__main__":
    asyncio.run(main())