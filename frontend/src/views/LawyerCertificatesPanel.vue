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
        <el-button type="success" @click="showBatchUploadDialog = true">
          <el-icon><Upload /></el-icon>
          批量上传
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
              
              <el-dropdown trigger="click" @command="(cmd) => handleAction(cmd, scope.row)">
                <el-button size="small" circle>
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="upload">重新上传证书</el-dropdown-item>
                    <el-dropdown-item command="reanalyze">重新AI分析</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除律师证</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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

        <!-- 文件上传区域 -->
        <el-form-item label="律师证文件" v-if="!editingCert">
          <el-upload
            ref="createUploadRef"
            :auto-upload="false"
            :limit="5"
            :file-list="createFileList"
            :on-change="handleCreateFileChange"
            :on-remove="handleCreateFileRemove"
            :before-upload="beforeUpload"
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            multiple
            drag
          >
            <div class="upload-content">
              <el-icon class="upload-icon"><Upload /></el-icon>
              <div class="upload-text">点击或拖拽文件到此区域上传</div>
              <div class="upload-hint">支持 PDF、图片、Word 文档，可多选</div>
            </div>
          </el-upload>
          <div class="form-help">
            <el-icon><InfoFilled /></el-icon>
            上传律师执业证书文件，系统将自动进行AI识别和信息提取
          </div>
        </el-form-item>

        <!-- AI处理选项 -->
        <el-form-item label="AI处理选项" v-if="!editingCert && createFileList.length > 0">
          <el-checkbox v-model="createOptions.enable_ai_analysis" style="display: block; margin-bottom: 8px;">
            启用AI智能识别
          </el-checkbox>
          <el-checkbox v-model="createOptions.enable_vision_analysis" :disabled="!createOptions.enable_ai_analysis">
            启用视觉分析（推荐）
          </el-checkbox>
          <div class="form-help">
            <el-icon><InfoFilled /></el-icon>
            AI识别可自动提取律师姓名、执业证号、事务所等信息
          </div>
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

    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      :title="`重新上传证书 - ${uploadingCert?.lawyer_name}`"
      width="600px"
    >
      <div class="upload-section">
        <el-alert
          title="上传说明"
          description="上传新的律师证文件将替换原有文件，可以选择是否启用AI分析重新提取信息。"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px;"
        />

        <el-form label-width="120px">
          <el-form-item label="选择文件">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              :file-list="uploadFileList"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :before-upload="beforeUpload"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              drag
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><Upload /></el-icon>
                <div class="upload-text">点击或拖拽文件到此区域上传</div>
                <div class="upload-hint">支持 PDF、图片、Word 文档</div>
              </div>
            </el-upload>
          </el-form-item>

          <el-form-item label="上传选项">
            <el-checkbox v-model="uploadOptions.replace_existing" style="display: block; margin-bottom: 8px;">
              替换现有文件
            </el-checkbox>
            <el-checkbox v-model="uploadOptions.enable_ai_analysis" style="display: block; margin-bottom: 8px;">
              启用AI分析
            </el-checkbox>
            <el-checkbox v-model="uploadOptions.enable_vision_analysis" :disabled="!uploadOptions.enable_ai_analysis">
              启用视觉分析
            </el-checkbox>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeUploadDialog">取消</el-button>
          <el-button 
            type="primary" 
            @click="performUpload" 
            :loading="uploading"
            :disabled="!uploadFileList.length"
          >
            上传文件
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 重新分析对话框 -->
    <el-dialog
      v-model="showReanalyzeDialog"
      :title="`重新分析 - ${reanalyzingCert?.lawyer_name}`"
      width="500px"
    >
      <div class="reanalyze-section">
        <el-alert
          title="重新分析说明"
          description="使用AI重新分析现有的律师证文件，可能会更新律师证信息。"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 20px;"
        />

        <el-form label-width="120px">
          <el-form-item label="分析选项">
            <el-checkbox v-model="reanalyzeOptions.enable_vision_analysis" style="display: block; margin-bottom: 8px;">
              启用视觉分析
            </el-checkbox>
            <el-checkbox v-model="reanalyzeOptions.enable_ocr" style="display: block; margin-bottom: 8px;">
              启用OCR识别
            </el-checkbox>
            <el-checkbox v-model="reanalyzeOptions.update_fields" style="display: block;">
              使用AI结果更新字段
            </el-checkbox>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeReanalyzeDialog">取消</el-button>
          <el-button 
            type="primary" 
            @click="performReanalyze" 
            :loading="reanalyzing"
          >
            开始分析
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量上传对话框 -->
    <el-dialog
      v-model="showBatchUploadDialog"
      title="批量上传律师证"
      width="800px"
      :before-close="closeBatchUploadDialog"
    >
      <div class="batch-upload-section">
        <el-alert
          title="批量上传说明"
          description="支持同时上传多个律师证文件，系统将自动识别并创建律师证记录。建议每个文件命名包含律师姓名以便识别。"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 20px;"
        />

        <el-form label-width="120px">
          <el-form-item label="选择文件">
            <el-upload
              ref="batchUploadRef"
              :auto-upload="false"
              :limit="20"
              :file-list="batchFileList"
              :on-change="handleBatchFileChange"
              :on-remove="handleBatchFileRemove"
              :before-upload="beforeUpload"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              multiple
              drag
            >
              <div class="upload-content">
                <el-icon class="upload-icon"><Upload /></el-icon>
                <div class="upload-text">点击或拖拽文件到此区域批量上传</div>
                <div class="upload-hint">支持 PDF、图片、Word 文档，最多20个文件</div>
              </div>
            </el-upload>
          </el-form-item>

          <el-form-item label="批量处理选项">
            <el-checkbox v-model="batchOptions.enable_ai_analysis" style="display: block; margin-bottom: 8px;">
              启用AI智能识别
            </el-checkbox>
            <el-checkbox v-model="batchOptions.enable_vision_analysis" :disabled="!batchOptions.enable_ai_analysis" style="display: block; margin-bottom: 8px;">
              启用视觉分析
            </el-checkbox>
            <el-checkbox v-model="batchOptions.auto_verify" style="display: block; margin-bottom: 8px;">
              自动验证高置信度结果
            </el-checkbox>
            <el-checkbox v-model="batchOptions.skip_duplicates" style="display: block;">
              跳过重复的执业证号
            </el-checkbox>
          </el-form-item>

          <!-- 文件列表预览 -->
          <el-form-item label="文件列表" v-if="batchFileList.length > 0">
            <div class="file-list-preview">
              <div class="file-count">
                已选择 {{ batchFileList.length }} 个文件
              </div>
              <el-table :data="batchFileList" size="small" style="width: 100%">
                <el-table-column prop="name" label="文件名" min-width="200" />
                <el-table-column label="大小" width="100">
                  <template #default="scope">
                    {{ formatFileSize(scope.row.size) }}
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="100">
                  <template #default="scope">
                    <el-tag size="small" type="info">待上传</el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-form-item>

          <!-- 上传进度 -->
          <el-form-item label="上传进度" v-if="batchUploading">
            <el-progress 
              :percentage="batchProgress.percentage" 
              :status="batchProgress.status"
              :stroke-width="8"
            />
            <div class="progress-info">
              {{ batchProgress.current }} / {{ batchProgress.total }} - {{ batchProgress.message }}
            </div>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeBatchUploadDialog" :disabled="batchUploading">取消</el-button>
          <el-button 
            type="primary" 
            @click="performBatchUpload" 
            :loading="batchUploading"
            :disabled="!batchFileList.length"
          >
            <el-icon><Upload /></el-icon>
            开始批量上传
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Plus, Refresh, Search, View, Edit, Delete, MoreFilled, Upload, InfoFilled
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showUploadDialog = ref(false)
const showReanalyzeDialog = ref(false)
const showBatchUploadDialog = ref(false)
const editingCert = ref(null)
const currentCert = ref(null)
const uploadingCert = ref(null)
const reanalyzingCert = ref(null)
const formRef = ref()
const uploadRef = ref()
const createUploadRef = ref()
const batchUploadRef = ref()

