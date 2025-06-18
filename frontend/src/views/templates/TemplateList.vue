<template>
  <div class="templates-container">
    <div class="page-header">
      <h1>文档模板管理</h1>
      <el-button type="primary" @click="showUploadDialog">上传新模板</el-button>
    </div>

    <el-card class="filter-card">
      <div class="filter-container">
        <el-select
          v-model="filter.type"
          placeholder="模板类型"
          clearable
          @change="handleFilterChange"
        >
          <el-option label="封面模板" value="cover" />
          <el-option label="投标函" value="bid_form" />
          <el-option label="授权委托书" value="authorization" />
          <el-option label="投标一览表" value="bid_overview" />
          <el-option label="投标封条" value="seal" />
          <el-option label="其他" value="other" />
        </el-select>

        <el-select
          v-model="filter.default"
          placeholder="是否默认模板"
          clearable
          @change="handleFilterChange"
        >
          <el-option label="默认模板" :value="true" />
          <el-option label="非默认模板" :value="false" />
        </el-select>
      </div>
    </el-card>

    <el-card v-if="loading" class="loading-card">
      <div class="loading-container">
        <el-spinner text="加载中..." />
      </div>
    </el-card>

    <el-empty v-else-if="templates.length === 0" description="暂无模板" />

    <div v-else class="template-grid">
      <el-card
        v-for="template in templates"
        :key="template.id"
        class="template-card"
        shadow="hover"
        @click="viewTemplate(template.id)"
      >
        <div class="template-icon">
          <el-icon size="40px"><Document /></el-icon>
        </div>
        <div class="template-info">
          <h3 class="template-name">{{ template.name }}</h3>
          <div class="template-type">
            <el-tag size="small">{{ getTemplateTypeLabel(template.type) }}</el-tag>
            <el-tag v-if="template.is_default" type="success" size="small" class="default-tag">默认</el-tag>
          </div>
          <p class="template-description">{{ template.description || '无描述信息' }}</p>
        </div>
      </el-card>
    </div>

    <!-- 上传模板对话框 -->
    <el-dialog
      v-model="uploadDialog.visible"
      title="上传模板"
      width="500px"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-position="top"
        status-icon
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入模板名称"></el-input>
        </el-form-item>

        <el-form-item label="模板类型" prop="template_type">
          <el-select v-model="uploadForm.template_type" placeholder="请选择模板类型" style="width: 100%">
            <el-option label="封面模板" value="cover" />
            <el-option label="投标函" value="bid_form" />
            <el-option label="授权委托书" value="authorization" />
            <el-option label="投标一览表" value="bid_overview" />
            <el-option label="投标封条" value="seal" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="模板描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述（可选）"
          ></el-input>
        </el-form-item>

        <el-form-item label="是否设为默认模板">
          <el-switch v-model="uploadForm.is_default" />
        </el-form-item>

        <el-form-item label="模板文件" prop="file">
          <el-upload
            ref="fileUploadRef"
            class="template-file-uploader"
            action="#"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="uploadForm.fileList"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                请上传Word文档模板(.docx格式)
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="自动分析字段">
          <el-switch v-model="uploadForm.analyze" />
          <div class="field-hint">
            开启后会自动分析模板中的占位符字段，用于后续替换
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="uploadDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="uploadTemplate" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

