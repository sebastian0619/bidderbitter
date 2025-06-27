<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 侧边栏 -->
      <el-aside width="250px" class="app-aside">
        <div class="logo">
          <h2>{{ appName }}</h2>
          <div class="subtitle">{{ appSubtitle }}</div>
        </div>
        
        <el-menu
          :default-active="$route.path"
          class="app-menu"
          router
          :unique-opened="true"
        >
          <template v-if="!isProduction">
            <el-menu-item index="/dashboard">
              <el-icon><House /></el-icon>
              <span>数据管理</span>
            </el-menu-item>
            
            <el-menu-item index="/projects">
              <el-icon><Folder /></el-icon>
              <span>投标项目管理</span>
            </el-menu-item>
            
            <el-menu-item index="/section-manager">
              <el-icon><Connection /></el-icon>
              <span>智能章节管理</span>
            </el-menu-item>
            
            <el-menu-item index="/award-search">
              <el-icon><Search /></el-icon>
              <span>AI自动检索奖项</span>
            </el-menu-item>
            
            
            
            <el-menu-item index="/ai-assistant">
              <el-icon><ChatDotRound /></el-icon>
              <span>AI智能助手</span>
            </el-menu-item>
            
            <el-menu-item index="/templates">
              <el-icon><Files /></el-icon>
              <span>模板管理</span>
            </el-menu-item>
          </template>
          
          <el-menu-item index="/converter">
            <el-icon><Document /></el-icon>
            <span>文件转Word</span>
          </el-menu-item>
          
          <template v-if="!isProduction">
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="app-header">
          <div class="header-content">
            <div class="breadcrumb">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: isProduction ? '/converter' : '/dashboard' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item v-if="currentRoute.meta?.title">
                  {{ currentRoute.meta.title }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            
            <div class="header-actions">
              <el-button @click="toggleDark" circle>🌙</el-button>
              <el-badge :value="processingTasks" class="badge-item">
                <el-button circle>🔔</el-button>
              </el-badge>
            </div>
          </div>
        </el-header>
        
        <!-- 主要内容 -->
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
    
    <!-- 全局加载遮罩 -->
    <el-backtop :right="40" :bottom="40" />
    
    <!-- 全局通知 -->
    <Teleport to="body">
      <div v-if="globalLoading" class="global-loading">
        <el-loading-spinner size="50" />
        <p>{{ loadingText }}</p>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { House, Document, Setting, Folder, Files, Connection, Search, ChatDotRound, User } from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()

const isDark = ref(false)
const toggleDark = () => {
  isDark.value = !isDark.value
}

const currentRoute = computed(() => route)
const processingTasks = ref(0)
const globalLoading = computed(() => appStore.loading)
const loadingText = computed(() => appStore.loadingText)

const appName = ref('投标苦')
const appSubtitle = ref('法律人的投标自救工具')

// 判断是否生产环境
const isProduction = (import.meta.env.VITE_PRODUCTION + '').toLowerCase() === 'true'

// 从API获取应用信息
const loadAppInfo = async () => {
  try {
    const response = await fetch('/api/app-info')
    if (response.ok) {
      const appInfo = await response.json()
      appName.value = appInfo.app_name
      appSubtitle.value = appInfo.app_subtitle
    }
  } catch (error) {
    console.warn('无法获取应用信息，使用默认名称')
  }
}

onMounted(() => {
  // 初始化应用
  appStore.initApp()
  // 加载应用信息
  loadAppInfo()
  // 支持后续动态变更
  window.__setAppName = (v) => appName.value = v
  window.__setAppSubtitle = (v) => appSubtitle.value = v
})
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
}

.app-aside {
  background-color: var(--el-menu-bg-color);
  border-right: 1px solid var(--el-border-color);
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid var(--el-border-color);
  
  h2 {
    margin: 0;
    color: var(--el-text-color-primary);
    font-size: 18px;
    font-weight: 600;
  }
  .subtitle {
    color: #888;
    font-size: 13px;
    margin-top: 4px;
    letter-spacing: 1px;
  }
}

.app-menu {
  border-right: none;
}

.app-header {
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.badge-item {
  margin-top: 6px;
}

.app-main {
  background-color: var(--el-bg-color-page);
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  
  p {
    margin-top: 20px;
    color: white;
    font-size: 16px;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 