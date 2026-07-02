<template>
  <div class="project-manager">
    <div class="page-header">
      <div>
        <h1 class="page-title">投标项目</h1>
        <p class="page-subtitle">管理您的投标项目</p>
      </div>
      <el-button type="primary" @click="showCreateDialog = true">
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

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingProject ? '编辑项目' : '新增项目'"
      width="600px"
    >
      <el-form :model="projectForm" label-width="100px">
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
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProject" :disabled="!projectForm.name">
          {{ editingProject ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { projectApi } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, View, Delete } from '@element-plus/icons-vue'

const router = useRouter()
const projects = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const search = ref('')
const status = ref('')
const showCreateDialog = ref(false)
const editingProject = ref(null)
const projectForm = ref({
  name: '',
  tender_company: '',
  tender_agency: '',
  bidder_name: '',
  deadline: null,
  description: ''
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
  return diff > 0 && diff < 3 * 24 * 60 * 60 * 1000 // 3天内
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

const editProject = (project) => {
  editingProject.value = project
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
    editingProject.value = null
    projectForm.value = { name: '', tender_company: '', tender_agency: '', bidder_name: '', deadline: null, description: '' }
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
</style>
