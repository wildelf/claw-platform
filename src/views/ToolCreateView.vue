<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useToolsStore } from '@/stores/tools'

const router = useRouter()
const toolsStore = useToolsStore()

const toolTypes = [
  { value: 'CUSTOM', label: 'Custom' },
  { value: 'MCP', label: 'MCP (HTTP API)' }
]

const authTypes = [
  { value: 'none', label: 'None' },
  { value: 'bearer', label: 'Bearer Token' },
  { value: 'apikey', label: 'API Key Header' }
]

const argPositions = [
  { value: 'body', label: 'Body' },
  { value: 'query', label: 'Query Param' },
  { value: 'path', label: 'Path Param' },
  { value: 'header', label: 'Header' }
]

const form = ref({
  name: '',
  description: '',
  type: 'MCP' as 'CUSTOM' | 'MCP',
  server_name: '',
  endpoint: '',
  method: 'POST',
  auth_type: 'none',
  auth_token: '',
  auth_header_name: 'X-API-Key',
  headers: [] as { key: string; value: string }[],
  args: [] as { name: string; position: string; required: boolean; arg_type: string }[],
  request_template: '',
  response_template: '',
})

const loading = ref(false)
const error = ref<string | null>(null)

const isMCP = computed(() => form.value.type === 'MCP')

function addHeader() {
  form.value.headers.push({ key: '', value: '' })
}

function removeHeader(index: number) {
  form.value.headers.splice(index, 1)
}

function addArg() {
  form.value.args.push({ name: '', position: 'body', required: false, arg_type: 'string' })
}

function removeArg(index: number) {
  form.value.args.splice(index, 1)
}

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Name is required'
    return
  }
  if (isMCP.value && !form.value.endpoint.trim()) {
    error.value = 'Endpoint URL is required for MCP tools'
    return
  }

  loading.value = true
  error.value = null

  try {
    const payload: any = {
      name: form.value.name,
      description: form.value.description,
      type: form.value.type,
      config: {},
      allowed_tools: [],
    }

    if (isMCP.value) {
      payload.server_name = form.value.server_name || null
      payload.mcp_config = {
        endpoint: form.value.endpoint,
        method: form.value.method,
        auth: {
          type: form.value.auth_type,
          token: form.value.auth_type !== 'none' ? form.value.auth_token : null,
          header_name: form.value.auth_header_name,
        },
        headers: Object.fromEntries(
          form.value.headers.filter(h => h.key.trim() !== '').map(h => [h.key, h.value] as [string, string])
        ),
        request_template: form.value.request_template || null,
        response_template: form.value.response_template || null,
      }
      payload.args = form.value.args.filter(a => a.name.trim() !== '')
    }

    await toolsStore.createTool(payload)
    router.push('/tools')
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create tool'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push('/tools')
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-gray-900">Create New Tool</h1>

    <Card v-if="error" class="bg-red-50">
      <p class="text-red-600">{{ error }}</p>
    </Card>

    <Card title="Basic Information">
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <Input v-model="form.name" placeholder="e.g. mes_wip_query" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              v-model="form.type"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option v-for="t in toolTypes" :key="t.value" :value="t.value">
                {{ t.label }}
              </option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            v-model="form.description"
            placeholder="Describe what this tool does..."
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- MCP-specific fields -->
        <template v-if="isMCP">
          <div class="border-t pt-4 mt-4">
            <h3 class="text-sm font-semibold text-gray-700 mb-3">MCP Configuration</h3>

            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Server Name</label>
                <Input v-model="form.server_name" placeholder="e.g. mes-server (groups tools)" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">HTTP Method</label>
                <select
                  v-model="form.method"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            </div>

            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">HTTP Endpoint URL *</label>
              <Input v-model="form.endpoint" placeholder="http://mes-fab01:8080/api/v1/wip" />
            </div>

            <!-- Auth -->
            <div class="grid grid-cols-3 gap-4 mb-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Auth Type</label>
                <select
                  v-model="form.auth_type"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option v-for="a in authTypes" :key="a.value" :value="a.value">
                    {{ a.label }}
                  </option>
                </select>
              </div>
              <div v-if="form.auth_type !== 'none'">
                <label class="block text-sm font-medium text-gray-700 mb-1">Token / Value</label>
                <Input v-model="form.auth_token" type="password" placeholder="Secret token" />
              </div>
              <div v-if="form.auth_type === 'apikey'">
                <label class="block text-sm font-medium text-gray-700 mb-1">Header Name</label>
                <Input v-model="form.auth_header_name" placeholder="X-API-Key" />
              </div>
            </div>

            <!-- Custom Headers -->
            <div class="mb-4">
              <div class="flex justify-between items-center mb-2">
                <label class="block text-sm font-medium text-gray-700">Custom Headers</label>
                <Button type="button" variant="ghost" size="sm" @click="addHeader">+ Add</Button>
              </div>
              <div v-for="(header, i) in form.headers" :key="i" class="flex gap-2 mb-2">
                <Input v-model="header.key" placeholder="Header name" class="flex-1" />
                <Input v-model="header.value" placeholder="Header value" class="flex-1" />
                <Button type="button" variant="ghost" size="sm" @click="removeHeader(i)">✕</Button>
              </div>
              <p v-if="form.headers.length === 0" class="text-xs text-gray-500">No custom headers</p>
            </div>

            <!-- Args -->
            <div class="mb-4">
              <div class="flex justify-between items-center mb-2">
                <label class="block text-sm font-medium text-gray-700">Arguments</label>
                <Button type="button" variant="ghost" size="sm" @click="addArg">+ Add Arg</Button>
              </div>
              <div v-for="(arg, i) in form.args" :key="i" class="grid grid-cols-4 gap-2 mb-2 items-end">
                <Input v-model="arg.name" placeholder="arg_name" class="flex-1" />
                <select
                  v-model="arg.position"
                  class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option v-for="p in argPositions" :key="p.value" :value="p.value">{{ p.label }}</option>
                </select>
                <label class="flex items-center gap-1 text-sm">
                  <input type="checkbox" v-model="arg.required" class="w-4 h-4" />
                  Required
                </label>
                <Button type="button" variant="ghost" size="sm" @click="removeArg(i)">✕</Button>
              </div>
              <p v-if="form.args.length === 0" class="text-xs text-gray-500">No arguments defined</p>
            </div>

            <!-- Templates -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Request Template</label>
                <textarea
                  v-model="form.request_template"
                  placeholder='{"lot_id": "{{.Args.lot_id}}"}'
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs"
                />
                <p class="text-xs text-gray-500 mt-1">
                  Use &#123;&#123;.Args.xxx&#125;&#125; for args, &#123;&#123;.Config.yyy&#125;&#125; for config
                </p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Response Template</label>
                <textarea
                  v-model="form.response_template"
                  placeholder='{"wip_data": {{.Response.data}}}'
                  rows="4"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs"
                />
                <p class="text-xs text-gray-500 mt-1">
                  Use &#123;&#123;.Response.data&#125;&#125; for response fields
                </p>
              </div>
            </div>
          </div>
        </template>

        <div class="flex gap-3 pt-4">
          <Button type="submit" variant="primary" :loading="loading">
            Create Tool
          </Button>
          <Button type="button" variant="secondary" @click="handleCancel">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>