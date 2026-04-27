# 模型配置管理页面实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建模型配置管理页面（列表/创建/编辑），并在 Agent 创建/编辑页添加模型选择

**Architecture:**
- 前端页面：ModelsView（列表）、ModelCreateView（创建）、ModelEditView（编辑）
- 路由配置：添加 /models, /models/create, /models/:id/edit
- Agent 编辑：在 AgentCreateView/AgentEditView 中添加 model_config_id 下拉选择

**Tech Stack:** Vue 3, Pinia, Vue Router, TypeScript

---

## 文件结构

```
frontend/
├── views/
│   ├── ModelsView.vue          # 创建: 模型列表页
│   ├── ModelCreateView.vue     # 创建: 模型创建页
│   └── ModelEditView.vue       # 创建: 模型编辑页
├── router/index.ts             # 修改: 添加路由
├── views/AgentCreateView.vue   # 修改: 添加模型选择
└── views/AgentEditView.vue     # 修改: 添加模型选择
```

---

## Task 1: 添加路由配置

**Files:**
- Modify: `frontend/router/index.ts`

- [ ] **Step 1: 添加路由**

在 routes 数组中添加:

```typescript
{
  path: '/models',
  name: 'models',
  component: () => import('@/views/ModelsView.vue')
},
{
  path: '/models/create',
  name: 'model-create',
  component: () => import('@/views/ModelCreateView.vue')
},
{
  path: '/models/:id/edit',
  name: 'model-edit',
  component: () => import('@/views/ModelEditView.vue')
},
```

- [ ] **Step 2: 验证**

Run: `grep -n "models" frontend/router/index.ts`
Expected: 显示3处路由配置

- [ ] **Step 3: 提交**

```bash
git add frontend/router/index.ts
git commit -m "feat: add routes for model config pages"
```

---

## Task 2: 创建 ModelsView 列表页

**Files:**
- Create: `frontend/views/ModelsView.vue`

- [ ] **Step 1: 创建 ModelsView.vue**

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Table from '@/components/ui/Table.vue'
import { useModelsStore } from '@/stores/models'

const router = useRouter()
const modelsStore = useModelsStore()

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'type', label: 'Provider', width: '120px' },
  { key: 'model', label: 'Model' },
  { key: 'base_url', label: 'Base URL' },
  { key: 'actions', label: 'Actions', width: '200px' }
]

onMounted(() => {
  modelsStore.fetchModels()
})

function handleEdit(modelId: string) {
  router.push(`/models/${modelId}/edit`)
}

async function handleDelete(modelId: string) {
  if (confirm('Are you sure you want to delete this model config?')) {
    await modelsStore.deleteModel(modelId)
  }
}

