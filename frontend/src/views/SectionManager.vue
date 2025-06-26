<template>
  <div class="section-manager">
    <el-card class="header-card">
      <div class="header-content">
        <h2>智能章节管理</h2>
        <p>管理投标项目的章节类型、数据映射和智能推荐</p>
      </div>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <!-- 左侧：章节类型管理 -->
      <el-col :span="8">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span>章节类型管理</span>
              <el-button type="primary" size="small" @click="showSectionTypeDialog = true">
                新增类型
              </el-button>
            </div>
          </template>
          
          <div class="section-types">
            <el-tree
              :data="sectionTypes"
              :props="treeProps"
              node-key="id"
              @node-click="handleSectionTypeClick"
            >
              <template #default="{ node, data }">
                <div class="section-type-node">
                  <el-icon :color="data.color">
                    <component :is="data.icon || 'Document'" />
                  </el-icon>
                  <span>{{ data.display_name || data.name }}</span>
                  <div class="node-actions">
                    <el-button type="text" size="small" @click.stop="editSectionType(data)">
                      编辑
                    </el-button>
                    <el-button type="text" size="small" @click.stop="deleteSectionType(data)">
                      删除
                    </el-button>
                  </div>
                </div>
              </template>
            </el-tree>
          </div>
        </el-card>
      </el-col>

      <!-- 中间：项目管理 -->
      <el-col :span="8">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span>项目管理</span>
              <el-select v-model="selectedProject" placeholder="选择项目" @change="loadProjectSections">
                <el-option
                  v-for="project in projects"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </div>
          </template>
          
          <div class="project-sections">
            <div v-if="selectedProject">
              <div class="section-list">
                <div
                  v-for="section in projectSections"
                  :key="section.id"
                  class="section-item"
                  :class="{ active: selectedSection?.id === section.id }"
                  @click="selectSection(section)"
                >
                  <div class="section-info">
                    <h4>{{ section.title }}</h4>
                    <p>{{ section.description }}</p>
                  </div>
                  <div class="section-actions">
                    <el-button type="text" size="small" @click.stop="showDataMapping(section)">
                      数据映射
                    </el-button>
                    <el-button type="text" size="small" @click.stop="getRecommendations(section)">
                      智能推荐
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <el-empty description="请选择一个项目" />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：数据映射和推荐 -->
      <el-col :span="8">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <span>数据映射</span>
              <el-button v-if="selectedSection" type="primary" size="small" @click="showMappingDialog = true">
                添加映射
              </el-button>
            </div>
          </template>
          
          <div class="data-mappings">
            <div v-if="selectedSection">
              <div class="mapping-list">
                <div
                  v-for="mapping in sectionMappings"
                  :key="mapping.id"
                  class="mapping-item"
                >
                  <div class="mapping-info">
                    <el-tag :type="mapping.data_type === 'award' ? 'success' : 'warning'">
                      {{ mapping.data_type === 'award' ? '奖项' : '业绩' }}
                    </el-tag>
                    <span class="mapping-title">{{ mapping.custom_title || mapping.data?.title || mapping.data?.project_name }}</span>
                  </div>
                  <div class="mapping-actions">
                    <el-button type="text" size="small" @click="editMapping(mapping)">
                      编辑
                    </el-button>
                    <el-button type="text" size="small" @click="deleteMapping(mapping)">
                      删除
                    </el-button>
                  </div>
                </div>
              </div>
              
              <!-- 智能推荐结果 -->
              <div v-if="recommendations.length > 0" class="recommendations">
                <h4>智能推荐</h4>
                <div class="recommendation-list">
                  <div
                    v-for="item in recommendations"
                    :key="item.id"
                    class="recommendation-item"
                  >
                    <div class="recommendation-info">
                      <el-tag :type="item.type === 'award' ? 'success' : 'warning'" size="small">
                        {{ item.type === 'award' ? '奖项' : '业绩' }}
                      </el-tag>
                      <span>{{ item.title || item.project_name }}</span>
                    </div>
                    <el-button type="text" size="small" @click="addToMapping(item)">
                      添加
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <el-empty description="请选择一个章节" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 章节类型对话框 -->
    <el-dialog
      v-model="showSectionTypeDialog"
      :title="editingSectionType ? '编辑章节类型' : '新增章节类型'"
      width="500px"
    >
      <el-form :model="sectionTypeForm" label-width="100px">
        <el-form-item label="类型名称">
          <el-input v-model="sectionTypeForm.name" placeholder="请输入类型名称" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="sectionTypeForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="sectionTypeForm.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="sectionTypeForm.icon" placeholder="请输入图标名称" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="sectionTypeForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSectionTypeDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSectionType">保存</el-button>
      </template>
    </el-dialog>

    <!-- 数据映射对话框 -->
    <el-dialog
      v-model="showMappingDialog"
      title="添加数据映射"
      width="600px"
    >
      <el-form :model="mappingForm" label-width="100px">
        <el-form-item label="数据类型">
          <el-radio-group v-model="mappingForm.data_type">
            <el-radio label="award">奖项</el-radio>
            <el-radio label="performance">业绩</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择数据">
          <el-select
            v-model="mappingForm.data_id"
            placeholder="请选择数据"
            filterable
            remote
            :remote-method="searchData"
            :loading="searchLoading"
          >
            <el-option
              v-for="item in searchResults"
              :key="item.id"
              :label="item.title || item.project_name"
              :value="item.id"
            >
              <div class="option-content">
                <span>{{ item.title || item.project_name }}</span>
                <small>{{ item.brand || item.client_name }} - {{ item.year }}</small>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="自定义标题">
          <el-input v-model="mappingForm.custom_title" placeholder="可选，留空使用原标题" />
        </el-form-item>
        <el-form-item label="自定义描述">
          <el-input v-model="mappingForm.custom_description" type="textarea" placeholder="可选，留空使用原描述" />
        </el-form-item>
        <el-form-item label="显示顺序">
          <el-input-number v-model="mappingForm.display_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMappingDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMapping">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/services/api'

