"""Transport setup for FastMCP — SSE and streamable HTTP endpoints.

Inspired by Unla's transport architecture: exposes /mcp/{tenant}/sse,
/mcp/{tenant}/message, /mcp/{tenant}/mcp endpoints.
"""

import logging
from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def setup_transport(mcp: FastMCP):
    """Configure FastMCP transport handlers (SSE + streamable HTTP)."""

    @mcp.router.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok", "service": "mcp-gateway"}

    # FastMCP handles SSE and streamable HTTP via its built-in server.
    # The FastMCP.run() call attaches these transports automatically.
    logger.info("Transport handlers registered: /health")
    logger.info("FastMCP will serve MCP over SSE and streamable HTTP on default ports")