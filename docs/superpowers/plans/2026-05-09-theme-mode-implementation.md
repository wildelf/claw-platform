# 主题模式实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 claw-platform 添加白色/黑色两种主题模式，用户可在导航栏随时切换

**Architecture:** 使用 CSS 变量 + `data-theme` 属性方案。在 `main.css` 定义两套变量，切换时修改 `<html data-theme>` 属性，主题偏好存 localStorage

**Tech Stack:** Vue 3 + TypeScript + Tailwind CSS + Pinia (如需 store)

---

## 文件结构

需要修改的文件：
- `src/assets/main.css` — 定义 `[data-theme="light"]` 和 `[data-theme="dark"]` CSS 变量
- `src/main.ts` — 入口读取 localStorage 并设置 `data-theme` 到 `<html>`
- `src/components/layout/AppHeader.vue` — 添加主题切换按钮
- `src/components/layout/AppSidebar.vue` — 使用 CSS 变量替代硬编码颜色
- `src/components/ui/Card.vue` — 使用 CSS 变量
- `src/components/ui/Modal.vue` — 使用 CSS 变量
- `src/components/ui/Input.vue` — 使用 CSS 变量
- `src/components/ui/Select.vue` — 使用 CSS 变量
- `src/components/ui/Table.vue` — 使用 CSS 变量

---

## Task 1: 定义 CSS 变量主题系统

**Files:**
- Modify: `src/assets/main.css:1-50`

- [ ] **Step 1: 更新 main.css 添加两套主题变量**

将文件内容替换为：

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #3b82f6;
  --color-success: #22c55e;
  --color-danger: #ef4444;
}

/* 白色主题 (默认) */
[data-theme="light"],
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --bg-tertiary: #e5e5e5;
  --border-color: #d4d4d4;
  --text-primary: #171717;
  --text-secondary: #525252;
  --text-muted: #a3a3a3;
}

/* 黑色主题 */
[data-theme="dark"] {
  --bg-primary: #1f1f1f;
  --bg-secondary: #262626;
  --bg-tertiary: #333333;
  --border-color: #404040;
  --text-primary: #fafafa;
  --text-secondary: #a3a3a3;
  --text-muted: #737373;
}
```

- [ ] **Step 2: 提交**

```bash
git add src/assets/main.css
git commit -m "feat(frontend): add theme CSS variables for light/dark mode"
```

---

## Task 2: 主题初始化逻辑

**Files:**
- Modify: `src/main.ts:1-12`

- [ ] **Step 1: 更新 main.ts 添加主题初始化**

将 `src/main.ts` 内容替换为：

```ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './assets/main.css'
import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 初始化主题：从 localStorage 读取或默认白色主题
const savedTheme = localStorage.getItem('theme') || 'light'
document.documentElement.setAttribute('data-theme', savedTheme)

app.mount('#app')
```

- [ ] **Step 2: 提交**

```bash
git add src/main.ts
git commit -m "feat(frontend): init theme from localStorage on app start"
```

---

## Task 3: AppHeader 主题切换按钮

**Files:**
- Modify: `src/components/layout/AppHeader.vue:1-104`

- [ ] **Step 1: 更新 AppHeader.vue 添加主题切换按钮**

在 `src/components/layout/AppHeader.vue` 的 `<script setup>` 中添加：

```ts
const theme = ref(localStorage.getItem('theme') || 'light')

function toggleTheme() {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme.value)
  localStorage.setItem('theme', theme.value)
}
```

在 `AppHeader.vue` 的导航栏区域 `<nav class="hidden md:flex...">` 之后、`<div class="flex items-center space-x-4">` 之前添加切换按钮：

```html
<button
  @click="toggleTheme"
  class="p-2 rounded-md hover:bg-gray-100 transition-colors"
  :aria-label="theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'"
>
  <!-- 太阳图标 (light mode) -->
  <svg v-if="theme === 'light'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-600">
    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
  </svg>
  <!-- 月亮图标 (dark mode) -->
  <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-gray-400">
    <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
  </svg>
</button>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/layout/AppHeader.vue
git commit -m "feat(frontend): add theme toggle button to AppHeader"
```

---

## Task 4: AppSidebar 适配主题

**Files:**
- Modify: `src/components/layout/AppSidebar.vue:69-114`

- [ ] **Step 1: 更新 AppSidebar.vue 使用 CSS 变量**

第 72 行 `bg-white` → `bg-[var(--bg-primary)]`
第 72 行 `border-r border-gray-200` → `border-r border-[var(--border-color)]`
第 83 行 `hover:bg-gray-100` → `hover:bg-[var(--bg-secondary)]`
第 96 行 `text-gray-700` → `text-[var(--text-secondary)]`
第 100 行 `border-t border-gray-200` → `border-t border-[var(--border-color)]`
第 101 行 `text-gray-500` → `text-[var(--text-muted)]`
第 107 行 `hover:bg-gray-100` → `hover:bg-[var(--bg-secondary)]`

修改后模板部分应该像这样（第 69-114 行）：

```html
<aside
  :class="[
    'fixed left-0 top-14 bottom-0 bg-[var(--bg-primary)] border-r border-[var(--border-color)] transition-all duration-300 z-40',
    sidebarWidth
  ]"
