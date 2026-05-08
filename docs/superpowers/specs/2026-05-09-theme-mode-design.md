# 主题模式设计文档

**日期**: 2026/05/09
**状态**: 设计中

## 背景与目标

为 claw-platform 添加白色/黑色两种主题模式，用户可在导航栏随时切换，主题偏好保存在浏览器 localStorage 中。

## 设计方案

### 颜色变量定义

在 `src/assets/main.css` 中定义两套 CSS 变量：

**白色主题 (默认)**
```css
[data-theme="light"] {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --bg-tertiary: #e5e5e5;
  --border-color: #d4d4d4;
  --text-primary: #171717;
  --text-secondary: #525252;
  --text-muted: #a3a3a3;
}
```

**黑色主题**
```css
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

品牌色 (primary/success/danger) 在两种主题下保持不变。

### 切换机制

在 `AppHeader.vue` 中添加主题切换按钮：
- 图标按钮（太阳/月亮图标）
- 点击时切换 `data-theme` 属性到 `<html>` 元素
- 同时写入 localStorage

### 主题初始化

`main.ts` 入口逻辑：
1. 从 localStorage 读取 `theme` 值
2. 如存在则应用到 `<html>` 的 `data-theme`
3. 如不存在则默认白色主题

### 组件适配

需要修改的文件：
- `src/assets/main.css` — 添加 CSS 变量定义
- `src/components/layout/AppHeader.vue` — 添加切换按钮
- `src/components/layout/AppSidebar.vue` — 适配深色背景
- 各页面和组件 — 使用 CSS 变量而非硬编码颜色

适配方式：在各组件的 `<style>` 中使用 `var(--bg-primary)` 等变量。

## 实现步骤

1. 修改 `src/assets/main.css` — 定义 `[data-theme="light"]` 和 `[data-theme="dark"]` 两套 CSS 变量
2. 修改 `src/main.ts` — 入口读取 localStorage 并设置 `data-theme` 到 `<html>`
3. 修改 `src/components/layout/AppHeader.vue` — 添加太阳/月亮图标切换按钮，点击时切换主题并存入 localStorage
4. 修改 `src/components/layout/AppSidebar.vue` — 将硬编码背景色改为 CSS 变量
5. 修改其他有硬编码颜色的组件（Card、Modal、Input 等）— 改为使用 CSS 变量