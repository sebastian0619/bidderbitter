<template>
  <div class="converter-page">
    <!-- 页面头部 -->
    <div class="page-hero">
      <div class="hero-content">
        <div class="hero-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="hero-text">
          <h1>文件转Word工具</h1>
          <p>智能转换PDF和图片为Word文档，支持水印、标题配置等高级功能</p>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat-item">
          <span class="stat-number">{{ allSelectedFiles.length }}</span>
          <span class="stat-label">已选文件</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ selectedPermanentFiles.length }}</span>
          <span class="stat-label">常驻文件</span>
        </div>
      </div>
    </div>

    <div class="page-content">
      <el-row :gutter="24">
        <!-- 左侧配置区域 -->
        <el-col :lg="16" :md="24">
          <div class="config-panel">
            <!-- 文档设置卡片 -->
            <div class="config-card document-card">
              <div class="card-header">
                <div class="header-icon">
                  <el-icon><Setting /></el-icon>
                </div>
                <div class="header-text">
                  <h3>文档配置</h3>
                  <p>设置文档标题和结构</p>
                </div>
              </div>
              <div class="card-content">
                <div class="form-group">
                  <label class="form-label">
                    <el-icon><Edit /></el-icon>
                    文档标题
                  </label>
                  <el-input 
                    v-model="form.documentTitle" 
                    placeholder="请输入生成的Word文档标题"
                    class="modern-input"
                  />
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <div class="switch-group">
                      <el-switch v-model="form.showMainTitle" />
                      <div class="switch-text">
                        <span class="switch-title">主标题显示</span>
                        <span class="switch-desc">在文档开头显示主标题</span>
                      </div>
                    </div>
                    <div v-if="form.showMainTitle" class="level-selector">
                      <el-select v-model="form.mainTitleLevel" placeholder="大纲级别">
                        <el-option label="标题1 (最高级)" :value="1" />
                        <el-option label="标题2" :value="2" />
                        <el-option label="标题3" :value="3" />
                        <el-option label="标题4" :value="4" />
                        <el-option label="标题5" :value="5" />
                        <el-option label="标题6 (最低级)" :value="6" />
                      </el-select>
                    </div>
                  </div>
                  
                  <div class="form-group">
                    <div class="switch-group">
                      <el-switch v-model="form.showFileTitles" />
                      <div class="switch-text">
                        <span class="switch-title">文件标题显示</span>
                        <span class="switch-desc">为每个文件单独显示标题</span>
                      </div>
                    </div>
                    <div v-if="form.showFileTitles" class="level-selector">
                      <el-select v-model="form.fileTitleLevel" placeholder="大纲级别">
                        <el-option label="标题1 (最高级)" :value="1" />
                        <el-option label="标题2" :value="2" />
                        <el-option label="标题3" :value="3" />
                        <el-option label="标题4" :value="4" />
                        <el-option label="标题5" :value="5" />
                        <el-option label="标题6 (最低级)" :value="6" />
                      </el-select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 水印设置卡片 -->
            <div class="config-card watermark-card">
              <div class="card-header">
                <div class="header-icon watermark-icon">
                  <el-icon><Brush /></el-icon>
                </div>
                <div class="header-text">
                  <h3>水印设置</h3>
                  <p>为文档添加个性化水印</p>
                </div>
                <div class="header-control">
                  <el-switch 
                    v-model="form.enableWatermark" 
                    size="large"
                    active-text="启用"
                    inactive-text="关闭"
                  />
                </div>
              </div>
              
              <div v-if="form.enableWatermark" class="card-content watermark-content">
                <div class="watermark-basic">
                  <div class="form-group">
                    <label class="form-label">
                      <el-icon><ChatLineSquare /></el-icon>
                      水印文字
                    </label>
                    <el-input 
                      v-model="form.watermarkText" 
                      placeholder="请输入水印文字，如：机密文档"
                      class="modern-input"
                      maxlength="20"
                      show-word-limit
                    />
                  </div>
                  
                  <div class="position-selector">
                    <label class="form-label">
                      <el-icon><Aim /></el-icon>
                      水印位置
                    </label>
                    <div class="position-grid">
                      <div class="position-main">
                        <el-radio-group v-model="form.watermarkPosition" class="position-buttons">
                          <el-radio-button value="center">
                            <el-icon><Aim /></el-icon>
                            居中
                          </el-radio-button>
                          <el-radio-button value="repeat">
                            <el-icon><Grid /></el-icon>
                            平铺
                          </el-radio-button>
                          <el-radio-button value="background">
                            <el-icon><Picture /></el-icon>
                            背景
                          </el-radio-button>
                        </el-radio-group>
                      </div>
                      <div class="position-corners">
                        <el-radio-group v-model="form.watermarkPosition" class="corner-buttons">
                          <el-radio-button value="top-left">左上</el-radio-button>
                          <el-radio-button value="top-right">右上</el-radio-button>
                          <el-radio-button value="bottom-left">左下</el-radio-button>
                          <el-radio-button value="bottom-right">右下</el-radio-button>
                        </el-radio-group>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="watermark-style">
                  <div class="style-grid">
                    <div class="style-item">
                      <label class="style-label">
                        <el-icon><Edit /></el-icon>
                        字体大小
                      </label>
                      <div class="slider-control">
                        <el-slider
                          v-model="form.watermarkFontSize"
                          :min="12"
                          :max="100"
                          :step="2"
                          show-input
                          :show-input-controls="false"
                          input-size="small"
                        />
                        <span class="unit">px</span>
                      </div>
                    </div>
                    
                    <div class="style-item">
                      <label class="style-label">
                        <el-icon><Refresh /></el-icon>
                        倾斜角度
                      </label>
                      <div class="slider-control">
                        <el-slider
                          v-model="form.watermarkAngle"
                          :min="-90"
                          :max="90"
                          :step="5"
                          show-input
                          :show-input-controls="false"
                          input-size="small"
                        />
                        <span class="unit">°</span>
                      </div>
                    </div>
                    
                    <div class="style-item">
                      <label class="style-label">
                        <el-icon><View /></el-icon>
                        透明度
                      </label>
                      <div class="slider-control">
                        <el-slider
                          v-model="form.watermarkOpacity"
                          :min="10"
                          :max="100"
                          :step="5"
                          show-input
                          :show-input-controls="false"
                          input-size="small"
                        />
                        <span class="unit">%</span>
                      </div>
                    </div>
                    
                    <div class="style-item">
                      <label class="style-label">
                        <el-icon><Brush /></el-icon>
                        颜色
                      </label>
                      <div class="color-control">
                        <el-color-picker 
                          v-model="form.watermarkColor"
                          color-format="hex"
                          :predefine="predefineColors"
                          size="large"
                        />
                        <div class="color-info">
                          <span class="color-preview" :style="{ backgroundColor: form.watermarkColor }"></span>
                          <span class="color-value">{{ form.watermarkColor }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="watermark-preview">
                    <div class="preview-header">
                      <el-icon><View /></el-icon>
                      预览效果
                    </div>
                    <div class="preview-area">
                      <div 
                        class="preview-watermark"
                        :style="{
                          fontSize: Math.max(form.watermarkFontSize / 3, 12) + 'px',
                          color: form.watermarkColor,
                          opacity: form.watermarkOpacity / 100,
                          transform: `rotate(${form.watermarkAngle}deg)`
                        }"
                      >
                        {{ form.watermarkText || '水印预览' }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 文件上传卡片 -->
            <div class="config-card upload-card">
              <div class="card-header">
                <div class="header-icon upload-icon">
                  <el-icon><Upload /></el-icon>
                </div>
                <div class="header-text">
                  <h3>文件上传</h3>
                  <p>支持PDF、图片格式，最大{{ MAX_UPLOAD_SIZE_MB }}MB</p>
                </div>
              </div>
              <div class="card-content">
                <FileUpload
                  ref="fileUploadRef"
                  :allowed-types="['pdf', 'image']"
                  :multiple="true"
                  :max-size="MAX_UPLOAD_SIZE"
                  accept=".pdf,.jpg,.jpeg,.png,.bmp,.gif,.tiff"
                  @upload="handleFilesSelected"
                  @change="handleFileChange"
                />
                
                <!-- 常驻文件选择 -->
                <div class="permanent-section">
                  <div class="section-header">
                    <h4>
                      <el-icon><FolderOpened /></el-icon>
                      常驻文件库
                    </h4>
                    <el-button type="primary" text @click="showPermanentFilesDialog = true">
                      <el-icon><Plus /></el-icon>
                      选择文件
                    </el-button>
                  </div>
                  
                  <div v-if="selectedPermanentFiles.length > 0" class="permanent-files">
                    <div
                      v-for="(file, index) in selectedPermanentFiles"
                      :key="`perm-${file.id}`"
                      class="permanent-file"
                    >
                      <div class="file-info">
                        <i :class="getFileIcon(file.file_type)" class="file-icon"></i>
                        <div class="file-details">
                          <span class="file-name">{{ file.display_name }}</span>
                          <span class="file-meta">{{ formatFileSize(file.file_size) }} • {{ file.category }}</span>
                        </div>
                      </div>
                      <div class="file-actions">
                        <el-switch
                          v-model="file.enableWatermark"
                          size="small"
                          active-text="水印"
                        />
                        <el-button
                          size="small"
                          text
                          type="danger"
                          @click="removePermanentFile(index)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 文件列表卡片 -->
            <div v-if="allSelectedFiles.length > 0" class="config-card files-card">
              <div class="card-header">
                <div class="header-icon files-icon">
                  <el-icon><DocumentCopy /></el-icon>
                </div>
                <div class="header-text">
                  <h3>待转换文件</h3>
                  <p>{{ allSelectedFiles.length + selectedPermanentFiles.length }} 个文件将按顺序转换</p>
                </div>
                <div class="header-controls">
                  <el-button size="small" text type="info" @click="toggleAllWatermarks">
                    <el-icon><Brush /></el-icon>
                    {{ areAllWatermarksEnabled() ? '全部关闭水印' : '全部开启水印' }}
                  </el-button>
                  <el-button size="small" text type="danger" @click="clearAllFiles">
                    <el-icon><Delete /></el-icon>
                    清空
                  </el-button>
                </div>
              </div>
              <div class="card-content">
                <div class="files-grid">
                  <div
                    v-for="(file, index) in allSelectedFiles"
                    :key="`selected-${index}`"
                    class="file-card"
                  >
                    <div class="file-index">{{ index + 1 }}</div>
                    <div class="file-content">
                      <div class="file-name">{{ file.name }}</div>
                      <div class="file-size">{{ formatFileSize(file.size) }}</div>
                    </div>
                    <div class="file-controls">
                      <el-switch
                        v-model="file.enableWatermark"
                        size="small"
                        active-text="水印"
                      />
                      <el-button
                        size="small"
                        text
                        type="danger"
                        @click="removeSelectedFile(index)"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 转换按钮 -->
            <div class="convert-section">
              <el-button 
                type="primary" 
                size="large"
                :loading="converting"
                :disabled="(allSelectedFiles.length + selectedPermanentFiles.length) === 0"
                @click="convertFiles"
                class="convert-button"
              >
                <el-icon><DocumentAdd /></el-icon>
                开始转换为Word文档
              </el-button>
            </div>
          </div>
        </el-col>

        <!-- 右侧结果区域 -->
        <el-col :lg="8" :md="24">
          <div class="result-panel">
            <div class="result-card">
              <div class="card-header">
                <div class="header-icon result-icon">
                  <el-icon><Monitor /></el-icon>
                </div>
                <div class="header-text">
                  <h3>转换结果</h3>
                  <p>查看转换进度和下载文件</p>
                </div>
              </div>
              <div class="card-content result-content">
                <!-- 转换进度 -->
                <div v-if="converting" class="converting-status">
                  <div class="progress-wrapper">
                    <div class="progress-icon">
                      <el-icon class="rotating"><Loading /></el-icon>
                    </div>
                    <div class="progress-text">
                      <h4>正在转换文件...</h4>
                      <p>请稍候，正在处理您的文件</p>
                    </div>
                  </div>
                  <el-progress 
                    :percentage="convertProgress" 
                    :stroke-width="8"
                    :color="[
                      { color: '#f56c6c', percentage: 20 },
                      { color: '#e6a23c', percentage: 40 },
                      { color: '#5cb87a', percentage: 60 },
                      { color: '#1989fa', percentage: 80 },
                      { color: '#6f7ad3', percentage: 100 }
                    ]"
                  />
                </div>

                <!-- 转换成功 -->
                <div v-else-if="convertResult?.success" class="result-success">
                  <div class="success-icon">
                    <el-icon><CircleCheck /></el-icon>
                  </div>
                  <div class="success-content">
                    <h3>转换完成！</h3>
                    <p>成功处理 {{ convertResult.processed_files?.length || 0 }} 个文件</p>
                    
                    <div class="result-info">
                      <div class="info-item">
                        <span class="label">输出文件:</span>
                        <span class="value">{{ convertResult.output_file }}</span>
                      </div>
                      
                      <div v-if="convertResult.processed_files?.length" class="processed-files">
                        <span class="label">处理的文件:</span>
                        <div class="file-tags">
                          <el-tag
                            v-for="(file, index) in convertResult.processed_files"
                            :key="`file-${index}`"
                            size="small"
                            effect="light"
                          >
                            {{ file }}
                          </el-tag>
                        </div>
                      </div>
                    </div>
                    
                    <div class="action-buttons">
                      <el-button 
                        type="success" 
                        size="large"
                        @click="downloadFile"
                        class="download-btn"
                      >
                        <el-icon><Download /></el-icon>
                        下载Word文档
                      </el-button>
                      <el-button 
                        text
                        @click="resetConverter"
                      >
                        <el-icon><Refresh /></el-icon>
                        重新开始
                      </el-button>
                    </div>
                  </div>
                </div>

                <!-- 转换失败 -->
                <div v-else-if="convertResult?.success === false" class="result-error">
                  <div class="error-icon">
                    <el-icon><CircleClose /></el-icon>
                  </div>
                  <div class="error-content">
                    <h3>转换失败</h3>
                    <p>{{ convertResult.message }}</p>
                    <el-button type="primary" @click="resetConverter">
                      <el-icon><Refresh /></el-icon>
                      重新开始
                    </el-button>
                  </div>
                </div>

                <!-- 初始状态 -->
                <div v-else class="result-empty">
                  <div class="empty-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="empty-content">
                    <h3>等待文件转换</h3>
                    <p>请先选择要转换的文件</p>
                    
                    <div class="features-list">
                      <div class="feature-item">
                        <el-icon><Check /></el-icon>
                        <span>支持PDF、图片格式</span>
                      </div>
                      <div class="feature-item">
                        <el-icon><Check /></el-icon>
                        <span>智能水印配置</span>
                      </div>
                      <div class="feature-item">
                        <el-icon><Check /></el-icon>
                        <span>自定义标题结构</span>
                      </div>
                      <div class="feature-item">
                        <el-icon><Check /></el-icon>
                        <span>批量文件处理</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 常驻文件选择对话框 -->
    <el-dialog v-model="showPermanentFilesDialog" title="选择常驻文件" width="800px">
      <div class="permanent-files-dialog">
        <!-- 搜索和筛选 -->
        <div class="search-section mb-4">
          <el-input
            v-model="permanentFileSearch"
            placeholder="搜索文件名..."
            style="width: 300px; margin-right: 16px;"
            @input="searchPermanentFiles"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select 
            v-model="permanentFileCategory" 
            placeholder="选择分类" 
            style="width: 200px;"
            @change="searchPermanentFiles"
          >
            <el-option label="全部分类" value=""></el-option>
            <el-option label="合同文件" value="contract"></el-option>
            <el-option label="证书文件" value="certificate"></el-option>
            <el-option label="模板文件" value="template"></el-option>
            <el-option label="参考资料" value="reference"></el-option>
            <el-option label="其他" value="other"></el-option>
          </el-select>
        </div>
        
        <!-- 文件列表 -->
        <el-table 
          :data="permanentFilesList" 
          v-loading="permanentFilesLoading" 
          max-height="400"
          @selection-change="handlePermanentFileSelection"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column label="文件名" min-width="200">
            <template #default="scope">
              <div class="flex items-center">
                <i :class="getFileIcon(scope.row.file_type)" class="mr-2"></i>
                <span>{{ scope.row.display_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column label="大小" width="100">
            <template #default="scope">
              {{ formatFileSize(scope.row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column prop="access_count" label="使用次数" width="100" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
        </el-table>
        
        <!-- 分页 -->
        <el-pagination
          v-if="permanentFilesTotalCount > 0"
          class="mt-4"
          @current-change="handlePermanentFilesPageChange"
          :current-page="permanentFilesPage"
          :page-size="permanentFilesPageSize"
          :total="permanentFilesTotalCount"
          layout="total, prev, pager, next"
          small
        />
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPermanentFilesDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmPermanentFileSelection">
            确定选择 ({{ tempSelectedPermanentFiles.length }} 个文件)
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, DocumentAdd, Download, Clock, Refresh, Delete, InfoFilled, Warning,
  Edit, Setting, View, Brush, Aim, Grid, Picture, ChatLineSquare, FolderOpened, Search, Plus,
  CircleCheck, CircleClose, Check, Loading, Monitor, DocumentCopy, Upload
} from '@element-plus/icons-vue'
import { apiService } from '@/services/api'
import FileUpload from '@/components/FileUpload.vue'

// 读取最大上传大小（MB）
const MAX_UPLOAD_SIZE_MB = Number(import.meta.env.VITE_MAX_UPLOAD_SIZE_MB) || 50
const MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

// 预定义颜色
const predefineColors = ref([
  '#808080', // 灰色
  '#ff0000', // 红色
  '#0066cc', // 蓝色
  '#00cc66', // 绿色
  '#ff6600', // 橙色
  '#9900cc', // 紫色
  '#cc6600', // 棕色
  '#6699cc', // 蓝灰色
])

// 响应式数据
const fileUploadRef = ref()
const converting = ref(false)
const convertProgress = ref(0)
const convertResult = ref(null)
const selectedFiles = ref([])
const uploadedFiles = ref([])
const allSelectedFiles = ref([]) // 累积所有选择的文件
const conversionHistory = ref([])

// 常驻文件相关
const selectedPermanentFiles = ref([])
const showPermanentFilesDialog = ref(false)
const permanentFilesList = ref([])
const permanentFilesLoading = ref(false)
const permanentFileSearch = ref('')
const permanentFileCategory = ref('')
const permanentFilesPage = ref(1)
const permanentFilesPageSize = ref(10)
const permanentFilesTotalCount = ref(0)
const tempSelectedPermanentFiles = ref([])

const form = reactive({
  documentTitle: '转换文档',
  showMainTitle: true,
  showFileTitles: true,
  mainTitleLevel: 1,
  fileTitleLevel: 2,
  enableWatermark: false,
  watermarkText: '',
  watermarkFontSize: 24,
  watermarkAngle: -45,
  watermarkOpacity: 30,
  watermarkColor: '#808080',
  watermarkPosition: 'center'
})

// 根据选择的文件自动设置文档标题
const updateDocumentTitle = () => {
  if (allSelectedFiles.value.length > 0) {
    if (allSelectedFiles.value.length === 1) {
      // 单个文件，使用文件名
      const firstFileName = allSelectedFiles.value[0].name
      const baseName = firstFileName.split('.').slice(0, -1).join('.')
      form.documentTitle = baseName || '转换文档'
    } else {
      // 多个文件，使用合并文档标题
      form.documentTitle = `合并文档_${allSelectedFiles.value.length}个文件`
    }
  } else {
    form.documentTitle = '转换文档'
  }
}

// 监听FileUpload组件的change事件，累积添加文件
const handleFilesSelected = (files) => {
  // 添加新选择的文件到总列表，并为每个文件添加水印开关
  files.forEach(file => {
    // 提取文件基本信息，避免reactive包装影响File对象属性访问
    const fileInfo = {
      // 保留原始File对象用于上传
      originalFile: file,
      // 提取基本信息
      name: file.name || 'unknown',
      size: file.size || 0,
      type: file.type || '',
      lastModified: file.lastModified || Date.now(),
      // 添加水印开关 - 根据总开关状态设置默认值
      enableWatermark: form.enableWatermark
    }
    
    // 使用reactive包装文件信息对象
    const reactiveFile = reactive(fileInfo)
    allSelectedFiles.value.push(reactiveFile)
  })
  updateDocumentTitle()
  
  // 清空当前上传组件，为下次上传做准备
  setTimeout(() => {
    fileUploadRef.value?.clearFiles()
  }, 100)
}

const handleFileChange = (fileList) => {
  // 这个事件主要用于实时更新当前上传组件的显示
  selectedFiles.value = fileList.map((f, index) => ({ 
    name: f.name || f.file?.name, 
    size: f.size || f.file?.size, 
    id: index 
  }))
}

// 移除特定文件
const removeSelectedFile = (index) => {
  allSelectedFiles.value.splice(index, 1)
  updateDocumentTitle()
}

// 清空所有文件
const clearAllFiles = () => {
  allSelectedFiles.value = []
  fileUploadRef.value?.clearFiles()
  updateDocumentTitle()
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 检查是否所有文件都启用了水印
const areAllWatermarksEnabled = () => {
  const allFiles = [...allSelectedFiles.value, ...selectedPermanentFiles.value]
  return allFiles.length > 0 && allFiles.every(file => file.enableWatermark === true)
}

// 切换所有文件的水印状态
const toggleAllWatermarks = () => {
  const newState = !areAllWatermarksEnabled()
  
  // 更新上传的文件
  allSelectedFiles.value.forEach(file => {
    file.enableWatermark = newState
  })
  
  // 更新常驻文件
  selectedPermanentFiles.value.forEach(file => {
    file.enableWatermark = newState
  })
  
  ElMessage.success(newState ? '已开启所有文件水印' : '已关闭所有文件水印')
}

// 转换文件 - 已被下面的增强版本替代

// 下载文件
const downloadFile = () => {
  if (!convertResult.value?.download_url) return

  const downloadUrl = convertResult.value.download_url
  // 直接用后端返回的download_url，不再拼接/api
  window.open(downloadUrl, '_blank')
  ElMessage.success('开始下载文件')
}

// 重置转换器
const resetConverter = () => {
  convertResult.value = null
  fileUploadRef.value?.clearFiles()
  selectedFiles.value = []
  allSelectedFiles.value = []
  form.documentTitle = '转换文档'
  form.showMainTitle = true
  form.showFileTitles = true
  form.mainTitleLevel = 1
  form.fileTitleLevel = 2
  form.enableWatermark = false
  form.watermarkText = ''
  form.watermarkFontSize = 24
  form.watermarkAngle = -45
  form.watermarkOpacity = 30
  form.watermarkColor = '#808080'
  form.watermarkPosition = 'center'
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
  if (record.output_file) {
    // 使用output_file字段构造下载URL
    window.open(`/api/download/${record.output_file}`, '_blank')
    ElMessage.success('开始下载文件')
  } else if (record.download_url) {
    // 兼容旧格式
    window.open(`/api${record.download_url}`, '_blank')
    ElMessage.success('开始下载文件')
  } else {
    ElMessage.error('文件不存在或已被删除')
  }
}

// 获取状态类型
const getStatusType = (status) => {
  switch (status) {
    case 'success':
      return 'success'
    case 'failed':
      return 'danger'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'success':
      return '成功'
    case 'failed':
      return '失败'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

// 清空转换历史
const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有转换历史吗？此操作不可撤销。', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const response = await apiService.delete('/convert-history')
    if (response && response.success) {
      conversionHistory.value = []
      ElMessage.success('转换历史已清空')
    } else {
      ElMessage.error('清空历史失败: ' + (response?.message || '未知错误'))
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空历史失败:', error)
      ElMessage.error('清空历史失败: ' + (error.response?.data?.message || error.message))
    }
  }
}

// 常驻文件相关方法
const fetchPermanentFiles = async () => {
  permanentFilesLoading.value = true
  try {
    const params = {
      file_category: 'permanent',
      page: permanentFilesPage.value,
      page_size: permanentFilesPageSize.value
    }
    
    if (permanentFileSearch.value) {
      params.search = permanentFileSearch.value
    }
    
    if (permanentFileCategory.value) {
      params.category = permanentFileCategory.value
    }
    
    const response = await apiService.get('/files/list', { params })
    if (response && response.data && response.data.success) {
      permanentFilesList.value = response.data.files
      permanentFilesTotalCount.value = response.data.pagination.total
    }
  } catch (error) {
    console.error('获取常驻文件列表失败:', error)
    ElMessage.error('获取常驻文件列表失败')
  } finally {
    permanentFilesLoading.value = false
  }
}

const searchPermanentFiles = () => {
  permanentFilesPage.value = 1
  fetchPermanentFiles()
}

const handlePermanentFilesPageChange = (page) => {
  permanentFilesPage.value = page
  fetchPermanentFiles()
}

const handlePermanentFileSelection = (selection) => {
  tempSelectedPermanentFiles.value = selection
}

const confirmPermanentFileSelection = () => {
  // 添加选中的常驻文件到列表，避免重复
  const newFiles = tempSelectedPermanentFiles.value.filter(file => 
    !selectedPermanentFiles.value.some(existing => existing.id === file.id)
  )
  
  // 为每个文件添加水印开关，使用reactive确保响应式 - 根据总开关状态设置默认值
  const reactiveNewFiles = newFiles.map(file => reactive({
    ...file,
    enableWatermark: form.enableWatermark // 跟随总开关状态
  }))
  
  selectedPermanentFiles.value.push(...reactiveNewFiles)
  showPermanentFilesDialog.value = false
  tempSelectedPermanentFiles.value = []
  
  if (newFiles.length > 0) {
    ElMessage.success(`已添加 ${newFiles.length} 个常驻文件`)
  }
}

const removePermanentFile = (index) => {
  selectedPermanentFiles.value.splice(index, 1)
  ElMessage.success('已移除文件')
}

// 文件图标
const getFileIcon = (fileType) => {
  const icons = {
    'pdf': 'fa fa-file-pdf-o text-red-600',
    'image': 'fa fa-file-image-o text-green-600',
    'document': 'fa fa-file-word-o text-blue-600',
    'text': 'fa fa-file-text-o text-gray-600',
    'other': 'fa fa-file-o text-gray-400'
  }
  return icons[fileType] || icons['other']
}

// 修改转换函数，包含常驻文件
const convertFiles = async () => {
  // 合并上传的文件和选择的常驻文件
  const totalFiles = allSelectedFiles.value.length + selectedPermanentFiles.value.length
  
  if (totalFiles === 0) {
    ElMessage.warning('请先选择要转换的文件')
    return
  }

  converting.value = true
  convertResult.value = null
  convertProgress.value = 0

  try {
    const formData = new FormData()
    
    // 添加上传的文件（按顺序）
    allSelectedFiles.value.forEach(file => {
      // 使用原始File对象进行上传
      formData.append('files', file.originalFile || file)
    })
    
    // 添加文档标题
    formData.append('document_title', form.documentTitle)
    
    // 添加标题配置选项
    formData.append('show_main_title', form.showMainTitle)
    formData.append('show_file_titles', form.showFileTitles)
    formData.append('main_title_level', form.mainTitleLevel)
    formData.append('file_title_level', form.fileTitleLevel)
    
    // 添加每个文件的水印设置（包括上传的文件和常驻文件）
    const allFileWatermarkSettings = [
      ...allSelectedFiles.value.map(file => file.enableWatermark),
      ...selectedPermanentFiles.value.map(file => file.enableWatermark)
    ]
    formData.append('file_watermark_settings', JSON.stringify(allFileWatermarkSettings))
    
    // 添加选择的常驻文件ID
    const permanentFileIds = selectedPermanentFiles.value.map(file => file.id)
    formData.append('permanent_file_ids', JSON.stringify(permanentFileIds))
    
    // 添加全局水印参数（作为默认配置）
    formData.append('enable_watermark', form.enableWatermark)
    if (form.watermarkText) {
      formData.append('watermark_text', form.watermarkText)
      formData.append('watermark_font_size', form.watermarkFontSize)
      formData.append('watermark_angle', form.watermarkAngle)
      formData.append('watermark_opacity', form.watermarkOpacity)
      formData.append('watermark_color', form.watermarkColor)
      formData.append('watermark_position', form.watermarkPosition)
    }

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
    
    // 转换成功后加载历史记录
    loadHistory()
    
    ElMessage.success('文件转换完成！')
    
  } catch (error) {
    console.error('转换失败:', error)
    convertResult.value = {
      success: false,
      message: error.response?.data?.message || '转换过程中出现错误，请重试'
    }
    ElMessage.error('转换失败: ' + (error.response?.data?.message || error.message))
  } finally {
    converting.value = false
  }
}

// 监听对话框显示，自动加载常驻文件
const handlePermanentFilesDialogOpen = () => {
  if (showPermanentFilesDialog.value) {
    fetchPermanentFiles()
  }
}

// 页面加载时获取历史记录
onMounted(() => {
  loadHistory()
})

// 监听对话框状态
import { watch } from 'vue'
watch(showPermanentFilesDialog, (newVal) => {
  if (newVal) {
    fetchPermanentFiles()
  }
})

// 监听总开关状态变化，自动同步所有文件的水印开关
watch(() => form.enableWatermark, (newValue) => {
  // 同步所有上传文件的水印开关
  allSelectedFiles.value.forEach(file => {
    file.enableWatermark = newValue
  })
  
  // 同步所有常驻文件的水印开关
  selectedPermanentFiles.value.forEach(file => {
    file.enableWatermark = newValue
  })
  
  if (allSelectedFiles.value.length > 0 || selectedPermanentFiles.value.length > 0) {
    ElMessage.success(newValue ? '已为所有文件开启水印' : '已为所有文件关闭水印')
  }
})
</script>

<style lang="scss" scoped>
// 页面整体布局
.converter-page {
  min-height: 100vh;
  background: linear-gradient(135deg, 
    rgba(99, 102, 241, 0.05) 0%, 
    rgba(168, 85, 247, 0.05) 50%, 
    rgba(236, 72, 153, 0.05) 100%);
  padding: 0;
}

// 页面头部英雄区
.page-hero {
  background: linear-gradient(135deg, 
    rgba(99, 102, 241, 0.8) 0%, 
    rgba(168, 85, 247, 0.8) 50%, 
    rgba(236, 72, 153, 0.8) 100%);
  color: white;
  padding: 40px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  .hero-content {
    display: flex;
    align-items: center;
    gap: 20px;
    
    .hero-icon {
      width: 80px;
      height: 80px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(10px);
      
      .el-icon {
        font-size: 40px;
      }
    }
    
    .hero-text {
      h1 {
        margin: 0 0 8px 0;
        font-size: 32px;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
      
      p {
        margin: 0;
        font-size: 16px;
        opacity: 0.9;
      }
    }
  }
  
  .hero-stats {
    display: flex;
    gap: 30px;
    
    .stat-item {
      text-align: center;
      
      .stat-number {
        display: block;
        font-size: 28px;
        font-weight: 700;
        line-height: 1;
      }
      
      .stat-label {
        display: block;
        font-size: 14px;
        opacity: 0.8;
        margin-top: 4px;
      }
    }
  }
}

// 页面内容区域
.page-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px 40px;
}

// 配置面板
.config-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

// 配置卡片通用样式
.config-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.06);
  
  &:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    transform: translateY(-2px);
  }
  
  .card-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 24px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    position: relative;
    
    .header-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        font-size: 24px;
        color: white;
      }
      
      &:not(.watermark-icon):not(.upload-icon):not(.files-icon):not(.result-icon) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }
    }
    
    .watermark-icon {
      background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    }
    
    .upload-icon {
      background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    }
    
    .files-icon {
      background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    }
    
    .result-icon {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .header-text {
      flex: 1;
      
      h3 {
        margin: 0 0 4px 0;
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }
      
      p {
        margin: 0;
        font-size: 14px;
        color: var(--el-text-color-regular);
      }
    }
    
    .header-control,
    .header-controls {
      display: flex;
      gap: 8px;
      align-items: center;
    }
  }
  
  .card-content {
    padding: 24px;
  }
}

