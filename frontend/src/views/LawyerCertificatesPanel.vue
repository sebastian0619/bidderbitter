<template>
  <div class="lawyer-certificates-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <div class="header-left">
        <h2>
          <el-icon><User /></el-icon>
          律师证管理
        </h2>
        <p>管理律师执业证书信息，支持AI智能识别和手动录入</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          添加律师证
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <div class="search-bar">
        <el-input
          v-model="searchForm.search"
          placeholder="搜索律师姓名、执业证号、事务所..."
          @input="onSearchChange"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-model="searchForm.position"
          placeholder="职位筛选"
          clearable
          @change="onFilterChange"
          class="position-select"
        >
          <el-option label="合伙人" value="合伙人" />
          <el-option label="律师" value="律师" />
          <el-option label="高级律师" value="高级律师" />
        </el-select>
        
        <el-select
          v-model="searchForm.is_verified"
          placeholder="验证状态"
          clearable
          @change="onFilterChange"
          class="status-select"
        >
          <el-option label="已验证" :value="true" />
          <el-option label="未验证" :value="false" />
        </el-select>
      </div>
    </div>

    <!-- 律师证列表 -->
    <div class="certificates-table-container">
      <el-table 
        :data="certificates" 
        v-loading="loading" 
        class="certificates-table"
        :header-cell-style="{ backgroundColor: '#f8fafc', color: '#475569', fontWeight: '600' }"
      >
        <el-table-column prop="lawyer_name" label="律师姓名" min-width="120">
          <template #default="scope">
            <div class="lawyer-info">
              <div class="lawyer-name">{{ scope.row.lawyer_name }}</div>
              <div class="cert-number">{{ scope.row.certificate_number }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="law_firm" label="律师事务所" min-width="200">
          <template #default="scope">
            <div class="law-firm">{{ scope.row.law_firm }}</div>
          </template>
        </el-table-column>
        
        <el-table-column prop="position" label="职位" width="100">
          <template #default="scope">
            <el-tag size="small" type="primary">{{ scope.row.position }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="issuing_authority" label="发证机关" width="140">
          <template #default="scope">
            <span>{{ scope.row.issuing_authority || '未知' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_verified" label="验证状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_verified ? 'success' : 'warning'" size="small">
              {{ scope.row.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="tags" label="标签" width="180">
          <template #default="scope">
            <div class="tags-container">
              <el-tag 
                v-for="tag in (scope.row.position_tags || []).slice(0, 1)" 
                :key="'pos-' + tag" 
                size="small" 
                type="primary"
                effect="light"
              >
                {{ tag }}
              </el-tag>
              <el-tag 
                v-for="tag in (scope.row.business_field_tags || []).slice(0, 1)" 
                :key="'biz-' + tag" 
                size="small" 
                type="success"
                effect="light"
              >
                {{ tag }}
              </el-tag>
              <span v-if="getTotalTags(scope.row) > 2" class="more-tags">
                +{{ getTotalTags(scope.row) - 2 }}
              </span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="scope">
            <span class="create-time">{{ formatDate(scope.row.created_at) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
              <el-tooltip content="查看详情" placement="top">
                <el-button size="small" circle @click="viewCertificate(scope.row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="编辑" placement="top">
                <el-button size="small" type="primary" circle @click="editCertificate(scope.row)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="删除" placement="top">
                <el-button size="small" type="danger" circle @click="deleteCertificate(scope.row)">
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
          v-if="pagination.total > 0"
          @current-change="onPageChange"
          :current-page="pagination.page"
          :page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, prev, pager, next, jumper"
          background
        />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingCert ? '编辑律师证' : '添加律师证'"
      width="700px"
      :before-close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
        class="cert-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="律师姓名" prop="lawyer_name">
              <el-input v-model="form.lawyer_name" placeholder="请输入律师姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执业证号" prop="certificate_number">
              <el-input v-model="form.certificate_number" placeholder="请输入执业证号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="律师事务所" prop="law_firm">
          <el-input v-model="form.law_firm" placeholder="请输入律师事务所名称" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发证机关">
              <el-input v-model="form.issuing_authority" placeholder="如：北京市司法局" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-select v-model="form.position" placeholder="请选择职位">
                <el-option label="合伙人" value="合伙人" />
                <el-option label="律师" value="律师" />
                <el-option label="高级律师" value="高级律师" />
                <el-option label="资深律师" value="资深律师" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="职位标签">
          <el-select
            v-model="form.position_tags"
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
            v-model="form.business_field_tags"
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

        <el-form-item label="验证备注">
          <el-input
            v-model="form.verification_notes"
            type="textarea"
            :rows="3"
            placeholder="验证备注（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleDialogClose">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ editingCert ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`律师证详情 - ${currentCert?.lawyer_name}`"
      width="800px"
    >
      <div v-if="currentCert" class="cert-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="律师姓名">
            {{ currentCert.lawyer_name }}
          </el-descriptions-item>
          <el-descriptions-item label="执业证号">
            {{ currentCert.certificate_number }}
          </el-descriptions-item>
          <el-descriptions-item label="律师事务所">
            {{ currentCert.law_firm }}
          </el-descriptions-item>
          <el-descriptions-item label="发证机关">
            {{ currentCert.issuing_authority || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="职位">
            {{ currentCert.position || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="验证状态">
            <el-tag :type="currentCert.is_verified ? 'success' : 'warning'">
              {{ currentCert.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="tags-section" v-if="currentCert.position_tags?.length || currentCert.business_field_tags?.length">
          <h4>标签信息</h4>
          <div class="tags-group">
            <div v-if="currentCert.position_tags?.length">
              <span class="tags-label">职位标签：</span>
              <el-tag
                v-for="tag in currentCert.position_tags"
                :key="'pos-' + tag"
                type="primary"
                size="small"
              >
                {{ tag }}
              </el-tag>
            </div>
            <div v-if="currentCert.business_field_tags?.length">
              <span class="tags-label">业务领域：</span>
              <el-tag
                v-for="tag in currentCert.business_field_tags"
                :key="'biz-' + tag"
                type="success"
                size="small"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Plus, Refresh, Search, View, Edit, Delete
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const editingCert = ref(null)
const currentCert = ref(null)
const formRef = ref()

// 数据
const certificates = ref([])
const tagSuggestions = ref({
  position_tags: [],
  business_field_tags: []
})

// 搜索表单
const searchForm = reactive({
  search: '',
  position: '',
  is_verified: null
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 表单数据
const form = reactive({
  lawyer_name: '',
  certificate_number: '',
  law_firm: '',
  issuing_authority: '',
  position: '律师',
  position_tags: [],
  business_field_tags: [],
  verification_notes: ''
})

// 表单验证规则
const formRules = {
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

// 方法
const fetchCertificates = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (searchForm.search) params.search = searchForm.search
    if (searchForm.position) params.position = searchForm.position
    if (searchForm.is_verified !== null) params.is_verified = searchForm.is_verified

    const response = await axios.get('/api/lawyer-certificates/list', { params })
    
    if (response.data.success) {
      certificates.value = response.data.certificates
      pagination.total = response.data.pagination.total
    }
  } catch (error) {
    console.error('获取律师证列表失败:', error)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

const fetchTagSuggestions = async () => {
  try {
    const response = await axios.get('/api/lawyer-certificates/tags/suggestions')
    if (response.data.success) {
      tagSuggestions.value = response.data.tag_suggestions
    }
  } catch (error) {
    console.error('获取标签建议失败:', error)
  }
}

const refreshData = () => {
  fetchCertificates()
}

const onSearchChange = () => {
  pagination.page = 1
  fetchCertificates()
}

const onFilterChange = () => {
  pagination.page = 1
  fetchCertificates()
}

const onPageChange = () => {
  fetchCertificates()
}

const viewCertificate = async (cert) => {
  try {
    const response = await axios.get(`/api/lawyer-certificates/${cert.id}`)
    if (response.data.success) {
      currentCert.value = response.data.certificate
      showDetailDialog.value = true
    }
  } catch (error) {
    ElMessage.error('获取详情失败')
  }
}

const editCertificate = (cert) => {
  editingCert.value = cert
  Object.assign(form, {
    lawyer_name: cert.lawyer_name,
    certificate_number: cert.certificate_number,
    law_firm: cert.law_firm,
    issuing_authority: cert.issuing_authority || '',
    position: cert.position || '律师',
    position_tags: cert.position_tags || [],
    business_field_tags: cert.business_field_tags || [],
    verification_notes: cert.verification_notes || ''
  })
  showCreateDialog.value = true
}

const deleteCertificate = async (cert) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除律师证"${cert.lawyer_name} (${cert.certificate_number})"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    const response = await axios.delete(`/api/lawyer-certificates/${cert.id}`)
    if (response.data.success) {
      ElMessage.success('删除成功')
      refreshData()
    } else {
      ElMessage.error(response.data.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const handleDialogClose = () => {
  showCreateDialog.value = false
  editingCert.value = null
  resetForm()
}

const resetForm = () => {
  Object.assign(form, {
    lawyer_name: '',
    certificate_number: '',
    law_firm: '',
    issuing_authority: '',
    position: '律师',
    position_tags: [],
    business_field_tags: [],
    verification_notes: ''
  })
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const formData = new FormData()
    
    Object.keys(form).forEach(key => {
      if (form[key] !== null && form[key] !== '') {
        if (Array.isArray(form[key])) {
          formData.append(key, JSON.stringify(form[key]))
        } else {
          formData.append(key, form[key])
        }
      }
    })

    let response
    if (editingCert.value) {
      response = await axios.put(`/api/lawyer-certificates/${editingCert.value.id}`, formData)
    } else {
      response = await axios.post('/api/lawyer-certificates/create', formData)
    }

    if (response.data.success) {
      ElMessage.success(editingCert.value ? '更新成功' : '创建成功')
      handleDialogClose()
      refreshData()
    } else {
      ElMessage.error(response.data.message || '操作失败')
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

const getTotalTags = (row) => {
  return (row.position_tags?.length || 0) + (row.business_field_tags?.length || 0)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit'
  })
}

// 暴露给父组件的方法
defineExpose({
  refreshData
})

// 初始化
onMounted(() => {
  fetchCertificates()
  fetchTagSuggestions()
})
</script>

<style scoped>
.lawyer-certificates-panel {
  background: white;
  border-radius: 8px;
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.header-left h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #1f2937;
}

.header-left p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-section {
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  max-width: 300px;
}

.position-select,
.status-select {
  width: 120px;
}

.certificates-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.certificates-table {
  width: 100%;
}

.lawyer-info {
  line-height: 1.4;
}

.lawyer-name {
  font-weight: 600;
  color: #1f2937;
}

.cert-number {
  font-size: 12px;
  color: #6b7280;
  font-family: monospace;
}

.law-firm {
  color: #374151;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.more-tags {
  color: #6b7280;
  font-size: 12px;
}

.create-time {
  font-size: 12px;
  color: #6b7280;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.cert-form {
  max-height: 60vh;
  overflow-y: auto;
}

.dialog-footer {
  text-align: right;
}

.cert-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.tags-section {
  margin: 20px 0;
}

.tags-section h4 {
  margin: 0 0 12px 0;
  color: #1f2937;
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
  color: #374151;
  min-width: 80px;
}
</style>