// 数据
const certificates = ref([])
const tagSuggestions = ref({
  position_tags: [],
  business_field_tags: []
})

// 上传相关
const uploading = ref(false)
const uploadFileList = ref([])
const uploadOptions = reactive({
  replace_existing: true,
  enable_ai_analysis: true,
  enable_vision_analysis: true
})

// 重新分析相关
const reanalyzing = ref(false)
const reanalyzeOptions = reactive({
  enable_vision_analysis: true,
  enable_ocr: true,
  update_fields: false
})

// 创建时上传相关
const createFileList = ref([])
const createOptions = reactive({
  enable_ai_analysis: true,
  enable_vision_analysis: true
})

// 批量上传相关
const batchUploading = ref(false)
const batchFileList = ref([])
const batchOptions = reactive({
  enable_ai_analysis: true,
  enable_vision_analysis: true,
  auto_verify: false,
  skip_duplicates: true
})
const batchProgress = reactive({
  percentage: 0,
  current: 0,
  total: 0,
  message: '',
  status: ''
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

    const response = await axios.get('/lawyer-certificates/list', { params })
    
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
    const response = await axios.get('/lawyer-certificates/tags/suggestions')
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
    const response = await axios.get(`/lawyer-certificates/${cert.id}`)
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

    const response = await axios.delete(`/lawyer-certificates/${cert.id}`)
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
  
  // 清理文件列表
  createFileList.value = []
  createOptions.enable_ai_analysis = true
  createOptions.enable_vision_analysis = true
  
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
      // 编辑模式，不处理文件上传
      response = await axios.put(`/lawyer-certificates/${editingCert.value.id}`, formData)
    } else {
      // 创建模式，检查是否有文件上传
      if (createFileList.value.length > 0) {
        // 有文件上传，使用create-from-file接口
        const fileFormData = new FormData()
        fileFormData.append('file', createFileList.value[0].raw)
        
        // 添加表单数据
        Object.keys(form).forEach(key => {
          if (form[key] !== null && form[key] !== '') {
            if (Array.isArray(form[key])) {
              fileFormData.append(key, JSON.stringify(form[key]))
            } else {
              fileFormData.append(key, form[key])
            }
          }
        })
        
        // 添加AI处理选项
        fileFormData.append('enable_ai_analysis', createOptions.enable_ai_analysis)
        fileFormData.append('enable_vision_analysis', createOptions.enable_vision_analysis)
        
        response = await axios.post('/lawyer-certificates/create-from-file', fileFormData)
      } else {
        // 没有文件上传，使用普通create接口
        response = await axios.post('/lawyer-certificates/create', formData)
      }
    }

    if (response.data.success) {
      let message = editingCert.value ? '更新成功' : '创建成功'
      
      // 显示AI分析结果
      if (response.data.ai_analysis && response.data.ai_analysis.confidence) {
        const confidence = Math.round(response.data.ai_analysis.confidence * 100)
        message += `\nAI置信度: ${confidence}%`
      }
      
      ElMessage.success(message)
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

const handleAction = async (cmd, cert) => {
  try {
    if (cmd === 'upload') {
      uploadingCert.value = cert
      showUploadDialog.value = true
    } else if (cmd === 'reanalyze') {
      reanalyzingCert.value = cert
      showReanalyzeDialog.value = true
    } else if (cmd === 'delete') {
      await deleteCertificate(cert)
    }
  } catch (error) {
    console.error('处理操作失败:', error)
    ElMessage.error(error.response?.data?.detail || '处理失败')
  }
}

// 文件上传相关方法
const handleFileChange = (file, fileList) => {
  uploadFileList.value = fileList
}

const handleFileRemove = (file, fileList) => {
  uploadFileList.value = fileList
}

const beforeUpload = (file) => {
  const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 
                     'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  const isValidType = validTypes.includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isValidType) {
    ElMessage.error('文件格式不支持！请上传 PDF、图片或 Word 文档')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return true
}

const performUpload = async () => {
  if (!uploadFileList.value.length || !uploadingCert.value) {
    ElMessage.error('请选择要上传的文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFileList.value[0].raw)
    formData.append('replace_existing', uploadOptions.replace_existing)
    formData.append('enable_ai_analysis', uploadOptions.enable_ai_analysis)
    formData.append('enable_vision_analysis', uploadOptions.enable_vision_analysis)

    const response = await axios.post(
      `/lawyer-certificates/${uploadingCert.value.id}/upload-file`,
      formData
    )

    if (response.data.success) {
      ElMessage.success('文件上传成功')
      
      // 如果有AI分析结果，显示更新信息
      if (response.data.updated_fields && Object.keys(response.data.updated_fields).length > 0) {
        const updatedFields = Object.keys(response.data.updated_fields).join('、')
        ElMessage.info(`AI分析已更新以下字段：${updatedFields}`)
      }
      
      closeUploadDialog()
      refreshData()
    } else {
      ElMessage.error(response.data.message || '上传失败')
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const closeUploadDialog = () => {
  showUploadDialog.value = false
  uploadingCert.value = null
  uploadFileList.value = []
  
  // 重置上传选项
  uploadOptions.replace_existing = true
  uploadOptions.enable_ai_analysis = true
  uploadOptions.enable_vision_analysis = true
}

// 重新分析相关方法
const performReanalyze = async () => {
  if (!reanalyzingCert.value) {
    ElMessage.error('没有选择要分析的律师证')
    return
  }

  reanalyzing.value = true
  try {
    const formData = new FormData()
    formData.append('enable_vision_analysis', reanalyzeOptions.enable_vision_analysis)
    formData.append('enable_ocr', reanalyzeOptions.enable_ocr)
    formData.append('update_fields', reanalyzeOptions.update_fields)

    const response = await axios.post(
      `/lawyer-certificates/${reanalyzingCert.value.id}/reanalyze`,
      formData
    )

    if (response.data.success) {
      ElMessage.success('重新分析完成')
      
      // 显示分析结果
      if (response.data.classification) {
        const confidence = Math.round(response.data.confidence_score * 100)
        ElMessage.info(`AI置信度：${confidence}%`)
      }
      
      // 如果更新了字段，显示更新信息
      if (response.data.updated_fields && Object.keys(response.data.updated_fields).length > 0) {
        const updatedFields = Object.keys(response.data.updated_fields).join('、')
        ElMessage.info(`已更新字段：${updatedFields}`)
      }
      
      closeReanalyzeDialog()
      refreshData()
    } else {
      ElMessage.error(response.data.message || '分析失败')
    }
  } catch (error) {
    console.error('重新分析失败:', error)
    ElMessage.error(error.response?.data?.detail || '分析失败')
  } finally {
    reanalyzing.value = false
  }
}

const closeReanalyzeDialog = () => {
  showReanalyzeDialog.value = false
  reanalyzingCert.value = null
  
  // 重置分析选项
  reanalyzeOptions.enable_vision_analysis = true
  reanalyzeOptions.enable_ocr = true
  reanalyzeOptions.update_fields = false
}

// 创建时文件上传相关方法
const handleCreateFileChange = (file, fileList) => {
  createFileList.value = fileList
}

const handleCreateFileRemove = (file, fileList) => {
  createFileList.value = fileList
}

// 批量上传相关方法
const handleBatchFileChange = (file, fileList) => {
  batchFileList.value = fileList
}

const handleBatchFileRemove = (file, fileList) => {
  batchFileList.value = fileList
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const performBatchUpload = async () => {
  if (!batchFileList.value.length) {
    ElMessage.error('请选择要上传的文件')
    return
  }

  batchUploading.value = true
  batchProgress.percentage = 0
  batchProgress.current = 0
  batchProgress.total = batchFileList.value.length
  batchProgress.status = ''
  
  const results = {
    success: 0,
    failed: 0,
    skipped: 0,
    details: []
  }

  try {
    for (let i = 0; i < batchFileList.value.length; i++) {
      const file = batchFileList.value[i]
      batchProgress.current = i + 1
      batchProgress.message = `正在处理: ${file.name}`
      batchProgress.percentage = Math.round(((i + 1) / batchFileList.value.length) * 100)

      try {
        const formData = new FormData()
        formData.append('file', file.raw)
        formData.append('enable_ai_analysis', batchOptions.enable_ai_analysis)
        formData.append('enable_vision_analysis', batchOptions.enable_vision_analysis)
        formData.append('auto_verify', batchOptions.auto_verify)
        formData.append('skip_duplicates', batchOptions.skip_duplicates)

        const response = await axios.post('/lawyer-certificates/create-from-file', formData)

        if (response.data.success) {
          results.success++
          results.details.push({
            file: file.name,
            status: 'success',
            message: response.data.message || '创建成功',
            certificate: response.data.certificate
          })
        } else {
          if (response.data.skipped) {
            results.skipped++
            results.details.push({
              file: file.name,
              status: 'skipped',
              message: response.data.message || '已跳过'
            })
          } else {
            results.failed++
            results.details.push({
              file: file.name,
              status: 'failed',
              message: response.data.message || '创建失败'
            })
          }
        }
      } catch (error) {
        results.failed++
        results.details.push({
          file: file.name,
          status: 'failed',
          message: error.response?.data?.detail || '上传失败'
        })
      }

      // 短暂延迟避免过快请求
      if (i < batchFileList.value.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 100))
      }
    }

    batchProgress.status = 'success'
    batchProgress.message = '批量上传完成'

    // 显示结果摘要
    let message = `批量上传完成！成功: ${results.success}, 失败: ${results.failed}`
    if (results.skipped > 0) {
      message += `, 跳过: ${results.skipped}`
    }
    ElMessage.success(message)

    // 显示详细结果（如果有失败的）
    if (results.failed > 0) {
      const failedFiles = results.details
        .filter(d => d.status === 'failed')
        .map(d => `${d.file}: ${d.message}`)
        .join('\n')
      
      await ElMessageBox.alert(
        `以下文件处理失败：\n${failedFiles}`,
        '批量上传结果',
        { type: 'warning' }
      )
    }

    closeBatchUploadDialog()
    refreshData()

  } catch (error) {
    console.error('批量上传失败:', error)
    ElMessage.error('批量上传过程中发生错误')
    batchProgress.status = 'exception'
  } finally {
    batchUploading.value = false
  }
}

const closeBatchUploadDialog = () => {
  showBatchUploadDialog.value = false
  batchFileList.value = []
  
  // 重置批量上传选项
  batchOptions.enable_ai_analysis = true
  batchOptions.enable_vision_analysis = true
  batchOptions.auto_verify = false
  batchOptions.skip_duplicates = true
  
  // 重置进度
  batchProgress.percentage = 0
  batchProgress.current = 0
  batchProgress.total = 0
  batchProgress.message = ''
  batchProgress.status = ''
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
  margin-top: 20px;
}

.cert-form {
  max-height: 60vh;
  overflow-y: auto;
}

.cert-detail {
  max-height: 50vh;
  overflow-y: auto;
}

.tags-section {
  margin-top: 20px;
}

.tags-section h4 {
  margin: 0 0 12px 0;
  color: #1f2937;
  font-size: 14px;
}

.tags-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tags-label {
  font-weight: 600;
  color: #374151;
  margin-right: 8px;
}

.upload-content {
  text-align: center;
  padding: 40px 20px;
}

.upload-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: #909399;
}

.upload-section,
.reanalyze-section {
  padding: 0;
}

.batch-upload-section {
  padding: 0;
}

.file-list-preview {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  background-color: #f9fafb;
}

.file-count {
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.progress-info {
  margin-top: 8px;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}

.form-help {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background-color: #f0f9ff;
}

:deep(.el-dialog__body) {
  padding: 20px 24px;
}
</style>