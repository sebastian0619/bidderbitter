<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">投标项目管理</h1>
      <p class="page-description">管理所有投标项目，跟踪项目进度和状态</p>
    </div>

    <DataTable
      :data="projects"
      :columns="projectColumns"
      :loading="loading"
      :total-count="total"
      @refresh="fetchProjects"
      @edit="editProject"
      @delete="deleteProject"
      @page-change="handlePageChange"
      @search="handleSearch"
    >
      <template #toolbar-left>
        <el-select 
          v-model="filter.status" 
          placeholder="项目状态" 
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="草稿" value="draft" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </template>
      
      <template #toolbar-right>
        <el-button type="primary" @click="goToCreate">
          <el-icon><Plus /></el-icon>
          创建新项目
        </el-button>
      </template>
      
      <template #name="{ row }">
        <router-link :to="`/projects/${row.id}`" class="project-link">
          {{ row.name }}
        </router-link>
      </template>
      
      <template #deadline="{ row }">
        <span v-if="row.deadline" :class="getDeadlineClass(row.deadline)">
          {{ formatDate(row.deadline) }}
        </span>
        <span v-else class="text-muted">未设置</span>
      </template>
      
      <template #status="{ row }">
        <el-tag :type="getStatusType(row.status)" size="small">
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>
      
      <template #sections_count="{ row }">
        <el-badge :value="row.sections_count || 0" class="item">
          <el-button size="small" text>
            <el-icon><Document /></el-icon>
          </el-button>
        </el-badge>
      </template>
      
      <template #progress="{ row }">
        <el-progress 
          :percentage="row.progress || 0" 
          :show-text="false"
          size="small"
          :color="getProgressColor(row.progress)"
        />
        <span class="progress-text">{{ row.progress || 0 }}%</span>
      </template>
      
      <template #actions="{ row }">
        <el-button-group>
          <el-button 
            type="primary" 
            size="small"
            text
            @click="viewProject(row)"
          >
            <el-icon><View /></el-icon>
            查看
          </el-button>
          <el-button 
            type="info" 
            size="small"
            text
            @click="editProject(row)"
          >
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button 
            v-if="canGenerate(row)"
            type="success" 
            size="small"
            text
            @click="generateDocument(row)"
          >
            <el-icon><DocumentAdd /></el-icon>
            生成
          </el-button>
        </el-button-group>
      </template>
    </DataTable>
    
    <!-- 统计信息卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-icon draft">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.draft }}</div>
            <div class="stat-label">草稿项目</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-icon progress">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.inProgress }}</div>
            <div class="stat-label">进行中</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="8">
        <div class="stat-card">
          <div class="stat-icon completed">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.completed }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, 
  Plus, 
  Document, 
  View, 
  Edit, 
  DocumentAdd, 
  Clock, 
  CircleCheck 
} from '@element-plus/icons-vue'
import { apiService } from '@/services/api'
import { useAppStore } from '@/stores/app'
import DataTable from '@/components/DataTable.vue'

// 组合式API设置
const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const projects = ref([])
const loading = ref(true)
const total = ref(0)
const searchQuery = ref('')

// 过滤条件
const filter = reactive({
  status: ''
})

// 统计数据
const stats = ref({
  draft: 0,
  inProgress: 0,
  completed: 0
})

// 表格列配置
const projectColumns = [
  { 
    prop: 'name', 
    label: '项目名称', 
    slot: 'name', 
    minWidth: 200,
    sortable: true
  },
  { 
    prop: 'bidder_name', 
    label: '投标人', 
    minWidth: 150 
  },
  { 
    prop: 'tender_company', 
    label: '招标人', 
    minWidth: 150 
  },
  { 
    prop: 'deadline', 
    label: '截止日期', 
    slot: 'deadline', 
    width: 120,
    sortable: true
  },
  { 
    prop: 'status', 
    label: '状态', 
    slot: 'status', 
    width: 100 
  },
  { 
    prop: 'sections_count', 
    label: '章节数', 
    slot: 'sections_count', 
    width: 100 
  },
  { 
    prop: 'progress', 
    label: '进度', 
    slot: 'progress', 
    width: 120 
  },
  { 
    prop: 'created_at', 
    label: '创建时间', 
    width: 150, 
    formatter: formatDate 
  }
]

// 计算属性
const totalProjects = computed(() => 
  stats.value.draft + stats.value.inProgress + stats.value.completed
)

