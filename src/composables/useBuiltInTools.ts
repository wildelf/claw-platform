import { ref } from 'vue'
import type { BuiltInTool } from '@/types'
import { BUILTIN_TOOLS } from '@/types'

const enabledTools = ref<Set<string>>(new Set())

export function useBuiltInTools() {
  function enableTool(toolName: string) {
    enabledTools.value.add(toolName)
  }

  function disableTool(toolName: string) {
    enabledTools.value.delete(toolName)
  }

  function isEnabled(toolName: string): boolean {
    return enabledTools.value.has(toolName)
  }

  function getEnabledTools(): BuiltInTool[] {
    return BUILTIN_TOOLS.map(tool => ({
      ...tool,
      enabled: enabledTools.value.has(tool.name)
    }))
  }

  function setEnabledTools(toolNames: string[]) {
    enabledTools.value = new Set(toolNames)
  }

  return {
    enabledTools,
    enableTool,
    disableTool,
    isEnabled,
    getEnabledTools,
    setEnabledTools,
    builtinTools: BUILTIN_TOOLS
  }
}