export default {
  name: 'SectionManager',
  setup() {
    // 响应式数据
    const sectionTypes = ref([])
    const projects = ref([])
    const selectedProject = ref(null)
    const projectSections = ref([])
    const selectedSection = ref(null)
    const sectionMappings = ref([])
    const recommendations = ref([])
    
    // 对话框状态
    const showSectionTypeDialog = ref(false)
    const showMappingDialog = ref(false)
    const editingSectionType = ref(null)
    
    // 表单数据
    const sectionTypeForm = reactive({
      name: '',
      display_name: '',
      description: '',
      icon: '',
      color: '#409EFF',
      is_active: true,
      related_award_types: [],
      related_performance_types: []
    })
    
    const mappingForm = reactive({
      data_type: 'award',
      data_id: null,
      custom_title: '',
      custom_description: '',
      display_order: 0,
      is_visible: true
    })
    
    // 搜索相关
    const searchResults = ref([])
    const searchLoading = ref(false)
    
    // 树形配置
    const treeProps = {
      children: 'children',
      label: 'display_name'
    }
    
    // 方法
    const loadSectionTypes = async () => {
      try {
        const response = await api.get('/sections/types')
        sectionTypes.value = response.data
      } catch (error) {
        console.error('获取章节类型失败:', error)
      }
    }
    
    const loadProjects = async () => {
      try {
        const response = await api.get('/projects')
        projects.value = response.data
      } catch (error) {
        console.error('获取项目列表失败:', error)
      }
    }
    
    const loadProjectSections = async () => {
      if (!selectedProject.value) return
      
      try {
        const response = await api.get(`/projects/${selectedProject.value}/sections`)
        projectSections.value = response.data.sections
      } catch (error) {
        ElMessage.error('加载项目章节失败')
      }
    }
    
    const selectSection = async (section) => {
      selectedSection.value = section
      await loadSectionMappings(section.id)
    }
    
    const loadSectionMappings = async (sectionId) => {
      try {
        const response = await api.get(`/sections/${sectionId}/mappings`)
        sectionMappings.value = response.data
      } catch (error) {
        ElMessage.error('加载数据映射失败')
      }
    }
    
    const handleSectionTypeClick = (data) => {
      console.log('点击章节类型:', data)
    }
    
    const editSectionType = (data) => {
      editingSectionType.value = data
      Object.assign(sectionTypeForm, data)
      showSectionTypeDialog.value = true
    }
    
    const deleteSectionType = async (data) => {
      try {
        await ElMessageBox.confirm('确定要删除这个章节类型吗？', '确认删除')
        await api.delete(`/sections/types/${data.id}`)
        ElMessage.success('删除成功')
        await loadSectionTypes()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    const saveSectionType = async () => {
      try {
        if (editingSectionType.value) {
          await api.put(`/sections/types/${editingSectionType.value.id}`, sectionTypeForm)
        } else {
          await api.post('/sections/types', sectionTypeForm)
        }
        ElMessage.success('保存成功')
        showSectionTypeDialog.value = false
        await loadSectionTypes()
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }
    
    const showDataMapping = (section) => {
      selectSection(section)
      showMappingDialog.value = true
    }
    
    const getRecommendations = async (section) => {
      try {
        const response = await api.post('/sections/recommendations', {
          section_title: section.title,
          section_description: section.description,
          project_id: selectedProject.value
        })
        recommendations.value = [
          ...response.data.awards.map(item => ({ ...item, type: 'award' })),
          ...response.data.performances.map(item => ({ ...item, type: 'performance' }))
        ]
      } catch (error) {
        ElMessage.error('获取推荐失败')
      }
    }
    
    const searchData = async (query) => {
      if (!query) return
      
      searchLoading.value = true
      try {
        const endpoint = mappingForm.data_type === 'award' ? '/awards' : '/performances'
        const response = await api.get(endpoint, {
          params: { search: query, limit: 10 }
        })
        searchResults.value = response.data.awards || response.data.performances || []
      } catch (error) {
        ElMessage.error('搜索失败')
      } finally {
        searchLoading.value = false
      }
    }
    
    const saveMapping = async () => {
      if (!selectedSection.value) return
      
      try {
        await api.post(`/sections/${selectedSection.value.id}/mappings`, mappingForm)
        ElMessage.success('添加映射成功')
        showMappingDialog.value = false
        await loadSectionMappings(selectedSection.value.id)
      } catch (error) {
        ElMessage.error('添加映射失败')
      }
    }
    
    const editMapping = (mapping) => {
      Object.assign(mappingForm, mapping)
      showMappingDialog.value = true
    }
    
    const deleteMapping = async (mapping) => {
      try {
        await ElMessageBox.confirm('确定要删除这个映射吗？', '确认删除')
        await api.delete(`/sections/mappings/${mapping.id}`)
        ElMessage.success('删除成功')
        await loadSectionMappings(selectedSection.value.id)
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }
    
    const addToMapping = async (item) => {
      mappingForm.data_type = item.type
      mappingForm.data_id = item.id
      mappingForm.custom_title = item.title || item.project_name
      await saveMapping()
    }
    
    // 生命周期
    onMounted(() => {
      loadSectionTypes()
      loadProjects()
    })
    
    return {
      // 数据
      sectionTypes,
      projects,
      selectedProject,
      projectSections,
      selectedSection,
      sectionMappings,
      recommendations,
      showSectionTypeDialog,
      showMappingDialog,
      editingSectionType,
      sectionTypeForm,
      mappingForm,
      searchResults,
      searchLoading,
      treeProps,
      
      // 方法
      loadSectionTypes,
      loadProjects,
      loadProjectSections,
      selectSection,
      handleSectionTypeClick,
      editSectionType,
      deleteSectionType,
      saveSectionType,
      showDataMapping,
      getRecommendations,
      searchData,
      saveMapping,
      editMapping,
      deleteMapping,
      addToMapping
    }
  }
}
</script>

<style scoped lang="scss">
.section-manager {
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
    .section-card {
      height: 600px;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }
  }
  
  .section-types {
    .section-type-node {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;
      
      .node-actions {
        margin-left: auto;
        opacity: 0;
        transition: opacity 0.3s;
      }
      
      &:hover .node-actions {
        opacity: 1;
      }
    }
  }
  
  .project-sections {
    .section-list {
      .section-item {
        padding: 12px;
        border: 1px solid #e4e7ed;
        border-radius: 4px;
        margin-bottom: 8px;
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
        
        .section-info {
          h4 {
            margin: 0 0 4px 0;
            font-size: 14px;
          }
          
          p {
            margin: 0;
            font-size: 12px;
            color: #909399;
          }
        }
        
        .section-actions {
          margin-top: 8px;
        }
      }
    }
    
    .empty-state {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 200px;
    }
  }
  
  .data-mappings {
    .mapping-list {
      .mapping-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        
        .mapping-info {
          display: flex;
          align-items: center;
          gap: 8px;
          
          .mapping-title {
            font-size: 14px;
          }
        }
      }
    }
    
    .recommendations {
      margin-top: 20px;
      
      h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        color: #303133;
      }
      
      .recommendation-list {
        .recommendation-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f0f0f0;
          
          .recommendation-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
          }
        }
      }
    }
    
    .empty-state {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 200px;
    }
  }
  
  .option-content {
    display: flex;
    flex-direction: column;
    
    small {
      color: #909399;
      font-size: 12px;
    }
  }
}
</style> 