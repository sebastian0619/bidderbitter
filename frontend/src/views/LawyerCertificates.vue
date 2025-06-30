<template>
  <div class="lawyer-certificates-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-title">
        <h1>
          <el-icon class="page-icon"><User /></el-icon>
          律师证管理
        </h1>
        <p class="page-subtitle">智能识别和管理律师执业证书信息，为投标文档提供专业支撑</p>
      </div>
      <div class="page-actions">
        <el-button type="primary" @click="showCreateDialog = true" size="large">
          <el-icon><Plus /></el-icon>
          手动添加律师证
        </el-button>
        <el-button @click="refreshData" :loading="loading" size="large">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section" v-if="stats">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card total-card">
            <div class="stat-content">
              <div class="stat-icon total-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="stat-details">
                <div class="stat-number">{{ stats.total_certificates }}</div>
                <div class="stat-label">律师证总数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card verified-card">
            <div class="stat-content">
              <div class="stat-icon verified-icon">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <div class="stat-details">
                <div class="stat-number">{{ stats.verified_certificates }}</div>
                <div class="stat-label">已验证</div>
                <div class="stat-rate">{{ stats.verification_rate }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card manual-card">
            <div class="stat-content">
              <div class="stat-icon manual-icon">
                <el-icon><Edit /></el-icon>
              </div>
              <div class="stat-details">
                <div class="stat-number">{{ stats.manual_certificates }}</div>
                <div class="stat-label">手动录入</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card distribution-card">
            <div class="stat-content">
              <div class="stat-icon distribution-icon">
                <el-icon><PieChart /></el-icon>
              </div>
              <div class="stat-details">
                <div class="stat-number">{{ stats.position_distribution?.length || 0 }}</div>
                <div class="stat-label">职位类型</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-section">
      <div class="search-form">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-input
              v-model="searchForm.search"
              placeholder="搜索律师姓名、执业证号、事务所..."
              @input="onSearchChange"
              clearable
              size="large"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="searchForm.position"
              placeholder="职位筛选"
              clearable
              size="large"
              @change="onFilterChange"
            >
              <el-option label="合伙人" value="合伙人" />
              <el-option label="律师" value="律师" />
              <el-option label="高级律师" value="高级律师" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="searchForm.is_verified"
              placeholder="验证状态"
              clearable
              size="large"
              @change="onFilterChange"
            >
              <el-option label="已验证" :value="true" />
              <el-option label="未验证" :value="false" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select
              v-model="searchForm.law_firm"
              placeholder="律师事务所"
              clearable
              filterable
              size="large"
              @change="onFilterChange"
            >
              <el-option
                v-for="firm in topLawFirms"
                :key="firm.law_firm"
                :label="firm.law_firm"
                :value="firm.law_firm"
              />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="resetSearch" size="large">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 律师证列表 -->
    <el-card class="list-section">
      <template #header>
        <div class="list-header">
          <div class="list-title">
            <h3>律师证列表</h3>
            <span class="list-count">共 {{ pagination.total }} 条记录</span>
          </div>
          <div class="list-actions">
            <el-select v-model="sortBy" @change="onSortChange" size="default">
              <el-option label="按创建时间排序" value="created_at" />
              <el-option label="按更新时间排序" value="updated_at" />
              <el-option label="按律师姓名排序" value="lawyer_name" />
              <el-option label="按事务所排序" value="law_firm" />
            </el-select>
            <el-select v-model="sortOrder" @change="onSortChange" size="default">
              <el-option label="降序" value="desc" />
              <el-option label="升序" value="asc" />
            </el-select>
          </div>
        </div>
      </template>

      <div v-loading="loading">
        <div v-if="certificates.length === 0 && !loading" class="empty-state">
          <el-empty description="暂无律师证记录">
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              添加第一个律师证
            </el-button>
          </el-empty>
        </div>

        <div v-else class="certificates-grid">
          <div
            v-for="cert in certificates"
            :key="cert.id"
            class="certificate-card"
            @click="viewCertificate(cert)"
          >
            <div class="certificate-header">
              <div class="certificate-info">
                <h4 class="lawyer-name">{{ cert.lawyer_name }}</h4>
                <div class="certificate-number">证号：{{ cert.certificate_number }}</div>
              </div>
              <div class="certificate-status">
                <el-tag :type="cert.is_verified ? 'success' : 'warning'" size="large">
                  <el-icon><CircleCheckFilled v-if="cert.is_verified" /><Warning v-else /></el-icon>
                  {{ cert.is_verified ? '已验证' : '待验证' }}
                </el-tag>
                <el-tag v-if="cert.is_manual_input" type="info" size="small">手动录入</el-tag>
              </div>
            </div>

            <div class="certificate-body">
              <div class="law-firm">
                <el-icon><OfficeBuilding /></el-icon>
                {{ cert.law_firm }}
              </div>
              <div class="position" v-if="cert.position">
                <el-icon><UserFilled /></el-icon>
                {{ cert.position }}
              </div>
              <div class="issuing-authority" v-if="cert.issuing_authority">
                <el-icon><Stamp /></el-icon>
                {{ cert.issuing_authority }}
              </div>
            </div>

            <div class="certificate-tags" v-if="cert.position_tags?.length || cert.business_field_tags?.length">
              <el-tag
                v-for="tag in (cert.position_tags || []).slice(0, 2)"
                :key="'pos-' + tag"
                type="primary"
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              <el-tag
                v-for="tag in (cert.business_field_tags || []).slice(0, 3)"
                :key="'biz-' + tag"
                type="success"
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              <span v-if="(cert.position_tags?.length || 0) + (cert.business_field_tags?.length || 0) > 5" class="more-tags">
                +{{ (cert.position_tags?.length || 0) + (cert.business_field_tags?.length || 0) - 5 }}
              </span>
            </div>

            <div class="certificate-footer">
              <div class="confidence" v-if="cert.confidence_score">
                <el-progress
                  :percentage="Math.round(cert.confidence_score * 100)"
                  :stroke-width="6"
                  :show-text="false"
                  :color="getConfidenceColor(cert.confidence_score)"
                />
                <span class="confidence-text">置信度 {{ Math.round(cert.confidence_score * 100) }}%</span>
              </div>
              <div class="meta-info">
                <span class="files-count" v-if="cert.files_count">
                  <el-icon><Document /></el-icon>
                  {{ cert.files_count }} 个文件
                </span>
                <span class="created-time">
                  <el-icon><Clock /></el-icon>
                  {{ formatDate(cert.created_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-section" v-if="pagination.total > 0">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="onPageSizeChange"
            @current-change="onPageChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 手动添加律师证对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="手动添加律师证"
      width="800px"
      :before-close="handleCreateDialogClose"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
        class="create-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="律师姓名" prop="lawyer_name">
              <el-input v-model="createForm.lawyer_name" placeholder="请输入律师姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执业证号" prop="certificate_number">
              <el-input v-model="createForm.certificate_number" placeholder="请输入执业证号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="律师事务所" prop="law_firm">
          <el-input v-model="createForm.law_firm" placeholder="请输入律师事务所名称" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发证机关">
              <el-input v-model="createForm.issuing_authority" placeholder="如：北京市司法局" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-select v-model="createForm.position" placeholder="请选择职位">
                <el-option label="合伙人" value="合伙人" />
                <el-option label="律师" value="律师" />
                <el-option label="高级律师" value="高级律师" />
                <el-option label="资深律师" value="资深律师" />
                <el-option label="首席律师" value="首席律师" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="年龄">
              <el-input-number v-model="createForm.age" :min="20" :max="80" placeholder="年龄" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="颁发日期">
              <el-date-picker
                v-model="createForm.issue_date"
                type="date"
                placeholder="选择颁发日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="职位标签">
          <el-select
            v-model="createForm.position_tags"
            multiple
            placeholder="请选择职位标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in tagSuggestions.position_tags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="业务领域标签">
          <el-select
            v-model="createForm.business_field_tags"
            multiple
            placeholder="请选择业务领域标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in tagSuggestions.business_field_tags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="身份证号">
          <el-input v-model="createForm.id_number" placeholder="身份证号（可选）" />
        </el-form-item>

        <el-form-item label="验证备注">
          <el-input
            v-model="createForm.verification_notes"
            type="textarea"
            :rows="3"
            placeholder="验证备注（可选）"
          />
        </el-form-item>

        <el-form-item label="相关文件">
          <el-upload
            ref="uploadRef"
            v-model:file-list="createForm.files"
            :auto-upload="false"
            multiple
            :limit="5"
            accept=".pdf,.png,.jpg,.jpeg,.docx"
            class="upload-area"
          >
            <el-button type="primary" plain>
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、图片、Word 文档，最多上传 5 个文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCreateDialogClose">取消</el-button>
          <el-button type="primary" @click="submitCreate" :loading="createLoading">
            创建律师证
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 律师证详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`律师证详情 - ${currentCertificate?.lawyer_name}`"
      width="1000px"
    >
      <div v-if="currentCertificate" class="certificate-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="律师姓名">
            {{ currentCertificate.lawyer_name }}
          </el-descriptions-item>
          <el-descriptions-item label="执业证号">
            {{ currentCertificate.certificate_number }}
          </el-descriptions-item>
          <el-descriptions-item label="律师事务所">
            {{ currentCertificate.law_firm }}
          </el-descriptions-item>
          <el-descriptions-item label="发证机关">
            {{ currentCertificate.issuing_authority || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="职位">
            {{ currentCertificate.position || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="年龄">
            {{ currentCertificate.age || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="身份证号">
            {{ currentCertificate.id_number || '未提供' }}
          </el-descriptions-item>
          <el-descriptions-item label="颁发日期">
            {{ currentCertificate.issue_date ? formatDate(currentCertificate.issue_date) : '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="验证状态">
            <el-tag :type="currentCertificate.is_verified ? 'success' : 'warning'">
              {{ currentCertificate.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="录入方式">
            <el-tag :type="currentCertificate.is_manual_input ? 'info' : 'primary'">
              {{ currentCertificate.is_manual_input ? '手动录入' : 'AI识别' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="置信度" v-if="currentCertificate.confidence_score">
            <el-progress
              :percentage="Math.round(currentCertificate.confidence_score * 100)"
              :stroke-width="8"
              :color="getConfidenceColor(currentCertificate.confidence_score)"
            />
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(currentCertificate.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="tags-section" v-if="currentCertificate.position_tags?.length || currentCertificate.business_field_tags?.length">
          <h4>标签信息</h4>
          <div class="tags-group">
            <div v-if="currentCertificate.position_tags?.length">
              <span class="tags-label">职位标签：</span>
              <el-tag
                v-for="tag in currentCertificate.position_tags"
                :key="'pos-' + tag"
                type="primary"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
            </div>
            <div v-if="currentCertificate.business_field_tags?.length">
              <span class="tags-label">业务领域：</span>
              <el-tag
                v-for="tag in currentCertificate.business_field_tags"
                :key="'biz-' + tag"
                type="success"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="files-section" v-if="currentCertificate.files?.length">
          <h4>相关文件</h4>
          <div class="files-list">
            <div
              v-for="file in currentCertificate.files"
              :key="file.id"
              class="file-item"
            >
              <el-icon><Document /></el-icon>
              <span class="file-name">{{ file.file_name }}</span>
              <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
              <span class="file-time">{{ formatDate(file.created_at) }}</span>
            </div>
          </div>
        </div>

        <div class="notes-section" v-if="currentCertificate.verification_notes">
          <h4>验证备注</h4>
          <div class="notes-content">
            {{ currentCertificate.verification_notes }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Plus, Refresh, Document, CircleCheckFilled, Edit, PieChart, Warning,
  Search, RefreshLeft, OfficeBuilding, UserFilled, Stamp, Clock, Upload
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const createLoading = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const createFormRef = ref()
const uploadRef = ref()

// 数据
const certificates = ref([])
const stats = ref(null)
const tagSuggestions = ref({
  position_tags: [],
  business_field_tags: [],
  common_custom_tags: []
})
const currentCertificate = ref(null)

// 搜索和筛选
const searchForm = reactive({
  search: '',
  position: '',
  is_verified: null,
  law_firm: ''
})

// 排序
const sortBy = ref('created_at')
const sortOrder = ref('desc')

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0
})

// 创建表单
const createForm = reactive({
  lawyer_name: '',
  certificate_number: '',
  law_firm: '',
  issuing_authority: '',
  age: null,
  id_number: '',
  issue_date: null,
  position: '律师',
  position_tags: [],
  business_field_tags: [],
  custom_tags: [],
  verification_notes: '',
  files: []
})

// 表单验证规则
const createRules = {
  lawyer_name: [
    { required: true, message: '请输入律师姓名', trigger: 'blur' }
  ],
  certificate_number: [
    { required: true, message: '请输入执业证号', trigger: 'blur' }
  ],
  law_firm: [
    { required: true, message: '请输入律师事务所名称', trigger: 'blur' }
  ]
}

// 计算属性
const topLawFirms = computed(() => {
  return stats.value?.top_law_firms || []
})

// 方法
const fetchCertificates = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }

    // 添加搜索和筛选参数
    if (searchForm.search) params.search = searchForm.search
    if (searchForm.position) params.position = searchForm.position
    if (searchForm.is_verified !== null) params.is_verified = searchForm.is_verified
    if (searchForm.law_firm) params.law_firm = searchForm.law_firm

    const response = await axios.get('/lawyer-certificates/list', { params })
    
    if (response.data.success) {
      certificates.value = response.data.certificates
      pagination.total = response.data.pagination.total
      pagination.total_pages = response.data.pagination.total_pages
    }
  } catch (error) {
    console.error('获取律师证列表失败:', error)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const response = await axios.get('/lawyer-certificates/stats')
    
    if (response.data.success) {
      stats.value = response.data.stats
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchTagSuggestions = async () => {
  try {
    const response = await axios.get('/lawyer-certificates/tags/suggestions')
    if (response.data.success) {
      tagSuggestions.value = response.data.tag_suggestions
    }
  } catch (error) {
    console.error('获取标签建议失败:', error)
  }
}

const fetchCertificateDetail = async (certId) => {
  try {
    const response = await axios.get(`/lawyer-certificates/${certId}`)
    if (response.data.success) {
      currentCertificate.value = response.data.certificate
      showDetailDialog.value = true
    }
  } catch (error) {
    console.error('获取律师证详情失败:', error)
    ElMessage.error('获取律师证详情失败')
  }
}

const refreshData = async () => {
  await Promise.all([
    fetchCertificates(),
    fetchStats()
  ])
}

const onSearchChange = () => {
  // 重置到第一页并搜索
  pagination.page = 1
  fetchCertificates()
}

const onFilterChange = () => {
  // 重置到第一页并筛选
  pagination.page = 1
  fetchCertificates()
}

const onSortChange = () => {
  fetchCertificates()
}

const onPageChange = () => {
  fetchCertificates()
}

const onPageSizeChange = () => {
  pagination.page = 1
  fetchCertificates()
}

const resetSearch = () => {
  searchForm.search = ''
  searchForm.position = ''
  searchForm.is_verified = null
  searchForm.law_firm = ''
  pagination.page = 1
  fetchCertificates()
}

const viewCertificate = (cert) => {
  fetchCertificateDetail(cert.id)
}

const handleCreateDialogClose = () => {
  showCreateDialog.value = false
  resetCreateForm()
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    lawyer_name: '',
    certificate_number: '',
    law_firm: '',
    issuing_authority: '',
    age: null,
    id_number: '',
    issue_date: null,
    position: '律师',
    position_tags: [],
    business_field_tags: [],
    custom_tags: [],
    verification_notes: '',
    files: []
  })
  createFormRef.value?.clearValidate()
}

const submitCreate = async () => {
  if (!createFormRef.value) return

  const valid = await createFormRef.value.validate().catch(() => false)
  if (!valid) return

  createLoading.value = true
  try {
    const formData = new FormData()
    
    // 添加基本字段
    formData.append('lawyer_name', createForm.lawyer_name)
    formData.append('certificate_number', createForm.certificate_number)
    formData.append('law_firm', createForm.law_firm)
    if (createForm.issuing_authority) formData.append('issuing_authority', createForm.issuing_authority)
    if (createForm.age) formData.append('age', createForm.age)
    if (createForm.id_number) formData.append('id_number', createForm.id_number)
    if (createForm.issue_date) formData.append('issue_date', createForm.issue_date.toISOString())
    formData.append('position', createForm.position)
    if (createForm.verification_notes) formData.append('verification_notes', createForm.verification_notes)

    // 添加标签（JSON格式）
    if (createForm.position_tags.length) {
      formData.append('position_tags', JSON.stringify(createForm.position_tags))
    }
    if (createForm.business_field_tags.length) {
      formData.append('business_field_tags', JSON.stringify(createForm.business_field_tags))
    }
    if (createForm.custom_tags.length) {
      formData.append('custom_tags', JSON.stringify(createForm.custom_tags))
    }

    // 添加文件
    createForm.files.forEach(fileItem => {
      if (fileItem.raw) {
        formData.append('files', fileItem.raw)
      }
    })

    const response = await axios.post('/lawyer-certificates/create', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.data.success) {
      ElMessage.success('律师证创建成功')
      showCreateDialog.value = false
      resetCreateForm()
      refreshData()
    } else {
      ElMessage.error(response.data.message || '创建失败')
    }
  } catch (error) {
    console.error('创建律师证失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建失败')
  } finally {
    createLoading.value = false
  }
}

const getConfidenceColor = (score) => {
  if (score >= 0.8) return '#67c23a'
  if (score >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 初始化
onMounted(() => {
  refreshData()
  fetchTagSuggestions()
})
</script>

<style scoped>
.lawyer-certificates-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title h1 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #303133;
}

.page-icon {
  color: #409eff;
}

.page-subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.page-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.total-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.verified-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.manual-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.distribution-icon { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

.stat-details {
  flex: 1;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-rate {
  font-size: 12px;
  color: #67c23a;
  font-weight: 500;
}

/* 搜索区域 */
.search-section {
  margin-bottom: 24px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.search-form {
  padding: 20px;
}

/* 列表区域 */
.list-section {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.list-title h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.list-count {
  color: #909399;
  font-size: 14px;
}

.list-actions {
  display: flex;
  gap: 12px;
}

/* 律师证卡片网格 */
.certificates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.certificate-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #ebeef5;
  cursor: pointer;
  transition: all 0.3s ease;
}

.certificate-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 20px 0 rgba(64, 158, 255, 0.1);
  transform: translateY(-2px);
}

.certificate-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.lawyer-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.certificate-number {
  font-size: 13px;
  color: #909399;
  font-family: monospace;
}

.certificate-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.certificate-body {
  margin-bottom: 16px;
}

.certificate-body > div {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.certificate-body .el-icon {
  color: #909399;
  font-size: 16px;
}

.certificate-tags {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  font-size: 12px;
}

.more-tags {
  color: #909399;
  font-size: 12px;
}

.certificate-footer {
  border-top: 1px solid #f0f2f5;
  padding-top: 12px;
}

.confidence {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.confidence .el-progress {
  flex: 1;
}

.confidence-text {
  font-size: 12px;
  color: #606266;
  min-width: 70px;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.meta-info > span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 分页 */
.pagination-section {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

/* 对话框 */
.create-form {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 10px;
}

.upload-area {
  width: 100%;
}

.dialog-footer {
  text-align: right;
}

/* 详情对话框 */
.certificate-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.tags-section {
  margin: 20px 0;
}

.tags-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.tags-group > div {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tags-label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.files-section,
.notes-section {
  margin: 20px 0;
}

.files-section h4,
.notes-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 14px;
}

.file-name {
  flex: 1;
  color: #303133;
}

.file-size,
.file-time {
  color: #909399;
  font-size: 12px;
}

.notes-content {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  color: #606266;
  white-space: pre-wrap;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}
</style>