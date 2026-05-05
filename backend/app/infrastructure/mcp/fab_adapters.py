"""MCP Gateway adapters for fab internal systems (MES/YMS/DMS/FDC).

Each adapter translates between the platform's MCP tool format and
the specific HTTP API of each fab system.
"""

import json
import logging
from abc import abstractmethod
from typing import Any

import httpx

from app.deepagents.exceptions import MCPAuthError, MCPParseError, MCPTimeoutError

logger = logging.getLogger(__name__)


class FabSystemAdapter:
    """Base adapter for fab internal system MCP gateways.

    Subclass this for each fab system (MES, YMS, DMS, FDC).
    Handles HTTP API → MCP Tool translation and retry logic.
    """

    # Override in subclass
    BASE_URL: str = ""
    SYSTEM_NAME: str = "fab"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key
        self._base_url = base_url or self.BASE_URL
        self._client: httpx.AsyncClient | None = None

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def _do_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Retries up to 3 times with exponential backoff on transient failures.
        Raises MCPAuthError on 403, MCPParseError on malformed response.
        """
        from app.infrastructure.mcp.client import MAX_RETRIES, RETRY_BACKOFF_SECS

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            try:
                return await self._request(method, path, params, json_data)
            except MCPTimeoutError as e:
                last_error = e
                logger.warning(f"[{self.SYSTEM_NAME}] {method} {path} timed out (attempt {attempt + 1}/{MAX_RETRIES})")
            except MCPAuthError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.SYSTEM_NAME}] {method} {path} failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES - 1:
                backoff = RETRY_BACKOFF_SECS[min(attempt, len(RETRY_BACKOFF_SECS) - 1)]
                import asyncio
                await asyncio.sleep(backoff)

        raise last_error or RuntimeError(f"[{self.SYSTEM_NAME}] request failed after {MAX_RETRIES} retries")

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Single HTTP request without retry."""
        client = await self._get_client()

        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            response = await client.request(
                method=method,
                url=path,
                params=params,
                json=json_data,
                headers=headers,
            )
        except httpx.TimeoutException:
            raise MCPTimeoutError(tool_name=f"{self.SYSTEM_NAME}:{path}", timeout=30.0)

        if response.status_code == 403:
            raise MCPAuthError(tool_name=f"{self.SYSTEM_NAME}:{path}")

        if response.status_code >= 400:
            raise RuntimeError(f"[{self.SYSTEM_NAME}] HTTP {response.status_code}: {response.text[:200]}")

        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise MCPParseError(tool_name=f"{self.SYSTEM_NAME}:{path}", reason=str(e))

    @abstractmethod
    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools for this fab system.

        Returns list of MCP tool definitions.
        """
        ...

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on this fab system.

        Translates MCP tool call to system-specific HTTP API.
        """
        ...


class MESAdapter(FabSystemAdapter):
    """Adapter for MES (Manufacturing Execution System)."""

    BASE_URL = ""
    SYSTEM_NAME = "MES"

    async def list_tools(self) -> list[dict[str, Any]]:
        """MES tools: FDC data, batch data, lot tracking."""
        return [
            {
                "name": "mes_fdc_api",
                "description": "Get FDC (Fault Detection & Classification) metrics",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string", "description": "Metric name (e.g., defect_rate, run_rate)"},
                        "threshold": {"type": "number", "description": "Threshold value"},
                        "time_range": {"type": "string", "description": "Time range (e.g., 24h, 7d)"},
                    },
                    "required": ["metric"],
                },
            },
            {
                "name": "mes_batch_api",
                "description": "Get batch/lot production data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filters": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter fields: lot_id, wafer_id, product_id",
                        },
                        "limit": {"type": "integer", "description": "Max results"},
                    },
                },
            },
            {
                "name": "mes_lot_tracking",
                "description": "Track lot movement through fab",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "lot_id": {"type": "string", "description": "Lot ID"},
                    },
                    "required": ["lot_id"],
                },
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call MES API endpoint."""
        endpoint_map = {
            "mes_fdc_api": "/api/v1/fdc/metrics",
            "mes_batch_api": "/api/v1/batch/query",
            "mes_lot_tracking": "/api/v1/lot/track",
        }
        path = endpoint_map.get(tool_name, f"/api/v1/{tool_name}")
        result = await self._do_request("POST", path, json_data=arguments)
        return result


class YMSAdapter(FabSystemAdapter):
    """Adapter for YMS (Yield Management System)."""

    BASE_URL = ""
    SYSTEM_NAME = "YMS"

    async def list_tools(self) -> list[dict[str, Any]]:
        """YMS tools: yield analysis, bin maps, WAT data."""
        return [
            {
                "name": "yms_yield_api",
                "description": "Get yield data by product/lot",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "Product ID"},
                        "lot_id": {"type": "string", "description": "Lot ID (optional)"},
                        "start_time": {"type": "string", "description": "Start time (ISO format)"},
                        "end_time": {"type": "string", "description": "End time (ISO format)"},
                    },
                },
            },
            {
                "name": "yms_bin_map",
                "description": "Get bin map data for wafer",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "wafer_id": {"type": "string", "description": "Wafer ID"},
                        "bin_type": {"type": "string", "description": "Bin type (default: default)"},
                    },
                    "required": ["wafer_id"],
                },
            },
            {
                "name": "yms_wat_data",
                "description": "Get WAT (Wafer Acceptance Test) data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "wafer_id": {"type": "string", "description": "Wafer ID"},
                        "parameters": {"type": "array", "items": {"type": "string"}, "description": "WAT parameters"},
                    },
                    "required": ["wafer_id"],
                },
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call YMS API endpoint."""
        endpoint_map = {
            "yms_yield_api": "/api/v1/yield/query",
            "yms_bin_map": "/api/v1/binmap",
            "yms_wat_data": "/api/v1/wat/data",
        }
        path = endpoint_map.get(tool_name, f"/api/v1/{tool_name}")
        result = await self._do_request("POST", path, json_data=arguments)
        return result


