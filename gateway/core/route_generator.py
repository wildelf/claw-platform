"""Dynamic FastMCP route generation from tool configurations.

Inspired by Unla's YAML-driven tool config approach — given a tool config,
registers a FastMCP tool handler that translates MCP calls to HTTP backend requests.
"""

import logging
import re
from typing import Optional, Dict, Any

from fastmcp import FastMCP

from gateway.core.tool_registry import ToolConfig, ToolRegistry

logger = logging.getLogger(__name__)


class RouteGenerator:
    """Generates and registers FastMCP routes from tool configs."""

    def __init__(self, mcp: FastMCP, tool_registry: ToolRegistry):
        self.mcp = mcp
        self.tool_registry = tool_registry
        self._registered: Dict[str, bool] = {}

    def register_tool(self, config: ToolConfig):
        """Register a single tool as a FastMCP tool handler."""
        if config.name in self._registered:
            logger.debug(f"Tool {config.name} already registered, skipping")
            return

        tool_name = config.name
        logger.info(f"Registering MCP tool: {tool_name} → {config.method} {config.endpoint}")

        @self.mcp.tool(name=tool_name, description=config.description)
        async def tool_handler(**kwargs) -> str:
            return await self._execute_tool(config, kwargs)

        self._registered[config.name] = True

    async def _execute_tool(self, config: ToolConfig, args: Dict[str, Any]) -> str:
        """Execute an MCP tool: build HTTP request, call backend, transform response."""
        import httpx

        # 1. Build request URL with path/query args
        url = self._build_url(config, args)

        # 2. Build headers
        headers = self._build_headers(config, args)

        # 3. Build body
        body = self._build_body(config, args)

        # 4. Execute HTTP request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=config.method,
                url=url,
                headers=headers,
                content=body if body else None,
            )
            response.raise_for_status()
            result_text = response.text

        # 5. Apply response template
        if config.response_template:
            result_text = self._apply_response_template(config.response_template, result_text)

        return result_text

    def _build_url(self, config: ToolConfig, args: Dict[str, Any]) -> str:
        """Build final URL, substituting path and query params."""
        url = config.endpoint

        # Substitute path params: {{.Args.param}} in URL path
        for match in re.finditer(r'\{\{\.Args\.(\w+)\}\}', url):
            arg_name = match.group(1)
            value = str(args.get(arg_name, ""))
            url = url.replace(match.group(0), value)

        # Append query params for args with position=query
        query_parts = []
        for arg in config.args:
            if arg.get("position") == "query" and arg["name"] in args:
                query_parts.append(f"{arg['name']}={args[arg['name']]}")
        if query_parts and "?" not in url:
            url += "?" + "&".join(query_parts)

        return url

    def _build_headers(self, config: ToolConfig, args: Dict[str, Any]) -> Dict[str, str]:
        """Build request headers including auth and custom headers."""
        headers = dict(config.headers)

        # Auth header
        if config.auth.get("type") == "bearer" and config.auth.get("token"):
            headers["Authorization"] = f"Bearer {config.auth['token']}"
        elif config.auth.get("type") == "apikey" and config.auth.get("token"):
            header_name = config.auth.get("header_name", "X-API-Key")
            headers[header_name] = config.auth["token"]

        # Substitute {{.Args.xxx}} in header values
        for key, value in headers.items():
            if isinstance(value, str):
                for match in re.finditer(r'\{\{\.Args\.(\w+)\}\}', value):
                    arg_name = match.group(1)
                    headers[key] = value.replace(match.group(0), str(args.get(arg_name, "")))

        return headers

    def _build_body(self, config: ToolConfig, args: Dict[str, Any]) -> Optional[str]:
        """Build request body using request_template or arg positions."""
        if config.request_template:
            return self._apply_request_template(config.request_template, args)

        # Fallback: build JSON from body-position args
        body_args = {
            arg["name"]: args.get(arg["name"])
            for arg in config.args
            if arg.get("position") == "body" and arg["name"] in args
        }
        if body_args:
            import json
            return json.dumps(body_args)
        return None

    def _apply_request_template(self, template: str, args: Dict[str, Any]) -> str:
        """Apply {{.Args.xxx}} and {{.Config.xxx}} substitutions in request template."""
        result = template

        # {{.Args.xxx}}
        for match in re.finditer(r'\{\{\.Args\.(\w+)\}\}', result):
            arg_name = match.group(1)
            value = args.get(arg_name, "")
            if isinstance(value, (dict, list)):
                import json
                value = json.dumps(value)
            result = result.replace(match.group(0), str(value))

        # {{.Config.xxx}} - server-level config (not implemented in v1, reserved)
        result = re.sub(r'\{\{\.Config\.\w+\}\}', '', result)

        return result

    def _apply_response_template(self, template: str, response_body: str) -> str:
        """Apply {{.Response.data.field}} transformations to response."""
        import json

        try:
            data = json.loads(response_body)
        except json.JSONDecodeError:
            return response_body

        result = template

        # {{.Response.data}} → entire response data
        result = result.replace("{{.Response.data}}", json.dumps(data) if isinstance(data, (dict, list)) else str(data))

        # {{.Response.data.field}} → nested field access
        def replace_field(match):
            path = match.group(1).split(".")
            # path[0] should be "data", rest is the field path
            if path[0] == "data" and len(path) > 1:
                val = data
                for key in path[1:]:
                    if isinstance(val, dict):
                        val = val.get(key, "")
                    else:
                        return ""
                return str(val) if val is not None else ""
            return match.group(0)

        result = re.sub(r'\{\{\.Response\.data\.(\w+(?:\.\w+)*)\}\}', replace_field, result)

        return result

    def register_all(self, configs: list):
        """Register multiple tools."""
        for cfg in configs:
            if isinstance(cfg, ToolConfig):
                self.register_tool(cfg)
            else:
                # Already dict from poller
                pass