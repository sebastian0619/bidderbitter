<template>
  <div class="award-search">
    <el-card class="header-card">
      <div class="header-content">
        <h2>AI自动检索奖项</h2>
        <p>自动从钱伯斯、Legal 500等权威网站检索律师事务所的获奖信息</p>
      </div>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <!-- 左侧：搜索配置 -->
      <el-col :span="8">
        <el-card class="search-card">
          <template #header>
            <div class="card-header">
              <span>搜索配置</span>
            </div>
          </template>
          
          <el-form :model="searchForm" label-width="100px" class="search-form">
            <el-form-item label="数据源">
              <el-select v-model="searchForm.data_source_id" placeholder="选择数据源">
                <el-option
                  v-for="source in dataSources"
                  :key="source.id"
                  :label="source.name"
                  :value="source.id"
                >
                  <div class="source-option">
                    <span>{{ source.name }}</span>
                    <small>{{ source.description }}</small>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="律师事务所">
              <el-input
                v-model="searchForm.law_firm_name"
                placeholder="请输入律师事务所名称"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="搜索年份">
              <el-date-picker
                v-model="searchForm.search_year"
                type="year"
                placeholder="选择年份"
                format="YYYY"
                value-format="YYYY"
              />
            </el-form-item>
            
            <el-form-item label="业务领域">
              <el-select
                v-model="searchForm.business_field"
                placeholder="选择业务领域"
                clearable
                filterable
              >
                <el-option
                  v-for="field in businessFields"
                  :key="field.id"
                  :label="field.name"
                  :value="field.name"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="搜索关键词">
              <el-input
                v-model="searchForm.search_keywords"
                placeholder="请输入搜索关键词，用逗号分隔"
                clearable
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="startSearch" :loading="searching">
                开始搜索
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 快速搜索模板 -->
          <div class="quick-templates">
            <h4>快速搜索模板</h4>
            <div class="template-list">
              <el-button
                v-for="template in quickTemplates"
                :key="template.id"
                size="small"
                @click="useTemplate(template)"
              >
                {{ template.name }}
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 中间：搜索任务 -->
      <el-col :span="8">
        <el-card class="task-card">
          <template #header>
            <div class="card-header">
              <span>搜索任务</span>
              <el-button type="primary" size="small" @click="loadTasks">
                刷新
              </el-button>
            </div>
          </template>
          
          <div class="task-list">
            <div
              v-for="task in searchTasks"
              :key="task.id"
              class="task-item"
              :class="{ active: selectedTask?.id === task.id }"
              @click="selectTask(task)"
            >
              <div class="task-header">
                <h4>{{ task.task_name }}</h4>
                <el-tag :type="getTaskStatusType(task.status)">
                  {{ getTaskStatusText(task.status) }}
                </el-tag>
              </div>
              
              <div class="task-info">
                <p><strong>律师事务所:</strong> {{ task.law_firm_name }}</p>
                <p><strong>搜索年份:</strong> {{ task.search_year }}</p>
                <p><strong>业务领域:</strong> {{ task.business_field || '全部' }}</p>
              </div>
              
              <div class="task-progress" v-if="task.status === 'running'">
                <el-progress :percentage="task.progress" :show-text="false" />
                <span class="progress-text">{{ task.progress }}%</span>
              </div>
              
              <div class="task-stats" v-if="task.status === 'completed'">
                <div class="stat-item">
                  <span class="stat-label">找到:</span>
                  <span class="stat-value">{{ task.total_found }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">成功:</span>
                  <span class="stat-value success">{{ task.success_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">错误:</span>
                  <span class="stat-value error">{{ task.error_count }}</span>
                </div>
              </div>
              
              <div class="task-actions">
                <el-button type="text" size="small" @click.stop="viewTaskResults(task)">
                  查看结果
                </el-button>
                <el-button type="text" size="small" @click.stop="deleteTask(task)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：搜索结果 -->
      <el-col :span="8">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>搜索结果</span>
              <div class="header-actions">
                <el-button
                  v-if="selectedTask"
                  type="primary"
                  size="small"
                  @click="importAllResults"
                  :disabled="!hasUnimportedResults"
                >
                  批量导入
                </el-button>
                <el-button size="small" @click="loadResults">
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="result-list">
            <div v-if="selectedTask">
              <div
                v-for="result in searchResults"
                :key="result.id"
                class="result-item"
                :class="{ imported: result.status === 'imported' }"
              >
                <div class="result-header">
                  <h4>{{ result.award_name }}</h4>
                  <el-tag :type="getResultStatusType(result.status)" size="small">
                    {{ getResultStatusText(result.status) }}
                  </el-tag>
                </div>
                
                <div class="result-info">
                  <p><strong>律师事务所:</strong> {{ result.law_firm_name }}</p>
                  <p><strong>年份:</strong> {{ result.award_year }}</p>
                  <p><strong>业务领域:</strong> {{ result.business_field }}</p>
                  <p v-if="result.ranking"><strong>排名:</strong> {{ result.ranking }}</p>
                  <p v-if="result.tier"><strong>等级:</strong> {{ result.tier }}</p>
                </div>
                
                <div class="result-actions">
                  <el-button
                    v-if="result.status === 'pending'"
                    type="primary"
                    size="small"
                    @click="importResult(result)"
                  >
                    导入
                  </el-button>
                  <el-button
                    v-if="result.status === 'imported'"
                    type="success"
                    size="small"
                    disabled
                  >
                    已导入
                  </el-button>
                  <el-button type="text" size="small" @click="viewSource(result)">
                    查看来源
                  </el-button>
                  <el-button type="text" size="small" @click="deleteResult(result)">
                    删除
                  </el-button>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <el-empty description="请选择一个搜索任务" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据源管理对话框 -->
    <el-dialog
      v-model="showDataSourceDialog"
      title="数据源管理"
      width="600px"
    >
      <div class="data-source-list">
        <div
          v-for="source in dataSources"
          :key="source.id"
          class="data-source-item"
        >
          <div class="source-info">
            <h4>{{ source.name }}</h4>
            <p>{{ source.description }}</p>
            <small>{{ source.base_url }}</small>
          </div>
          <div class="source-status">
            <el-tag :type="source.is_active ? 'success' : 'danger'">
              {{ source.is_active ? '启用' : '禁用' }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/services/api'

export default {
  name: 'AwardSearch',
  setup() {
    // 响应式数据
    const dataSources = ref([])
    const businessFields = ref([])
    const searchTasks = ref([])
    const selectedTask = ref(null)
    const searchResults = ref([])
    const searching = ref(false)
    
    // 对话框状态
    const showDataSourceDialog = ref(false)
    
    // 搜索表单
    const searchForm = reactive({
      data_source_id: 1,
      law_firm_name: '',
      search_year: new Date().getFullYear().toString(),
      business_field: '',
      search_keywords: ''
    })
    
    // 快速搜索模板
    const quickTemplates = ref([
      {
        id: 1,
        name: '钱伯斯2024',
        data_source_id: 1,
        search_year: '2024'
      },
      {
        id: 2,
        name: 'Legal 500 2024',
        data_source_id: 2,
        search_year: '2024'
      },
      {
        id: 3,
        name: '钱伯斯2023',
        data_source_id: 1,
        search_year: '2023'
      }
    ])
    
    // 计算属性
    const hasUnimportedResults = computed(() => {
      return searchResults.value.some(result => result.status === 'pending')
    })
    
    // 方法
    const loadDataSources = async () => {
      try {
        const response = await api.get('/api/search/sources')
        dataSources.value = response.data
      } catch (error) {
        ElMessage.error('加载数据源失败')
      }
    }
    
    const loadBusinessFields = async () => {
      try {
        const response = await api.get('/api/config/business-fields')
        businessFields.value = response.data.business_fields
      } catch (error) {
        ElMessage.error('加载业务领域失败')
      }
    }
    
    const loadTasks = async () => {
      try {
        const response = await api.get('/api/search/tasks')
        searchTasks.value = response.data
      } catch (error) {
        ElMessage.error('加载搜索任务失败')
      }
    }
    
    const loadResults = async () => {
      if (!selectedTask.value) return
      
      try {
        const response = await api.get('/api/search/results', {
          params: { task_id: selectedTask.value.id }
        })
        searchResults.value = response.data
      } catch (error) {
        ElMessage.error('加载搜索结果失败')
      }
    }
    
    const startSearch = async () => {
      if (!searchForm.law_firm_name || !searchForm.search_year) {
        ElMessage.warning('请填写律师事务所名称和搜索年份')
        return
      }
      
      searching.value = true
      try {
        const taskData = {
          ...searchForm,
          task_name: `搜索${searchForm.law_firm_name}在${searchForm.search_year}年的奖项`,
          search_keywords: searchForm.search_keywords ? searchForm.search_keywords.split(',').map(k => k.trim()) : []
        }
        
        const response = await api.post('/api/search/tasks', taskData)
        ElMessage.success('搜索任务已创建，正在后台执行')
        
        // 刷新任务列表
        await loadTasks()
        
        // 重置表单
        resetForm()
      } catch (error) {
        ElMessage.error('创建搜索任务失败')
      } finally {
        searching.value = false
      }
    }
    
    const resetForm = () => {
      Object.assign(searchForm, {
        data_source_id: 1,
        law_firm_name: '',
        search_year: new Date().getFullYear().toString(),
        business_field: '',
        search_keywords: ''
      })
    }
    
    const useTemplate = (template) => {
      searchForm.data_source_id = template.data_source_id
      searchForm.search_year = template.search_year
    }
    
    const selectTask = async (task) => {
      selectedTask.value = task
      await loadResults()
    }
    
    const viewTaskResults = (task) => {
      selectTask(task)
    }
    
    const deleteTask = async (task) => {
      try {
        await ElMessageBox.confirm('确定要删除这个搜索任务吗？', '确认删除')
        await api.delete(`/api/search/tasks/${task.id}`)
        ElMessage.success('删除成功')
        await loadTasks()
        
        if (selectedTask.value?.id === task.id) {
          selectedTask.value = null
          searchResults.value = []
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    const importResult = async (result) => {
      try {
        await api.post(`/api/search/results/${result.id}/import`)
        ElMessage.success('导入成功')
        await loadResults()
      } catch (error) {
        ElMessage.error('导入失败')
      }
    }
    
    const importAllResults = async () => {
      const unimportedResults = searchResults.value.filter(result => result.status === 'pending')
      
      if (unimportedResults.length === 0) {
        ElMessage.warning('没有可导入的结果')
        return
      }
      
      try {
        await ElMessageBox.confirm(`确定要导入所有 ${unimportedResults.length} 个结果吗？`, '确认批量导入')
        
        for (const result of unimportedResults) {
          await api.post(`/api/search/results/${result.id}/import`)
        }
        
        ElMessage.success(`成功导入 ${unimportedResults.length} 个结果`)
        await loadResults()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量导入失败')
        }
      }
    }
    
    const viewSource = (result) => {
      if (result.source_url) {
        window.open(result.source_url, '_blank')
      } else {
        ElMessage.warning('没有来源链接')
      }
    }
    
    const deleteResult = async (result) => {
      try {
        await ElMessageBox.confirm('确定要删除这个搜索结果吗？', '确认删除')
        await api.delete(`/api/search/results/${result.id}`)
        ElMessage.success('删除成功')
        await loadResults()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    // 状态相关方法
    const getTaskStatusType = (status) => {
      const statusMap = {
        pending: 'info',
        running: 'warning',
        completed: 'success',
        failed: 'danger'
      }
      return statusMap[status] || 'info'
    }
    
    const getTaskStatusText = (status) => {
      const statusMap = {
        pending: '等待中',
        running: '执行中',
        completed: '已完成',
        failed: '失败'
      }
      return statusMap[status] || status
    }
    
    const getResultStatusType = (status) => {
      const statusMap = {
        pending: 'info',
        processed: 'warning',
        imported: 'success',
        ignored: 'danger'
      }
      return statusMap[status] || 'info'
    }
    
    const getResultStatusText = (status) => {
      const statusMap = {
        pending: '待处理',
        processed: '已处理',
        imported: '已导入',
        ignored: '已忽略'
      }
      return statusMap[status] || status
    }
    
    // 生命周期
    onMounted(() => {
      loadDataSources()
      loadBusinessFields()
      loadTasks()
    })
    
    return {
      // 数据
      dataSources,
      businessFields,
      searchTasks,
      selectedTask,
      searchResults,
      searching,
      showDataSourceDialog,
      searchForm,
      quickTemplates,
      hasUnimportedResults,
      
      // 方法
      loadDataSources,
      loadBusinessFields,
      loadTasks,
      loadResults,
      startSearch,
      resetForm,
      useTemplate,
      selectTask,
      viewTaskResults,
      deleteTask,
      importResult,
      importAllResults,
      viewSource,
      deleteResult,
      getTaskStatusType,
      getTaskStatusText,
      getResultStatusType,
      getResultStatusText
    }
  }
}
</script>

<style scoped lang="scss">
.award-search {
  padding: 20px;
  
  .header-card {
    margin-bottom: 20px;
    
    .header-content {
      h2 {
        margin: 0 0 10px 0;
        color: #303133;
      }
      
      p {
        margin: 0;
        color: #606266;
      }
    }
  }
  
  .main-content {
    .search-card,
    .task-card,
    .result-card {
      height: 700px;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }
  }
  
  .search-form {
    .source-option {
      display: flex;
      flex-direction: column;
      
      small {
        color: #909399;
        font-size: 12px;
      }
    }
  }
  
  .quick-templates {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #f0f0f0;
    
    h4 {
      margin: 0 0 12px 0;
      font-size: 14px;
      color: #303133;
    }
    
    .template-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }
  
  .task-list {
    .task-item {
      padding: 16px;
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      margin-bottom: 12px;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        border-color: #409eff;
        background-color: #f5f7fa;
      }
      
      &.active {
        border-color: #409eff;
        background-color: #ecf5ff;
      }
      
      .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        h4 {
          margin: 0;
          font-size: 14px;
        }
      }
      
      .task-info {
        margin-bottom: 12px;
        
        p {
          margin: 4px 0;
          font-size: 12px;
          color: #606266;
        }
      }
      
      .task-progress {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        
        .progress-text {
          font-size: 12px;
          color: #909399;
        }
      }
      
      .task-stats {
        display: flex;
        gap: 16px;
        margin-bottom: 12px;
        
        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
          
          .stat-value {
            font-size: 16px;
            font-weight: bold;
            
            &.success {
              color: #67c23a;
            }
            
            &.error {
              color: #f56c6c;
            }
          }
        }
      }
      
      .task-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
  
  .result-list {
    .result-item {
      padding: 16px;
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      margin-bottom: 12px;
      
      &.imported {
        background-color: #f0f9ff;
        border-color: #67c23a;
      }
      
      .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        h4 {
          margin: 0;
          font-size: 14px;
        }
      }
      
      .result-info {
        margin-bottom: 12px;
        
        p {
          margin: 4px 0;
          font-size: 12px;
          color: #606266;
        }
      }
      
      .result-actions {
        display: flex;
        gap: 8px;
      }
    }
    
    .empty-state {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 200px;
    }
  }
  
  .data-source-list {
    .data-source-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #f0f0f0;
      
      .source-info {
        h4 {
          margin: 0 0 4px 0;
          font-size: 14px;
        }
        
        p {
          margin: 0 0 4px 0;
          font-size: 12px;
          color: #606266;
        }
        
        small {
          color: #909399;
          font-size: 11px;
        }
      }
    }
  }
}
</style> 