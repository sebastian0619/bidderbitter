<template>
  <div class="project-manager">
    <div class="page-header">
      <div>
        <h1 class="page-title">投标项目</h1>
        <p class="page-subtitle">管理您的投标项目</p>
      </div>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增项目
      </el-button>
    </div>

    <el-card>
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input
          v-model="search"
          placeholder="搜索项目名称..."
          style="width: 280px;"
          clearable
          @clear="loadProjects"
          @keyup.enter="loadProjects"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="status" placeholder="项目状态" clearable @change="loadProjects" style="width: 140px;">
          <el-option label="全部状态" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </div>

      <!-- 项目列表 -->
      <el-table :data="projects" style="width: 100%; margin-top: 16px;" @row-click="viewProject">
        <el-table-column prop="name" label="项目名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" :underline="false">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="tender_company" label="招标人" width="180" />
        <el-table-column prop="deadline" label="截止日期" width="120">
          <template #default="{ row }">
            <span :class="{ 'text-danger': isDeadlineSoon(row.deadline) }">
              {{ formatDate(row.deadline) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_count" label="文件数" width="80" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click.stop="editProject(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button size="small" @click.stop="viewProject(row)">
                <el-icon><View /></el-icon>
              </el-button>
              <el-button size="small" type="danger" @click.stop="deleteProject(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
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
          @size-change="loadProjects"
          @current-change="loadProjects"
        />
      </div>
    </el-card>

    <!-- 新增项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingProject ? '编辑项目' : '新增项目'"
      width="650px"
      @close="resetCreateDialog"
    >
      <!-- 新增模式：选择创建方式 -->
      <div v-if="!editingProject && !createMode" class="create-mode-select">
        <div class="mode-card" @click="createMode = 'manual'">
          <div class="mode-icon">
            <el-icon :size="32"><Edit /></el-icon>
          </div>
          <div class="mode-info">
            <div class="mode-title">手动创建</div>
            <div class="mode-desc">手动填写项目信息</div>
          </div>
        </div>
        <div class="mode-card" @click="createMode = 'tender'">
          <div class="mode-icon" style="background: #ecfdf5; color: #10b981;">
            <el-icon :size="32"><Upload /></el-icon>
          </div>
          <div class="mode-info">
            <div class="mode-title">从招标文件创建</div>
            <div class="mode-desc">上传招标文件，自动提取项目信息</div>
          </div>
        </div>
      </div>

      <!-- 手动创建 / 编辑模式 -->
      <el-form v-if="createMode === 'manual' || editingProject" :model="projectForm" label-width="100px">
        <el-form-item label="项目名称" required>
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="招标人">
          <el-input v-model="projectForm.tender_company" placeholder="请输入招标人名称" />
        </el-form-item>
        <el-form-item label="招标代理">
          <el-input v-model="projectForm.tender_agency" placeholder="请输入招标代理机构" />
        </el-form-item>
        <el-form-item label="投标人">
          <el-input v-model="projectForm.bidder_name" placeholder="请输入投标人全称" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="projectForm.deadline"
            type="datetime"
            placeholder="选择截止日期"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
      </el-form>

      <!-- 招标文件上传模式 -->
      <div v-if="createMode === 'tender' && !editingProject">
        <!-- 未分析状态：上传文件 -->
        <div v-if="!tenderAnalysis">
          <el-upload
            ref="tenderUploadRef"
            :auto-upload="false"
            :on-change="handleTenderFileChange"
            :limit="1"
            accept=".docx,.pdf"
            drag
            class="tender-upload"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽招标文件到此处或<em>点击上传</em></div>
            <div class="upload-hint">支持 .docx 和 .pdf 格式</div>
          </el-upload>
          <el-button 
            type="primary" 
            style="width: 100%; margin-top: 16px;" 
            :disabled="!tenderFile"
            :loading="analyzing"
            @click="analyzeTender"
          >
            <el-icon><MagicStick /></el-icon>
            分析招标文件
          </el-button>
        </div>

        <!-- 分析完成：显示结果 -->
        <div v-else class="tender-result">
          <el-alert 
            :title="`已识别 ${tenderAnalysis.sections.length} 个章节`" 
            type="success" 
            show-icon 
            :closable="false"
            style="margin-bottom: 16px;"
          />
          
          <el-form :model="tenderForm" label-width="100px">
            <el-form-item label="项目名称">
              <el-input v-model="tenderForm.name" />
            </el-form-item>
            <el-form-item label="招标人">
              <el-input v-model="tenderForm.tender_company" />
            </el-form-item>
            <el-form-item label="招标代理">
              <el-input v-model="tenderForm.tender_agency" />
            </el-form-item>
            <el-form-item label="截止日期">
              <el-input v-model="tenderForm.deadline" />
            </el-form-item>
          </el-form>

          <!-- 需要提交的材料 -->
          <div class="materials-preview" v-if="tenderAnalysis.required_materials?.length">
            <h4>本次需要提交的材料：</h4>
            <div class="materials-list">
              <div v-for="mat in tenderAnalysis.required_materials" :key="mat.name" class="material-item">
                <el-icon color="#67C23A"><CircleCheckFilled /></el-icon>
                <span class="material-name">{{ mat.name }}</span>
                <span class="material-desc">{{ mat.description }}</span>
              </div>
            </div>
          </div>

          <!-- 章节结构 -->
          <div class="sections-preview">
            <h4>投标文件章节结构：</h4>
            <div class="section-tree">
              <div v-for="section in tenderAnalysis.sections" :key="section.order" class="section-node" :class="{ 'is-required': section.is_required }">
                <el-icon><Document /></el-icon>
                <span>{{ section.title }}</span>
                <el-tag v-if="section.is_required" size="small" type="success">必填</el-tag>
                <el-tag v-else size="small" type="info">{{ section.section_type }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="handleDialogBack" v-if="createMode && !editingProject">
          {{ createMode === 'tender' && tenderAnalysis ? '重新分析' : '返回' }}
        </el-button>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button 
          v-if="createMode === 'manual' || editingProject"
          type="primary" 
          @click="saveProject" 
          :disabled="!projectForm.name"
        >
          {{ editingProject ? '保存' : '创建' }}
        </el-button>
        <el-button 
          v-if="createMode === 'tender' && tenderAnalysis"
          type="primary" 
          :loading="creating"
          @click="createProjectFromTender"
        >
          创建项目
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectApi, tenderApi } from '../../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, View, Delete, Upload, UploadFilled, MagicStick, Document, CircleCheckFilled } from '@element-plus/icons-vue'

const router = useRouter()
const projects = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const status = ref('')

// 创建对话框相关
const showCreateDialog = ref(false)
const editingProject = ref(null)
const createMode = ref(null) // null | 'manual' | 'tender'
const projectForm = ref({
  name: '',
  tender_company: '',
  tender_agency: '',
  bidder_name: '',
  deadline: null,
  description: ''
})

// 招标文件相关
const tenderFile = ref(null)
const tenderAnalysis = ref(null)
const analyzing = ref(false)
const creating = ref(false)
const tenderForm = ref({
  name: '',
  tender_company: '',
  tender_agency: '',
  deadline: ''
})

const getStatusType = (status) => {
  const map = { draft: 'info', in_progress: 'warning', completed: 'success' }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = { draft: '草稿', in_progress: '进行中', completed: '已完成' }
  return map[status] || status
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const isDeadlineSoon = (deadline) => {
  if (!deadline) return false
  const diff = new Date(deadline) - new Date()
  return diff > 0 && diff < 3 * 24 * 60 * 60 * 1000
}

const loadProjects = async () => {
  try {
    const res = await projectApi.list({
      page: currentPage.value,
      page_size: pageSize.value,
      search: search.value || undefined,
      status: status.value || undefined
    })
    projects.value = res.data.projects
    total.value = res.data.total
  } catch (error) {
    ElMessage.error('加载项目列表失败')
  }
}

const openCreateDialog = () => {
  editingProject.value = null
  createMode.value = null
  resetTenderState()
  showCreateDialog.value = true
}

const resetCreateDialog = () => {
  createMode.value = null
  editingProject.value = null
  projectForm.value = { name: '', tender_company: '', tender_agency: '', bidder_name: '', deadline: null, description: '' }
  resetTenderState()
}

const resetTenderState = () => {
  tenderFile.value = null
  tenderAnalysis.value = null
  tenderForm.value = { name: '', tender_company: '', tender_agency: '', deadline: '' }
}

const handleDialogBack = () => {
  if (createMode.value === 'tender' && tenderAnalysis.value) {
    resetTenderState()
  } else {
    createMode.value = null
  }
}

const editProject = (project) => {
  editingProject.value = project
  createMode.value = 'manual'
  projectForm.value = {
    name: project.name,
    tender_company: project.tender_company || '',
    tender_agency: project.tender_agency || '',
    bidder_name: project.bidder_name || '',
    deadline: project.deadline ? new Date(project.deadline) : null,
    description: project.description || ''
  }
  showCreateDialog.value = true
}

const viewProject = (project) => {
  router.push(`/projects/${project.id}`)
}

const saveProject = async () => {
  try {
    const data = {
      ...projectForm.value,
      deadline: projectForm.value.deadline?.toISOString()
    }
    
    if (editingProject.value) {
      await projectApi.update(editingProject.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await projectApi.create(data)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    resetCreateDialog()
    loadProjects()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deleteProject = async (project) => {
  try {
    await ElMessageBox.confirm(`确定删除项目 "${project.name}"？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await projectApi.delete(project.id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 招标文件相关
const handleTenderFileChange = (file) => {
  tenderFile.value = file.raw
}

const analyzeTender = async () => {
  if (!tenderFile.value) return
  
  analyzing.value = true
  try {
    const res = await tenderApi.analyze(tenderFile.value)
    tenderAnalysis.value = res.data
    
    const info = res.data.project_info
    tenderForm.value = {
      name: info.project_name || '',
      tender_company: info.tender_company || '',
      tender_agency: info.tender_agency || '',
      deadline: info.deadline || ''
    }
    
    ElMessage.success(`分析完成，识别到 ${res.data.sections.length} 个章节`)
  } catch (error) {
    ElMessage.error('分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    analyzing.value = false
  }
}

const createProjectFromTender = async () => {
  creating.value = true
  try {
    const res = await tenderApi.createFromTender(
      tenderAnalysis.value.file_id,
      tenderForm.value.name
    )
    
    if (res.data.success) {
      ElMessage.success(`项目"${res.data.project_name}"创建成功，包含 ${res.data.sections_count} 个章节`)
      showCreateDialog.value = false
      resetCreateDialog()
      loadProjects()
    }
  } catch (error) {
    ElMessage.error('创建失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    creating.value = false
  }
}

onMounted(loadProjects)
</script>

<style scoped>
.project-manager {
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

.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}

.text-danger {
  color: var(--danger);
  font-weight: 600;
}

/* 创建方式选择 */
.create-mode-select {
  display: flex;
  gap: 16px;
}

.mode-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px solid var(--neutral-200);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-card:hover {
  border-color: var(--primary-400);
  background: var(--primary-50);
}

.mode-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: var(--primary-50);
  color: var(--primary-600);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mode-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--neutral-800);
}

.mode-desc {
  font-size: 13px;
  color: var(--neutral-500);
  margin-top: 4px;
}

/* 招标文件上传 */
.tender-upload {
  margin-bottom: 16px;
}

.upload-icon {
  font-size: 48px;
  color: var(--neutral-300);
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: var(--neutral-600);
}

.upload-text em {
  color: var(--primary-600);
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: var(--neutral-400);
  margin-top: 4px;
}

.tender-result {
  max-height: 400px;
  overflow-y: auto;
}

.sections-preview {
  margin-top: 16px;
}

.sections-preview h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.section-tree {
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-md);
  padding: 8px;
}

.section-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  font-size: 13px;
}

.section-node:hover {
  background: var(--neutral-50);
  border-radius: var(--radius-sm);
}

.section-node.is-required {
  font-weight: 500;
}

.materials-preview {
  margin-top: 16px;
  margin-bottom: 16px;
}

.materials-preview h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--success);
}

.materials-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  background: #f0fdf4;
  border-radius: var(--radius-md);
  border: 1px solid #bbf7d0;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.material-name {
  font-weight: 500;
  color: var(--neutral-800);
}

.material-desc {
  color: var(--neutral-500);
  font-size: 12px;
}
</style>
