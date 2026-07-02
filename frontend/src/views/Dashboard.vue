<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div>
        <h1 class="dashboard-title">仪表盘</h1>
        <p class="dashboard-subtitle">欢迎使用 BidderBitter</p>
      </div>
      <el-button type="primary" @click="$router.push('/files')">
        <el-icon><Upload /></el-icon>
        上传文件
      </el-button>
    </div>

    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: var(--primary-50); color: var(--primary-600);">
            <el-icon :size="20"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalFiles }}</div>
            <div class="stat-label">总文件数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fef2f2; color: var(--danger);">
            <el-icon :size="20"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pdfFiles }}</div>
            <div class="stat-label">PDF 文件</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #ecfdf5; color: var(--success);">
            <el-icon :size="20"><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.imageFiles }}</div>
            <div class="stat-label">图片文件</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f5f3ff; color: var(--info);">
            <el-icon :size="20"><PriceTag /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.totalTags }}</div>
            <div class="stat-label">标签数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">最近文件</span>
              <el-button text type="primary" @click="$router.push('/files')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentFiles" style="width: 100%" :show-header="false">
            <el-table-column width="44">
              <template #default="{ row }">
                <div class="file-icon" :class="row.file_type">
                  <el-icon :size="16">
                    <Document v-if="row.file_type === 'pdf'" />
                    <Picture v-else-if="row.file_type === 'image'" />
                    <Files v-else />
                  </el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column>
              <template #default="{ row }">
                <span class="file-name">{{ row.filename }}</span>
              </template>
            </el-table-column>
            <el-table-column width="100">
              <template #default="{ row }">
                <span class="file-meta">{{ formatSize(row.file_size) }}</span>
              </template>
            </el-table-column>
            <el-table-column width="120">
              <template #default="{ row }">
                <span class="file-meta">{{ formatDate(row.created_at) }}</span>
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
            <el-button @click="$router.push('/pdf-tools')">
              <el-icon><DocumentCopy /></el-icon>
              PDF 合并
            </el-button>
            <el-button @click="$router.push('/pdf-tools')">
              <el-icon><Picture /></el-icon>
              图片转 PDF
            </el-button>
            <el-button @click="$router.push('/pdf-tools')">
              <el-icon><Crop /></el-icon>
              PDF 提取图片
            </el-button>
            <el-button @click="$router.push('/tags')">
              <el-icon><PriceTag /></el-icon>
              管理标签
            </el-button>
          </div>
        </el-card>

        <el-card style="margin-top: 16px;">
          <template #header>
            <span class="card-title">使用提示</span>
          </template>
          <div class="tips">
            <div class="tip-item">
              <span class="tip-number">1</span>
              <span>上传投标文件 (PDF/Word/图片)</span>
            </div>
            <div class="tip-item">
              <span class="tip-number">2</span>
              <span>为文件添加标签分类</span>
            </div>
            <div class="tip-item">
              <span class="tip-number">3</span>
              <span>使用 PDF 工具处理文件</span>
            </div>
            <div class="tip-item">
              <span class="tip-number">4</span>
              <span>下载生成的文件</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fileApi, tagApi } from '../services/api'
import {
  Document, Picture, PriceTag, Upload, Files,
  DocumentCopy, Crop
} from '@element-plus/icons-vue'

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
  max-width: 1200px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.dashboard-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--neutral-900);
  letter-spacing: -0.02em;
}

.dashboard-subtitle {
  font-size: 14px;
  color: var(--neutral-500);
  margin-top: 4px;
}

.stat-cards .el-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.stat-cards .el-card:hover {
  transform: translateY(-1px);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--neutral-900);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.stat-label {
  font-size: 13px;
  color: var(--neutral-500);
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--neutral-800);
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
  background: #fef2f2;
  color: var(--danger);
}

.file-icon.image {
  background: #ecfdf5;
  color: var(--success);
}

.file-icon.document {
  background: var(--primary-50);
  color: var(--primary-600);
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--neutral-800);
}

.file-meta {
  font-size: 13px;
  color: var(--neutral-400);
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
  font-weight: 500;
}

.tips {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--neutral-600);
}

.tip-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary-50);
  color: var(--primary-600);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}
</style>
