import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSkillsStore } from '@/stores/skills'
import { skillsApi } from '@/api/skills'
import type { SkillConfig } from '@/types'

export type Mode = 'create' | 'edit'

export interface SkillForm {
  name: string
  description: string
  definition: string
  category: string
  tags: string
}

export function useSkillWorkbench() {
  const router = useRouter()
  const skillsStore = useSkillsStore()

  // Mode
  const mode = ref<Mode>('create')
  const skillId = ref<string | null>(null)

  // Form state
  const form = ref<SkillForm>({
    name: '',
    description: '',
    definition: '',
    category: '',
    tags: ''
  })

  // Config
  const localConfig = ref<SkillConfig>({
    model_id: null,
    timeout_ms: 30000,
    max_retries: 3,
    rate_limit: null,
    cache_enabled: false,
    cache_ttl_seconds: 300,
    priority: 'medium',
    max_concurrent: 5
  })

  // Generation state
  const generationProgress = ref<'idle' | 'generating' | 'success' | 'error'>('idle')
  const generationOutput = ref('')
  const testResult = ref<{output: any; metrics: any} | null>(null)

  // Files
  const generatedFiles = ref<Record<string, string>>({})
  const loadedFiles = ref<Record<string, string>>({})
  const selectedFile = ref<string | null>(null)

  // Error
  const error = ref<string | null>(null)

  // Category options
  const categoryOptions = [
    { value: 'content', label: 'Content Creation' },
    { value: 'data', label: 'Data Processing' },
    { value: 'video', label: 'Video Processing' },
    { value: 'image', label: 'Image Processing' },
    { value: 'audio', label: 'Audio Processing' },
    { value: 'coding', label: 'Coding & Development' },
    { value: 'other', label: 'Other' }
  ]

  // Computed
  const isEditMode = computed(() => mode.value === 'edit')
  const isGenerating = computed(() => generationProgress.value === 'generating')
  const canSave = computed(() => generationProgress.value === 'success' || isEditMode.value)
  const canTest = computed(() => (generationProgress.value === 'success' && skillId.value) || isEditMode.value)
  const allFiles = computed(() => {
    const files: Record<string, string> = {}
    // In edit mode, include loaded files
    if (isEditMode.value) {
      Object.assign(files, loadedFiles.value)
    }
    // Include generated files
    Object.assign(files, generatedFiles.value)
    return files
  })
  const fileNames = computed(() => Object.keys(allFiles.value))

  // Initialize for create
  function initializeForCreate() {
    mode.value = 'create'
    skillId.value = null
    form.value = { name: '', description: '', definition: '', category: '', tags: '' }
    localConfig.value = {
      model_id: null,
      timeout_ms: 30000,
      max_retries: 3,
      rate_limit: null,
      cache_enabled: false,
      cache_ttl_seconds: 300,
      priority: 'medium',
      max_concurrent: 5
    }
    generationProgress.value = 'idle'
    generationOutput.value = ''
    testResult.value = null
    generatedFiles.value = {}
    loadedFiles.value = {}
    selectedFile.value = null
    error.value = null
  }

  // Initialize for edit
  async function initializeForEdit(id: string) {
    mode.value = 'edit'
    skillId.value = id
    error.value = null
    generationProgress.value = 'idle'
    generationOutput.value = ''
    testResult.value = null
    generatedFiles.value = {}
    selectedFile.value = null

    try {
      // Fetch skill
      await skillsStore.fetchSkill(id)
      const skill = skillsStore.currentSkill
      if (skill) {
        form.value = {
          name: skill.name,
          description: skill.description,
          definition: (skill.metadata as any)?.definition || '',
          category: (skill.metadata as any)?.category || '',
          tags: (skill.metadata as any)?.tags || ''
        }
        // Load config from metadata if available
        const savedConfig = (skill.metadata as any)?.config
        if (savedConfig) {
          localConfig.value = { ...localConfig.value, ...savedConfig }
        }
      }

      // Load files
      const fileNames = await skillsApi.getFiles(id)
      const contents: Record<string, string> = {}
      for (const filename of fileNames) {
        contents[filename] = await skillsApi.getFileContent(id, filename)
      }
      loadedFiles.value = contents
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load skill'
    }
  }

  // Append to output
  function appendOutput(text: string) {
    generationOutput.value += text
  }

  // Build prompt
  function buildPrompt(): string {
    const parts = []
    if (form.value.description) {
      parts.push(`Description: ${form.value.description}`)
    }
    if (form.value.definition) {
      parts.push(`Definition: ${form.value.definition}`)
    }
    if (form.value.category) {
      parts.push(`Category: ${form.value.category}`)
    }
    if (form.value.tags) {
      parts.push(`Tags: ${form.value.tags}`)
    }
    return parts.join('\n')
  }

  // Handle generation (create mode)
  function handleGenerate() {
    if (!form.value.name.trim()) {
      error.value = 'Name is required'
      return
    }

    error.value = null
    generationProgress.value = 'generating'
    generationOutput.value = ''
    generatedFiles.value = {}

    const prompt = buildPrompt()

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/skills/generate', true)
    xhr.setRequestHeader('Content-Type', 'application/json')

    let buffer = ''
    const seenEvents = new Set<string>()

    xhr.onprogress = () => {
      buffer += xhr.responseText.substring(buffer.length)
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            // Deduplicate by type + skill_id + filename
            const eventId = data.type + (data.skill_id || '') + (data.filename || '')
            if (seenEvents.has(eventId)) continue
            seenEvents.add(eventId)
            if (data.type === 'content') {
              appendOutput(data.content)
            } else if (data.type === 'error') {
              appendOutput('\nError: ' + data.error)
            } else if (data.type === 'done') {
              appendOutput('\n\n✓ Skill generation completed!')
              generationProgress.value = 'success'
              if (data.skill_id) {
                skillId.value = data.skill_id
              }
            } else if (data.type === 'start') {
              appendOutput('Starting skill generation...\n')
            } else if (data.type === 'file') {
              const filename = data.filename || ''
              const content = data.content || ''
              if (filename && content) {
                generatedFiles.value[filename] = content
              }
            }
          } catch (e) {}
        }
      }
    }

    xhr.onload = () => {
      const remaining = buffer + xhr.responseText.substring(buffer.length)
      const lines = remaining.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            const eventId = data.type + (data.skill_id || '') + (data.filename || '')
            if (seenEvents.has(eventId)) continue
            seenEvents.add(eventId)
            if (data.type === 'content') {
              appendOutput(data.content)
            } else if (data.type === 'done') {
              generationProgress.value = 'success'
              if (data.skill_id) {
                skillId.value = data.skill_id
              }
            } else if (data.type === 'file') {
              const filename = data.filename || ''
              const content = data.content || ''
              if (filename && content) {
                generatedFiles.value[filename] = content
              }
            }
          } catch (e) {}
        }
      }
      if (generationProgress.value !== 'success') {
        generationProgress.value = 'success'
      }
    }

    xhr.onerror = () => {
      generationProgress.value = 'error'
      appendOutput('\nNetwork error')
    }

    xhr.send(JSON.stringify({
      name: form.value.name,
      description: form.value.description || `A ${form.value.category || 'general purpose'} skill: ${form.value.name}`,
      prompt,
      config: localConfig.value
    }))

    // Fallback timeout
    setTimeout(() => {
      if (generationProgress.value === 'generating') {
        generationProgress.value = 'success'
      }
    }, 30000)
  }

  // Handle modification (edit mode)
  function handleModify(changes: string) {
    if (!changes.trim()) {
      error.value = 'Please describe the changes'
      return
    }

    error.value = null
    generationProgress.value = 'generating'
    generationOutput.value = ''
    generatedFiles.value = {}

    // Build prompt with existing files context
    const filesContext = Object.entries(loadedFiles.value)
      .map(([name, content]) => `--- ${name} ---\n${content}`)
      .join('\n\n')

    const prompt = `MODIFY EXISTING SKILL: ${changes}\n\n=== EXISTING FILES ===\n${filesContext}\n\n=== REQUESTED CHANGES ===\n${changes}\n\nOutput only the modified files in JSON format.`

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/skills/generate', true)
    xhr.setRequestHeader('Content-Type', 'application/json')

    let buffer = ''
    const seenModEvents = new Set<string>()

    xhr.onprogress = () => {
      buffer += xhr.responseText.substring(buffer.length)
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            const eventId = data.type + (data.skill_id || '') + (data.filename || '')
            if (seenModEvents.has(eventId)) continue
            seenModEvents.add(eventId)
            if (data.type === 'content') {
              appendOutput(data.content)
            } else if (data.type === 'error') {
              appendOutput('\nError: ' + data.error)
            } else if (data.type === 'done') {
              appendOutput('\n\n✓ Modification completed!')
              generationProgress.value = 'success'
            } else if (data.type === 'start') {
              appendOutput('Applying modifications...\n')
            } else if (data.type === 'file') {
              const filename = data.filename || ''
              const content = data.content || ''
              if (filename && content) {
                generatedFiles.value[filename] = content
              }
            }
          } catch (e) {}
        }
      }
    }

    xhr.onload = () => {
      const remaining = buffer + xhr.responseText.substring(buffer.length)
      const lines = remaining.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            const eventId = data.type + (data.skill_id || '') + (data.filename || '')
            if (seenModEvents.has(eventId)) continue
            seenModEvents.add(eventId)
            if (data.type === 'content') {
              appendOutput(data.content)
            } else if (data.type === 'done') {
              generationProgress.value = 'success'
            } else if (data.type === 'file') {
              const filename = data.filename || ''
              const content = data.content || ''
              if (filename && content) {
                generatedFiles.value[filename] = content
              }
            }
          } catch (e) {}
        }
      }
      if (generationProgress.value !== 'success') {
        generationProgress.value = 'success'
      }
    }

    xhr.onerror = () => {
      generationProgress.value = 'error'
      appendOutput('\nNetwork error')
    }

    xhr.send(JSON.stringify({
      name: form.value.name,
      description: form.value.description,
      prompt,
      config: localConfig.value
    }))

    // Fallback timeout
    setTimeout(() => {
      if (generationProgress.value === 'generating') {
        generationProgress.value = 'success'
      }
    }, 30000)
  }

  // Select file
  function selectFile(name: string) {
    selectedFile.value = name
  }

  // Save skill
  async function handleSave() {
    try {
      if (mode.value === 'create') {
        const skill = await skillsStore.createSkill({
          name: form.value.name,
          description: form.value.description,
          metadata: {
            category: form.value.category,
            tags: form.value.tags,
            definition: form.value.definition,
            config: localConfig.value
          }
        })
        // Set skillId after creation so test can run
        skillId.value = skill.id
        mode.value = 'edit'
        router.push('/skills')
      } else if (skillId.value) {
        await skillsStore.updateSkill(skillId.value, {
          name: form.value.name,
          description: form.value.description,
          metadata: {
            category: form.value.category,
            tags: form.value.tags,
            definition: form.value.definition,
            config: localConfig.value
          }
        })
        router.push('/skills')
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to save skill'
    }
  }

  // Run test - execute the skill with test input
  async function handleRunTest(input: string): Promise<void> {
    if (!skillId.value) {
      testResult.value = {
        output: { error: 'No skill loaded for testing' },
        metrics: { duration_ms: 0, tokens_used: 0, cache_hit: false }
      }
      return
    }

    generationProgress.value = 'generating'
    generationOutput.value = ''

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `/api/skills/${skillId.value}/execute`, true)
    xhr.setRequestHeader('Content-Type', 'application/json')

    let buffer = ''
    const startTime = Date.now()

    xhr.onprogress = () => {
      buffer += xhr.responseText.substring(buffer.length)
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'content') {
              appendOutput(data.content)
            } else if (data.type === 'error') {
              appendOutput('\nError: ' + data.error)
            } else if (data.type === 'done') {
              appendOutput('\n\n✓ Execution completed!')
            }
          } catch (e) {}
        }
      }
    }

    xhr.onload = () => {
      const duration = Date.now() - startTime
      const remaining = buffer + xhr.responseText.substring(buffer.length)
      const lines = remaining.split('\n')
      let finalOutput = ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'content') finalOutput += data.content
          } catch (e) {}
        }
      }

      testResult.value = {
        output: { result: finalOutput || 'Execution completed' },
        metrics: { duration_ms: duration, tokens_used: 0, cache_hit: false }
      }
      generationProgress.value = 'idle'
    }

    xhr.onerror = () => {
      generationProgress.value = 'error'
      appendOutput('\nNetwork error')
      testResult.value = {
        output: { error: 'Network error during execution' },
        metrics: { duration_ms: 0, tokens_used: 0, cache_hit: false }
      }
    }

    xhr.send(JSON.stringify({
      task: input || 'Run the skill and return the result',
      model_config_id: localConfig.value.model_id
    }))

    // Fallback timeout
    setTimeout(() => {
      if (generationProgress.value === 'generating') {
        xhr.abort()
        generationProgress.value = 'idle'
        testResult.value = {
          output: { result: 'Execution timed out' },
          metrics: { duration_ms: 30000, tokens_used: 0, cache_hit: false }
        }
      }
    }, 60000)
  }

  // Clear test
  function handleClear() {
    testResult.value = null
  }

  // Cancel
  function handleCancel() {
    generationProgress.value = 'idle'
    generationOutput.value = ''
    router.push('/skills')
  }

  return {
    // State
    mode,
    skillId,
    form,
    localConfig,
    generationProgress,
    generationOutput,
    testResult,
    generatedFiles,
    loadedFiles,
    selectedFile,
    error,
    categoryOptions,
    // Computed
    isEditMode,
    isGenerating,
    canSave,
    canTest,
    allFiles,
    fileNames,
    // Methods
    initializeForCreate,
    initializeForEdit,
    handleGenerate,
    handleModify,
    selectFile,
    handleSave,
    handleRunTest,
    handleClear,
    handleCancel
  }
}