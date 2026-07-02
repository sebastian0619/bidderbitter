# Frontend UI Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the frontend UI with a minimalist modern style similar to Notion/Linear

**Architecture:** Update Vue components with new styling, improve visual hierarchy, add better spacing and typography

**Tech Stack:** Vue 3, Element Plus, CSS3

## Global Constraints

- Maintain all existing functionality
- Use Element Plus components where possible
- Keep the same API integration
- Ensure responsive design

---

### Task 1: Update Global Styles

**Covers:** Visual style improvement

**Files:**
- Modify: `frontend/src/App.vue`

**Interfaces:**
- Produces: Updated global CSS variables and styles

- [ ] **Step 1: Update App.vue styles**

```vue
<style>
:root {
  --primary-color: #3b82f6;
  --primary-hover: #2563eb;
  --bg-color: #f8fafc;
  --sidebar-bg: #ffffff;
  --sidebar-border: #e2e8f0;
  --card-bg: #ffffff;
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  background: var(--bg-color);
  color: var(--text-primary);
}

.app-container {
  height: 100vh;
}

.app-aside {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  transition: width 0.3s;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid var(--sidebar-border);
}

.logo h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.el-menu-vertical {
  border-right: none;
  padding: 8px;
}

.el-menu-item {
  border-radius: var(--radius-md);
  margin-bottom: 4px;
  height: 40px;
  line-height: 40px;
}

.el-menu-item:hover {
  background: var(--bg-color) !important;
}

.el-menu-item.is-active {
  background: rgba(59, 130, 246, 0.1) !important;
  color: var(--primary-color) !important;
}

.app-header {
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
}

.app-main {
  background: var(--bg-color);
  padding: 24px;
  overflow-y: auto;
}

.el-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.el-button--primary {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.el-button--primary:hover {
  background: var(--primary-hover);
  border-color: var(--primary-hover);
}
</style>
```

- [ ] **Step 2: Verify the changes**

Run: `cd /workingfile/0.Archive/dev-projects/bidtool/frontend && npm run dev`
Expected: Frontend starts without errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.vue
git commit -m "style: update global styles with minimalist design"
```

---

### Task 2: Update Dashboard Component

**Covers:** Dashboard visual improvement

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

**Interfaces:**
- Consumes: Updated global CSS variables
- Produces: Improved dashboard layout and styling

- [ ] **Step 1: Update Dashboard.vue template and styles**

```vue
<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>仪表盘</h1>
      <p>欢迎使用 BidderBitter</p>
    </div>

    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(59, 130, 246, 0.1); color: #3b82f6;">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalFiles }}</div>
            <div class="stat-label">总文件数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(239, 68, 68, 0.1); color: #ef4444;">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pdfFiles }}</div>
            <div class="stat-label">PDF 文件</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(16, 185, 129, 0.1); color: #10b981;">
            <el-icon :size="24"><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.imageFiles }}</div>
            <div class="stat-label">图片文件</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: rgba(245, 158, 11, 0.1); color: #f59e0b;">
            <el-icon :size="24"><PriceTag /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalTags }}</div>
            <div class="stat-label">标签数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 24px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">最近文件</span>
              <el-button text type="primary" @click="$router.push('/files')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentFiles" style="width: 100%" :show-header="false">
            <el-table-column width="50">
              <template #default="{ row }">
                <div class="file-icon" :class="row.file_type">
                  <el-icon :size="18">
                    <Document v-if="row.file_type === 'pdf'" />
                    <Picture v-else-if="row.file_type === 'image'" />
                    <Files v-else />
                  </el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="filename" />
            <el-table-column width="100">
              <template #default="{ row }">
                <span class="file-size">{{ formatSize(row.file_size) }}</span>
              </template>
            </el-table-column>
            <el-table-column width="120">
              <template #default="{ row }">
                <span class="file-time">{{ formatDate(row.created_at) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span class="card-title">快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" size="large" @click="$router.push('/files')">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
            <el-button size="large" @click="$router.push('/pdf-tools')">
              <el-icon><DocumentCopy /></el-icon>
              PDF 合并
            </el-button>
            <el-button size="large" @click="$router.push('/pdf-tools')">
              <el-icon><Picture /></el-icon>
              图片转 PDF
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fileApi, tagApi } from '../services/api'
import { Document, Picture, PriceTag, Upload, Files, DocumentCopy } from '@element-plus/icons-vue'

const stats = ref({
  totalFiles: 0,
  pdfFiles: 0,
  imageFiles: 0,
  totalTags: 0
})

const recentFiles = ref([])

const formatSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const filesRes = await fileApi.list({ page_size: 5 })
    stats.value.totalFiles = filesRes.data.total
    recentFiles.value = filesRes.data.files

    const tagsRes = await tagApi.list()
    stats.value.totalTags = tagsRes.data.length
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
}