// 表单组件样式
.form-group {
  margin-bottom: 20px;
  
  .form-label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    
    .el-icon {
      color: var(--el-color-primary);
    }
  }
  
  .modern-input {
    :deep(.el-input__wrapper) {
      border-radius: 10px;
      border: 2px solid var(--el-border-color-light);
      transition: all 0.3s ease;
      
      &:hover {
        border-color: var(--el-color-primary);
      }
      
      &.is-focus {
        border-color: var(--el-color-primary);
        box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
      }
    }
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

// 开关组样式
.switch-group {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  
  .switch-text {
    flex: 1;
    
    .switch-title {
      display: block;
      font-weight: 500;
      color: var(--el-text-color-primary);
      margin-bottom: 2px;
    }
    
    .switch-desc {
      display: block;
      font-size: 12px;
      color: var(--el-text-color-regular);
    }
  }
}

.level-selector {
  :deep(.el-select) {
    width: 100%;
    
    .el-select__wrapper {
      border-radius: 8px;
    }
  }
}

// 水印配置样式
.watermark-content {
  .watermark-basic {
    margin-bottom: 24px;
  }
  
  .position-selector {
    .position-grid {
      display: flex;
      flex-direction: column;
      gap: 12px;
      
      .position-buttons,
      .corner-buttons {
        display: flex;
        gap: 8px;
        
        :deep(.el-radio-button) {
          flex: 1;
          
          .el-radio-button__inner {
            width: 100%;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            font-size: 13px;
            padding: 8px 12px;
          }
        }
      }
      
      .corner-buttons {
        :deep(.el-radio-button__inner) {
          font-size: 12px;
          padding: 6px 8px;
        }
      }
    }
  }
  
  .style-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
    
    .style-item {
      .style-label {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: 500;
        color: var(--el-text-color-primary);
        
        .el-icon {
          color: var(--el-color-primary);
        }
      }
      
      .slider-control {
        display: flex;
        align-items: center;
        gap: 8px;
        
        :deep(.el-slider) {
          flex: 1;
        }
        
        .unit {
          font-size: 12px;
          color: var(--el-text-color-regular);
          min-width: 20px;
        }
      }
      
      .color-control {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .color-info {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .color-preview {
            width: 24px;
            height: 24px;
            border-radius: 6px;
            border: 1px solid var(--el-border-color);
          }
          
          .color-value {
            font-size: 12px;
            font-family: monospace;
            color: var(--el-text-color-regular);
          }
        }
      }
    }
  }
  
  .watermark-preview {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    overflow: hidden;
    
    .preview-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.8);
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
      font-size: 14px;
      font-weight: 500;
      color: var(--el-text-color-primary);
      
      .el-icon {
        color: var(--el-color-primary);
      }
    }
    
    .preview-area {
      height: 100px;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      
      &::before {
        content: '';
        position: absolute;
        inset: 0;
        background: repeating-linear-gradient(
          45deg,
          transparent,
          transparent 8px,
          rgba(255, 255, 255, 0.5) 8px,
          rgba(255, 255, 255, 0.5) 16px
        );
      }
      
      .preview-watermark {
        font-family: '楷体', 'KaiTi', serif;
        font-weight: bold;
        text-align: center;
        user-select: none;
        transition: all 0.3s ease;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        position: relative;
        z-index: 1;
      }
    }
  }
}

