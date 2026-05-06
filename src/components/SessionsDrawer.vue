<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSessionsStore } from '@/stores/sessions'
import IconButton from '@/components/ui/IconButton.vue'
import Input from '@/components/ui/Input.vue'

const props = defineProps<{
  open: boolean
  agentId: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', sessionId: string): void
}>()

const sessionsStore = useSessionsStore()
const editingId = ref<string | null>(null)
const editingName = ref('')

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await sessionsStore.fetchSessions()
  }
})

function formatTime(isoString: string): string {
  const d = new Date(isoString)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins}分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return d.toLocaleDateString()
}

function getDisplayName(session: { name: string; message_count: number }): string {
  if (session.name) return session.name
  return session.message_count > 0 ? '新会话' : '空会话'
}

async function handleNewSession() {
  const session = await sessionsStore.createSession(props.agentId)
  emit('select', session.id)
  emit('close')
}

function handleSelect(sessionId: string) {
  emit('select', sessionId)
  emit('close')
}

function startEdit(id: string, currentName: string) {
  editingId.value = id
  editingName.value = currentName
}

async function saveEdit(id: string) {
  if (editingName.value.trim()) {
    await sessionsStore.updateSession(id, editingName.value.trim())
  }
  editingId.value = null
}

async function handleDelete(id: string) {
  await sessionsStore.deleteSession(id)
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="drawer-overlay" @click="emit('close')" />
    <div :class="['drawer', { open }]">
      <div class="drawer-header">
        <span class="drawer-title">会话历史</span>
        <IconButton icon="close" @click="emit('close')" />
      </div>

      <div class="drawer-content">
        <button class="new-session-btn" @click="handleNewSession">
          + 新建会话
        </button>

        <div class="sessions-list">
          <div
            v-for="session in sessionsStore.sessions"
            :key="session.id"
            class="session-item"
          >
            <template v-if="editingId === session.id">
              <Input
                v-model="editingName"
                class="edit-input"
                @keyup.enter="saveEdit(session.id)"
                @blur="saveEdit(session.id)"
                @keyup.escape="editingId = null"
                autofocus
              />
            </template>
            <template v-else>
              <div class="session-info" @click="handleSelect(session.id)">
                <span class="session-name">{{ getDisplayName(session) }}</span>
                <span class="session-time">{{ formatTime(session.updated_at) }}</span>
              </div>
              <div class="session-actions">
                <IconButton
                  icon="edit"
                  size="small"
                  @click.stop="startEdit(session.id, session.name)"
                />
                <IconButton
                  icon="delete"
                  size="small"
                  @click.stop="handleDelete(session.id)"
                />
              </div>
            </template>
          </div>

          <div v-if="sessionsStore.sessions.length === 0" class="empty-state">
            暂无会话记录
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 320px;
  height: 100vh;
  background: var(--color-surface);
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.2s ease;
  z-index: 101;
  display: flex;
  flex-direction: column;
}

.drawer.open {
  transform: translateX(0);
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.drawer-title {
  font-weight: 600;
}

.drawer-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.new-session-btn {
  width: 100%;
  padding: 10px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 16px;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--color-background);
}

.session-item:hover .session-actions {
  opacity: 1;
}

.session-info {
  flex: 1;
  cursor: pointer;
  min-width: 0;
}

.session-name {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.session-time {
  display: block;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.session-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.edit-input {
  flex: 1;
}

.empty-state {
  text-align: center;
  color: var(--color-text-muted);
  padding: 24px;
}
</style>