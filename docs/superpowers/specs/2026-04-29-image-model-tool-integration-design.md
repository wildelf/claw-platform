# Image Model Tool Integration Design

**Date:** 2026-04-29
**Status:** Approved

---

## Overview

Agent has two model slots: `text_model` (主 LLM) and `image_model` (图像生成模型). When `image_model` is configured, the system automatically creates an image generation tool that the text LLM can call via the standard tool-call mechanism. Authentication is transparently sourced from the `image_model` config.

---

## Architecture

### Tool Lifecycle

- **No database storage** — dynamically created at agent runtime
- **Bound at runner creation** — if `agent.image_model_config_id` is set, `ImageGenerationTool` is injected into the agent's tool list
- **Auth from model config** — tool reads `api_key`/`base_url` from the associated `ModelConfig`

### Data Flow

```
Agent (with image_model_config_id set)
  → create_deep_agent()
    → DeepAgentsRunner.create()
      → detects image_model_config_id
        → creates ImageGenerationTool(model_config)
          → injects into tools list for create_deep_agent()

Agent run():
  → text LLM reasons and decides to call generate_image tool
    → ImageGenerationTool.execute(prompt="...")
      → calls image_model REST API with api_key/base_url
        → returns image URL or base64
```

---

## Tool Interface

### ToolType Enum

In `app/domain/tool.py`:
```python
class ToolType(str, Enum):
    MCP = "mcp"
    CUSTOM = "custom"
    IMAGE_GENERATION = "image_generation"  # NEW
```

### ImageGenerationTool

```python
class ImageGenerationTool(BaseTool):
    """Tool for generating images via a configured image model."""

    name = "generate_image"
    description = "Generates images from text descriptions. Use this when the user asks to create, generate, or draw an image."

    def __init__(self, model_config: ModelConfig, **kwargs):
        super().__init__(**kwargs)
        self._model_config = model_config

    async def invoke(self, tool_input: dict) -> str:
        prompt = tool_input.get("prompt", "")
        # Call image model REST API
        # Return image URL or base64
```

### Config Schema (tool.config field)

```json
{
  "model": "dall-e-3",       // model name to use
  "size": "1024x1024",        // optional, default 1024x1024
  "quality": "standard"      // optional, default "standard"
}
```

When created automatically from `image_model_config_id`, `config` comes from the `ModelConfig.config` dict (which already stores extra params).

---

## Runtime Injection

### DeepAgentsRunner Changes

In `wrapper.py` `create()` method, after loading tools from storage:

```python
# If agent has image_model configured, inject image generation tool
if self.agent.image_model_config_id:
    image_model_config = await self.storage.get_model_config(self.agent.image_model_config_id)
    if image_model_config:
        image_tool = ImageGenerationTool(model_config=image_model_config)
        tools.append(image_tool)
```

### Tool Call Contract

Text LLM calls `generate_image` with input:
```json
{"prompt": "a cute cat sitting on a windowsill"}
```

Tool returns (as `ToolMessage`):
```json
{"image_url": "https://..."}  // or base64 data URI
```

---

## Files to Create/Modify

### New File
- `backend/app/domain/tools/image_generation.py` — `ImageGenerationTool` class

### Modify
- `backend/app/domain/tool.py` — add `IMAGE_GENERATION` to `ToolType` enum
- `backend/app/deepagents/wrapper.py` — inject tool when `image_model_config_id` is set

---

## API Response Format

The image generation tool returns a structured result:

```json
{
  "image_url": "https://...",
  "revised_prompt": "..."  // if API returns one
}
```

Or base64:
```json
{
  "image_data": "data:image/png;base64,...",
  "format": "png"
}
```

---

## Notes

- `image_model` provider must be compatible with a simple REST API (OpenAI-compatible / DALL-E style). Local models like Fooocus need their own adapter.
- The tool is stateless — each invocation makes a fresh API call.
- If `image_model` is not set, no image generation tool is injected (graceful degradation).
- The tool is NOT saved to the tools table — it's purely runtime.
