# Agent 模型选择与文生图功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agent可选择不同模型执行任务，并支持文生图场景下前端展示生成的图片

**Architecture:**
- 后端：SSE事件流新增`image`类型事件，Agent执行API支持临时模型覆盖
- 前端：模型选择器 + 图片内联渲染 + 图片放大预览

**Tech Stack:** Vue 3, Pinia, FastAPI, SSE, SQLite

---

## 文件结构概览

```
backend/
├── app/api/agents.py          # 修改: RunAgentRequest添加model_config_id
├── app/deepagents/wrapper.py  # 修改: 支持模型覆盖，提取图片URL
frontend/
├── stores/models.ts          # 创建: 模型配置store
├── api/models.ts              # 创建: 模型配置API
├── views/AgentDetailView.vue  # 修改: 添加模型选择器，图片渲染
```

---

## Task 1: 后端 - 修改 RunAgentRequest 添加 model_config_id

**Files:**
- Modify: `backend/app/api/agents.py:118-122`

- [ ] **Step 1: 修改 RunAgentRequest**

```python
class RunAgentRequest(BaseModel):
    """Payload for running an agent."""
    task: str
    images: list[str] = Field(default_factory=list, description="Base64 encoded images")
    model_config_id: str | None = Field(default=None, description="临时覆盖默认模型")
```

- [ ] **Step 2: 验证语法正确**

Run: `cd backend && python -c "from app.api.agents import RunAgentRequest; print('OK')"`
Expected: `OK`

- [ ] **Step 3: 提交**

```bash
git add backend/app/api/agents.py
git commit -m "feat: add model_config_id to RunAgentRequest for model override"
```

---

## Task 2: 后端 - wrapper.py 支持模型覆盖

**Files:**
- Modify: `backend/app/deepagents/wrapper.py:50-100`

- [ ] **Step 1: 修改 create 方法签名，接收 model_config_id**

在 `DeepAgentsRunner.__init__` 中添加:
```python
def __init__(
    self,
    agent: Agent,
    storage: SQLiteStorage,
    extra_skill_paths: list[str] | None = None,
    system_prompt_override: str | None = None,
    override_model_config_id: str | None = None,  # 新增
):
    # ...
    self._override_model_config_id = override_model_config_id
```

- [ ] **Step 2: 修改 _resolve_model 方法**

更新 `_resolve_model` 方法，支持优先级:
1. `self._override_model_config_id` (临时覆盖)
2. `self.agent.model_config_id` (Agent默认)
3. `settings.models.default` (系统默认)

```python
async def _resolve_model(self):
    """Resolve model from agent configuration with override support."""
    from langchain_openai import ChatOpenAI

    # 优先级1: 临时覆盖
    if self._override_model_config_id:
        config = await self.storage.get_model_config(self._override_model_config_id)
        if config:
            return self._create_model_from_config(config)
        raise ValueError(f"Override model config not found: {self._override_model_config_id}")

    # 优先级2: Agent默认模型
    if self.agent.model_config_id:
        config = await self.storage.get_model_config(self.agent.model_config_id)
        if config:
            return self._create_model_from_config(config)

    # 优先级3: 系统默认
    default_model = settings.models.default
    if default_model.base_url:
        return ChatOpenAI(
            model=default_model.model,
            api_key=default_model.api_key,
            base_url=default_model.base_url,
        )
    return f"openai:{default_model.model}"

def _create_model_from_config(self, config: ModelConfig):
    """Create LangChain model from ModelConfig."""
    from langchain_openai import ChatOpenAI
    if config.base_url:
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
        )
    return f"openai:{config.model}"
```

- [ ] **Step 3: 修改 agents.py 的 run_agent 端点，传递 model_config_id**

修改 `run_agent` 函数:
```python
@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    request: RunAgentRequest,
    storage: Storage,
):
    # ...
    runner = DeepAgentsRunner(
        agent,
        storage,
        override_model_config_id=request.model_config_id,  # 新增
    )
```

- [ ] **Step 4: 验证语法**

Run: `cd backend && python -c "from app.deepagents.wrapper import DeepAgentsRunner; print('OK')"`
Expected: `OK`

- [ ] **Step 5: 提交**

```bash
git add backend/app/deepagents/wrapper.py backend/app/api/agents.py
git commit -m "feat: support model override in DeepAgentsRunner"
```

---

## Task 3: 后端 - SSE事件流支持图片

**Files:**
- Modify: `backend/app/deepagents/wrapper.py`

- [ ] **Step 1: 添加图片提取逻辑**

在 `DeepAgentsRunner` 中，当收到包含图片URL的响应时，提取并发送图片事件。

