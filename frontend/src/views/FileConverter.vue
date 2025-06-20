<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Document /></el-icon>
        文件转Word工具
      </h1>
      <p class="page-description">支持PDF转图片Word、图片直接插入Word</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧上传区域 -->
      <el-col :md="12">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">选择文件</h3>
          </div>
          <div class="card-body">
            <el-form :model="form" label-width="100px" class="mb-3">
              <el-form-item label="文档标题">
                <el-input 
                  v-model="form.documentTitle" 
                  placeholder="请输入生成的Word文档标题"
                />
              </el-form-item>
            </el-form>

            <FileUpload
              ref="fileUploadRef"
              :allowed-types="['pdf', 'image']"
              :multiple="true"
              :max-size="50 * 1024 * 1024"
              accept=".pdf,.jpg,.jpeg,.png,.bmp,.gif,.tiff"
              @upload="handleFilesSelected"
              @change="handleFileChange"
            />

            <div class="action-section mt-3">
              <el-button 
                type="primary" 
                size="large"
                :loading="converting"
                :disabled="selectedFiles.length === 0"
                @click="convertFiles"
                style="width: 100%"
              >
                <el-icon><DocumentAdd /></el-icon>
                开始转换为Word文档
              </el-button>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧结果区域 -->
      <el-col :md="12">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">转换结果</h3>
          </div>
          <div class="card-body">
            <!-- 转换进度 -->
            <div v-if="converting" class="converting-status">
              <el-progress 
                :percentage="convertProgress" 
                status="active"
                :show-text="false"
              />
              <p class="mt-2 text-center">正在转换文件，请稍候...</p>
            </div>

            <!-- 转换成功 -->
            <div v-else-if="convertResult?.success" class="result-success">
              <el-result
                icon="success"
                title="转换成功"
                :sub-title="`成功处理 ${convertResult.processed_files?.length || 0} 个文件`"
              >
                <template #extra>
                  <div class="result-details">
                    <p><strong>输出文件:</strong> {{ convertResult.output_file }}</p>
                    <div v-if="convertResult.processed_files?.length" class="processed-files">
                      <h5>处理的文件:</h5>
                      <el-tag
                        v-for="file in convertResult.processed_files"
                        :key="file"
                        size="small"
                        class="mr-1 mb-1"
                      >
                        {{ file }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <el-button 
                    type="success" 
                    size="large"
                    @click="downloadFile"
                  >
                    <el-icon><Download /></el-icon>
                    下载Word文档
                  </el-button>
                </template>
              </el-result>
            </div>

            <!-- 转换失败 -->
            <div v-else-if="convertResult?.success === false" class="result-error">
              <el-result
                icon="error"
                title="转换失败"
                :sub-title="convertResult.message"
              >
                <template #extra>
                  <el-button type="primary" @click="resetConverter">
                    重新开始
                  </el-button>
                </template>
              </el-result>
            </div>

            <!-- 初始状态 -->
            <div v-else class="initial-state">
              <el-empty description="请先选择要转换的文件">
                <template #image>
                  <el-icon size="80" color="var(--el-color-info)">
                    <Document />
                  </el-icon>
                </template>
              </el-empty>
              
              <div class="tips">
                <h4>使用说明</h4>
                <ul>
                  <li>支持PDF、JPG、PNG、BMP、GIF、TIFF格式</li>
                  <li>单个文件最大50MB，最多选择20个文件</li>
                  <li>PDF文件将转换为图片后插入Word</li>
                  <li>图片文件将直接插入Word文档</li>
                  <li>文件将按照上传顺序排列</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 转换历史 -->
    <div class="card mt-4">
      <div class="card-header">
        <h3 class="card-title">
          <el-icon><Clock /></el-icon>
          转换历史
        </h3>
        <el-button text @click="loadHistory">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      <div class="card-body">
        <el-table :data="conversionHistory" style="width: 100%">
          <el-table-column prop="document_title" label="文档标题" min-width="200" />
          <el-table-column prop="file_count" label="文件数量" width="100" />
          <el-table-column prop="created_at" label="转换时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'success'"
                type="primary"
                size="small"
                text
                @click="downloadHistoryFile(row)"
              >
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-empty v-if="conversionHistory.length === 0" description="暂无转换记录" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, DocumentAdd, Download, Clock, Refresh } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'
import FileUpload from '@/components/FileUpload.vue'