class DMSAdapter(FabSystemAdapter):
    """Adapter for DMS (Defect Management System)."""

    BASE_URL = ""
    SYSTEM_NAME = "DMS"

    async def list_tools(self) -> list[dict[str, Any]]:
        """DMS tools: defect counts, pareto, equipment matching."""
        return [
            {
                "name": "dms_defect_count",
                "description": "Get defect count by lot/wafer",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "lot_id": {"type": "string", "description": "Lot ID"},
                        "wafer_id": {"type": "string", "description": "Wafer ID"},
                        "defect_type": {"type": "string", "description": "Defect type filter"},
                    },
                },
            },
            {
                "name": "dms_pareto",
                "description": "Get defect pareto analysis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "lot_id": {"type": "string", "description": "Lot ID"},
                        "top_n": {"type": "integer", "description": "Number of top defects to return"},
                    },
                    "required": ["lot_id"],
                },
            },
            {
                "name": "dms_equipment_api",
                "description": "Equipment defect pattern matching",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "mode": {"type": "string", "description": "Matching mode: equipment_matching, recipe_matching"},
                        "lot_id": {"type": "string", "description": "Lot ID"},
                        "limit": {"type": "integer", "description": "Max matched results"},
                    },
                    "required": ["mode"],
                },
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call DMS API endpoint."""
        endpoint_map = {
            "dms_defect_count": "/api/v1/defect/count",
            "dms_pareto": "/api/v1/defect/pareto",
            "dms_equipment_api": "/api/v1/defect/equipment",
        }
        path = endpoint_map.get(tool_name, f"/api/v1/{tool_name}")
        result = await self._do_request("POST", path, json_data=arguments)
        return result


class FDCAdapter(FabSystemAdapter):
    """Adapter for FDC (Fault Detection & Classification)."""

    BASE_URL = ""
    SYSTEM_NAME = "FDC"

    async def list_tools(self) -> list[dict[str, Any]]:
        """FDC tools: real-time monitoring, equipment health, APC data."""
        return [
            {
                "name": "fdc_real_time",
                "description": "Get real-time FDC monitoring data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "equipment_id": {"type": "string", "description": "Equipment ID"},
                        "metrics": {"type": "array", "items": {"type": "string"}, "description": "Metric names"},
                        "time_range": {"type": "string", "description": "Time range (e.g., 1h, 24h)"},
                    },
                },
            },
            {
                "name": "fdc_equipment_health",
                "description": "Get equipment health score",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "equipment_id": {"type": "string", "description": "Equipment ID"},
                        "time_range": {"type": "string", "description": "Time range"},
                    },
                    "required": ["equipment_id"],
                },
            },
            {
                "name": "fdc_apc_data",
                "description": "Get APC (Advanced Process Control) data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "equipment_id": {"type": "string", "description": "Equipment ID"},
                        "recipe_id": {"type": "string", "description": "Recipe ID"},
                    },
                },
            },
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call FDC API endpoint."""
        endpoint_map = {
            "fdc_real_time": "/api/v1/fdc/real_time",
            "fdc_equipment_health": "/api/v1/fdc/health",
            "fdc_apc_data": "/api/v1/fdc/apc",
        }
        path = endpoint_map.get(tool_name, f"/api/v1/{tool_name}")
        result = await self._do_request("POST", path, json_data=arguments)
        return result


# Factory to get adapter by system type
def get_fab_adapter(
    system: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> FabSystemAdapter:
    """Get the appropriate adapter for a fab system.

    Args:
        system: One of "mes", "yms", "dms", "fdc"
        api_key: Optional API key
        base_url: Optional override base URL

    Returns:
        FabSystemAdapter instance

    Raises:
        ValueError: If system is unknown
    """
    adapters = {
        "mes": MESAdapter,
        "yms": YMSAdapter,
        "dms": DMSAdapter,
        "fdc": FDCAdapter,
    }
    cls = adapters.get(system.lower())
    if not cls:
        raise ValueError(f"Unknown fab system: {system}. Known: {list(adapters.keys())}")
    return cls(api_key=api_key, base_url=base_url)