// 方法
const fetchProjects = async (params = {}) => {
  loading.value = true
  try {
    const queryParams = {
      page: params.page || 1,
      size: params.size || 20,
      ...params
    }
    
    if (searchQuery.value) {
      queryParams.search = searchQuery.value
    }
    
    if (filter.status) {
      queryParams.status = filter.status
    }
    
    const response = await apiService.getProjects(queryParams)
    
    if (response) {
      projects.value = response.projects || []
      total.value = response.total || 0
      updateStats()
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    appStore.showMessage('获取项目列表失败', 'error')
  } finally {
    loading.value = false
  }
}

// 更新统计数据
const updateStats = () => {
  stats.value = {
    draft: projects.value.filter(p => p.status === 'draft').length,
    inProgress: projects.value.filter(p => p.status === 'in_progress').length,
    completed: projects.value.filter(p => p.status === 'completed').length
  }
}

// 删除项目
const deleteProject = async (project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await apiService.deleteProject(project.id)
    appStore.showMessage('项目删除成功')
    fetchProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('项目删除失败:', error)
      appStore.showMessage('项目删除失败', 'error')
    }
  }
}

// 页码变化处理
const handlePageChange = (params) => {
  fetchProjects(params)
}

// 搜索处理
const handleSearch = (query) => {
  searchQuery.value = query
  fetchProjects()
}

// 过滤条件变化
const handleFilterChange = () => {
  fetchProjects()
}

// 导航到创建页面
const goToCreate = () => {
  router.push('/projects/new')
}

// 查看项目详情
const viewProject = (project) => {
  router.push(`/projects/${project.id}`)
}

// 编辑项目
const editProject = (project) => {
  router.push(`/projects/${project.id}/edit`)
}

// 生成文档
const generateDocument = async (project) => {
  try {
    appStore.setLoading(true, '正在生成项目文档...')
    const result = await apiService.generateProjectDocument(project.id)
    
    if (result.success) {
      appStore.showMessage('文档生成成功')
      // 下载文件
      window.open(result.download_url, '_blank')
    }
  } catch (error) {
    console.error('生成文档失败:', error)
    appStore.showMessage('生成文档失败', 'error')
  } finally {
    appStore.setLoading(false)
  }
}

// 判断是否可以生成文档
const canGenerate = (project) => {
  return project.status !== 'draft' && (project.sections_count || 0) > 0
}

// 格式化日期
const formatDate = (row, column, cellValue) => {
  if (!cellValue) return '未设置'
  return new Date(cellValue).toLocaleDateString('zh-CN')
}

// 获取截止日期样式类
const getDeadlineClass = (deadline) => {
  if (!deadline) return ''
  
  const now = new Date()
  const deadlineDate = new Date(deadline)
  const diffDays = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24))
  
  if (diffDays < 0) return 'deadline-overdue'
  if (diffDays <= 3) return 'deadline-urgent'
  if (diffDays <= 7) return 'deadline-warning'
  return ''
}

// 获取状态标签
const getStatusLabel = (status) => {
  const statusMap = {
    'draft': '草稿',
    'in_progress': '进行中',
    'completed': '已完成'
  }
  return statusMap[status] || '未知'
}

// 获取状态标签类型
const getStatusType = (status) => {
  const typeMap = {
    'draft': 'info',
    'in_progress': 'warning',
    'completed': 'success'
  }
  return typeMap[status] || 'info'
}

// 获取进度条颜色
const getProgressColor = (progress) => {
  if (progress < 30) return '#f56c6c'
  if (progress < 70) return '#e6a23c'
  return '#67c23a'
}

// 组件挂载时获取数据
onMounted(() => {
  fetchProjects()
})
</script>

<style lang="scss" scoped>
.project-link {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
  
  &:hover {
    text-decoration: underline;
  }
}

.stats-cards {
  margin-top: 24px;
}

.stat-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  margin-bottom: 16px;
  
  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
  
  &.draft {
    background: linear-gradient(135deg, #909399, #606266);
  }
  
  &.progress {
    background: linear-gradient(135deg, #e6a23c, #d19e05);
  }
  
  &.completed {
    background: linear-gradient(135deg, #67c23a, #529b2e);
  }
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.progress-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.deadline-overdue {
  color: var(--el-color-danger);
  font-weight: 500;
}

.deadline-urgent {
  color: var(--el-color-warning);
  font-weight: 500;
}

.deadline-warning {
  color: var(--el-color-info);
}

.text-muted {
  color: var(--el-text-color-placeholder);
}

@media (max-width: 768px) {
  .stats-cards {
    margin-top: 16px;
  }
  
  .stat-card {
    margin-bottom: 12px;
    padding: 16px;
  }
  
  .stat-number {
    font-size: 20px;
  }
}
</style> 