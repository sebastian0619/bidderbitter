<template>
  <div class="data-management-page">
    <!-- 页面头部英雄区 -->
    <div class="page-hero">
      <div class="hero-content">
        <div class="hero-icon">
          <el-icon><DataBoard /></el-icon>
        </div>
        <div class="hero-text">
          <h1>数据管理中心</h1>
          <p>统一管理常驻文件和临时文件，支持AI智能分类与分析</p>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat-item">
          <span class="stat-number">{{ fileStats.total_files || 0 }}</span>
          <span class="stat-label">总文件数</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ formatFileSize(fileStats.total_size) }}</span>
          <span class="stat-label">存储空间</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ fileStats.permanent_files || 0 }}</span>
          <span class="stat-label">常驻文件</span>
        </div>
      </div>
    </div>

    <!-- 页面内容区域 -->
    <div class="page-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card total-files">
          <div class="card-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-content">
            <h3>总文件数</h3>
            <div class="stat-number">{{ fileStats.total_files || 0 }}</div>
            <div class="stat-change">
              <el-icon><TrendCharts /></el-icon>
              <span>管理所有文件</span>
            </div>
          </div>
        </div>
        
        <div class="stat-card permanent-files">
          <div class="card-icon">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <div class="card-content">
            <h3>常驻文件</h3>
            <div class="stat-number">{{ fileStats.permanent_files || 0 }}</div>
            <div class="stat-change">
              <el-icon><Check /></el-icon>
              <span>长期保存</span>
            </div>
          </div>
        </div>
        
        <div class="stat-card temporary-files">
          <div class="card-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="card-content">
            <h3>临时文件</h3>
            <div class="stat-number">{{ fileStats.temporary_files || 0 }}</div>
            <div class="stat-change">
              <el-icon><Timer /></el-icon>
              <span>定期清理</span>
            </div>
          </div>
        </div>
        
        <div class="stat-card storage-size">
          <div class="card-icon">
            <el-icon><PieChart /></el-icon>
          </div>
          <div class="card-content">
            <h3>存储大小</h3>
            <div class="stat-number">{{ formatFileSize(fileStats.total_size) }}</div>
            <div class="stat-change">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据统计</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 文件管理区域 -->
      <div class="file-management-section">
        <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="custom-tabs">
          <el-tab-pane name="permanent">
            <template #label>
              <div class="tab-label">
                <el-icon><FolderOpened /></el-icon>
                <span>常驻文件</span>
                <el-badge v-if="fileStats.permanent_files" :value="fileStats.permanent_files" class="tab-badge" />
              </div>
            </template>
            
            <div class="file-panel">
              <div class="panel-header">
                <div class="header-left">
                  <h2>
                    <el-icon><FolderOpened /></el-icon>
                    常驻文件管理
                  </h2>
                  <p>长期保存的重要文件，支持AI智能分类</p>
                </div>
                <div class="header-actions">
                  <el-button type="primary" @click="showUploadDialog = true" class="upload-btn">
                    <el-icon><Upload /></el-icon>
                    上传文件
                  </el-button>
                  <el-button @click="refreshFiles" class="refresh-btn">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </div>
              
              <!-- 搜索和筛选 -->
              <div class="search-section">
                <div class="search-bar">
                  <el-input
                    v-model="searchQuery"
                    placeholder="搜索文件名、描述、标签..."
                    @input="searchFiles"
                    class="search-input"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  
                  <el-select 
                    v-model="selectedCategory" 
                    placeholder="选择分类" 
                    @change="searchFiles"
                    class="category-select"
                  >
                    <el-option label="全部分类" value=""></el-option>
                    <el-option 
                      v-for="cat in aiCategories" 
                      :key="cat.code" 
                      :label="cat.name" 
                      :value="cat.code"
                    ></el-option>
                  </el-select>
                </div>
              </div>
              
              <!-- 文件列表 -->
              <div class="file-table-container">
                <el-table 
                  :data="permanentFiles" 
                  v-loading="filesLoading" 
                  class="file-table"
                  :header-cell-style="{ backgroundColor: '#f8fafc', color: '#475569', fontWeight: '600' }"
                >
                  <el-table-column prop="display_name" label="文件名" min-width="250">
                    <template #default="scope">
                      <div class="file-item">
                        <div class="file-icon-wrapper">
                          <i :class="getFileIcon(scope.row.file_type)"></i>
                        </div>
                        <div class="file-details">
                          <div class="file-name">{{ scope.row.display_name }}</div>
                          <div class="file-meta">
                            {{ scope.row.original_filename }}
                          </div>
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="category" label="分类" width="140">
                    <template #default="scope">
                      <el-tag v-if="scope.row.category" size="small" type="success" effect="light">
                        {{ getCategoryName(scope.row.category) }}
                      </el-tag>
                      <span v-else class="text-placeholder">未分类</span>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="tags" label="标签" width="200">
                    <template #default="scope">
                      <div class="tags-container">
                        <el-tag 
                          v-for="tag in (scope.row.tags || []).slice(0, 2)" 
                          :key="tag" 
                          size="small" 
                          type="info"
                          effect="light"
                          class="tag-item"
                        >
                          {{ tag }}
                        </el-tag>
                        <el-tooltip 
                          v-if="scope.row.tags && scope.row.tags.length > 2"
                          :content="scope.row.tags.slice(2).join(', ')"
                          placement="top"
                        >
                          <el-tag size="small" type="info" effect="light">
                            +{{ scope.row.tags.length - 2 }}
                          </el-tag>
                        </el-tooltip>
                        <span v-if="!scope.row.tags || scope.row.tags.length === 0" class="text-placeholder">
                          无标签
                        </span>
                      </div>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="file_size" label="大小" width="100">
                    <template #default="scope">
                      <span class="file-size">{{ formatFileSize(scope.row.file_size) }}</span>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="access_count" label="使用次数" width="100">
                    <template #default="scope">
                      <el-badge :value="scope.row.access_count || 0" type="info" />
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="created_at" label="创建时间" width="160">
                    <template #default="scope">
                      <div class="time-info">
                        <div class="date">{{ formatDate(scope.row.created_at) }}</div>
                      </div>
                    </template>
                  </el-table-column>
                  
                  <el-table-column label="操作" width="140" fixed="right">
                    <template #default="scope">
                      <div class="action-buttons">
                        <el-tooltip content="下载" placement="top">
                          <el-button size="mini" circle @click="downloadFile(scope.row)">
                            <el-icon><Download /></el-icon>
                          </el-button>
                        </el-tooltip>
                        
                        <el-tooltip content="AI分析" placement="top">
                          <el-button size="mini" type="warning" circle @click="analyzeDocument(scope.row.id)">
                            <el-icon><MagicStick /></el-icon>
                          </el-button>
                        </el-tooltip>
                        
                        <el-tooltip content="编辑" placement="top">
                          <el-button size="mini" type="primary" circle @click="editFile(scope.row)">
                            <el-icon><Edit /></el-icon>
                          </el-button>
                        </el-tooltip>
                        
                        <el-tooltip content="删除" placement="top">
                          <el-button size="mini" type="danger" circle @click="deleteFile(scope.row)">
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
                
                <!-- 分页 -->
                <div class="pagination-container">
                  <el-pagination
                    v-if="totalFiles > 0"
                    @current-change="handlePageChange"
                    :current-page="currentPage"
                    :page-size="pageSize"
                    :total="totalFiles"
                    layout="total, prev, pager, next, jumper"
                    background
                  />
                </div>
              </div>
            </div>
          </el-tab-pane>
          
          <el-tab-pane name="lawyer-certificates">
            <template #label>
              <div class="tab-label">
                <el-icon><User /></el-icon>
                <span>律师证管理</span>
                <el-badge v-if="lawyerStats.total_certificates" :value="lawyerStats.total_certificates" class="tab-badge" />
              </div>
            </template>
            
            <div class="lawyer-certificates-panel">
              <LawyerCertificatesPanel />
            </div>
          </el-tab-pane>
          
          <el-tab-pane name="temporary">
            <template #label>
              <div class="tab-label">
                <el-icon><Clock /></el-icon>
                <span>临时文件</span>
                <el-badge v-if="fileStats.temporary_files" :value="fileStats.temporary_files" class="tab-badge" />
              </div>
            </template>
            
            <div class="file-panel">
              <div class="panel-header">
                <div class="header-left">
                  <h2>
                    <el-icon><Clock /></el-icon>
                    临时文件管理
                  </h2>
                  <p>系统生成的临时文件，将定期自动清理</p>
                </div>
                <div class="header-actions">
                  <el-button @click="refreshFiles" class="refresh-btn">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </div>
              
              <div class="file-table-container">
                <el-table 
                  :data="temporaryFiles" 
                  v-loading="filesLoading" 
                  class="file-table"
                  :header-cell-style="{ backgroundColor: '#f8fafc', color: '#475569', fontWeight: '600' }"
                >
                  <el-table-column prop="display_name" label="文件名" min-width="250">
                    <template #default="scope">
                      <div class="file-item">
                        <div class="file-icon-wrapper">
                          <i :class="getFileIcon(scope.row.file_type)"></i>
                        </div>
                        <div class="file-details">
                          <div class="file-name">{{ scope.row.display_name }}</div>
                          <div class="file-meta">
                            <el-tag 
                              v-if="scope.row.file_category === 'temporary_upload'" 
                              size="small" 
                              type="warning"
                              effect="light"
                            >
                              上传文件
                            </el-tag>
                            <el-tag 
                              v-else-if="scope.row.file_category === 'temporary_generated'" 
                              size="small" 
                              type="info"
                              effect="light"
                            >
                              生成文件
                            </el-tag>
                          </div>
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="file_size" label="大小" width="100">
                    <template #default="scope">
                      <span class="file-size">{{ formatFileSize(scope.row.file_size) }}</span>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="expires_at" label="过期时间" width="180">
                    <template #default="scope">
                      <div class="expire-info">
                        <div :class="{ 'text-danger': scope.row.is_expired, 'text-warning': !scope.row.is_expired }">
                          {{ formatDate(scope.row.expires_at) }}
                        </div>
                        <div class="expire-rule">
                          {{ scope.row.file_category === 'temporary_upload' ? '30天自动清理' : '180天自动清理' }}
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                  
                  <el-table-column prop="created_at" label="创建时间" width="160">
                    <template #default="scope">
                      <div class="time-info">
                        <div class="date">{{ formatDate(scope.row.created_at) }}</div>
                      </div>
                    </template>
                  </el-table-column>
                  
                  <el-table-column label="操作" width="100" fixed="right">
                    <template #default="scope">
                      <div class="action-buttons">
                        <el-tooltip content="下载" placement="top">
                          <el-button size="mini" circle @click="downloadFile(scope.row)">
                            <el-icon><Download /></el-icon>
                          </el-button>
                        </el-tooltip>
                        
                        <el-tooltip content="删除" placement="top">
                          <el-button size="mini" type="danger" circle @click="deleteFile(scope.row)">
                            <el-icon><Delete /></el-icon>
                          </el-button>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog 
      v-model="showUploadDialog" 
      title="上传常驻文件" 
      width="600px"
      :close-on-click-modal="false"
      class="upload-dialog"
    >
      <el-form :model="uploadForm" label-width="100px" class="upload-form">
        <el-form-item label="显示名称" required>
          <el-input 
            v-model="uploadForm.display_name" 
            placeholder="请输入文件显示名称"
            :prefix-icon="Document"
          />
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select 
            v-model="uploadForm.category" 
            placeholder="可选择分类或使用AI自动分类" 
            style="width: 100%"
          >
            <el-option label="🤖 使用AI自动分类（推荐）" value=""></el-option>
            <el-option 
              v-for="cat in aiCategories" 
              :key="cat.code" 
              :label="`📁 ${cat.name}`" 
              :value="cat.code"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="uploadForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="文件描述（可选，有助于AI分类）"
          />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select 
            v-model="uploadForm.tags" 
            multiple 
            filterable 
            allow-create 
            placeholder="添加标签或让AI智能提取" 
            style="width: 100%"
          >
            <el-option 
              v-for="tag in commonTags" 
              :key="tag" 
              :label="tag" 
              :value="tag"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="AI功能">
          <div class="ai-options">
            <el-checkbox v-model="uploadForm.enableAiClassification" class="ai-checkbox">
              <div class="checkbox-content">
                <el-icon><MagicStick /></el-icon>
                <span>启用AI智能分类</span>
              </div>
            </el-checkbox>
            <el-checkbox v-model="uploadForm.enableVisionAnalysis" class="ai-checkbox">
              <div class="checkbox-content">
                <el-icon><View /></el-icon>
                <span>启用视觉内容分析</span>
              </div>
            </el-checkbox>
          </div>
        </el-form-item>
        
        <el-form-item label="文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            drag
            class="upload-area"
          >
            <div class="upload-content">
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">将文件拖到此处，或<em>点击上传</em></div>
              <div class="upload-tip">支持 PDF、Word、图片等格式，大小不超过200MB</div>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showUploadDialog = false" size="large">取消</el-button>
          <el-button 
            type="primary" 
            :loading="uploading" 
            @click="uploadFile" 
            size="large"
            class="upload-confirm-btn"
          >
            <el-icon><Upload /></el-icon>
            {{ uploading ? '正在上传...' : '开始上传' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 编辑文件对话框 -->
    <el-dialog 
      v-model="showEditDialog" 
      title="编辑文件信息" 
      width="600px"
      :close-on-click-modal="false"
      class="edit-dialog"
    >
      <el-form :model="editForm" label-width="100px" class="edit-form">
        <el-form-item label="显示名称" required>
          <el-input 
            v-model="editForm.display_name" 
            placeholder="请输入文件显示名称"
            :prefix-icon="Document"
          />
        </el-form-item>
        
        <el-form-item label="分类">
          <el-select 
            v-model="editForm.category" 
            placeholder="选择文件分类" 
            style="width: 100%"
            clearable
          >
            <el-option 
              v-for="cat in aiCategories" 
              :key="cat.code" 
              :label="cat.name" 
              :value="cat.code"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="editForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="文件描述"
          />
        </el-form-item>
        
        <el-form-item label="关键词">
          <el-input 
            v-model="editForm.keywords" 
            placeholder="关键词，用空格分隔"
          />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select 
            v-model="editForm.tags" 
            multiple 
            filterable 
            allow-create 
            placeholder="选择或创建标签" 
            style="width: 100%"
          >
            <el-option 
              v-for="tag in commonTags" 
              :key="tag" 
              :label="tag" 
              :value="tag"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="可见性">
          <el-switch 
            v-model="editForm.is_public"
            active-text="公开"
            inactive-text="私有"
          />
        </el-form-item>
        
        <el-form-item label="AI功能">
          <el-checkbox v-model="editForm.enable_ai_reanalysis" class="ai-checkbox">
            <div class="checkbox-content">
              <el-icon><MagicStick /></el-icon>
              <span>重新进行AI智能分析</span>
            </div>
          </el-checkbox>
          <div class="ai-tip">
            <el-text size="small" type="info">
              开启后将使用最新的AI模型重新分析文档内容和分类
            </el-text>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false" size="large">取消</el-button>
          <el-button 
            type="primary" 
            @click="saveFileEdit" 
            size="large"
            class="save-btn"
          >
            <el-icon><Check /></el-icon>
            保存更改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DataBoard, Document, FolderOpened, Clock, PieChart, TrendCharts, Check, Timer, DataAnalysis,
  Upload, Refresh, Search, Download, Edit, Delete, MagicStick, View, UploadFilled, User
} from '@element-plus/icons-vue'
import { apiService } from '@/services/api'
import LawyerCertificatesPanel from './LawyerCertificatesPanel.vue'

// 文件统计数据
const fileStats = ref({})

// 律师证统计数据
const lawyerStats = ref({})

// 标签页
const activeTab = ref('permanent')

// 文件列表
const permanentFiles = ref([])
const temporaryFiles = ref([])
const filesLoading = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalFiles = ref(0)

// 搜索和筛选
const searchQuery = ref('')
const selectedCategory = ref('')
// AI分类建议
const aiCategories = ref([])
const commonTags = ref([
  '业绩合同', '荣誉奖项', '资质证明文件', '其他杂项',
  '公司法律服务', '金融法律服务', '争议解决', '专业法律领域',
  '基础设施与能源', '房地产与土地', '国际贸易与海事',
  '劳动与社会保障', '税务与财务', '新兴业务领域',
  '政府与公共事务', '跨境业务', '特殊行业'
])

// 上传对话框
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadRef = ref()
const uploadForm = ref({
  display_name: '',
  category: '',
  description: '',
  tags: [],
  keywords: '',
  file: null,
  enableAiClassification: true,
  enableVisionAnalysis: true
})

// 获取文件统计
const fetchFileStats = async () => {
  try {
    const response = await apiService.get('/files/stats')
    const data = response?.data || response
    if (data && data.success) {
      fileStats.value = data.stats
    } else {
      ElMessage.error('获取文件统计失败')
    }
  } catch (error) {
    console.error('获取文件统计失败:', error)
    ElMessage.error('获取文件统计失败')
  }
}

// 获取律师证统计
const fetchLawyerStats = async () => {
  try {
    const response = await apiService.get('/lawyer-certificates/stats')
    const data = response?.data || response
    if (data && data.success) {
      lawyerStats.value = data.stats
    }
  } catch (error) {
    console.error('获取律师证统计失败:', error)
  }
}

// 获取文件列表
const fetchFiles = async (category = '') => {
  filesLoading.value = true
  try {
    const params = {
      file_category: category,
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }
    
    const response = await apiService.get('/files/list', { params })
    const data = response?.data || response
    if (data && data.success) {
      if (category === 'permanent') {
        permanentFiles.value = data.files
      } else {
        // 所有非permanent的都归为临时文件
        temporaryFiles.value = data.files
      }
      totalFiles.value = data.pagination.total
    } else {
      ElMessage.error('获取文件列表失败')
    }
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('获取文件列表失败')
  } finally {
    filesLoading.value = false
  }
}

// 刷新文件列表
const refreshFiles = async () => {
  await fetchFileStats()
  if (activeTab.value === 'permanent') {
    await fetchFiles('permanent')
  } else if (activeTab.value === 'temporary') {
    // 获取所有临时文件（包括上传的和生成的）
    await fetchFiles('temporary')
  }
}

// 搜索文件
const searchFiles = () => {
  currentPage.value = 1
  if (activeTab.value === 'permanent') {
    fetchFiles('permanent')
  } else if (activeTab.value === 'temporary') {
    fetchFiles('temporary')
  }
}

// 分页处理
const handlePageChange = (page) => {
  currentPage.value = page
  if (activeTab.value === 'permanent') {
    fetchFiles('permanent')
  } else if (activeTab.value === 'temporary') {
    fetchFiles('temporary')
  }
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

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取分类名称
const getCategoryName = (categoryCode) => {
  const category = aiCategories.value.find(cat => cat.code === categoryCode)
  return category ? category.name : categoryCode
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '无'
  try {
    const date = new Date(dateStr)
    // 检查日期是否有效
    if (isNaN(date.getTime())) return '无效日期'
    
    // 格式化为本地时间
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    console.error('日期格式化失败:', error)
    return '格式错误'
  }
}

// 下载文件
const downloadFile = (file) => {
  const url = `/api/files/${file.id}/download`
  window.open(url, '_blank')
  ElMessage.success('开始下载文件')
}

// 编辑文件
const showEditDialog = ref(false)
const editingFile = ref(null)
const editForm = ref({
  display_name: '',
  category: '',
  description: '',
  tags: [],
  keywords: '',
  is_public: true,
  enable_ai_reanalysis: false
})

const editFile = (file) => {
  editingFile.value = file
  editForm.value = {
    display_name: file.display_name,
    category: file.category || '',
    description: file.description || '',
    tags: file.tags || [],
    keywords: file.keywords || '',
    is_public: file.is_public,
    enable_ai_reanalysis: false
  }
  showEditDialog.value = true
}

// 删除文件
const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${file.display_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await apiService.delete(`/files/${file.id}`)
    if (response.data.success) {
      ElMessage.success('文件删除成功')
      refreshFiles()
    } else {
      ElMessage.error(response.data.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error)
      ElMessage.error('删除文件失败')
    }
  }
}

// 处理文件选择
const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
  if (!uploadForm.value.display_name) {
    uploadForm.value.display_name = file.name
  }
}

