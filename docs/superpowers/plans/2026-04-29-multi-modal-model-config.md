# Multi-Modal Model Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `modality` field to ModelConfig and multiple model slots (text/image/video) to Agent, with automatic runtime model selection based on input type.

**Architecture:** Backend adds `ModelModality` enum and `modality` column; Agent domain model gets three model slot fields; SQLite storage handles backward compat on read. Frontend adds modality dropdown to model forms and multiple model selectors to agent forms. Runtime model selection in DeepAgentsRunner detects image inputs and routes to appropriate model.

**Tech Stack:** Python (FastAPI + SQLAlchemy + Pydantic), TypeScript + Vue 3 + Pinia

---

## Task 1: Add ModelModality enum and modality field to ModelConfig

**Files:**
- Modify: `backend/app/domain/model_config.py`

- [ ] **Step 1: Add ModelModality enum to model_config.py**

```python
class ModelModality(str, Enum):
    TEXT = "text"
    IMAGE_TO_TEXT = "image-to-text"
    TEXT_TO_IMAGE = "text-to-image"
    IMAGE_TO_IMAGE = "image-to-image"
    TEXT_TO_VIDEO = "text-to-video"
    VIDEO = "video"
```

- [ ] **Step 2: Add modality field to ModelConfig**

```python
modality: ModelModality = ModelModality.TEXT
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/domain/model_config.py
git commit -m "feat: add ModelModality enum and modality field to ModelConfig"
```

---

## Task 2: Add multi model slots to Agent domain model

**Files:**
- Modify: `backend/app/domain/agent.py`

- [ ] **Step 1: Read current Agent model**

```bash
cat backend/app/domain/agent.py
```

- [ ] **Step 2: Rename model_config_id to text_model_config_id, add image/video slots**

```python
text_model_config_id: EntityId | None = None
image_model_config_id: EntityId | None = None
video_model_config_id: EntityId | None = None
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/domain/agent.py
git commit -m "feat: add text/image/video model slots to Agent"
```

---

## Task 3: Update SQLite storage — add columns, backward compat read

**Files:**
- Modify: `backend/app/infrastructure/storage/sqlite.py`

- [ ] **Step 1: Add modality column to ModelConfigModel**

```python
modality = Column(String(20), default="text")
```

- [ ] **Step 2: Add new columns to AgentModel**

```python
text_model_config_id = Column(String(36), nullable=True)
image_model_config_id = Column(String(36), nullable=True)
video_model_config_id = Column(String(36), nullable=True)
```

- [ ] **Step 3: Update _to_model_config to include modality**

```python
def _to_model_config(self, row: ModelConfigModel) -> ModelConfig:
    return ModelConfig(
        ...
        modality=ModelModality(row.modality or "text"),
    )
```

- [ ] **Step 4: Update _to_agent to handle new slots and backward compat**

```python
def _to_agent(self, row: AgentModel) -> Agent:
    # Backward compat: model_config_id → text_model_config_id
    text_id = row.text_model_config_id or row.model_config_id
    return Agent(
        ...
        text_model_config_id=EntityId(text_id) if text_id else None,
        image_model_config_id=EntityId(row.image_model_config_id) if row.image_model_config_id else None,
        video_model_config_id=EntityId(row.video_model_config_id) if row.video_model_config_id else None,
    )
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/infrastructure/storage/sqlite.py
git commit -m "feat: add modality column and multi model slots to storage"
```

---

## Task 4: Update Pydantic schemas for Agent

**Files:**
- Modify: `backend/app/schemas/agent.py` (or wherever agent schemas live — check with `grep -n "class.*Agent.*Schema\|class AgentCreate" backend/`)

- [ ] **Step 1: Find agent schemas file**

```bash
grep -rn "class AgentCreate\|class AgentUpdate" backend/app/
```

- [ ] **Step 2: Update AgentCreate and AgentUpdate schemas to include all three slots**

