<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 侧边栏 -->
      <el-aside width="250px" class="app-aside">
        <div class="logo">
          <h2>投标软件系统</h2>
        </div>
        
        <el-menu
          :default-active="$route.path"
          class="app-menu"
          router
          :unique-opened="true"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          
          <el-sub-menu index="awards">
            <template #title>
              <el-icon><Trophy /></el-icon>
              <span>获奖管理</span>
            </template>
            <el-menu-item index="/awards/list">获奖列表</el-menu-item>
            <el-menu-item index="/awards/upload">上传获奖文档</el-menu-item>
            <el-menu-item index="/awards/manual">手动录入</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="performances">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>业绩管理</span>
            </template>
            <el-menu-item index="/performances/list">业绩列表</el-menu-item>
            <el-menu-item index="/performances/upload">上传业绩文档</el-menu-item>
            <el-menu-item index="/performances/manual">手动录入</el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="generate">
            <template #title>
              <el-icon><DocumentAdd /></el-icon>
              <span>文档生成</span>
            </template>
            <el-menu-item index="/generate/awards">获奖文档</el-menu-item>
            <el-menu-item index="/generate/performances">业绩文档</el-menu-item>
            <el-menu-item index="/generate/combined">综合文档</el-menu-item>
          </el-sub-menu>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="app-header">
          <div class="header-content">
            <div class="breadcrumb">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item v-if="currentRoute.meta?.title">
                  {{ currentRoute.meta.title }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            
            <div class="header-actions">
              <el-button :icon="isDark ? 'Sunny' : 'Moon'" @click="toggleDark" circle />
              <el-badge :value="processingTasks" class="badge-item">
                <el-button icon="Bell" circle />
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
import { useDark, useToggle } from '@vueuse/core'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const appStore = useAppStore()

const isDark = useDark()
const toggleDark = useToggle(isDark)

const currentRoute = computed(() => route)
const processingTasks = ref(0)
const globalLoading = computed(() => appStore.loading)
const loadingText = computed(() => appStore.loadingText)

onMounted(() => {
  // 初始化应用
  appStore.initApp()
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