// 文件上传区域
.permanent-section {
  margin-top: 24px;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h4 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-size: 16px;
      color: var(--el-text-color-primary);
      
      .el-icon {
        color: var(--el-color-primary);
      }
    }
  }
  
  .permanent-files {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .permanent-file {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: var(--el-fill-color-extra-light);
      border-radius: 10px;
      border: 1px solid var(--el-border-color-extra-light);
      transition: all 0.3s ease;
      
      &:hover {
        background: var(--el-fill-color-light);
        border-color: var(--el-color-primary);
      }
      
      .file-info {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        
        .file-icon {
          font-size: 18px;
        }
        
        .file-details {
          display: flex;
          flex-direction: column;
          
          .file-name {
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }
          
          .file-meta {
            font-size: 12px;
            color: var(--el-text-color-regular);
          }
        }
      }
      
      .file-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
  }
}

// 文件列表网格
.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  
  .file-card {
    display: flex;
    align-items: center;
    padding: 16px;
    background: var(--el-fill-color-extra-light);
    border-radius: 10px;
    border: 1px solid var(--el-border-color-extra-light);
    transition: all 0.3s ease;
    
    &:hover {
      background: var(--el-fill-color-light);
      border-color: var(--el-color-primary);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .file-index {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
      color: white;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      font-size: 14px;
      margin-right: 12px;
    }
    
    .file-content {
      flex: 1;
      min-width: 0;
      
      .file-name {
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .file-size {
        font-size: 12px;
        color: var(--el-text-color-regular);
      }
    }
    
    .file-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}

// 转换按钮
.convert-section {
  .convert-button {
    width: 100%;
    height: 56px;
    font-size: 16px;
    font-weight: 600;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
    border: none;
    
    &:hover {
      background: linear-gradient(135deg, var(--el-color-primary-dark-2) 0%, var(--el-color-primary) 100%);
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
  }
}

// 结果面板
.result-panel {
  .result-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    border: 1px solid rgba(0, 0, 0, 0.06);
    height: fit-content;
    min-height: 500px;
    
    .card-header {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 24px;
      border-bottom: 1px solid rgba(0, 0, 0, 0.06);
      
      .header-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        
        .el-icon {
          font-size: 24px;
          color: white;
        }
      }
      
      .header-text {
        flex: 1;
        
        h3 {
          margin: 0 0 4px 0;
          font-size: 18px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        p {
          margin: 0;
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }
    
    .result-content {
      min-height: 400px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      text-align: center;
      padding: 20px;
    }
  }
}

// 转换状态样式
.converting-status {
  text-align: center;
  padding: 20px;
  width: 100%;
  
  .progress-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 24px;
    
    .progress-icon {
      margin-bottom: 16px;
      
      .el-icon {
        font-size: 48px;
        color: var(--el-color-primary);
        
        &.rotating {
          animation: rotate 2s linear infinite;
        }
      }
    }
    
    .progress-text {
      h4 {
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
        font-size: 18px;
      }
      
      p {
        margin: 0;
        color: var(--el-text-color-regular);
        font-size: 14px;
      }
    }
  }
  
  .el-progress {
    width: 100%;
    max-width: 300px;
    margin: 0 auto;
  }
}

.result-success {
  text-align: center;
  padding: 20px;
  width: 100%;
  
  .success-icon {
    margin-bottom: 24px;
    
    .el-icon {
      font-size: 64px;
      color: var(--el-color-success);
    }
  }
  
  .success-content {
    h3 {
      margin: 0 0 8px 0;
      color: var(--el-text-color-primary);
      font-size: 20px;
    }
    
    > p {
      margin: 0 0 24px 0;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
    
    .result-info {
      background: var(--el-fill-color-extra-light);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
      text-align: left;
      
      .info-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 12px;
        
        .label {
          font-weight: 500;
          color: var(--el-text-color-primary);
          font-size: 13px;
        }
        
        .value {
          color: var(--el-text-color-regular);
          font-family: monospace;
          font-size: 12px;
        }
      }
      
      .processed-files {
        .label {
          display: block;
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 8px;
          font-size: 13px;
        }
        
        .file-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
      }
    }
    
    .action-buttons {
      display: flex;
      flex-direction: column;
      gap: 12px;
      
      .download-btn {
        height: 48px;
        padding: 0 24px;
        font-size: 16px;
        font-weight: 600;
        border-radius: 10px;
      }
    }
  }
}

.result-error {
  text-align: center;
  padding: 20px;
  width: 100%;
  
  .error-icon {
    margin-bottom: 24px;
    
    .el-icon {
      font-size: 64px;
      color: var(--el-color-danger);
    }
  }
  
  .error-content {
    h3 {
      margin: 0 0 8px 0;
      color: var(--el-text-color-primary);
      font-size: 20px;
    }
    
    p {
      margin: 0 0 24px 0;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
  }
}

.result-empty {
  text-align: center;
  padding: 20px;
  width: 100%;
  
  .empty-icon {
    margin-bottom: 24px;
    
    .el-icon {
      font-size: 64px;
      color: var(--el-text-color-placeholder);
    }
  }
  
  .empty-content {
    h3 {
      margin: 0 0 8px 0;
      color: var(--el-text-color-primary);
      font-size: 18px;
    }
    
    > p {
      margin: 0 0 24px 0;
      color: var(--el-text-color-regular);
      font-size: 14px;
    }
    
    .features-list {
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
      max-width: 280px;
      margin: 0 auto;
      
      .feature-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: var(--el-fill-color-extra-light);
        border-radius: 8px;
        font-size: 13px;
        color: var(--el-text-color-regular);
        text-align: left;
        
        .el-icon {
          color: var(--el-color-success);
          font-size: 14px;
        }
      }
    }
  }
}

// 动画
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .page-content {
    padding: 0 16px 40px;
  }
  
  .hero-stats {
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .page-hero {
    flex-direction: column;
    text-align: center;
    gap: 20px;
    padding: 30px 16px;
    
    .hero-content {
      flex-direction: column;
      text-align: center;
      
      .hero-text h1 {
        font-size: 24px;
      }
    }
    
    .hero-stats {
      justify-content: center;
    }
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .style-grid {
    grid-template-columns: 1fr;
  }
  
  .files-grid {
    grid-template-columns: 1fr;
  }
  
  .config-card .card-header {
    flex-wrap: wrap;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .page-hero {
    padding: 20px 12px;
    
    .hero-content .hero-icon {
      width: 60px;
      height: 60px;
      
      .el-icon {
        font-size: 30px;
      }
    }
    
    .hero-text h1 {
      font-size: 20px;
    }
  }
  
  .config-card .card-content {
    padding: 16px;
  }
}
</style> 