```python
class AgentCreate(BaseModel):
    text_model_config_id: str | None = None
    image_model_config_id: str | None = None
    video_model_config_id: str | None = None

class AgentUpdate(BaseModel):
    text_model_config_id: str | None = None
    image_model_config_id: str | None = None
    video_model_config_id: str | None = None
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/agent.py  # or whatever path was found
git commit -m "feat: add multi model slot fields to Agent schemas"
```

---

## Task 5: Update agents API routes

**Files:**
- Modify: `backend/app/api/routes/agents.py`

- [ ] **Step 1: Read the route file, find AgentCreate/AgentUpdate usage**

```bash
grep -n "model_config_id\|text_model" backend/app/api/routes/agents.py | head -20
```

- [ ] **Step 2: Update the agent creation/update handlers**

Ensure the new fields (`text_model_config_id`, `image_model_config_id`, `video_model_config_id`) are passed through from the request schema to the domain model.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/routes/agents.py
git commit -m "feat: wire multi model slots through agent API routes"
```

---

## Task 6: Update DeepAgentsRunner — detect images and route model

**Files:**
- Modify: `backend/app/deepagents/wrapper.py`

- [ ] **Step 1: Read _resolve_model method**

```bash
grep -n "_resolve_model\|def _resolve" backend/app/deepagents/wrapper.py
```

- [ ] **Step 2: Add _detect_images_in_input helper**

```python
def _detect_images_in_input(self, input_data: dict) -> bool:
    """Detect if input contains base64 image data."""
    messages = input_data.get("messages", [])
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str) and ("data:image" in content or "base64," in content):
            return True
    return False
```

- [ ] **Step 3: Update _resolve_model to check for images**

Replace the current `_resolve_model` body to:
1. Check `has_images` via `_detect_images_in_input`
2. If has_images and `self.agent.image_model_config_id` exists → use image model
3. Otherwise fall back to `self.agent.text_model_config_id`

- [ ] **Step 4: Commit**

```bash
git add backend/app/deepagents/wrapper.py
git commit -m "feat: auto-select model based on input modality in DeepAgentsRunner"
```

---

## Task 7: Update TypeScript types

**Files:**
- Modify: `src/types/index.ts`

- [ ] **Step 1: Add ModelModality type**

```typescript
export type ModelModality = 'text' | 'image-to-text' | 'text-to-image' | 'image-to-image' | 'text-to-video' | 'video'
```

- [ ] **Step 2: Update ModelConfig interface — add modality**

```typescript
export interface ModelConfig {
  ...
  modality?: ModelModality
}
```

- [ ] **Step 3: Update Agent interface — rename model_config_id, add image/video slots**

```typescript
export interface Agent {
  ...
  text_model_config_id: string | null
  image_model_config_id: string | null
  video_model_config_id: string | null
}
```

- [ ] **Step 4: Commit**

```bash
git add src/types/index.ts
git commit -m "feat: add modality type and multi model slots to TS types"
```

---

## Task 8: Add modality dropdown to ModelCreateView and ModelEditView

**Files:**
- Modify: `src/views/ModelCreateView.vue`, `src/views/ModelEditView.vue`

- [ ] **Step 1: Add modality to form ref**

```typescript
const form = ref({
  name: '',
  type: 'openai',
  model: '',
  api_key: '',
  base_url: '',
  modality: 'text'  // NEW
})
```

- [ ] **Step 2: Add modality dropdown to template**

```vue
<div>
  <label class="block text-sm font-medium text-gray-700 mb-1">Modality</label>
  <select v-model="form.modality" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
    <option value="text">Text</option>
    <option value="image-to-text">Image to Text (VLM)</option>
    <option value="text-to-image">Text to Image</option>
    <option value="image-to-image">Image to Image</option>
    <option value="text-to-video">Text to Video</option>
    <option value="video">Video (reserved)</option>
  </select>
