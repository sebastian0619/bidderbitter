<template>
  <el-container class="app-container">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="app-aside">
      <div class="logo" @click="isCollapse = !isCollapse">
        <div class="logo-mark">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="6" fill="#2563eb"/>
            <path d="M8 8h12v2H8V8zm0 4h12v2H8v-2zm0 4h8v2H8v-2z" fill="white"/>
          </svg>
        </div>
        <div v-if="!isCollapse" class="logo-text">
          <span class="logo-title">BidderBitter</span>
          <span class="logo-subtitle">投标文件工具</span>
        </div>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        class="el-menu-vertical"
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <template #title>投标项目</template>
        </el-menu-item>
        <el-menu-item index="/files">
          <el-icon><FolderOpened /></el-icon>
          <template #title>文件管理</template>
        </el-menu-item>
        <el-menu-item index="/pdf-tools">
          <el-icon><Document /></el-icon>
          <template #title>PDF 工具</template>
        </el-menu-item>
        <el-menu-item index="/tags">
          <el-icon><PriceTag /></el-icon>
          <template #title>标签管理</template>
        </el-menu-item>
      </el-menu>
      <div v-if="!isCollapse" class="sidebar-footer">
        <div class="sidebar-footer-text">
          <span>v0.1.0</span>
        </div>
      </div>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip content="GitHub" placement="bottom">
            <el-button :icon="Link" circle @click="openGithub" />
          </el-tooltip>
          <el-tooltip content="API 文档" placement="bottom">
            <el-button :icon="Document" circle @click="openApiDocs" />
          </el-tooltip>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Odometer, FolderOpened, Document, PriceTag, Link, Folder } from '@element-plus/icons-vue'

const route = useRoute()
const isCollapse = ref(false)
const activeMenu = computed(() => {
  // 处理项目详情页面
  if (route.path.startsWith('/projects/')) {
    return '/projects'
  }
  return route.path
})

const currentPageTitle = computed(() => {
  const map = {
    '/': '仪表盘',
    '/projects': '投标项目',
    '/files': '文件管理',
    '/pdf-tools': 'PDF 工具',
    '/tags': '标签管理'
  }
  if (route.path.startsWith('/projects/')) {
    return '项目详情'
  }
  return map[route.path] || ''
})

const openGithub = () => {
  window.open('https://github.com/sebastian0619/bidderbitter', '_blank')
}

const openApiDocs = () => {
  window.open('http://localhost:8000/docs', '_blank')
}
</script>

<style>
:root {
  /* Primary palette - Professional blue */
  --primary-50: #eff6ff;
  --primary-100: #dbeafe;
  --primary-200: #bfdbfe;
  --primary-300: #93c5fd;
  --primary-400: #60a5fa;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  --primary-700: #1d4ed8;
  --primary-800: #1e40af;
  --primary-900: #1e3a8a;

  /* Neutral palette */
  --neutral-50: #f8fafc;
  --neutral-100: #f1f5f9;
  --neutral-200: #e2e8f0;
  --neutral-300: #cbd5e1;
  --neutral-400: #94a3b8;
  --neutral-500: #64748b;
  --neutral-600: #475569;
  --neutral-700: #334155;
  --neutral-800: #1e293b;
  --neutral-900: #0f172a;

  /* Semantic colors */
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --info: #6366f1;

  /* Layout */
  --sidebar-bg: #ffffff;
  --sidebar-border: var(--neutral-200);
  --sidebar-hover: var(--neutral-50);
  --sidebar-active: var(--primary-50);
  --sidebar-active-border: var(--primary-600);
  --header-bg: #ffffff;
  --header-border: var(--neutral-200);
  --main-bg: var(--neutral-50);

  /* Shadows */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);

  /* Border radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--neutral-800);
  background: var(--main-bg);
}

.app-container {
  height: 100vh;
}

.app-aside {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.logo-mark {
  flex-shrink: 0;
}

.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.logo-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--neutral-900);
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.logo-subtitle {
  font-size: 11px;
  color: var(--neutral-400);
  font-weight: 500;
  letter-spacing: 0.02em;
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
  padding: 8px;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 240px;
}

.el-menu-item {
  border-radius: var(--radius-md);
  margin-bottom: 2px;
  height: 40px;
  line-height: 40px;
  font-weight: 500;
  font-size: 14px;
  color: var(--neutral-600);
  transition: all 0.15s ease;
}

.el-menu-item:hover {
  background: var(--sidebar-hover) !important;
  color: var(--neutral-800);
}

.el-menu-item.is-active {
  background: var(--sidebar-active) !important;
  color: var(--primary-700) !important;
  font-weight: 600;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.sidebar-footer-text {
  font-size: 11px;
  color: var(--neutral-400);
  text-align: center;
}

.app-header {
  background: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 8px;
}

.app-main {
  background: var(--main-bg);
  padding: 24px;
  overflow-y: auto;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Element Plus overrides */
.el-card {
  background: var(--header-bg);
  border: 1px solid var(--sidebar-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
  transition: box-shadow 0.2s ease;
}

.el-card:hover {
  box-shadow: var(--shadow-sm);
}

.el-button--primary {
  --el-button-bg-color: var(--primary-600);
  --el-button-border-color: var(--primary-600);
  --el-button-hover-bg-color: var(--primary-700);
  --el-button-hover-border-color: var(--primary-700);
  font-weight: 500;
}

.el-table {
  --el-table-border-color: var(--neutral-200);
  --el-table-header-bg-color: var(--neutral-50);
  --el-table-header-text-color: var(--neutral-600);
  font-size: 14px;
}

.el-tag {
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.el-breadcrumb {
  font-size: 14px;
}

.el-breadcrumb__inner {
  color: var(--neutral-500) !important;
}

.el-breadcrumb__inner.is-link {
  color: var(--neutral-400) !important;
}

.el-breadcrumb__inner.is-link:hover {
  color: var(--primary-600) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--neutral-300);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--neutral-400);
}
</style>
