<template>
  <div class="projects-container">
    <div class="page-header">
      <h1>投标项目管理</h1>
      <el-button type="primary" @click="goToCreate">创建新项目</el-button>
    </div>

    <el-card class="filter-card">
      <div class="filter-container">
        <el-input 
          v-model="searchQuery" 
          placeholder="项目名称搜索" 
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select 
          v-model="filter.status" 
          placeholder="项目状态" 
          clearable
          @change="handleFilterChange"
        >
          <el-option label="草稿" value="draft" />
          <el-option label="进行中" value="in_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
      </div>
    </el-card>

    <el-card v-if="loading" class="loading-card">
      <div class="loading-container">
        <el-spinner text="加载中..." />
      </div>
    </el-card>

    <el-empty v-else-if="projects.length === 0" description="暂无项目" />

    <el-card v-else class="projects-list">
      <el-table :data="projects" border style="width: 100%">
        <el-table-column prop="name" label="项目名称" min-width="150">
          <template #default="scope">
            <router-link :to="`/projects/${scope.row.id}`" class="project-link">
              {{ scope.row.name }}
            </router-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="bidder_name" label="投标人" min-width="120" />
        
        <el-table-column prop="tender_company" label="招标人" min-width="120" />
        
        <el-table-column prop="deadline" label="截止日期" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.deadline) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button-group>
              <el-button 
                type="primary" 
                size="small"
                @click="viewProject(scope.row)"
              >
                查看
              </el-button>
              <el-button 
                type="info" 
                size="small"
                @click="editProject(scope.row)"
              >
                编辑
              </el-button>
              <el-button 
                type="danger" 
                size="small"
                @click="confirmDelete(scope.row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-if="total > pageSize"
          background
          layout="prev, pager, next"
          :total="total"
          :current-page="currentPage"
          :page-size="pageSize"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '@/services/api'

export default {
  name: 'ProjectList',
  
  setup() {
    // 路由
    const router = useRouter()
    
    // 数据
    const projects = ref([])
    const loading = ref(true)
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const searchQuery = ref('')
    
    // 过滤条件
    const filter = reactive({
      status: ''
    })
    
    // 获取项目列表
    const fetchProjects = async () => {
      loading.value = true
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        
        if (searchQuery.value) {
          params.search = searchQuery.value
        }
        
        if (filter.status) {
          params.status = filter.status
        }
        
        const response = await api.get('/projects', { params })
        
        if (response.data) {
          projects.value = response.data
          total.value = response.total || response.data.length
        }
      } catch (error) {
        ElMessage.error('获取项目列表失败')
        console.error('获取项目列表失败', error)
      } finally {
        loading.value = false
      }
    }
    
    // 删除项目
    const deleteProject = async (project) => {
      try {
        await api.delete(`/projects/${project.id}`)
        ElMessage.success('项目删除成功')
        fetchProjects()
      } catch (error) {
        ElMessage.error('项目删除失败')
        console.error('项目删除失败', error)
      }
    }
    
    // 确认删除对话框
    const confirmDelete = (project) => {
      ElMessageBox.confirm(
        `确定要删除项目 "${project.name}" 吗？此操作不可撤销。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
        .then(() => {
          deleteProject(project)
        })
        .catch(() => {
          // 用户取消，不做任何操作
        })
    }
    
    // 页码变化处理
    const handlePageChange = (page) => {
      currentPage.value = page
      fetchProjects()
    }
    
    // 搜索处理
    const handleSearch = () => {
      currentPage.value = 1
      fetchProjects()
    }
    
    // 过滤条件变化
    const handleFilterChange = () => {
      currentPage.value = 1
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
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '无截止日期'
      
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN')
    }
    
    // 获取状态标签
    const getStatusLabel = (status) => {
      switch (status) {
        case 'draft':
          return '草稿'
        case 'in_progress':
          return '进行中'
        case 'completed':
          return '已完成'
        default:
          return '未知'
      }
    }
    
    // 获取状态标签类型
    const getStatusType = (status) => {
      switch (status) {
        case 'draft':
          return 'info'
        case 'in_progress':
          return 'warning'
        case 'completed':
          return 'success'
        default:
          return 'info'
      }
    }
    
    onMounted(() => {
      fetchProjects()
    })
    
    return {
      projects,
      loading,
      total,
      currentPage,
      pageSize,
      searchQuery,
      filter,
      fetchProjects,
      handlePageChange,
      handleSearch,
      handleFilterChange,
      goToCreate,
      viewProject,
      editProject,
      confirmDelete,
      formatDate,
      getStatusLabel,
      getStatusType
    }
  }
}
</script>

<style scoped>
.projects-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-container {
  display: flex;
  gap: 10px;
}

.projects-list {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.project-link {
  color: var(--el-color-primary);
  text-decoration: none;
}

.loading-card {
  min-height: 200px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style> 