function getProviderBadge(type: string): string {
  switch (type) {
    case 'openai': return 'blue'
    case 'anthropic': return 'purple'
    case 'deepseek': return 'green'
    default: return 'gray'
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">Model Configurations</h1>
      <router-link to="/models/create">
        <Button variant="primary">Create Model</Button>
      </router-link>
    </div>

    <Card v-if="modelsStore.loading" class="text-center py-8 text-gray-500">
      Loading...
    </Card>

    <Card v-else-if="modelsStore.models.length === 0" class="text-center py-8">
      <p class="text-gray-500 mb-4">No model configurations yet</p>
      <router-link to="/models/create">
        <Button variant="primary">Create Your First Model</Button>
      </router-link>
    </Card>

    <Card v-else :padding="false">
      <Table :columns="columns" :data="modelsStore.models">
        <template #cell-name="{ row }">
          <span class="font-medium">{{ row.name }}</span>
        </template>
        <template #cell-type="{ row }">
          <span :class="`px-2 py-1 rounded text-xs bg-${getProviderBadge(row.type)}-100 text-${getProviderBadge(row.type)}-800`">
            {{ row.type }}
          </span>
        </template>
        <template #cell-model="{ row }">
          <span class="text-gray-600">{{ row.model }}</span>
        </template>
        <template #cell-base_url="{ row }">
          <span class="text-gray-500 text-sm">{{ row.base_url || '-' }}</span>
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-2">
            <Button variant="ghost" size="sm" @click="handleEdit(row.id)">Edit</Button>
            <Button variant="danger" size="sm" @click="handleDelete(row.id)">Delete</Button>
          </div>
        </template>
      </Table>
    </Card>
  </div>
</template>
```

- [ ] **Step 2: 验证**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无错误

- [ ] **Step 3: 提交**

```bash
git add frontend/views/ModelsView.vue
git commit -m "feat: add ModelsView list page"
```

---

## Task 3: 创建 ModelCreateView 创建页

**Files:**
- Create: `frontend/views/ModelCreateView.vue`

- [ ] **Step 1: 创建 ModelCreateView.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useModelsStore } from '@/stores/models'

const router = useRouter()
const modelsStore = useModelsStore()

const form = ref({
  name: '',
  type: 'openai',
  model: '',
  api_key: '',
  base_url: ''
})

const loading = ref(false)
const error = ref<string | null>(null)

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'local', label: 'Local' },
  { value: 'other', label: 'Other' }
]

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }
  if (!form.value.model.trim()) {
    error.value = 'Model name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await modelsStore.createModel({
      name: form.value.name,
      type: form.value.type as any,
      model: form.value.model,
      api_key: form.value.api_key || undefined,
      base_url: form.value.base_url || undefined
    })
    router.push('/models')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create model'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/models')
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Create Model Configuration</h1>

    <Card v-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card title="Model Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <Input
            v-model="form.name"
            placeholder="e.g., OpenAI GPT-4o"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Provider *</label>
          <select
            v-model="form.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Model Name *</label>
          <Input
            v-model="form.model"
            placeholder="e.g., gpt-4o"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
          <input
            v-model="form.api_key"
            type="password"
            placeholder="Optional - for API authentication"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
          <Input
            v-model="form.base_url"
            placeholder="e.g., https://api.openai.com/v1"
          />
          <p class="text-sm text-gray-500 mt-1">
            Optional - leave empty to use provider's default endpoint
          </p>
        </div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Create
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>
```

- [ ] **Step 2: 验证**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无错误

- [ ] **Step 3: 提交**

```bash
git add frontend/views/ModelCreateView.vue
git commit -m "feat: add ModelCreateView page"
```

---

## Task 4: 创建 ModelEditView 编辑页

**Files:**
- Create: `frontend/views/ModelEditView.vue`

- [ ] **Step 1: 创建 ModelEditView.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useModelsStore } from '@/stores/models'

const route = useRoute()
const router = useRouter()
const modelsStore = useModelsStore()

const modelId = route.params.id as string

const form = ref({
  name: '',
  type: 'openai',
  model: '',
  api_key: '',
  base_url: ''
})

const loading = ref(false)
const error = ref<string | null>(null)

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'local', label: 'Local' },
  { value: 'other', label: 'Other' }
]