>
  <nav class="p-2">
    <RouterLink
      v-for="item in navItems"
      :key="item.path"
      :to="item.path"
      active-class="bg-[var(--bg-secondary)] text-[var(--color-primary)]"
      exact-active-class="bg-[var(--bg-secondary)] text-[var(--color-primary)]"
      class="flex items-center px-3 py-2.5 rounded-md hover:bg-[var(--bg-secondary)] transition-colors mb-1"
      :class="collapsed ? 'justify-center' : ''"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
        :class="['w-5 h-5', collapsed ? '' : 'mr-3']"
      >
        <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
      </svg>
      <span v-if="!collapsed" class="text-sm text-[var(--text-secondary)]">{{ item.label }}</span>
    </RouterLink>
  </nav>

  <div v-if="!collapsed" class="px-4 pt-4 border-t border-[var(--border-color)] mt-4">
    <h3 class="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-3">Recent Agents</h3>
    <div class="space-y-2">
      <button
        v-for="agent in recentAgents"
        :key="agent.id"
        @click="router.push(`/agents/${agent.id}`)"
        class="w-full text-left px-3 py-2 text-sm text-[var(--text-secondary)] rounded-md hover:bg-[var(--bg-secondary)] transition-colors"
      >
        {{ agent.name }}
      </button>
    </div>
  </div>
</aside>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/layout/AppSidebar.vue
git commit -m "refactor(frontend): use CSS variables for theme support in AppSidebar"
```

---

## Task 5: Card 组件适配主题

**Files:**
- Modify: `src/components/ui/Card.vue:12-21`

- [ ] **Step 1: 更新 Card.vue 使用 CSS 变量**

第 13 行 `bg-white rounded-lg shadow border border-gray-200` → `bg-[var(--bg-primary)] rounded-lg shadow border border-[var(--border-color)]`
第 14 行 `border-b border-gray-200` → `border-b border-[var(--border-color)]`
第 15 行 `text-gray-900` → `text-[var(--text-primary)]`

修改后模板：

```html
<div class="bg-[var(--bg-primary)] rounded-lg shadow border border-[var(--border-color)]">
  <div v-if="title" class="px-4 py-3 border-b border-[var(--border-color)]">
    <h3 class="text-lg font-semibold text-[var(--text-primary)]">{{ title }}</h3>
  </div>
  <div :class="[' rounded-b-lg', { 'p-4': padding }]">
    <slot />
  </div>
</div>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/ui/Card.vue
git commit -m "refactor(frontend): use CSS variables for theme support in Card"
```

---

## Task 6: Modal 组件适配主题

**Files:**
- Modify: `src/components/ui/Modal.vue:13-60`

- [ ] **Step 1: 更新 Modal.vue 使用 CSS 变量**

第 24 行 `bg-white rounded-lg shadow-xl` → `bg-[var(--bg-primary)] rounded-lg shadow-xl`
第 25 行 `border-b border-gray-200` → `border-b border-[var(--border-color)]`
第 26 行 `text-gray-900` → `text-[var(--text-primary)]`
第 30-31 行 `text-gray-400 hover:text-gray-600` → `text-[var(--text-muted)] hover:text-[var(--text-primary)]`
第 41 行 `border-t border-gray-200 bg-gray-50` → `border-t border-[var(--border-color)] bg-[var(--bg-secondary)]`

修改后模板关键部分：

```html
<div class="relative bg-[var(--bg-primary)] rounded-lg shadow-xl max-w-lg w-full mx-4">
  <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--border-color)]">
    <h3 class="text-lg font-semibold text-[var(--text-primary)]">
      {{ title || '' }}
    </h3>
    <button
      class="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
      @click="emit('close')"
    >
      <!-- close icon -->
    </button>
  </div>
  <div class="p-4">
    <slot />
  </div>
  <div v-if="$slots.footer" class="px-4 py-3 border-t border-[var(--border-color)] bg-[var(--bg-secondary)] rounded-b-lg">
    <slot name="footer" />
  </div>
</div>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/ui/Modal.vue
git commit -m "refactor(frontend): use CSS variables for theme support in Modal"
```

---

## Task 7: Input 组件适配主题

**Files:**
- Modify: `src/components/ui/Input.vue:16-34`

- [ ] **Step 1: 更新 Input.vue 使用 CSS 变量**

第 26 行 `border-gray-300` → `border-[var(--border-color)]`
第 27 行 `border-red-500` → `border-[var(--color-danger)]`
第 28 行 `bg-gray-100` → `bg-[var(--bg-tertiary)]`
第 29 行 `bg-white` → `bg-[var(--bg-primary)]`

修改后模板部分：

```html
<input
  :type="type || 'text'"
  :value="modelValue"
  :placeholder="placeholder"
  :disabled="disabled"
  :class="[
    'w-full px-3 py-2 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500',
    {
      'border-[var(--border-color)]': !error,
      'border-[var(--color-danger)]': error,
      'bg-[var(--bg-tertiary)] cursor-not-allowed': disabled,
      'bg-[var(--bg-primary)]': !disabled
    }
  ]"
  @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
