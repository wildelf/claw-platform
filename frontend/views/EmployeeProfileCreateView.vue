<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/ui/Card.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { useEmployeeProfilesStore } from '@/stores/employeeProfiles'

const router = useRouter()
const store = useEmployeeProfilesStore()

const form = ref({
  name: '',
  role: '',
  goal: '',
  backstory: '',
  personality: '',
  constraints: '',
  working_rules: ''
})

const errors = ref<Record<string, string>>({})
const submitting = ref(false)

function validate(): boolean {
  errors.value = {}
  if (!form.value.name.trim()) {
    errors.value.name = '员工名称为必填项'
  }
  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  if (!validate()) return
  submitting.value = true
  try {
    const result = await store.createProfile(form.value)
    router.push(`/employee-profiles/${result.id}`)
  } catch {
    // Error is handled by the store
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <Button variant="ghost" @click="router.push('/employee-profiles')">
        <svg class="w-5 h-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回列表
      </Button>
    </div>

    <div>
      <h1 class="text-2xl font-bold text-gray-900">创建数字员工</h1>
      <p class="text-sm text-gray-500 mt-1">配置员工的身份、性格和工作规则</p>
    </div>

    <form @submit.prevent="handleSubmit" class="space-y-6">
      <Card>
        <h2 class="text-lg font-semibold text-gray-900 mb-4">基本信息</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">名称 <span class="text-red-500">*</span></label>
            <Input v-model="form.name" placeholder="例如：数据分析师" :error="errors.name" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">角色</label>
            <Input v-model="form.role" placeholder="例如：高级数据分析师" />
          </div>
        </div>
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">目标</label>
          <Input v-model="form.goal" placeholder="例如：分析数据并生成洞察报告" />
        </div>
      </Card>

      <Card>
        <h2 class="text-lg font-semibold text-gray-900 mb-4">性格与背景</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">背景故事</label>
            <textarea
              v-model="form.backstory"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="描述该员工的背景和经验..."
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">性格特征</label>
            <textarea
              v-model="form.personality"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              placeholder="例如：注重细节，喜欢问澄清问题..."
            />
          </div>
        </div>
      </Card>

      <Card>
        <h2 class="text-lg font-semibold text-gray-900 mb-4">约束与规则</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">约束条件</label>
            <textarea
              v-model="form.constraints"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
              placeholder="- 绝不修改生产数据&#10;- 未经批准不发送外部通知"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">工作规则</label>
            <textarea
              v-model="form.working_rules"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm font-mono"
              placeholder="- 分析前先验证数据质量&#10;- 发现异常时明确报告"
            />
          </div>
        </div>
      </Card>

      <div class="flex justify-end gap-3">
        <Button variant="secondary" @click="router.push('/employee-profiles')">取消</Button>
        <Button variant="primary" :loading="submitting" type="submit">创建员工</Button>
      </div>
    </form>
  </div>
</template>
