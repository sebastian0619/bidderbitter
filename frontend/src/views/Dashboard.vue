<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>总文件数</span>
              <el-icon><Document /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ stats.totalFiles }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>PDF 文件</span>
              <el-icon><Document /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ stats.pdfFiles }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>图片文件</span>
              <el-icon><Picture /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ stats.imageFiles }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span>标签数</span>
              <el-icon><PriceTag /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ stats.totalTags }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近文件</span>
            </div>
          </template>
          <el-table :data="recentFiles" style="width: 100%">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="file_type" label="类型" width="100" />
            <el-table-column prop="file_size" label="大小" width="120">
              <template #default="{ row }">
                {{ formatSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/files')">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
            <el-button @click="$router.push('/pdf-tools')">
              <el-icon><Document /></el-icon>
              PDF 合并
            </el-button>
            <el-button @click="$router.push('/pdf-tools')">
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
import { Document, Picture, PriceTag, Upload } from '@element-plus/icons-vue'

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

onMounted(async () => {
  try {
    // 获取文件统计
    const filesRes = await fileApi.list({ page_size: 1 })
    stats.value.totalFiles = filesRes.data.total

    // 获取标签
    const tagsRes = await tagApi.list()
    stats.value.totalTags = tagsRes.data.length

    // 获取最近文件
    const recentRes = await fileApi.list({ page_size: 5 })
    recentFiles.value = recentRes.data.files
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-actions .el-button {
  width: 100%;
}
</style>