图片URL可能出现在:
1. LLM回复的markdown格式: `![alt](url)`
2. Tool返回的图片路径
3. 自定义事件中的image字段

在 `run` 方法的async for循环中，处理 `image` 类型事件:

```python
# 在 _extract_message_content 或处理chunk时
# 检测图片内容
def _extract_images_from_content(self, content: str) -> list[dict]:
    """Extract image URLs from content (markdown image syntax)."""
    import re
    images = []
    # Match markdown image: ![alt](url)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    for alt, url in matches:
        images.append({"url": url, "alt": alt})
    return images
```

- [ ] **Step 2: 在 run 方法中发送图片事件**

在 `run` 方法的async for循环中，处理图片:

```python
# 在 content 事件处理后
# 检测并发送图片事件
images = self._extract_images_from_content(content)
for img in images:
    yield {
        "type": "image",
        "url": img["url"],
        "alt": img["alt"],
    }
```

- [ ] **Step 3: 在 start 事件中添加 model 信息**

修改 `stream_events` 中的 start 事件:
```python
# 获取当前使用的模型名称
model_name = config.model if config else default_model.model
yield f"data: {json.dumps({'type': 'start', 'task': task, 'model': model_name})}\n\n"
```

- [ ] **Step 4: 验证**

Run: `cd backend && python -c "from app.deepagents.wrapper import DeepAgentsRunner; print('OK')"`
Expected: `OK`

- [ ] **Step 5: 提交**

```bash
git add backend/app/deepagents/wrapper.py
git commit -m "feat: add image event support in SSE stream"
```

---

## Task 4: 前端 - 创建模型配置 Store 和 API

**Files:**
- Create: `frontend/api/models.ts`
- Create: `frontend/stores/models.ts`

- [ ] **Step 1: 创建 models API**

```typescript
// frontend/api/models.ts
import client from './client'
import type { ModelConfig } from '@/types'

export const modelsApi = {
  async list(): Promise<ModelConfig[]> {
    const { data } = await client.get('/models')
    return data
  },

  async get(id: string): Promise<ModelConfig> {
    const { data } = await client.get(`/models/${id}`)
    return data
  },

  async create(config: Partial<ModelConfig>): Promise<ModelConfig> {
    const { data } = await client.post('/models', config)
    return data
  },

  async update(id: string, config: Partial<ModelConfig>): Promise<ModelConfig> {
    const { data } = await client.put(`/models/${id}`, config)
    return data
  },

  async delete(id: string): Promise<void> {
    await client.delete(`/models/${id}`)
  }
}
```

- [ ] **Step 2: 创建 models Store**

```typescript
// frontend/stores/models.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ModelConfig } from '@/types'
import { modelsApi } from '@/api/models'

export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelConfig[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchModels(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      models.value = await modelsApi.list()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch models'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { models, loading, error, fetchModels }
})
```

- [ ] **Step 3: 在 stores/index.ts 中导出**

```typescript
// frontend/stores/index.ts
export { useModelsStore } from './models'
```

- [ ] **Step 4: 添加 ModelConfig 类型到 types/index.ts**

```typescript
// 如果类型不存在，添加
export interface ModelConfig {
  id: string
  name: string
  type: 'openai' | 'anthropic' | 'local' | 'deepseek' | 'other'
  model: string
  api_key?: string
  base_url?: string
  config: Record<string, any>
  user_id: string
  created_at: string
  updated_at: string
}
```

- [ ] **Step 5: 验证类型检查**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无类型错误

- [ ] **Step 6: 提交**

```bash
git add frontend/api/models.ts frontend/stores/models.ts frontend/stores/index.ts frontend/types/index.ts
git commit -m "feat: add model config store and API"
```

---

## Task 5: 前端 - AgentDetailView 添加模型选择器

**Files:**
- Modify: `frontend/views/AgentDetailView.vue`

- [ ] **Step 1: 添加 models store 引用**

```typescript
import { useModelsStore } from '@/stores/models'
// 添加
const modelsStore = useModelsStore()
```

- [ ] **Step 2: 添加模型选择状态**

```typescript
const selectedModelId = ref<string | null>(null)
```

- [ ] **Step 3: 在 onMounted 中获取模型列表**

```typescript
onMounted(async () => {
  await agentsStore.fetchAgent(agentId.value)
  await modelsStore.fetchModels()
  // 设置默认选中的模型
  if (agent.value?.model_config_id) {
    selectedModelId.value = agent.value.model_config_id
  }
})
```

- [ ] **Step 4: 添加模型选择器UI**