onMounted(async () => {
  const model = await modelsStore.getModel(modelId)
  if (model) {
    form.value.name = model.name
    form.value.type = model.type
    form.value.model = model.model
    form.value.api_key = model.api_key || ''
    form.value.base_url = model.base_url || ''
  }
})

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }
  if (!form.value.model.trim()) {
    error.value = 'Model name is required'
    return
  }

  loading.value = true
  error.value = null

  try {
    await modelsStore.updateModel(modelId, {
      name: form.value.name,
      type: form.value.type as any,
      model: form.value.model,
      api_key: form.value.api_key || undefined,
      base_url: form.value.base_url || undefined
    })
    router.push('/models')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to update model'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/models')
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Edit Model Configuration</h1>

    <Card v-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card title="Model Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
          <Input
            v-model="form.name"
            placeholder="e.g., OpenAI GPT-4o"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Provider *</label>
          <select
            v-model="form.type"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="opt in providerOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Model Name *</label>
          <Input
            v-model="form.model"
            placeholder="e.g., gpt-4o"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
          <input
            v-model="form.api_key"
            type="password"
            placeholder="Leave empty to keep current"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p class="text-sm text-gray-500 mt-1">
            Leave empty to keep current API key
          </p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
          <Input
            v-model="form.base_url"
            placeholder="e.g., https://api.openai.com/v1"
          />
        </div>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Save Changes
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>
```

- [ ] **Step 2: 更新 models store 添加 getModel 方法**

检查 `frontend/stores/models.ts` 是否已有 `getModel` 方法。如果没有，添加:

```typescript
async function getModel(id: string): Promise<ModelConfig | null> {
  try {
    return await modelsApi.get(id)
  } catch {
    return null
  }
}

// 在 return 中添加 getModel
return { models, loading, error, fetchModels, getModel, createModel, updateModel, deleteModel }
```

- [ ] **Step 3: 验证**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无错误

- [ ] **Step 4: 提交**

```bash
git add frontend/views/ModelEditView.vue frontend/stores/models.ts
git commit -m "feat: add ModelEditView page"
```

---

## Task 5: AgentCreateView 添加模型选择

**Files:**
- Modify: `frontend/views/AgentCreateView.vue`

- [ ] **Step 1: 添加 model_config_id 到表单**

在 formData ref 中添加 model_config_id:

```typescript
const formData = ref({
  name: '',
  description: '',
  role: '',
  goal: '',
  backstory: '',
  skill_ids: [] as string[],
  model_config_id: null as string | null  // 新增
})
```

- [ ] **Step 2: 获取模型列表**

在 onMounted 中添加:
```typescript
onMounted(async () => {
  await skillsStore.fetchSkills()
  await modelsStore.fetchModels()  // 新增
})
```

- [ ] **Step 3: 添加模型选择器 UI**

在 Skills 选择之后添加:

```vue
<div>
  <label class="block text-sm font-medium text-gray-700 mb-2">Default Model</label>
  <select
    v-model="formData.model_config_id"
    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option :value="null">System Default</option>
    <option v-for="model in modelsStore.models" :key="model.id" :value="model.id">
      {{ model.name }} ({{ model.model }})
    </option>
  </select>
  <p class="text-sm text-gray-500 mt-1">
    Optionally select a default model for this agent
  </p>
</div>
```

- [ ] **Step 4: 添加 stores 引用**

在 script 中添加:
```typescript
import { useModelsStore } from '@/stores/models'
const modelsStore = useModelsStore()
```

- [ ] **Step 5: 验证**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无错误

- [ ] **Step 6: 提交**

```bash
git add frontend/views/AgentCreateView.vue
git commit -m "feat: add model selection to AgentCreateView"
```

---

## Task 6: AgentEditView 添加模型选择

**Files:**
- Modify: `frontend/views/AgentEditView.vue`

- [ ] **Step 1: 读取 AgentEditView 内容并添加模型选择**

参考 AgentCreateView 的修改，添加:
1. model_config_id 到 formData
2. modelsStore.fetchModels() 在 onMounted
3. 模型选择下拉框 UI

- [ ] **Step 2: 验证**

Run: `npm run type-check 2>&1 | head -20`
Expected: 无错误

- [ ] **Step 3: 提交**

```bash
git add frontend/views/AgentEditView.vue
git commit -m "feat: add model selection to AgentEditView"
```

---

## 实现检查清单

- [ ] 路由配置添加
- [ ] ModelsView 列表页
- [ ] ModelCreateView 创建页
- [ ] ModelEditView 编辑页（含 getModel 方法）
- [ ] AgentCreateView 模型选择
- [ ] AgentEditView 模型选择

---

**Plan saved to:** `docs/superpowers/plans/2026-04-27-model-config-page-plan.md`