// 上传文件
const uploadFile = async () => {
  if (!uploadForm.value.file) {
    ElMessage.error('请选择文件')
    return
  }
  
  if (!uploadForm.value.display_name) {
    ElMessage.error('请输入显示名称')
    return
  }
  
  uploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('display_name', uploadForm.value.display_name)
    formData.append('category', uploadForm.value.category || '')
    formData.append('description', uploadForm.value.description || '')
    formData.append('tags', JSON.stringify(uploadForm.value.tags))
    formData.append('keywords', uploadForm.value.keywords || '')
    formData.append('is_public', 'true')
    formData.append('enable_ai_classification', uploadForm.value.enableAiClassification)
    formData.append('enable_vision_analysis', uploadForm.value.enableVisionAnalysis)
    
    const response = await apiService.post('/files/upload/permanent', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.success) {
      let message = '文件上传成功'
      
      // 显示AI分类结果
      if (response.data.ai_classification) {
        const classification = response.data.ai_classification
        message += `\nAI分类: ${classification.category_name || classification.category}`
        if (classification.business_field) {
          message += `\n业务领域: ${classification.business_field}`
        }
        if (classification.confidence) {
          message += `\n置信度: ${Math.round(classification.confidence * 100)}%`
        }
      }
      
      ElMessage.success(message)
      showUploadDialog.value = false
      resetUploadForm()
      refreshFiles()
    } else {
      ElMessage.error(response.data.message || '上传失败')
    }
  } catch (error) {
    console.error('上传文件失败:', error)
    ElMessage.error('上传文件失败')
  } finally {
    uploading.value = false
  }
}