// 响应式数据
const fileUploadRef = ref()
const converting = ref(false)
const convertProgress = ref(0)
const convertResult = ref(null)
const selectedFiles = ref([])
const conversionHistory = ref([])

const form = reactive({
  documentTitle: '转换文档'
})

// 处理文件选择
const handleFilesSelected = (files) => {
  selectedFiles.value = files
}

const handleFileChange = (files) => {
  selectedFiles.value = files
}

// 转换文件
const convertFiles = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要转换的文件')
    return
  }

  converting.value = true
  convertResult.value = null
  convertProgress.value = 0

  try {
    const formData = new FormData()
    
    // 添加文件
    selectedFiles.value.forEach(file => {
      formData.append('files', file)
    })
    
    // 添加文档标题
    formData.append('document_title', form.documentTitle)

    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (convertProgress.value < 90) {
        convertProgress.value += Math.random() * 20
      }
    }, 500)

    const response = await apiService.post('/convert-to-word', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    clearInterval(progressInterval)
    convertProgress.value = 100

    convertResult.value = response
    
    if (response.success) {
      ElMessage.success('文件转换成功！')
      // 清空文件列表
      fileUploadRef.value?.clearFiles()
      selectedFiles.value = []
      // 刷新历史记录
      loadHistory()
    } else {
      ElMessage.error('转换失败: ' + response.message)
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
    convertProgress.value = 0
  }
}

// 下载文件
const downloadFile = () => {
  if (!convertResult.value?.download_url) return
  
  const downloadUrl = convertResult.value.download_url
  if (downloadUrl.startsWith('http')) {
    // 完整URL
    window.open(downloadUrl, '_blank')
  } else {
    // 相对路径
    window.open(`/api${downloadUrl}`, '_blank')
  }
  
  ElMessage.success('开始下载文件')
}

// 重置转换器
const resetConverter = () => {
  convertResult.value = null
  fileUploadRef.value?.clearFiles()
  selectedFiles.value = []
  form.documentTitle = '转换文档'
}

// 加载转换历史
const loadHistory = async () => {
  try {
    const response = await apiService.get('/convert-history')
    if (response && response.history) {
      conversionHistory.value = response.history
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    // 使用模拟数据
    conversionHistory.value = [
      {
        id: 1,
        document_title: '项目投标文件',
        file_count: 3,
        status: 'success',
        created_at: '2024-01-15 14:30:00',
        download_url: '/download/sample.docx'
      },
      {
        id: 2,
        document_title: '合同扫描件',
        file_count: 5,
        status: 'success',
        created_at: '2024-01-14 10:15:00',
        download_url: '/download/contract.docx'
      }
    ]
  }
}

// 下载历史文件
const downloadHistoryFile = (record) => {
  if (record.download_url) {
    window.open(`/api${record.download_url}`, '_blank')
    ElMessage.success('开始下载文件')
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

// 页面加载时获取历史记录
onMounted(() => {
  loadHistory()
})
</script>

<style lang="scss" scoped>
.converting-status {
  text-align: center;
  padding: 40px 20px;
}

.result-success,
.result-error {
  .result-details {
    margin-bottom: 20px;
    text-align: left;
    
    p {
      margin: 8px 0;
      color: var(--el-text-color-regular);
    }
    
    .processed-files {
      margin-top: 16px;
      
      h5 {
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
        font-size: 14px;
      }
    }
  }
}

.initial-state {
  text-align: center;
  padding: 20px;
  
  .tips {
    margin-top: 30px;
    text-align: left;
    background: var(--el-fill-color-extra-light);
    padding: 20px;
    border-radius: 8px;
    
    h4 {
      margin: 0 0 12px 0;
      color: var(--el-text-color-primary);
    }
    
    ul {
      margin: 0;
      padding-left: 20px;
      
      li {
        margin: 8px 0;
        color: var(--el-text-color-regular);
        line-height: 1.5;
      }
    }
  }
}

.action-section {
  margin-top: 24px;
}

.mr-1 {
  margin-right: 8px;
}

.mb-1 {
  margin-bottom: 8px;
}

.mt-2 {
  margin-top: 16px;
}

.mt-3 {
  margin-top: 24px;
}

.mt-4 {
  margin-top: 32px;
}

.mb-3 {
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .page-container {
    padding: 12px;
  }
  
  .action-section {
    margin-top: 16px;
  }
}
</style> 