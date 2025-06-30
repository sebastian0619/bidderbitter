<template>
  <div class="performance-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <div class="header-left">
        <h2>
          <el-icon><TrendCharts /></el-icon>
          业绩管理
        </h2>
        <p>管理法律服务业绩案例，支持AI智能解析业务领域</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showUploadDialog = true" class="upload-btn">
          <el-icon><Upload /></el-icon>
          上传业绩文件
        </el-button>
        <el-button @click="showCreateDialog = true" class="create-btn">
          <el-icon><Plus /></el-icon>
          手动创建
        </el-button>
        <el-button @click="refreshPerformances" class="refresh-btn">
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
          placeholder="搜索项目名称、客户名称、业务领域..."
          @input="searchPerformances"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select 
          v-model="selectedBusinessField" 
          placeholder="选择业务领域" 
          @change="searchPerformances"
          class="field-select"
          clearable
        >
          <el-option 
            v-for="field in businessFields" 
            :key="field" 
            :label="field" 
            :value="field"
          ></el-option>
        </el-select>

        <el-select 
          v-model="selectedYear" 
          placeholder="选择年份" 
          @change="searchPerformances"
          class="year-select"
          clearable
        >
          <el-option 
            v-for="year in availableYears" 
            :key="year" 
            :label="year" 
            :value="year"
          ></el-option>
        </el-select>
      </div>
    </div>

    <!-- 业绩列表 -->
    <div class="performance-table-container">
      <el-table 
        :data="performances" 
        v-loading="performancesLoading" 
        class="performance-table"
        :header-cell-style="{ backgroundColor: '#f8fafc', color: '#475569', fontWeight: '600' }"
      >
        <el-table-column prop="project_name" label="项目名称" min-width="200">
          <template #default="scope">
            <div class="project-info">
              <div class="project-name">{{ scope.row.project_name }}</div>
              <div class="project-type">
                <el-tag size="small" :type="scope.row.project_type === '长期顾问' ? 'success' : 'warning'">
                  {{ scope.row.project_type }}
                </el-tag>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="client_name" label="客户名称" min-width="150">
          <template #default="scope">
            <div class="client-name">{{ scope.row.client_name }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="business_field" label="业务领域" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.business_field" size="small" type="info" effect="light">
              {{ scope.row.business_field }}
            </el-tag>
            <span v-else class="text-placeholder">未分类</span>
          </template>
        </el-table-column>

        <el-table-column prop="year" label="年份" width="80">
          <template #default="scope">
            <span class="year-info">{{ scope.row.year }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="contract_amount" label="合同金额" width="120">
          <template #default="scope">
            <div class="amount-info" v-if="scope.row.contract_amount">
              <span class="amount">{{ formatAmount(scope.row.contract_amount, scope.row.currency) }}</span>
            </div>
            <span v-else class="text-placeholder">未填写</span>
          </template>
        </el-table-column>

        <el-table-column prop="confidence_score" label="AI置信度" width="100">
          <template #default="scope">
            <div class="confidence-info" v-if="scope.row.confidence_score">
              <el-progress 
                :percentage="Math.round(scope.row.confidence_score * 100)" 
                :color="getConfidenceColor(scope.row.confidence_score)"
                :stroke-width="6"
                text-inside
              />
            </div>
            <el-tag v-else-if="scope.row.is_manual_input" size="small" type="success">
              手动录入
            </el-tag>
            <span v-else class="text-placeholder">未分析</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_verified" label="验证状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_verified ? 'success' : 'warning'" size="small">
              {{ scope.row.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
              <el-tooltip content="查看详情" placement="top">
                <el-button size="mini" circle @click="viewPerformance(scope.row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="AI重新分析" placement="top" v-if="scope.row.source_document">
                <el-button size="mini" type="warning" circle @click="reanalyzePerformance(scope.row)">
                  <el-icon><MagicStick /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="编辑" placement="top">
                <el-button size="mini" type="primary" circle @click="editPerformance(scope.row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="验证" placement="top" v-if="!scope.row.is_verified">
                <el-button size="mini" type="success" circle @click="verifyPerformance(scope.row)">
                  <el-icon><Check /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="删除" placement="top">
                <el-button size="mini" type="danger" circle @click="deletePerformance(scope.row)">
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
          v-if="totalPerformances > 0"
          @current-change="handlePageChange"
          :current-page="currentPage"
          :page-size="pageSize"
          :total="totalPerformances"
          layout="total, prev, pager, next, jumper"
          background
        />
      </div>
    </div>

    <!-- 上传文件对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传业绩文件" width="600px" class="upload-dialog">
      <el-form :model="uploadForm" label-width="120px" class="upload-form">
        <el-form-item label="文件选择" required>
          <el-upload
            ref="uploadRef"
            :file-list="uploadForm.fileList"
            :auto-upload="false"
            multiple
            :limit="10"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.bmp,.gif,.tiff"
            @change="handleFileChange"
            @exceed="handleExceed"
          >
            <template #trigger>
              <el-button type="primary">
                <el-icon><Upload /></el-icon>
                选择文件
              </el-button>
            </template>
            <div class="upload-tip">
              <el-icon><InfoFilled /></el-icon>
              <span>支持 PDF、Word 文档和图片格式，最多上传 10 个文件</span>
            </div>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="项目名称">
          <el-input 
            v-model="uploadForm.project_name" 
            placeholder="可选，AI将自动识别"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="客户名称">
          <el-input 
            v-model="uploadForm.client_name" 
            placeholder="可选，AI将自动识别"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="业务领域">
          <el-select 
            v-model="uploadForm.business_field" 
            placeholder="可选，AI将自动识别"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="field in businessFields"
              :key="field"
              :label="field"
              :value="field"
            />
          </el-select>
        </el-form-item>
        
        <el-divider content-position="left">AI分析设置</el-divider>
        
        <el-form-item label="AI文本分析">
          <el-switch 
            v-model="uploadForm.enableAiAnalysis" 
            active-text="启用"
            inactive-text="关闭"
          />
          <div class="form-tip">自动提取项目信息、客户名称等关键数据</div>
        </el-form-item>
        
        <el-form-item label="AI视觉分析">
          <el-switch 
            v-model="uploadForm.enableVisionAnalysis" 
            active-text="启用"
            inactive-text="关闭"
          />
          <div class="form-tip">识别图片中的文字信息和表格数据</div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="resetUploadDialog">取消</el-button>
          <el-button 
            type="primary" 
            @click="uploadPerformanceFiles"
            :loading="uploading"
            :disabled="uploadForm.fileList.length === 0"
          >
            <el-icon><UploadFilled /></el-icon>
            开始上传
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 手动创建业绩对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="手动创建业绩记录" 
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="createForm" label-width="120px" :rules="createRules" ref="createFormRef">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目名称" prop="project_name">
              <el-input v-model="createForm.project_name" placeholder="请输入项目名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="客户名称" prop="client_name">
              <el-input v-model="createForm.client_name" placeholder="请输入客户名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目类型" prop="project_type">
              <el-select v-model="createForm.project_type" placeholder="选择项目类型">
                <el-option label="长期顾问" value="长期顾问" />
                <el-option label="重大个案" value="重大个案" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业务领域" prop="business_field">
              <el-select v-model="createForm.business_field" placeholder="选择业务领域">
                <el-option 
                  v-for="field in businessFields" 
                  :key="field" 
                  :label="field" 
                  :value="field"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="年份" prop="year">
              <el-date-picker
                v-model="createForm.year"
                type="year"
                placeholder="选择年份"
                format="YYYY"
                value-format="YYYY"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="合同金额">
              <el-input v-model.number="createForm.contract_amount" placeholder="金额" type="number" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="货币单位">
              <el-select v-model="createForm.currency" placeholder="币种">
                <el-option label="人民币" value="CNY" />
                <el-option label="美元" value="USD" />
                <el-option label="港币" value="HKD" />
                <el-option label="欧元" value="EUR" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="createForm.start_date"
                type="date"
                placeholder="选择开始时间"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="createForm.end_date"
                type="date"
                placeholder="选择结束时间"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="项目描述">
          <el-input 
            v-model="createForm.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" :loading="creating" @click="createPerformance">
            {{ creating ? '正在创建...' : '创建业绩' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 业绩详情对话框 -->
    <el-dialog 
      v-model="showDetailDialog" 
      title="业绩详情" 
      width="800px"
    >
      <div v-if="selectedPerformance" class="performance-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="项目名称">
            {{ selectedPerformance.project_name }}
          </el-descriptions-item>
          <el-descriptions-item label="客户名称">
            {{ selectedPerformance.client_name }}
          </el-descriptions-item>
          <el-descriptions-item label="项目类型">
            <el-tag :type="selectedPerformance.project_type === '长期顾问' ? 'success' : 'warning'">
              {{ selectedPerformance.project_type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="业务领域">
            <el-tag type="info">{{ selectedPerformance.business_field }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="年份">
            {{ selectedPerformance.year }}
          </el-descriptions-item>
          <el-descriptions-item label="合同金额">
            {{ formatAmount(selectedPerformance.contract_amount, selectedPerformance.currency) }}
          </el-descriptions-item>
          <el-descriptions-item label="项目周期" span="2">
            {{ formatDateRange(selectedPerformance.start_date, selectedPerformance.end_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="验证状态">
            <el-tag :type="selectedPerformance.is_verified ? 'success' : 'warning'">
              {{ selectedPerformance.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="AI置信度">
            <div v-if="selectedPerformance.confidence_score">
              {{ Math.round(selectedPerformance.confidence_score * 100) }}%
            </div>
            <el-tag v-else-if="selectedPerformance.is_manual_input" type="success">手动录入</el-tag>
            <span v-else>未分析</span>
          </el-descriptions-item>
          <el-descriptions-item label="项目描述" span="2">
            {{ selectedPerformance.description || '暂无描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- AI分析结果 -->
        <div v-if="selectedPerformance.ai_analysis" class="ai-analysis-section">
          <h4>AI分析结果</h4>
          <el-collapse>
            <el-collapse-item title="详细分析数据" name="ai-data">
              <pre>{{ JSON.stringify(selectedPerformance.ai_analysis, null, 2) }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button type="primary" @click="editPerformance(selectedPerformance)">编辑</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  TrendCharts, Upload, Plus, Refresh, Search, View, MagicStick, Edit, Check, Delete, UploadFilled, InfoFilled
} from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

// 响应式数据
const performances = ref([])
const performancesLoading = ref(false)
const businessFields = ref([])

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalPerformances = ref(0)

// 搜索筛选
const searchQuery = ref('')
const selectedBusinessField = ref('')
const selectedYear = ref('')

// 对话框状态
const showUploadDialog = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedPerformance = ref(null)

// 加载状态
const uploading = ref(false)
const creating = ref(false)

// 表单数据
const uploadForm = reactive({
  fileList: [],
  project_name: '',
  client_name: '',
  business_field: '',
  enableAiAnalysis: true,
  enableVisionAnalysis: true
})

const createForm = reactive({
  project_name: '',
  client_name: '',
  project_type: '',
  business_field: '',
  year: new Date().getFullYear().toString(),
  contract_amount: null,
  currency: 'CNY',
  start_date: '',
  end_date: '',
  description: ''
})

// 表单验证规则
const createRules = {
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  client_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  project_type: [{ required: true, message: '请选择项目类型', trigger: 'change' }],
  business_field: [{ required: true, message: '请选择业务领域', trigger: 'change' }],
  year: [{ required: true, message: '请选择年份', trigger: 'change' }]
}

// 计算属性
const availableYears = computed(() => {
  const years = []
  const currentYear = new Date().getFullYear()
  for (let i = currentYear; i >= currentYear - 10; i--) {
    years.push(i.toString())
  }
  return years
})

// 方法
const refreshPerformances = async () => {
  await fetchPerformances()
}

const fetchPerformances = async () => {
  performancesLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    if (selectedBusinessField.value) {
      params.business_field = selectedBusinessField.value
    }
    if (selectedYear.value) {
      params.year = selectedYear.value
    }
    
    const response = await apiService.get('/performances/list', { params })
    const data = response?.data || response
    if (data && data.success) {
      performances.value = data.performances
      totalPerformances.value = data.pagination.total
    }
  } catch (error) {
    console.error('获取业绩列表失败:', error)
    ElMessage.error('获取业绩列表失败')
  } finally {
    performancesLoading.value = false
  }
}

const loadBusinessFields = async () => {
  try {
    const response = await apiService.get('/config/business-fields')
    const data = response?.data || response
    if (data && data.success) {
      businessFields.value = data.business_fields.map(field => field.name)
    }
  } catch (error) {
    console.error('加载业务领域失败:', error)
  }
}

const searchPerformances = () => {
  currentPage.value = 1
  fetchPerformances()
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchPerformances()
}

const handleFileChange = (file) => {
  uploadForm.fileList.push(file.raw)
}

const handleExceed = (files) => {
  ElMessage.warning(`最多只能上传 ${files.length} 个文件`)
}

const uploadPerformanceFiles = async () => {
  if (uploadForm.fileList.length === 0) {
    ElMessage.error('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    uploadForm.fileList.forEach(file => {
      formData.append('files', file)
    })
    formData.append('project_name', uploadForm.project_name || '')
    formData.append('client_name', uploadForm.client_name || '')
    formData.append('business_field', uploadForm.business_field || '')
    formData.append('enable_ai_analysis', uploadForm.enableAiAnalysis)
    formData.append('enable_vision_analysis', uploadForm.enableVisionAnalysis)
    
    const response = await apiService.post('/performances/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    const data = response?.data || response
    if (data && data.success) {
      ElMessage.success('业绩文件上传成功')
      showUploadDialog.value = false
      resetUploadForm()
      refreshPerformances()
    } else {
      ElMessage.error(data?.message || '上传失败')
    }
  } catch (error) {
    console.error('上传业绩文件失败:', error)
    ElMessage.error('上传业绩文件失败')
  } finally {
    uploading.value = false
  }
}

const createPerformance = async () => {
  const createFormRef = ref()
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
  } catch {
    return
  }
  
  creating.value = true
  try {
    const response = await apiService.post('/performances/create', {
      ...createForm,
      is_manual_input: true
    })
    
    const data = response?.data || response
    if (data && data.success) {
      ElMessage.success('业绩记录创建成功')
      showCreateDialog.value = false
      resetCreateForm()
      refreshPerformances()
    } else {
      ElMessage.error(data?.message || '创建失败')
    }
  } catch (error) {
    console.error('创建业绩记录失败:', error)
    ElMessage.error('创建业绩记录失败')
  } finally {
    creating.value = false
  }
}

const viewPerformance = (performance) => {
  selectedPerformance.value = performance
  showDetailDialog.value = true
}

const editPerformance = (performance) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中')
}

const verifyPerformance = async (performance) => {
  try {
    const response = await apiService.patch(`/performances/${performance.id}/verify`)
    const data = response?.data || response
    if (data && data.success) {
      ElMessage.success('业绩已验证')
      refreshPerformances()
    }
  } catch (error) {
    console.error('验证业绩失败:', error)
    ElMessage.error('验证业绩失败')
  }
}

const reanalyzePerformance = async (performance) => {
  try {
    ElMessage.info('正在重新分析业绩文件...')
    const response = await apiService.post(`/performances/${performance.id}/reanalyze`)
    const data = response?.data || response
    if (data && data.success) {
      ElMessage.success('重新分析完成')
      refreshPerformances()
    }
  } catch (error) {
    console.error('重新分析失败:', error)
    ElMessage.error('重新分析失败')
  }
}

const deletePerformance = async (performance) => {
  try {
    await ElMessageBox.confirm('确定要删除这条业绩记录吗？', '确认删除', {
      type: 'warning'
    })
    
    const response = await apiService.deletePerformance(performance.id)
    const data = response?.data || response
    if (data && data.success) {
      ElMessage.success('业绩记录已删除')
      refreshPerformances()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除业绩记录失败:', error)
      ElMessage.error('删除业绩记录失败')
    }
  }
}

const resetUploadForm = () => {
  Object.assign(uploadForm, {
    fileList: [],
    project_name: '',
    client_name: '',
    business_field: '',
    enableAiAnalysis: true,
    enableVisionAnalysis: true
  })
}

const resetUploadDialog = () => {
  showUploadDialog.value = false
  resetUploadForm()
  // 清空文件列表
  const uploadRef = ref()
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    project_name: '',
    client_name: '',
    project_type: '',
    business_field: '',
    year: new Date().getFullYear().toString(),
    contract_amount: null,
    currency: 'CNY',
    start_date: '',
    end_date: '',
    description: ''
  })
}

// 工具函数
const formatAmount = (amount, currency = 'CNY') => {
  if (!amount) return '未填写'
  const currencySymbols = {
    CNY: '¥',
    USD: '$',
    HKD: 'HK$',
    EUR: '€'
  }
  return `${currencySymbols[currency] || currency} ${amount.toLocaleString()}`
}

const formatDateRange = (startDate, endDate) => {
  if (!startDate && !endDate) return '未填写'
  if (!startDate) return `至 ${endDate}`
  if (!endDate) return `${startDate} 至今`
  return `${startDate} 至 ${endDate}`
}

const getConfidenceColor = (score) => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

// 组件挂载
onMounted(async () => {
  await loadBusinessFields()
  await fetchPerformances()
})
</script>

<style lang="scss" scoped>
.performance-panel {
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
    }
    
    .create-btn {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      border: none;
      color: white;
    }
    
    .refresh-btn {
      border: 1px solid #e2e8f0;
    }
  }
}

.search-section {
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  gap: 16px;
  align-items: center;
  
  .search-input {
    min-width: 320px;
  }
  
  .field-select,
  .year-select {
    min-width: 150px;
  }
}

.performance-table-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.performance-table {
  :deep(.el-table__header) {
    th {
      background-color: #f8fafc !important;
      color: #475569 !important;
      font-weight: 600 !important;
      border-bottom: 1px solid #e2e8f0;
    }
  }
}

.project-info {
  .project-name {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 4px;
  }
}

.client-name {
  font-weight: 500;
  color: #475569;
}

.year-info {
  font-weight: 500;
  color: #475569;
}

.amount-info {
  .amount {
    font-weight: 600;
    color: #059669;
  }
}

.confidence-info {
  width: 80px;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
  
  .el-button.is-circle {
    width: 28px;
    height: 28px;
    padding: 0;
  }
}

.pagination-container {
  padding: 20px;
  display: flex;
  justify-content: center;
  background: #f8fafc;
}

.upload-area {
  width: 100%;
  
  :deep(.el-upload) {
    width: 100%;
  }
  
  :deep(.el-upload-dragger) {
    width: 100%;
    height: 120px;
    border: 2px dashed #d1d5db;
    border-radius: 8px;
    background: #f9fafb;
    
    &:hover {
      border-color: #3b82f6;
    }
  }
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  
  .upload-icon {
    font-size: 40px;
    color: #9ca3af;
    margin-bottom: 8px;
  }
  
  .upload-text {
    font-size: 14px;
    color: #6b7280;
    margin-bottom: 4px;
    
    em {
      color: #3b82f6;
      font-style: normal;
    }
  }
  
  .upload-tip {
    font-size: 12px;
    color: #9ca3af;
  }
}

.performance-detail {
  .ai-analysis-section {
    margin-top: 24px;
    
    h4 {
      margin-bottom: 16px;
      color: #1e293b;
    }
    
    pre {
      background: #f1f5f9;
      padding: 16px;
      border-radius: 8px;
      font-size: 12px;
      max-height: 200px;
      overflow-y: auto;
    }
  }
}

.text-placeholder {
  color: #9ca3af;
  font-style: italic;
}

.upload-dialog {
  .upload-form {
    padding: 20px;
  }

  .form-tip {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 8px;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  padding: 20px;
}
</style> 