// 加载分类选项
const loadCategoryOptions = async () => {
  try {
    const response = await apiService.get('/files/categories/suggestions')
    const data = response?.data || response
    if (data && data.success) {
      aiCategories.value = data.categories
      // 合并业务领域到通用标签
      if (data.business_fields) {
        commonTags.value = [...commonTags.value, ...data.business_fields]
      }
    } else {
      ElMessage.error('加载分类选项失败')
    }
  } catch (error) {
    console.error('加载分类选项失败:', error)
    ElMessage.error('加载分类选项失败')
  }
}

// AI分析文档
const analyzeDocument = async (fileId, enableVision = true) => {
  try {
    ElMessage.info('正在进行AI分析，请稍候...')
    
    const response = await apiService.post('/files/analyze-document', null, {
      params: {
        file_id: fileId,
        enable_vision: enableVision,
        force_reanalyze: true
      }
    })
    
    const data = response?.data || response
    if (data && data.success) {
      const classification = data.classification
      let message = 'AI分析完成'
      
      if (classification) {
        message += `\n分类: ${classification.category_name || classification.category}`
        if (classification.business_field) {
          message += `\n业务领域: ${classification.business_field}`
        }
        if (classification.confidence) {
          message += `\n置信度: ${Math.round(classification.confidence * 100)}%`
        }
      }
      
      ElMessage.success(message)
      refreshFiles() // 刷新文件列表
    } else {
      ElMessage.error(data?.message || 'AI分析失败')
    }
  } catch (error) {
    console.error('AI分析失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || 'AI分析失败'
    ElMessage.error(errorMsg)
  }
}

// 保存文件编辑
const saveFileEdit = async () => {
  if (!editingFile.value) return
  
  try {
    const formData = new FormData()
    formData.append('display_name', editForm.value.display_name || '')
    formData.append('category', editForm.value.category || '')
    formData.append('description', editForm.value.description || '')
    formData.append('tags', JSON.stringify(editForm.value.tags || []))
    formData.append('keywords', editForm.value.keywords || '')
    formData.append('is_public', editForm.value.is_public ? 'true' : 'false')
    formData.append('enable_ai_reanalysis', editForm.value.enable_ai_reanalysis ? 'true' : 'false')
    
    const response = await apiService.put(`/files/${editingFile.value.id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    const data = response?.data || response
    if (data && data.success) {
      let message = '文件信息更新成功'
      
      // 显示AI分析结果
      if (editForm.value.enable_ai_reanalysis && data.ai_analysis) {
        const classification = data.ai_analysis
        message += `\nAI重新分析: ${classification.category_name || classification.category}`
        if (classification.confidence) {
          message += `\n置信度: ${Math.round(classification.confidence * 100)}%`
        }
      }
      
      ElMessage({
        type: 'success',
        message: message,
        duration: 3000
      })
      showEditDialog.value = false
      refreshFiles()
    } else {
      ElMessage.error(data?.message || '更新失败')
    }
  } catch (error) {
    console.error('更新文件信息失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '更新文件信息失败'
    ElMessage.error(errorMsg)
  }
}

// 重置上传表单
const resetUploadForm = () => {
  uploadForm.value = {
    display_name: '',
    category: '',
    description: '',
    tags: [],
    keywords: '',
    file: null,
    enableAiClassification: true,
    enableVisionAnalysis: true
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

onMounted(async () => {
  await fetchFileStats()
  await fetchLawyerStats()
  await fetchFiles('permanent')
  await loadCategoryOptions()
})

// 监听标签页变化
const handleTabChange = (tab) => {
  activeTab.value = tab
  currentPage.value = 1
  searchQuery.value = ''
  selectedCategory.value = ''
  
  if (tab === 'permanent') {
    fetchFiles('permanent')
  } else if (tab === 'temporary') {
    fetchFiles('temporary')
  }
}
</script>

<style lang="scss" scoped>
// 页面整体布局
.data-management-page {
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
    rgba(59, 130, 246, 0.8) 0%, 
    rgba(139, 92, 246, 0.8) 50%, 
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

// 统计卡片网格
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 0, 0, 0.06);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }
  
  .card-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    .el-icon {
      font-size: 32px;
      color: white;
    }
  }
  
  .card-content {
    flex: 1;
    
    h3 {
      margin: 0 0 8px 0;
      font-size: 14px;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .stat-number {
      font-size: 32px;
      font-weight: 700;
      line-height: 1;
      color: #1e293b;
      margin-bottom: 8px;
    }
    
    .stat-change {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      color: #64748b;
      
      .el-icon {
        font-size: 16px;
      }
    }
  }
  
  &.total-files .card-icon {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  }
  
  &.permanent-files .card-icon {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  }
  
  &.temporary-files .card-icon {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  }
  
  &.storage-size .card-icon {
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  }
}

// 文件管理区域
.file-management-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.custom-tabs {
  :deep(.el-tabs__header) {
    margin: 0;
    background: #f8fafc;
    padding: 0 24px;
    border-bottom: 1px solid #e2e8f0;
  }
  
  :deep(.el-tabs__nav-wrap) {
    &::after {
      display: none;
    }
  }
  
  :deep(.el-tabs__item) {
    padding: 16px 24px;
    font-size: 15px;
    font-weight: 500;
    color: #64748b;
    
    &.is-active {
      color: #3b82f6;
      background: white;
      border-radius: 12px 12px 0 0;
    }
  }
  
  .tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .el-icon {
      font-size: 18px;
    }
    
    .tab-badge {
      margin-left: 8px;
    }
  }
}

// 文件面板
.file-panel {
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left {
    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 700;
      color: #1e293b;
      display: flex;
      align-items: center;
      gap: 12px;
      
      .el-icon {
        font-size: 28px;
        color: #3b82f6;
      }
    }
    
    p {
      margin: 0;
      color: #64748b;
      font-size: 16px;
    }
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
    
    .upload-btn {
      background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      border: none;
      
      .el-icon {
        margin-right: 8px;
      }
    }
    
    .refresh-btn {
      border: 1px solid #e2e8f0;
      
      .el-icon {
        margin-right: 8px;
      }
    }
  }
}

// 搜索区域
.search-section {
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  gap: 16px;
  align-items: center;
  
  .search-input {
    min-width: 320px;
    
    :deep(.el-input__wrapper) {
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
  }
  
  .category-select {
    min-width: 200px;
    
    :deep(.el-select__wrapper) {
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }
  }
}

// 文件表格
.file-table-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.file-table {
  :deep(.el-table__header) {
    th {
      background-color: #f8fafc !important;
      color: #475569 !important;
      font-weight: 600 !important;
      border-bottom: 1px solid #e2e8f0;
    }
  }
  
  :deep(.el-table__body) {
    tr {
      &:hover {
        background-color: #f8fafc;
      }
    }
    
    td {
      border-bottom: 1px solid #f1f5f9;
      padding: 16px 12px;
    }
  }
}

// 文件项目
.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .file-icon-wrapper {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: #f1f5f9;
    display: flex;
    align-items: center;
    justify-content: center;
    
    i {
      font-size: 20px;
    }
  }
  
  .file-details {
    flex: 1;
    
    .file-name {
      font-weight: 600;
      color: #1e293b;
      margin-bottom: 4px;
    }
    
    .file-meta {
      font-size: 13px;
      color: #64748b;
    }
  }
}

// 标签容器
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  
  .tag-item {
    margin: 0;
  }
}

// 文件大小
.file-size {
  font-weight: 500;
  color: #475569;
}

// 时间信息
.time-info {
  .date {
    font-size: 14px;
    color: #475569;
  }
}

// 过期信息
.expire-info {
  .text-danger {
    color: #ef4444;
    font-weight: 600;
  }
  
  .text-warning {
    color: #f59e0b;
    font-weight: 500;
  }
  
  .expire-rule {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
  }
}

// 占位符文本
.text-placeholder {
  color: #9ca3af;
  font-style: italic;
}

// 操作按钮
.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
  
  .el-button {
    border-radius: 6px;
    
    &.is-circle {
      width: 28px;
      height: 28px;
      padding: 0;
      
      .el-icon {
        font-size: 14px;
      }
    }
  }
}

// 分页容器
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px 0 0 0;
  border-top: 1px solid #f1f5f9;
  margin-top: 24px;
}

// 上传对话框
.upload-dialog {
  :deep(.el-dialog) {
    border-radius: 16px;
    overflow: hidden;
  }
  
  :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    color: white;
    padding: 24px;
    
    .el-dialog__title {
      color: white;
      font-size: 20px;
      font-weight: 600;
    }
  }
  
  :deep(.el-dialog__body) {
    padding: 24px;
  }
}

.upload-form {
  :deep(.el-form-item__label) {
    font-weight: 600;
    color: #374151;
  }
  
  :deep(.el-input__wrapper) {
    border-radius: 8px;
  }
  
  :deep(.el-select__wrapper) {
    border-radius: 8px;
  }
  
  :deep(.el-textarea__inner) {
    border-radius: 8px;
  }
}

.ai-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .ai-checkbox {
    :deep(.el-checkbox__label) {
      .checkbox-content {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .el-icon {
          color: #3b82f6;
        }
      }
    }
  }
}

.upload-area {
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    border-radius: 12px;
    border: 2px dashed #d1d5db;
    background: #f9fafb;
    padding: 40px 20px;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: #3b82f6;
      background: #eff6ff;
    }
  }
  
  .upload-content {
    text-align: center;
    
    .upload-icon {
      font-size: 48px;
      color: #9ca3af;
      margin-bottom: 16px;
    }
    
    .upload-text {
      font-size: 16px;
      color: #374151;
      margin-bottom: 8px;
      
      em {
        color: #3b82f6;
        font-style: normal;
      }
    }
    
    .upload-tip {
      font-size: 14px;
      color: #6b7280;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0 0 0;
  border-top: 1px solid #f1f5f9;
  
  .upload-confirm-btn {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    border: none;
    
    .el-icon {
      margin-right: 8px;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .page-hero {
    flex-direction: column;
    text-align: center;
    gap: 24px;
    
    .hero-stats {
      gap: 20px;
    }
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .panel-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    
    .header-actions {
      justify-content: flex-start;
    }
  }
  
  .search-bar {
    flex-direction: column;
    align-items: stretch;
    
    .search-input,
    .category-select {
      min-width: auto;
    }
  }
  
  .action-buttons {
    flex-wrap: wrap;
  }
}

// 编辑对话框样式
.edit-dialog {
  .edit-form {
    .el-form-item {
      margin-bottom: 20px;
    }
    
    .ai-checkbox {
      .checkbox-content {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .el-icon {
          color: var(--el-color-primary);
        }
      }
    }
    
    .ai-tip {
      margin-top: 8px;
      padding-left: 24px;
    }
  }
  
  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    
    .save-btn {
      background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
      border: none;
      
      &:hover {
        background: linear-gradient(135deg, var(--el-color-primary-dark-2) 0%, var(--el-color-primary) 100%);
      }
    }
  }
}
</style>