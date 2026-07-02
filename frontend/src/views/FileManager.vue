<template>
  <div class="file-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>文件管理</span>
          <el-upload
            :action="uploadUrl"
            :on-success="handleUploadSuccess"
            :show-file-list="false"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              上传文件
            </el-button>
          </el-upload>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input
          v-model="search"
          placeholder="搜索文件名..."
          style="width: 200px;"
          clearable
          @clear="loadFiles"
          @keyup.enter="loadFiles"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="fileType" placeholder="文件类型" clearable @change="loadFiles">
          <el-option label="全部" value="" />
          <el-option label="PDF" value="pdf" />
          <el-option label="图片" value="image" />
          <el-option label="文档" value="document" />
        </el-select>
        <el-select v-model="category" placeholder="分类" clearable @change="loadFiles">
          <el-option label="全部" value="" />
          <el-option label="合同" value="合同" />
          <el-option label="证书" value="证书" />
          <el-option label="业绩" value="业绩" />
          <el-option label="生成" value="generated" />
        </el-select>
      </div>

      <!-- 文件列表 -->
      <el-table :data="files" style="width: 100%; margin-top: 15px;">
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="previewFile(row)">{{ row.filename }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.file_type)">{{ row.file_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="tag in row.tags"
              :key="tag.id"
              :color="tag.color"
              style="margin-right: 5px; color: #fff;"
              size="small"
            >
              {{ tag.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="downloadFile(row)">下载</el-button>
            <el-button size="small" type="danger" @click="deleteFile(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadFiles"
          @current-change="loadFiles"
        />
      </div>
    </el-card>

    <!-- 文件详情对话框 -->
    <el-dialog v-model="showDetail" title="文件详情" width="500px">
      <div v-if="selectedFile">
        <p><strong>文件名:</strong> {{ selectedFile.filename }}</p>
        <p><strong>类型:</strong> {{ selectedFile.file_type }}</p>
        <p><strong>大小:</strong> {{ formatSize(selectedFile.file_size) }}</p>
        <p><strong>分类:</strong> {{ selectedFile.category || '-' }}</p>
        <p><strong>描述:</strong> {{ selectedFile.description || '-' }}</p>
        <p><strong>标签:</strong></p>
        <div style="margin-top: 10px;">
          <el-tag
            v-for="tag in selectedFile.tags"
            :key="tag.id"
            :color="tag.color"
            style="margin-right: 5px; color: #fff;"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fileApi } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Search } from '@element-plus/icons-vue'

const files = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const fileType = ref('')
const category = ref('')
const showDetail = ref(false)
const selectedFile = ref(null)

const uploadUrl = '/api/files'

const getTypeTag = (type) => {
  const map = {
    pdf: 'danger',
    image: 'success',
    document: 'info'
  }
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
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm('确定删除该文件？', '提示', {
      type: 'warning'
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

const handleUploadSuccess = () => {
  ElMessage.success('上传成功')
  loadFiles()
}

onMounted(loadFiles)
</script>

<style scoped>
.file-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
