<template>
  <div class="file-manager">
    <div class="page-header">
      <div>
        <h1 class="page-title">文件管理</h1>
        <p class="page-subtitle">管理您的投标文件</p>
      </div>
      <el-upload
        :action="uploadUrl"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :show-file-list="false"
        multiple
      >
        <el-button type="primary">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
      </el-upload>
    </div>

    <el-card>
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input
          v-model="search"
          placeholder="搜索文件名..."
          style="width: 280px;"
          clearable
          @clear="loadFiles"
          @keyup.enter="loadFiles"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="fileType" placeholder="文件类型" clearable @change="loadFiles" style="width: 140px;">
          <el-option label="全部类型" value="" />
          <el-option label="PDF" value="pdf" />
          <el-option label="图片" value="image" />
          <el-option label="文档" value="document" />
        </el-select>
        <el-select v-model="category" placeholder="分类" clearable @change="loadFiles" style="width: 140px;">
          <el-option label="全部分类" value="" />
          <el-option label="合同" value="合同" />
          <el-option label="证书" value="证书" />
          <el-option label="业绩" value="业绩" />
          <el-option label="生成" value="generated" />
        </el-select>
        <div class="filter-right">
          <el-button-group>
            <el-button :type="viewMode === 'table' ? 'primary' : ''" @click="viewMode = 'table'" size="small">
              <el-icon><List /></el-icon>
            </el-button>
            <el-button :type="viewMode === 'grid' ? 'primary' : ''" @click="viewMode = 'grid'" size="small">
              <el-icon><Grid /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </div>

      <!-- 表格视图 -->
      <el-table v-if="viewMode === 'table'" :data="files" style="width: 100%; margin-top: 16px;">
        <el-table-column width="44">
          <template #default="{ row }">
            <div class="file-icon-sm" :class="row.file_type">
              <el-icon :size="16">
                <Document v-if="row.file_type === 'pdf'" />
                <Picture v-else-if="row.file_type === 'image'" />
                <Files v-else />
              </el-icon>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="filename" label="文件名" min-width="250" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="previewFile(row)" :underline="false">
              {{ row.filename }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.file_type)" size="small" effect="light">
              {{ row.file_type?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100" sortable>
          <template #default="{ row }">
            <span class="text-muted">{{ formatSize(row.file_size) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag.id"
              :color="tag.color"
              size="small"
              class="tag-item"
              effect="dark"
            >
              {{ tag.name }}
            </el-tag>
            <span v-if="!row.tags?.length" class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="120" sortable>
          <template #default="{ row }">
            <span class="text-muted">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="downloadFile(row)">
                <el-icon><Download /></el-icon>
              </el-button>
              <el-button size="small" @click="editFile(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click="deleteFile(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 网格视图 -->
      <div v-else class="grid-view">
        <div
          v-for="file in files"
          :key="file.id"
          class="grid-item"
          @click="previewFile(file)"
        >
          <div class="grid-item-icon" :class="file.file_type">
            <el-icon :size="32">
              <Document v-if="file.file_type === 'pdf'" />
              <Picture v-else-if="file.file_type === 'image'" />
              <Files v-else />
            </el-icon>
          </div>
          <div class="grid-item-info">
            <div class="grid-item-name" :title="file.filename">{{ file.filename }}</div>
            <div class="grid-item-meta">{{ formatSize(file.file_size) }}</div>
          </div>
          <div class="grid-item-actions">
            <el-button size="small" circle @click.stop="downloadFile(file)">
              <el-icon><Download /></el-icon>
            </el-button>
            <el-button size="small" circle type="danger" @click.stop="deleteFile(file)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadFiles"
          @current-change="loadFiles"
        />
      </div>
    </el-card>

    <!-- 文件详情对话框 -->
    <el-dialog v-model="showDetail" title="文件详情" width="500px">
      <div v-if="selectedFile" class="file-detail">
        <div class="file-preview">
          <div class="file-icon-lg" :class="selectedFile.file_type">
            <el-icon :size="48">
              <Document v-if="selectedFile.file_type === 'pdf'" />
              <Picture v-else-if="selectedFile.file_type === 'image'" />
              <Files v-else />
            </el-icon>
          </div>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="文件名">{{ selectedFile.filename }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedFile.file_type?.toUpperCase() }}</el-descriptions-item>
          <el-descriptions-item label="大小">{{ formatSize(selectedFile.file_size) }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ selectedFile.category || '-' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedFile.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="标签">
            <el-tag
              v-for="tag in selectedFile.tags"
              :key="tag.id"
              :color="tag.color"
              size="small"
              class="tag-item"
              effect="dark"
            >
              {{ tag.name }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">{{ selectedFile.created_at }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="showDetail = false">关闭</el-button>
        <el-button type="primary" @click="downloadFile(selectedFile)">下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fileApi } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, Search, Document, Picture, Files, Download,
  Edit, Delete, List, Grid
} from '@element-plus/icons-vue'

const files = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(24)
const search = ref('')
const fileType = ref('')
const category = ref('')
const viewMode = ref('table')
const showDetail = ref(false)
const selectedFile = ref(null)

const uploadUrl = '/api/files'

const getTypeTag = (type) => {
  const map = { pdf: 'danger', image: 'success', document: 'info' }
  return map[type] || ''
}

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

const loadFiles = async () => {
  try {
    const res = await fileApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      search: search.value || undefined,
      file_type: fileType.value || undefined,
      category: category.value || undefined
    })
    files.value = res.data.files
    total.value = res.data.total
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  }
}

const previewFile = (file) => {
  selectedFile.value = file
  showDetail.value = true
}

const downloadFile = async (file) => {
  try {
    const res = await fileApi.download(file.id)
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const editFile = (file) => {
  selectedFile.value = file
  showDetail.value = true
}

const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确定删除 "${file.filename}"？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await fileApi.delete(file.id)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleUploadSuccess = (response) => {
  ElMessage.success('上传成功')
  loadFiles()
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

onMounted(loadFiles)
</script>

<style scoped>
.file-manager {
  max-width: 1200px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--neutral-900);
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 14px;
  color: var(--neutral-500);
  margin-top: 4px;
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
  background: #fef2f2;
  color: var(--danger);
}

.file-icon-sm.image {
  background: #ecfdf5;
  color: var(--success);
}

.file-icon-sm.document {
  background: var(--primary-50);
  color: var(--primary-600);
}

.tag-item {
  margin-right: 4px;
  margin-bottom: 4px;
}

.text-muted {
  color: var(--neutral-400);
  font-size: 13px;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.grid-item {
  background: var(--header-bg);
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.grid-item:hover {
  border-color: var(--primary-300);
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
  background: #fef2f2;
  color: var(--danger);
}

.grid-item-icon.image {
  background: #ecfdf5;
  color: var(--success);
}

.grid-item-icon.document {
  background: var(--primary-50);
  color: var(--primary-600);
}

.grid-item-info {
  text-align: center;
}

.grid-item-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--neutral-800);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.grid-item-meta {
  font-size: 12px;
  color: var(--neutral-400);
  margin-top: 4px;
}

.grid-item-actions {
  position: absolute;
  bottom: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.grid-item:hover .grid-item-actions {
  opacity: 1;
}

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.file-detail-dialog .file-preview {
  text-align: center;
  margin-bottom: 24px;
}

.file-icon-lg {
  width: 100px;
  height: 100px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.file-icon-lg.pdf {
  background: #fef2f2;
  color: var(--danger);
}

.file-icon-lg.image {
  background: #ecfdf5;
  color: var(--success);
}

.file-icon-lg.document {
  background: var(--primary-50);
  color: var(--primary-600);
}
</style>