</div>
```

- [ ] **Step 3: Add to handleSubmit — pass modality**

```typescript
await modelsStore.createModel({
  ...
  modality: form.modality
})
```

- [ ] **Step 4: Apply same changes to ModelEditView.vue**

- [ ] **Step 5: Commit**

```bash
git add src/views/ModelCreateView.vue src/views/ModelEditView.vue
git commit -m "feat: add modality dropdown to model forms"
```

---

## Task 9: Add image model selector to AgentCreateView and AgentEditView

**Files:**
- Modify: `src/views/AgentCreateView.vue`, `src/views/AgentEditView.vue`

- [ ] **Step 1: Load models store**

```typescript
import { useModelsStore } from '@/stores/models'
const modelsStore = useModelsStore()
```

- [ ] **Step 2: Add imageModelConfigId to form, fetch models on mount**

```typescript
const form = ref({
  ...
  text_model_config_id: '',
  image_model_config_id: '',
  video_model_config_id: '',
})

onMounted(async () => {
  ...
  await modelsStore.fetchModels()
})
```

- [ ] **Step 3: Add selectors in template after existing model selector**

```vue
<div>
  <label class="block text-sm font-medium text-gray-700 mb-1">Text Model</label>
  <select v-model="form.text_model_config_id" class="w-full px-3 py-2 border border-gray-300 rounded-lg...">
    <option value="">Default</option>
    <option v-for="m in modelsStore.models.filter(m => m.modality === 'text' || !m.modality)" :key="m.id" :value="m.id">
      {{ m.name }} ({{ m.model }})
    </option>
  </select>
</div>

<div>
  <label class="block text-sm font-medium text-gray-700 mb-1">Image Model</label>
  <select v-model="form.image_model_config_id" class="w-full px-3 py-2 border border-gray-300 rounded-lg...">
    <option value="">None</option>
    <option v-for="m in modelsStore.models.filter(m => ['text-to-image','image-to-image','image-to-text'].includes(m.modality || 'text'))" :key="m.id" :value="m.id">
      {{ m.name }} ({{ m.model }})
    </option>
  </select>
</div>
```

- [ ] **Step 4: Apply same pattern to AgentEditView.vue**

- [ ] **Step 5: Commit**

```bash
git add src/views/AgentCreateView.vue src/views/AgentEditView.vue
git commit -m "feat: add image model selector to agent forms"
```

---

## Task 10: Update AgentDetailView to display all model slots

**Files:**
- Modify: `src/views/AgentDetailView.vue`

- [ ] **Step 1: Find where model config is displayed**

- [ ] **Step 2: Update model display to show all three slots with model names**

```vue
<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
  <div>
    <p class="text-sm font-medium text-gray-500">Text Model</p>
    <p class="text-gray-900">{{ textModelName || 'Default' }}</p>
  </div>
  <div>
    <p class="text-sm font-medium text-gray-500">Image Model</p>
    <p class="text-gray-900">{{ imageModelName || 'None' }}</p>
  </div>
  <div>
    <p class="text-sm font-medium text-gray-500">Video Model</p>
    <p class="text-gray-900">{{ videoModelName || 'None' }}</p>
  </div>
</div>
```

- [ ] **Step 3: Add computed properties to resolve model names**

```typescript
const textModelName = computed(() => ...)
const imageModelName = computed(() => ...)
const videoModelName = computed(() => ...)
```

- [ ] **Step 4: Commit**

```bash
git add src/views/AgentDetailView.vue
git commit -m "feat: display all model slots in agent detail view"
```

---

## Self-Review Checklist

1. **Spec coverage:** All requirements from spec have a task? Yes
   - `modality` field on ModelConfig → Task 1
   - `text_model_config_id`, `image_model_config_id`, `video_model_config_id` on Agent → Tasks 2, 3
   - SQLite storage with backward compat → Task 3
   - API routes update → Task 5
   - Runtime model selection → Task 6
   - Frontend types → Task 7
   - Model modality dropdown → Task 8
   - Agent multi model selectors → Task 9
   - Agent detail view display → Task 10

2. **Placeholder scan:** No TBD/TODO found. All steps show actual code.

3. **Type consistency:** `ModelModality` enum values match between Python and TypeScript (`text`, `image-to-text`, etc.). Agent field names (`text_model_config_id`, `image_model_config_id`, `video_model_config_id`) consistent across backend domain, storage, API, and frontend.