.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
}

.dashboard-header p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.stat-cards .el-card {
  cursor: pointer;
  transition: all 0.2s;
}

.stat-cards .el-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.file-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-icon.pdf {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.file-icon.image {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.file-icon.document {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.file-size,
.file-time {
  font-size: 13px;
  color: var(--text-muted);
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
}
</style>
```

- [ ] **Step 2: Verify the changes**

Run: `cd /workingfile/0.Archive/dev-projects/bidtool/frontend && npm run dev`
Expected: Frontend starts without errors, dashboard displays correctly

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "style: update dashboard with minimalist design"
```

---

### Task 3: Update FileManager Component

**Covers:** File manager visual improvement

**Files:**
- Modify: `frontend/src/views/FileManager.vue`

**Interfaces:**
- Consumes: Updated global CSS variables
- Produces: Improved file manager layout and styling

- [ ] **Step 1: Update FileManager.vue styles**

The FileManager component already has good structure. Update the styles to match the new design language:

```vue
<style scoped>
.file-manager {
  max-width: 1400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-right {
  margin-left: auto;
}

.file-icon-sm {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-icon-sm.pdf {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.file-icon-sm.image {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.file-icon-sm.document {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.tag-item {
  margin-right: 4px;
  margin-bottom: 4px;
}

.text-secondary {
  color: var(--text-muted);
  font-size: 13px;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.grid-item {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.grid-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
}

.grid-item-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.grid-item-icon.pdf {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.grid-item-icon.image {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.grid-item-icon.document {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.grid-item-info {
  text-align: center;
}

.grid-item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grid-item-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.grid-item-actions {
  position: absolute;
  bottom: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.grid-item:hover .grid-item-actions {
  opacity: 1;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
```

- [ ] **Step 2: Verify the changes**

Run: `cd /workingfile/0.Archive/dev-projects/bidtool/frontend && npm run dev`
Expected: Frontend starts without errors, file manager displays correctly

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/FileManager.vue
git commit -m "style: update file manager with minimalist design"
```

---

### Task 4: Update PDFTools Component

**Covers:** PDF tools visual improvement

**Files:**
- Modify: `frontend/src/views/PDFTools.vue`

**Interfaces:**
- Consumes: Updated global CSS variables
- Produces: Improved PDF tools layout and styling

- [ ] **Step 1: Update PDFTools.vue styles**

```vue
<style scoped>
.pdf-tools {
  max-width: 1400px;
}

.tool-card {
  transition: all 0.2s;
}

.tool-card:hover {
  box-shadow: var(--shadow-md);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tool-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.tool-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.tool-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 2px;
}

.tool-content {
  display: flex;
  flex-direction: column;
}

.extract-content {
  display: flex;
  gap: 12px;
  align-items: center;
}

.extract-result {
  margin-top: 16px;
}
</style>
```

- [ ] **Step 2: Verify the changes**

Run: `cd /workingfile/0.Archive/dev-projects/bidtool/frontend && npm run dev`
Expected: Frontend starts without errors, PDF tools displays correctly

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/PDFTools.vue
git commit -m "style: update PDF tools with minimalist design"
```

---

### Task 5: Update TagManager Component

**Covers:** Tag manager visual improvement

**Files:**
- Modify: `frontend/src/views/TagManager.vue`

**Interfaces:**
- Consumes: Updated global CSS variables
- Produces: Improved tag manager layout and styling

- [ ] **Step 1: Update TagManager.vue styles**

```vue
<style scoped>
.tag-manager {
  max-width: 1400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.tag-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  transition: all 0.2s;
}

.tag-card:hover {
  box-shadow: var(--shadow-md);
}

.tag-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.tag-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
}

.tag-card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.tag-card:hover .tag-card-actions {
  opacity: 1;
}

.color-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preset-colors {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s;
}

.preset-color:hover {
  transform: scale(1.1);
}
</style>
```

- [ ] **Step 2: Verify the changes**

Run: `cd /workingfile/0.Archive/dev-projects/bidtool/frontend && npm run dev`
Expected: Frontend starts without errors, tag manager displays correctly

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TagManager.vue
git commit -m "style: update tag manager with minimalist design"
```

---

## Summary

This plan updates the frontend UI with a minimalist modern style:
- Updated global CSS variables
- Improved card styling with softer shadows and rounded corners
- Better typography and spacing
- Consistent color scheme using CSS variables
- Maintained all existing functionality
