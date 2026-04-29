# Image Model Tool Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When an Agent has an `image_model_config_id` set, automatically inject an image generation tool that the text LLM can call via standard tool-call mechanism. Authentication is sourced from the image model config.

**Architecture:** Image generation is implemented as a runtime-only `BaseTool` (not stored in DB). When `DeepAgentsRunner.create()` finds an `image_model_config_id`, it creates `ImageGenerationTool` and injects it into the agent's tool list. Tool uses the model config's `api_key`/`base_url` for auth.

**Tech Stack:** Python (LangChain BaseTool), FastAPI, SQLAlchemy

---

## Task 1: Add IMAGE_GENERATION to ToolType enum

**Files:**
- Modify: `backend/app/domain/tool.py`

**Steps:**

1. Read the current `tool.py` to find the `ToolType` enum

2. Add `IMAGE_GENERATION = "image_generation"` to the enum:
```python
class ToolType(str, Enum):
    MCP = "mcp"
    CUSTOM = "custom"
    IMAGE_GENERATION = "image_generation"  # NEW
```

3. Run syntax check:
```bash
uv run python -m py_compile backend/app/domain/tool.py && echo "Syntax OK"
```

4. Commit:
```bash
git add backend/app/domain/tool.py
git commit -m "feat: add IMAGE_GENERATION tool type"
```

---

## Task 2: Create ImageGenerationTool class

**Files:**
- Create: `backend/app/domain/tools/image_generation.py`

**Steps:**

1. Read the spec for understanding the tool interface:
   - `name = "generate_image"`
   - `description = "Generates images from text descriptions..."`
   - Takes `prompt` string, returns image URL or base64

2. Create the file:
```python
"""Image generation tool using configured image model."""

from typing import Any

from langchain_core.tools import BaseTool

from app.domain.model_config import ModelConfig


class ImageGenerationTool(BaseTool):
    """Tool for generating images via a configured image model.

    The tool is dynamically created at agent runtime when image_model_config_id
    is set on the agent. It is NOT persisted to the database.
    """

    name: str = "generate_image"
    description: str = (
        "Generates images from text descriptions. "
        "Use this when the user asks to create, generate, draw, or paint an image. "
        "Input: {prompt: str}"
    )

    def __init__(self, model_config: ModelConfig, **kwargs):
        super().__init__(**kwargs)
        self._model_config = model_config

    async def _ainvoke(self, tool_input: dict) -> dict:
        """Execute image generation."""
        prompt = tool_input.get("prompt", "")
        if not prompt:
            return {"error": "prompt is required"}

        model = self._model_config.model
        api_key = self._model_config.api_key
        base_url = self._model_config.base_url

        # Build request to image model API
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": self._model_config.config.get("size", "1024x1024"),
            "quality": self._model_config.config.get("quality", "standard"),
        }

        # Determine endpoint based on model type
        if not base_url:
            return {"error": "image_model base_url is not configured"}

        # OpenAI-compatible images endpoint
        response = httpx.AsyncClient().post(
            f"{base_url.rstrip('/')}/v1/images/generations",
            json=payload,
            headers=headers,
            timeout=60.0,
        )

        if response.status_code != 200:
            return {"error": f"Image generation failed: {response.text}"}

        result = response.json()
        return {
            "image_url": result["data"][0]["url"],
            "revised_prompt": result["data"][0].get("revised_prompt"),
        }

    def _invoke(self, tool_input: dict) -> dict:
        """Sync invoke — delegate to async."""
        import asyncio
        return asyncio.run(self._ainvoke(tool_input))
```

3. Run syntax check:
```bash
uv run python -m py_compile backend/app/domain/tools/image_generation.py && echo "Syntax OK"
```

4. Commit:
```bash
git add backend/app/domain/tools/image_generation.py
git commit -m "feat: add ImageGenerationTool"
```

---

## Task 3: Inject tool in DeepAgentsRunner

**Files:**
- Modify: `backend/app/deepagents/wrapper.py`

**Steps:**

1. Read `wrapper.py` to find where tools are loaded and passed to `create_deep_agent`

2. Add import at top of `create()` method:
```python
from app.domain.tools.image_generation import ImageGenerationTool
```

3. In `create()`, after loading tools from storage, add:
```python
# If agent has image_model configured, inject image generation tool
if self.agent.image_model_config_id:
    image_model_config = await self.storage.get_model_config(self.agent.image_model_config_id)
    if image_model_config:
        image_tool = ImageGenerationTool(model_config=image_model_config)
        tools.append(image_tool)
```

Place this right before `create_deep_agent(model=model, tools=tools, ...)`.

4. Also update `run()` method's runner re-creation path (the `elif self._workspace_dir:` branch) to include the same injection logic.

5. Run syntax check:
```bash
uv run python -m py_compile backend/app/deepagents/wrapper.py && echo "Syntax OK"
```

6. Commit:
```bash
git add backend/app/deepagents/wrapper.py
git commit -m "feat: inject ImageGenerationTool when image_model_config_id is set"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - `IMAGE_GENERATION` enum value → Task 1
   - `ImageGenerationTool` class → Task 2
   - Runtime injection in runner → Task 3
   - Auth from model config → embedded in Task 2 (tool reads `_model_config.api_key`/`base_url`)
   - Tool interface (`generate_image(prompt)`) → Task 2

2. **Placeholder scan:** No TBD/TODO. All code is complete.

3. **Type consistency:** `ImageGenerationTool` uses `model_config: ModelConfig` (the domain entity), not a string ID. This matches the `_resolve_model` pattern already in the codebase.

---

## Execution Options

**1. Subagent-Driven (recommended)** — dispatch per task with review loops

**2. Inline Execution** — batch execute in current session

Which approach?