在任务输入区域上方添加:
```vue
<div class="mb-4">
  <label class="block text-sm font-medium text-gray-700 mb-1">Model</label>
  <select
    v-model="selectedModelId"
    class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
    :disabled="running"
  >
    <option :value="null">System Default</option>
    <option v-for="model in modelsStore.models" :key="model.id" :value="model.id">
      {{ model.name }} ({{ model.model }})
    </option>
  </select>
</div>
```

- [ ] **Step 5: 修改 handleRun 函数，传递 model_config_id**

```typescript
function handleRun() {
  // ...
  xhr.send(JSON.stringify({
    task: taskInput.value,
    images: uploadedImages.value,
    model_config_id: selectedModelId.value  // 新增
  }))
}
```

- [ ] **Step 6: 验证**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无类型错误

- [ ] **Step 7: 提交**

```bash
git add frontend/views/AgentDetailView.vue
git commit -m "feat: add model selector to AgentDetailView"
```

---

## Task 6: 前端 - SSE 图片事件处理与展示

**Files:**
- Modify: `frontend/views/AgentDetailView.vue`

- [ ] **Step 1: 添加图片状态**

```typescript
const generatedImages = ref<Array<{url: string, alt: string}>>([])
const imageModalOpen = ref(false)
const selectedImage = ref<{url: string, alt: string} | null>(null)
```

- [ ] **Step 2: 修改 handleEvent 处理 image 类型**

```typescript
case 'image':
  if (data.url) {
    generatedImages.value.push({ url: data.url, alt: data.alt || '' })
    events.value.push({
      type: 'image',
      url: data.url,
      alt: data.alt || '',
      timestamp: new Date()
    })
  }
  break

case 'start':
  // 清空上一次的图片
  generatedImages.value = []
  events.value.push({ ...event, content: `开始执行任务: ${data.task}`, model: data.model })
  break
```

- [ ] **Step 3: 修改 outputRef 显示图片**

将 `<pre ref="outputRef">` 改为支持图片渲染的容器:

```vue
<div class="space-y-4">
  <!-- Text Output -->
  <pre ref="outputRef" class="bg-gray-100 p-4 rounded text-sm overflow-x-auto max-h-96 whitespace-pre-wrap">Waiting for response...</pre>

  <!-- Generated Images -->
  <div v-if="generatedImages.length > 0" class="space-y-2">
    <label class="block text-sm font-medium text-gray-700">Generated Images</label>
    <div class="flex flex-wrap gap-3">
      <div
        v-for="(img, idx) in generatedImages"
        :key="idx"
        class="relative group cursor-pointer"
        @click="openImageModal(img)"
      >
        <img
          :src="img.url"
          :alt="img.alt"
          class="max-w-xs rounded border border-gray-300 hover:border-primary-500 transition-colors"
        />
        <div class="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs p-1 rounded-b">
          {{ img.alt || 'Generated image' }}
        </div>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 4: 添加图片放大 Modal**

在 template 末尾添加:
```vue
<!-- Image Modal -->
<div
  v-if="imageModalOpen"
  class="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
  @click="imageModalOpen = false"
>
  <div class="max-w-4xl max-h-full p-4" @click.stop>
    <img
      v-if="selectedImage"
      :src="selectedImage.url"
      :alt="selectedImage.alt"
      class="max-w-full max-h-screen object-contain"
    />
    <p v-if="selectedImage?.alt" class="text-white text-center mt-2">{{ selectedImage.alt }}</p>
    <button
      class="absolute top-4 right-4 text-white text-2xl hover:text-gray-300"
      @click="imageModalOpen = false"
    >
      ×
    </button>
  </div>
</div>
```

- [ ] **Step 5: 添加 openImageModal 方法**

```typescript
function openImageModal(img: {url: string, alt: string}) {
  selectedImage.value = img
  imageModalOpen.value = true
}
```

- [ ] **Step 6: ESC 关闭 Modal**

```typescript
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && imageModalOpen.value) {
    imageModalOpen.value = false
  }
}

onMounted(() => {
  // ...
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
```

- [ ] **Step 7: 验证**

Run: `npm run type-check 2>&1 | head -30`
Expected: 无类型错误

- [ ] **Step 8: 提交**

```bash
git add frontend/views/AgentDetailView.vue
git commit -m "feat: add image rendering and modal preview to AgentDetailView"
```

---

## 实现检查清单

- [ ] 后端: RunAgentRequest 支持 model_config_id
- [ ] 后端: DeepAgentsRunner 支持模型覆盖
- [ ] 后端: SSE 支持 image 事件
- [ ] 前端: models store 和 API
- [ ] 前端: 模型选择器
- [ ] 前端: 图片内联展示
- [ ] 前端: 图片放大预览

---

**Plan saved to:** `docs/superpowers/plans/2026-04-27-agent-model-and-image-plan.md`