export default {
  name: 'TemplateList',
  components: {
    Document
  },

  setup() {
    const router = useRouter()
    
    // 数据
    const templates = ref([])
    const loading = ref(true)
    
    // 过滤条件
    const filter = reactive({
      type: '',
      default: ''
    })
    
    // 上传对话框
    const uploadDialog = reactive({
      visible: false
    })
    
    // 上传表单引用
    const uploadFormRef = ref(null)
    const fileUploadRef = ref(null)
    
    // 上传状态
    const uploading = ref(false)
    
    // 上传表单数据
    const uploadForm = reactive({
      name: '',
      template_type: '',
      description: '',
      is_default: false,
      analyze: true,
      fileList: [],
      file: null
    })
    
    // 上传表单验证规则
    const uploadRules = {
      name: [
        { required: true, message: '请输入模板名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
      ],
      template_type: [
        { required: true, message: '请选择模板类型', trigger: 'change' }
      ],
      file: [
        { required: true, message: '请上传模板文件', trigger: 'change' }
      ]
    }
    
    // 获取模板列表
    const fetchTemplates = async () => {
      loading.value = true
      try {
        const params = {}
        
        if (filter.type) {
          params.template_type = filter.type
        }
        
        if (filter.default !== '') {
          params.is_default = filter.default
        }
        
        const response = await apiService.getTemplates(params)
        templates.value = response
      } catch (error) {
        console.error('获取模板列表失败:', error)
        ElMessage.error('获取模板列表失败')
      } finally {
        loading.value = false
      }
    }
    
    // 显示上传对话框
    const showUploadDialog = () => {
      resetUploadForm()
      uploadDialog.visible = true
    }
    
    // 重置上传表单
    const resetUploadForm = () => {
      uploadForm.name = ''
      uploadForm.template_type = ''
      uploadForm.description = ''
      uploadForm.is_default = false
      uploadForm.analyze = true
      uploadForm.fileList = []
      uploadForm.file = null
      
      if (uploadFormRef.value) {
        uploadFormRef.value.resetFields()
      }
    }
    
    // 文件变更处理
    const handleFileChange = (file) => {
      uploadForm.file = file.raw
    }
    
    // 文件移除处理
    const handleFileRemove = () => {
      uploadForm.file = null
    }
    
    // 上传模板
    const uploadTemplate = async () => {
      if (!uploadFormRef.value) return
      
      await uploadFormRef.value.validate(async (valid) => {
        if (!valid) return
        
        if (!uploadForm.file) {
          ElMessage.warning('请选择模板文件')
          return
        }
        
        uploading.value = true
        try {
          // 准备表单数据
          const formData = new FormData()
          formData.append('name', uploadForm.name)
          formData.append('template_type', uploadForm.template_type)
          formData.append('description', uploadForm.description || '')
          formData.append('is_default', uploadForm.is_default)
          formData.append('analyze', uploadForm.analyze)
          formData.append('file', uploadForm.file)
          
          // 发送请求
          await apiService.uploadTemplate({
            name: uploadForm.name,
            template_type: uploadForm.template_type,
            description: uploadForm.description || '',
            is_default: uploadForm.is_default,
            analyze: uploadForm.analyze,
            file: uploadForm.file
          })
          
          ElMessage.success('模板上传成功')
          uploadDialog.visible = false
          fetchTemplates()
        } catch (error) {
          console.error('上传模板失败:', error)
          ElMessage.error('上传模板失败')
        } finally {
          uploading.value = false
        }
      })
    }
    
    // 查看模板详情
    const viewTemplate = (templateId) => {
      router.push(`/templates/${templateId}`)
    }
    
    // 过滤条件变化处理
    const handleFilterChange = () => {
      fetchTemplates()
    }
    
    // 获取模板类型标签
    const getTemplateTypeLabel = (type) => {
      const types = {
        cover: '封面模板',
        bid_form: '投标函',
        authorization: '授权委托书',
        bid_overview: '投标一览表',
        seal: '投标封条',
        other: '其他'
      }
      
      return types[type] || type
    }
    
    // 组件挂载时获取数据
    onMounted(() => {
      fetchTemplates()
    })
    
    return {
      templates,
      loading,
      filter,
      uploadDialog,
      uploadFormRef,
      fileUploadRef,
      uploading,
      uploadForm,
      uploadRules,
      fetchTemplates,
      showUploadDialog,
      handleFileChange,
      handleFileRemove,
      uploadTemplate,
      viewTemplate,
      handleFilterChange,
      getTemplateTypeLabel
    }
  }
}
</script>

<style scoped>
.templates-container {
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

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.template-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.template-card:hover {
  transform: translateY(-5px);
}

.template-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
  color: #409eff;
}

.template-info {
  text-align: center;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-type {
  margin-bottom: 8px;
}

.default-tag {
  margin-left: 5px;
}

.template-description {
  font-size: 12px;
  color: #606266;
  margin: 0;
  height: 36px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.template-file-uploader {
  width: 100%;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style> 