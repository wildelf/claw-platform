"""Fab system adapters — placeholder for gateway.

Note: The actual FabSystemAdapter implementations (MES/YMS/DMS/FDC)
live in backend/app/infrastructure/mcp/fab_adapters.py.

The gateway uses them indirectly: when claw-platform has a tool registration
with type=MCP and mcp_config pointing to a fab system HTTP endpoint,
the RouteGenerator calls that endpoint directly via httpx.

If the fab adapters need to be used from the gateway directly (e.g., for
shared retry logic), they can be imported from the backend package or
moved to a shared location. For now, the gateway uses raw HTTP calls
with the endpoint/method/auth from the tool config.
"""

# Fab adapters are in backend/app/infrastructure/mcp/fab_adapters.py
# The gateway's route_generator makes raw HTTP calls to the endpoints
# specified in the MCP tool config (mcp_config.endpoint).