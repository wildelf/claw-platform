# Multi-Modal Model Configuration Design

**Date:** 2026-04-29
**Status:** Approved

---

## Overview

Support configuring multiple model slots per Agent, with automatic model selection at runtime based on input modality (text vs. image/video).

---

## Data Model

### ModelConfig Changes

Add `modality` field to `ModelConfig`:

| Field | Type | Default | Description |
|---|---|---|---|
| `modality` | `ModelModality` enum | `text` | Input/output modality type |

**Enum `ModelModality`:**

| Value | Description |
|---|---|
| `text` | Text-only conversation (default) |
| `image-to-text` | Image understanding (VLM) |
| `text-to-image` | Text-to-image generation |
| `image-to-image` | Image-to-image transformation |
| `text-to-video` | Text-to-video generation |
| `video` | Video generation/understanding (reserved) |

**Database column:** `modality VARCHAR(20) DEFAULT 'text'`

### Agent Changes

Rename `model_config_id` to `text_model_config_id` and add image/video slots:

| Field | Type | Description |
|---|---|---|
| `text_model_config_id` | `EntityId \| null` | Text对话模型（原有 model_config_id 重命名） |
| `image_model_config_id` | `EntityId \| null` | 图生图/图生视频模型 |
| `video_model_config_id` | `EntityId \| null` | 视频模型（预留） |

---

## Frontend

### ModelCreateView / ModelEditView

- Add modality dropdown with options: text, image-to-text, text-to-image, image-to-image, text-to-video, video
- Default to `text`

### AgentCreateView / AgentEditView

- Keep existing model config selector but rename label to "Text Model"
- Add "Image Model" selector (filtered to modalities: `text-to-image`, `image-to-image`, `image-to-text`)
- Add "Video Model" selector (filtered to modalities: `text-to-video`, `video`) — visible but disabled (reserved)

### AgentDetailView

- Display all three model slots with their selected model names
- Run panel uses automatic model selection (no UI change needed)

---

## Backend

### Routes

| Method | Path | Changes |
|---|---|---|
| `GET /agents/:id` | 返回更新后的 Agent，含所有 slot 字段 |
| `POST /agents/:id/run` | 根据输入自动分发到对应模型 |

### Model Selection Logic (DeepAgentsRunner)

```python
async def _resolve_model(self, input_data: dict) -> Any:
    has_images = self._detect_images_in_input(input_data)
    if has_images and self.agent.image_model_config_id:
        return await self._get_model(self.agent.image_model_config_id)
    return await self._get_model(self.agent.text_model_config_id)
```

Detection: check if input contains base64 image data in messages.

---

## Files to Modify

### Backend
- `app/domain/model_config.py` — add `ModelModality` enum and `modality` field
- `app/domain/agent.py` — rename `model_config_id` → `text_model_config_id`, add `image_model_config_id`, `video_model_config_id`
- `app/infrastructure/storage/sqlite.py` — add `modality` column, update `model_config_id` column name logic
- `app/api/routes/agents.py` — update AgentCreate/AgentUpdate schemas and run logic
- `app/deepagents/wrapper.py` — add `_detect_images_in_input` and update `_resolve_model`

### Frontend
- `src/types/index.ts` — update `ModelConfig` and `Agent` interfaces
- `src/views/ModelCreateView.vue` — add modality dropdown
- `src/views/ModelEditView.vue` — add modality dropdown
- `src/views/AgentCreateView.vue` — add image_model selector
- `src/views/AgentEditView.vue` — add image_model selector
- `src/views/AgentDetailView.vue` — display all model slots

---

## Migration

No Alembic migrations in this project. SQLite schema is created via `Base.metadata.create_all` on startup.

SQL column rename of `model_config_id` → `text_model_config_id` in `agents` table is a breaking change. Implement as:
1. Add new columns (`text_model_config_id`, `image_model_config_id`, `video_model_config_id`)
2. On read: copy value from `model_config_id` to `text_model_config_id` if new field is null
3. Keep `model_config_id` column for backward compatibility until a migration story is run

---

## Notes

- `image_model_config_id` is used for both image generation AND image understanding (VLMs). The runner detects input type (base64 images present) and routes accordingly.
- Video model slot is reserved; UI can show it as disabled.
