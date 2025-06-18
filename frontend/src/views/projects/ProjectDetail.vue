<template>
  <div class="project-detail-container">
    <div class="page-header">
      <el-page-header @back="goBack" title="项目详情">
        <template #content>
          <div class="flex-center">
            <span class="project-title">{{ project.name || '加载中...' }}</span>
            <el-tag 
              v-if="project.status" 
              :type="getStatusType(project.status)"
              class="status-tag"
            >
              {{ getStatusLabel(project.status) }}
            </el-tag>
          </div>
        </template>
      </el-page-header>
      <div class="action-buttons">
        <el-button-group>
          <el-button type="primary" @click="generateDocument" :loading="generating">
            生成投标文档
          </el-button>
          <el-button type="info" @click="editProject">
            编辑项目
          </el-button>
        </el-button-group>
      </div>
    </div>

    <el-skeleton :loading="loading" animated>
      <template #template>
        <div class="skeleton-content">
          <el-skeleton-item variant="p" style="width: 100%" />
          <el-skeleton-item variant="text" style="width: 60%" />
          <el-skeleton-item variant="h3" style="width: 80%" />
          <el-skeleton-item variant="text" style="width: 90%" />
        </div>
      </template>

      <template #default>
        <!-- 项目基本信息 -->
        <el-card class="project-info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="项目名称" :span="2">{{ project.name }}</el-descriptions-item>
            <el-descriptions-item label="招标人">{{ project.tender_company || '无' }}</el-descriptions-item>
            <el-descriptions-item label="招标代理机构">{{ project.tender_agency || '无' }}</el-descriptions-item>
            <el-descriptions-item label="投标人">{{ project.bidder_name || '无' }}</el-descriptions-item>
            <el-descriptions-item label="投标截止日期">{{ formatDate(project.deadline) || '无' }}</el-descriptions-item>
            <el-descriptions-item label="项目描述" :span="2">
              {{ project.description || '无项目描述' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 章节管理 -->
        <el-card class="sections-card">
          <template #header>
            <div class="card-header">
              <h3>投标文档章节</h3>
              <el-button type="primary" @click="showSectionDialog">添加章节</el-button>
            </div>
          </template>

          <!-- 章节列表 -->
          <el-empty v-if="sections.length === 0" description="暂无章节，请添加" />
          <div v-else>
            <div 
              v-for="(section, index) in sections" 
              :key="section.id" 
              class="section-item"
            >
              <div class="section-header">
                <div class="section-title">
                  <span class="section-number">{{ index + 1 }}. </span>
                  <span>{{ section.title }}</span>
                </div>
                <div class="section-actions">
                  <el-button type="success" size="small" @click="showUploadDialog(section.id)">
                    上传文档
                  </el-button>
                  <el-button type="primary" size="small" @click="editSection(section)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" @click="deleteSection(section)">
                    删除
                  </el-button>
                </div>
              </div>

              <!-- 章节文档 -->
              <div class="section-documents">
                <el-empty 
                  v-if="!section.documents || section.documents.length === 0" 
                  :description="`暂无文档，请上传`" 
                  :image-size="60"
                />
                <div v-else class="document-list">
                  <div 
                    v-for="doc in section.documents" 
                    :key="doc.id" 
                    class="document-item"
                  >
                    <div class="document-info">
                      <el-icon :class="getFileIconClass(doc.file_type)"></el-icon>
                      <span class="document-name">{{ doc.original_filename }}</span>
                      <el-tag 
                        size="small" 
                        :type="getDocumentStatusType(doc.processing_status)"
                      >
                        {{ getDocumentStatusLabel(doc.processing_status) }}
                      </el-tag>
                    </div>
                    <div class="document-actions">
                      <el-button 
                        type="danger" 
                        size="small"
                        circle
                        @click="deleteDocument(doc)"
                        title="删除文档"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </template>
    </el-skeleton>

    <!-- 添加/编辑章节对话框 -->
    <el-dialog
      v-model="sectionDialog.visible"
      :title="sectionDialog.isEdit ? '编辑章节' : '添加章节'"
      width="500px"
      @closed="resetSectionForm"
    >
      <el-form
        ref="sectionFormRef"
        :model="sectionForm"
        :rules="sectionRules"
        label-position="top"
        status-icon
      >
        <el-form-item label="章节标题" prop="title">
          <el-input v-model="sectionForm.title" placeholder="请输入章节标题"></el-input>
        </el-form-item>

        <el-form-item label="章节描述" prop="description">
          <el-input
            v-model="sectionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入章节描述（可选）"
          ></el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="sectionDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitSectionForm" :loading="sectionDialog.loading">
          {{ sectionDialog.isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传文档对话框 -->
    <el-dialog
      v-model="uploadDialog.visible"
      title="上传文档"
      width="500px"
    >
      <el-upload
        ref="uploadRef"
        class="document-uploader"
        drag
        :action="`/api/projects/sections/${uploadDialog.sectionId}/documents`"
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :file-list="uploadDialog.fileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持PDF、Word、图片等文档，将自动转换为Word格式
          </div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="uploadDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="uploadFiles" :loading="uploading">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 生成文档结果对话框 -->
    <el-dialog
      v-model="generateDialog.visible"
      title="文档生成结果"
      width="500px"
    >
      <el-result
        :icon="generateDialog.success ? 'success' : 'error'"
        :title="generateDialog.success ? '文档生成成功' : '文档生成失败'"
        :sub-title="generateDialog.message"
      >
        <template #extra>
          <el-button v-if="generateDialog.success" type="primary" @click="downloadGeneratedFile">
            下载文档
          </el-button>
          <el-button @click="generateDialog.visible = false">关闭</el-button>
        </template>
      </el-result>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, UploadFilled } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

export default {
  name: 'ProjectDetail',
  components: {
    Delete,
    UploadFilled
  },

  setup() {
    // 路由信息
    const route = useRoute()
    const router = useRouter()
    const projectId = computed(() => route.params.id)

    // 项目数据
    const project = ref({})
    const sections = ref([])
    const loading = ref(true)
    const generating = ref(false)

    // 章节对话框状态
    const sectionFormRef = ref(null)
    const sectionDialog = reactive({
      visible: false,
      isEdit: false,
      editId: null,
      loading: false
    })

    // 章节表单
    const sectionForm = reactive({
      title: '',
      description: '',
      order: 0
    })

    // 章节表单验证规则
    const sectionRules = {
      title: [
        { required: true, message: '请输入章节标题', trigger: 'blur' },
        { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
      ]
    }

    // 上传对话框状态
    const uploadRef = ref(null)
    const uploadDialog = reactive({
      visible: false,
      sectionId: null,
      fileList: []
    })
    const uploading = ref(false)

    // 文档生成对话框
    const generateDialog = reactive({
      visible: false,
      success: false,
      message: '',
      downloadUrl: ''
    })

    // 获取项目详情
    const fetchProject = async () => {
      loading.value = true
      try {
        const data = await apiService.getProject(projectId.value)
        project.value = data
      } catch (error) {
        console.error('获取项目详情失败:', error)
        ElMessage.error('获取项目详情失败')
      } finally {
        loading.value = false
      }
    }

    // 获取章节列表
    const fetchSections = async () => {
      try {
        const sectionsData = await apiService.getSections(projectId.value)
        
        // 获取每个章节的文档
        for (const section of sectionsData) {
          try {
            const documents = await apiService.getSectionDocuments(section.id)
            section.documents = documents
          } catch (error) {
            console.error(`获取章节 ${section.id} 的文档失败:`, error)
            section.documents = []
          }
        }
        
        sections.value = sectionsData
      } catch (error) {
        console.error('获取章节列表失败:', error)
        ElMessage.error('获取章节列表失败')
      }
    }

    // 显示添加章节对话框
    const showSectionDialog = () => {
      sectionDialog.isEdit = false
      sectionDialog.editId = null
      sectionDialog.visible = true
    }

    // 编辑章节
    const editSection = (section) => {
      sectionDialog.isEdit = true
      sectionDialog.editId = section.id
      sectionForm.title = section.title
      sectionForm.description = section.description || ''
      sectionDialog.visible = true
    }

    // 重置章节表单
    const resetSectionForm = () => {
      sectionForm.title = ''
      sectionForm.description = ''
      if (sectionFormRef.value) {
        sectionFormRef.value.resetFields()
      }
    }

    // 提交章节表单
    const submitSectionForm = async () => {
      if (!sectionFormRef.value) return

      await sectionFormRef.value.validate(async (valid) => {
        if (!valid) return

        sectionDialog.loading = true
        try {
          const data = { ...sectionForm }
          
          if (sectionDialog.isEdit) {
            await apiService.updateSection(sectionDialog.editId, data)
            ElMessage.success('章节更新成功')
          } else {
            await apiService.createSection(projectId.value, data)
            ElMessage.success('章节创建成功')
          }
          
          sectionDialog.visible = false
          fetchSections()
        } catch (error) {
          console.error('保存章节失败:', error)
          ElMessage.error('保存章节失败')
        } finally {
          sectionDialog.loading = false
        }
      })
    }

    // 删除章节
    const deleteSection = (section) => {
      ElMessageBox.confirm(
        `确定要删除章节 "${section.title}" 吗？此操作不可撤销，章节中的所有文档也将被删除。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
        .then(async () => {
          try {
            await apiService.deleteSection(section.id)
            ElMessage.success('章节删除成功')
            fetchSections()
          } catch (error) {
            console.error('删除章节失败:', error)
            ElMessage.error('删除章节失败')
          }
        })
        .catch(() => {
          // 用户取消，不做处理
        })
    }

    // 显示上传文档对话框
    const showUploadDialog = (sectionId) => {
      uploadDialog.sectionId = sectionId
      uploadDialog.fileList = []
      uploadDialog.visible = true
    }

    // 处理文件变更
    const handleFileChange = (file) => {
      console.log('文件变更:', file)
    }

    // 上传文件
    const uploadFiles = async () => {
      if (uploadRef.value && uploadDialog.fileList.length > 0) {
        uploading.value = true
        try {
          uploadRef.value.submit()
        } catch (error) {
          console.error('上传文件失败:', error)
          ElMessage.error('上传文件失败')
          uploading.value = false
        }
      } else {
        ElMessage.warning('请先选择文件')
      }
    }

    // 处理上传成功
    const handleUploadSuccess = (response) => {
      uploading.value = false
      ElMessage.success('文档上传成功')
      uploadDialog.visible = false
      uploadDialog.fileList = []
      fetchSections()
    }

    // 处理上传失败
    const handleUploadError = (error) => {
      uploading.value = false
      console.error('上传文件失败:', error)
      ElMessage.error('上传文件失败')
    }

    // 删除文档
    const deleteDocument = (document) => {
      ElMessageBox.confirm(
        `确定要删除文档 "${document.original_filename}" 吗？此操作不可撤销。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
        .then(async () => {
          try {
            await apiService.deleteDocument(document.id)
            ElMessage.success('文档删除成功')
            fetchSections()
          } catch (error) {
            console.error('删除文档失败:', error)
            ElMessage.error('删除文档失败')
          }
        })
        .catch(() => {
          // 用户取消，不做处理
        })
    }

    // 生成投标文档
    const generateDocument = async () => {
      generating.value = true
      try {
        const result = await apiService.generateProjectDocument(projectId.value)
        
        generateDialog.success = true
        generateDialog.message = result.message || '文档生成成功，点击下载按钮获取文档'
        generateDialog.downloadUrl = result.download_url
        generateDialog.visible = true
      } catch (error) {
        console.error('生成投标文档失败:', error)
        generateDialog.success = false
        generateDialog.message = '生成文档失败: ' + (error.response?.data?.detail || error.message || '未知错误')
        generateDialog.visible = true
      } finally {
        generating.value = false
      }
    }

    // 下载生成的文件
    const downloadGeneratedFile = () => {
      if (generateDialog.downloadUrl) {
        window.open(generateDialog.downloadUrl, '_blank')
      }
    }

    // 编辑项目
    const editProject = () => {
      router.push(`/projects/${projectId.value}/edit`)
    }

    // 返回列表
    const goBack = () => {
      router.push('/projects')
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '无'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
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

    // 获取文档处理状态标签
    const getDocumentStatusLabel = (status) => {
      switch (status) {
        case 'pending':
          return '待处理'
        case 'processing':
          return '处理中'
        case 'completed':
          return '已完成'
        case 'failed':
          return '处理失败'
        default:
          return '未知'
      }
    }

    // 获取文档处理状态标签类型
    const getDocumentStatusType = (status) => {
      switch (status) {
        case 'pending':
          return 'info'
        case 'processing':
          return 'warning'
        case 'completed':
          return 'success'
        case 'failed':
          return 'danger'
        default:
          return 'info'
      }
    }

    // 获取文件图标类名
    const getFileIconClass = (fileType) => {
      if (!fileType) return 'el-icon-document'
      
      fileType = fileType.toLowerCase()
      
      if (fileType === 'pdf') {
        return 'el-icon-document-pdf'
      } else if (['doc', 'docx'].includes(fileType)) {
        return 'el-icon-document-word'
      } else if (['jpg', 'jpeg', 'png', 'gif'].includes(fileType)) {
        return 'el-icon-document-image'
      } else {
        return 'el-icon-document'
      }
    }

    // 在组件挂载时获取项目详情
    onMounted(async () => {
      await fetchProject()
      await fetchSections()
    })

    return {
      project,
      sections,
      loading,
      generating,
      sectionFormRef,
      sectionDialog,
      sectionForm,
      sectionRules,
      uploadRef,
      uploadDialog,
      uploading,
      generateDialog,
      fetchProject,
      fetchSections,
      showSectionDialog,
      editSection,
      resetSectionForm,
      submitSectionForm,
      deleteSection,
      showUploadDialog,
      handleFileChange,
      uploadFiles,
      handleUploadSuccess,
      handleUploadError,
      deleteDocument,
      generateDocument,
      downloadGeneratedFile,
      editProject,
      goBack,
      formatDate,
      getStatusLabel,
      getStatusType,
      getDocumentStatusLabel,
      getDocumentStatusType,
      getFileIconClass
    }
  }
}
</script>

<style scoped>
.project-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.project-title {
  font-size: 18px;
  font-weight: bold;
  margin-right: 10px;
}

.status-tag {
  margin-left: 8px;
}

.skeleton-content {
  padding: 20px;
}

.project-info-card,
.sections-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-item {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
}

.section-number {
  color: #409eff;
  margin-right: 4px;
}

.section-documents {
  padding: 8px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.document-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  background-color: white;
  border: 1px solid #e6e6e6;
}

.document-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.document-name {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.flex-center {
  display: flex;
  align-items: center;
}

.document-uploader {
  width: 100%;
}
</style> 