/>
<p v-if="error" class="mt-1 text-sm text-[var(--color-danger)]">{{ error }}</p>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/ui/Input.vue
git commit -m "refactor(frontend): use CSS variables for theme support in Input"
```

---

## Task 8: Select 组件适配主题

**Files:**
- Modify: `src/components/ui/Select.vue:22-55`

- [ ] **Step 1: 更新 Select.vue 使用 CSS 变量**

第 34 行 `border-gray-300` → `border-[var(--border-color)]`
第 35 行 `border-red-500` → `border-[var(--color-danger)]`
第 36 行 `bg-gray-100` → `bg-[var(--bg-tertiary)]`
第 37 行 `bg-white` → `bg-[var(--bg-primary)]`
第 24 行 `text-gray-700` → `text-[var(--text-secondary)]`
第 48 行 `text-gray-400` → `text-[var(--text-muted)]`
第 53 行 `text-red-500` → `text-[var(--color-danger)]`

修改后模板部分：

```html
<label v-if="label" class="block text-sm font-medium text-[var(--text-secondary)] mb-1">
  {{ label }}
</label>
<div class="relative">
  <select
    :value="modelValue"
    :disabled="disabled"
    :class="[
      'w-full px-3 py-2 pr-8 border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none',
      {
        'border-[var(--border-color)]': !error,
        'border-[var(--color-danger)]': error,
        'bg-[var(--bg-tertiary)] cursor-not-allowed': disabled,
        'bg-[var(--bg-primary)]': !disabled && !error
      }
    ]"
    @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
  >
    <!-- options -->
  </select>
  <div class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
    <svg class="w-4 h-4 text-[var(--text-muted)]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
    </svg>
  </div>
</div>
<p v-if="error" class="mt-1 text-sm text-[var(--color-danger)]">{{ error }}</p>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/ui/Select.vue
git commit -m "refactor(frontend): use CSS variables for theme support in Select"
```

---

## Task 9: Table 组件适配主题

**Files:**
- Modify: `src/components/ui/Table.vue:16-54`

- [ ] **Step 1: 更新 Table.vue 使用 CSS 变量**

第 19 行 `bg-gray-50` → `bg-[var(--bg-secondary)]`
第 25 行 `text-gray-500` → `text-[var(--text-muted)]`
第 31 行 `bg-white divide-y divide-gray-200` → `bg-[var(--bg-primary)] divide-y divide-[var(--border-color)]`
第 33 行 `text-gray-500` → `text-[var(--text-muted)]`
第 40 行 `hover:bg-gray-50` → `hover:bg-[var(--bg-secondary)]`
第 45 行 `text-gray-900` → `text-[var(--text-primary)]`

修改后模板部分：

```html
<table class="min-w-full divide-y divide-[var(--border-color)]">
  <thead class="bg-[var(--bg-secondary)]">
    <tr>
      <th
        v-for="column in columns"
        :key="column.key"
        :style="column.width ? { width: column.width } : undefined"
        class="px-4 py-3 text-left text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider"
      >
        {{ column.label }}
      </th>
    </tr>
  </thead>
  <tbody class="bg-[var(--bg-primary)] divide-y divide-[var(--border-color)]">
    <tr v-if="props.data.length === 0">
      <td :colspan="columns.length" class="px-4 py-8 text-center text-[var(--text-muted)]">
        No data available
      </td>
    </tr>
    <tr
      v-for="(row, index) in props.data"
      :key="index"
      class="hover:bg-[var(--bg-secondary)]"
    >
      <td
        v-for="column in columns"
        :key="column.key"
        class="px-4 py-3 text-sm text-[var(--text-primary)]"
      >
        <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
          {{ row[column.key] }}
        </slot>
      </td>
    </tr>
  </tbody>
</table>
```

- [ ] **Step 2: 提交**

```bash
git add src/components/ui/Table.vue
git commit -m "refactor(frontend): use CSS variables for theme support in Table"
```

---

## Task 10: 验证与测试

- [ ] **Step 1: 启动开发服务器验证**

```bash
cd frontend && npm run dev
```

- [ ] **Step 2: 测试主题切换**
1. 打开浏览器访问 http://localhost:5173
2. 点击 Header 中的主题切换按钮（太阳/月亮图标）
3. 验证页面背景、边框、文本颜色在两种主题下都正确显示
4. 刷新页面，验证主题偏好被 localStorage 保留

- [ ] **Step 3: 检查各组件**
- Dashboard 页面背景正常
- 侧边栏导航正常
- Modal 弹窗背景正常
- Table 表格背景/边框正常
- Input/Select 输入框正常

---

## 总结

完成以上 10 个 Task 后，主题功能即可完整使用。