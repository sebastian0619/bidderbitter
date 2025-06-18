<template>
  <div class="file-converter">
    <el-card class="converter-card">
      <template #header>
        <div class="card-header">
          <h2>
            <el-icon><Document /></el-icon>
            文件转Word工具
          </h2>
          <p>支持PDF转图片Word、图片直接插入Word</p>
        </div>
      </template>

      <!-- 文件上传区域 -->
      <div class="upload-section">
        <el-form :model="form" label-width="120px">
          <el-form-item label="文档标题">
            <el-input 
              v-model="form.documentTitle" 
              placeholder="请输入生成的Word文档标题"
              style="width: 400px"
            />
          </el-form-item>
        </el-form>

        <el-upload
          ref="uploadRef"
          v-model:file-list="fileList"
          class="upload-demo"
          drag
          multiple
          :auto-upload="false"
          :accept="acceptedTypes"
          :limit="20"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击选择文件</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持PDF、JPG、PNG、BMP、GIF、TIFF格式，最多20个文件
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 文件列表 -->
      <div v-if="fileList.length > 0" class="file-list-section">
        <h3>已选择文件 ({{ fileList.length }})</h3>
        <el-table :data="fileList" style="width: 100%">
          <el-table-column prop="name" label="文件名" />
          <el-table-column label="大小" width="120">
            <template #default="{ row }">
              {{ formatFileSize(row.size) }}
            </template>
          </el-table-column>
          <el-table-column label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getFileTypeTag(row.name)">
                {{ getFileType(row.name) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ $index }">
              <el-button 
                type="danger" 
                size="small" 
                @click="removeFile($index)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 转换按钮 -->
      <div class="action-section">
        <el-button 
          type="primary" 
          size="large"
          :loading="converting"
          :disabled="fileList.length === 0"
          @click="convertFiles"
        >
          <el-icon><Document /></el-icon>
          开始转换为Word
        </el-button>
      </div>

      <!-- 转换结果 -->
      <div v-if="convertResult" class="result-section">
        <el-alert
          :title="convertResult.success ? '转换成功' : '转换失败'"
          :type="convertResult.success ? 'success' : 'error'"
          :description="convertResult.message"
          show-icon
        />
        
        <div v-if="convertResult.success" class="download-section">
          <el-card>
            <h4>转换结果</h4>
            <p><strong>输出文件:</strong> {{ convertResult.output_file }}</p>
            <div class="processed-files">
              <h5>处理的文件:</h5>
              <ul>
                <li v-for="file in convertResult.processed_files" :key="file">
                  {{ file }}
                </li>
              </ul>
            </div>
            <el-button 
              type="success" 
              size="large"
              @click="downloadFile"
            >
              <el-icon><Download /></el-icon>
              下载Word文档
            </el-button>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, UploadFilled, Download } from '@element-plus/icons-vue'
import api from '@/services/api'

// 响应式数据
const uploadRef = ref()
const fileList = ref([])
const converting = ref(false)
const convertResult = ref(null)

const form = reactive({
  documentTitle: '转换文档'
})

// 接受的文件类型
const acceptedTypes = '.pdf,.jpg,.jpeg,.png,.bmp,.gif,.tiff'

// 处理文件变化
const handleFileChange = (file, files) => {
  // 验证文件类型
  const allowedTypes = ['pdf', 'jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff']
  const fileExt = file.name.split('.').pop().toLowerCase()
  
  if (!allowedTypes.includes(fileExt)) {
    ElMessage.warning(`不支持的文件格式: ${file.name}`)
    const index = files.indexOf(file)
    if (index > -1) {
      files.splice(index, 1)
    }
    return false
  }
  
  // 验证文件大小 (50MB)
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.warning(`文件过大: ${file.name}，请选择小于50MB的文件`)
    const index = files.indexOf(file)
    if (index > -1) {
      files.splice(index, 1)
    }
    return false
  }
}

// 处理文件数量超限
const handleExceed = (files, fileList) => {
  ElMessage.warning('最多只能选择20个文件')
}

// 移除文件
const removeFile = (index) => {
  fileList.value.splice(index, 1)
}

// 格式化文件大小
const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

// 获取文件类型
const getFileType = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'PDF'
  if (['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'].includes(ext)) return '图片'
  return '未知'
}

// 获取文件类型标签样式
const getFileTypeTag = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'danger'
  if (['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'].includes(ext)) return 'success'
  return 'info'
}

// 转换文件
const convertFiles = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择要转换的文件')
    return
  }

  converting.value = true
  convertResult.value = null

  try {
    const formData = new FormData()
    
    // 添加文件
    fileList.value.forEach(file => {
      formData.append('files', file.raw)
    })
    
    // 添加文档标题
    formData.append('document_title', form.documentTitle)

    const response = await api.post('/convert-to-word', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    convertResult.value = response.data
    
    if (response.data.success) {
      ElMessage.success('文件转换成功！')
    } else {
      ElMessage.error('转换失败: ' + response.data.message)
    }

  } catch (error) {
    console.error('转换错误:', error)
    ElMessage.error('转换失败: ' + (error.response?.data?.message || error.message))
    convertResult.value = {
      success: false,
      message: '转换过程中发生错误'
    }
  } finally {
    converting.value = false
  }
}

// 下载文件
const downloadFile = () => {
  if (!convertResult.value?.download_url) return
  
  const downloadUrl = `${import.meta.env.VITE_API_URL}${convertResult.value.download_url}`
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = convertResult.value.output_file
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('开始下载文件')
}

// 重置表单
const resetForm = () => {
  fileList.value = []
  convertResult.value = null
  form.documentTitle = '转换文档'
}
</script>

<style scoped>
.file-converter {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.converter-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  color: #303133;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.card-header p {
  color: #909399;
  margin: 0;
}

.upload-section {
  margin: 30px 0;
}

.upload-demo {
  margin-top: 20px;
}

.file-list-section {
  margin: 30px 0;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.file-list-section h3 {
  margin: 0 0 20px 0;
  color: #303133;
}

.action-section {
  text-align: center;
  margin: 30px 0;
}

.result-section {
  margin-top: 30px;
}

.download-section {
  margin-top: 20px;
}

.processed-files ul {
  margin: 10px 0;
  padding-left: 20px;
}

.processed-files li {
  margin: 5px 0;
  color: #606266;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
}

:deep(.el-icon--upload) {
  font-size: 48px;
  color: #c0c4cc;
}

:deep(.el-upload__text) {
  font-size: 16px;
  color: #606266;
}

:deep(.el-upload__tip) {
  color: #909399;
  font-size: 14px;
}
</style> 