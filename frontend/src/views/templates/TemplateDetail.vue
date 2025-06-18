<template>
  <div class="template-detail-container">
    <div class="page-header">
      <el-page-header @back="goBack" title="模板详情">
        <template #content>
          <div class="flex-center">
            <span class="template-title">{{ template.name || '加载中...' }}</span>
            <el-tag v-if="template.is_default" type="success" size="small" class="default-tag">
              默认模板
            </el-tag>
          </div>
        </template>
      </el-page-header>
      <div class="action-buttons">
        <el-button-group>
          <el-button type="primary" @click="analyzeTemplate">分析字段</el-button>
          <el-button type="danger" @click="confirmDelete">删除模板</el-button>
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
        <!-- 模板基本信息 -->
        <el-card class="template-info-card">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="模板名称" :span="2">{{ template.name }}</el-descriptions-item>
            <el-descriptions-item label="模板类型">{{ getTemplateTypeLabel(template.type) }}</el-descriptions-item>
            <el-descriptions-item label="默认模板">{{ template.is_default ? '是' : '否' }}</el-descriptions-item>
            <el-descriptions-item label="模板文件路径" :span="2">{{ template.file_path }}</el-descriptions-item>
            <el-descriptions-item label="模板描述" :span="2">
              {{ template.description || '无描述信息' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 模板字段列表 -->
        <el-card class="fields-card">
          <template #header>
            <div class="card-header">
              <h3>模板字段</h3>
              <el-button type="primary" @click="addField">添加字段</el-button>
            </div>
          </template>

          <el-empty v-if="fields.length === 0" description="暂无字段，点击"分析字段"按钮自动识别" />
          
          <el-table v-else :data="fields" border style="width: 100%">
            <el-table-column prop="field_name" label="字段名称" min-width="120" />
            <el-table-column prop="field_key" label="字段键名" min-width="120" />
            <el-table-column prop="field_type" label="字段类型" width="100">
              <template #default="scope">
                {{ getFieldTypeLabel(scope.row.field_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="placeholder" label="占位符" min-width="150" />
            <el-table-column prop="is_required" label="必填" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.is_required ? 'danger' : 'info'" size="small">
                  {{ scope.row.is_required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="scope">
                <el-button-group>
                  <el-button type="primary" size="small" @click="editField(scope.row)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" @click="deleteField(scope.row)">
                    删除
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 模板应用 -->
        <el-card class="apply-card">
          <template #header>
            <div class="card-header">
              <h3>应用模板</h3>
            </div>
          </template>

          <el-form ref="applyFormRef" :model="applyForm" label-width="100px">
            <el-form-item label="选择项目">
              <el-select v-model="applyForm.projectId" placeholder="请选择项目" style="width: 100%">
                <el-option
                  v-for="project in projects"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>

            <div v-if="applyForm.projectId" class="field-values-container">
              <h4>填写字段值</h4>
              <el-divider />

              <el-form-item 
                v-for="field in fields"
                :key="field.id"
                :label="field.field_name"
                :prop="`fieldValues.${field.field_key}`"
                :required="field.is_required"
              >
                <!-- 根据字段类型渲染不同的输入控件 -->
                <el-date-picker 
                  v-if="field.field_type === 'date'"
                  v-model="applyForm.fieldValues[field.field_key]"
                  type="date"
                  placeholder="选择日期"
                  style="width: 100%"
                />
                <el-input-number 
                  v-else-if="field.field_type === 'number'"
                  v-model="applyForm.fieldValues[field.field_key]"
                  :min="0"
                  style="width: 100%"
                />
                <el-input 
                  v-else
                  v-model="applyForm.fieldValues[field.field_key]"
                  :placeholder="`请输入${field.field_name}`"
                />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="applyTemplate" :loading="applying">
                  应用模板
                </el-button>
              </el-form-item>
            </div>
          </el-form>
        </el-card>
      </template>
    </el-skeleton>

    <!-- 字段编辑对话框 -->
    <el-dialog
      v-model="fieldDialog.visible"
      :title="fieldDialog.isEdit ? '编辑字段' : '添加字段'"
      width="500px"
    >
      <el-form
        ref="fieldFormRef"
        :model="fieldForm"
        :rules="fieldRules"
        label-position="top"
        status-icon
      >
        <el-form-item label="字段名称" prop="field_name">
          <el-input v-model="fieldForm.field_name" placeholder="请输入字段名称"></el-input>
        </el-form-item>

        <el-form-item label="字段键名" prop="field_key">
          <el-input v-model="fieldForm.field_key" placeholder="请输入字段键名"></el-input>
        </el-form-item>

        <el-form-item label="字段类型" prop="field_type">
          <el-select v-model="fieldForm.field_type" placeholder="请选择字段类型" style="width: 100%">
            <el-option label="文本" value="text" />
            <el-option label="日期" value="date" />
            <el-option label="数字" value="number" />
          </el-select>
        </el-form-item>

        <el-form-item label="占位符" prop="placeholder">
          <el-input v-model="fieldForm.placeholder" placeholder="模板中的占位符文本"></el-input>
        </el-form-item>

        <el-form-item label="是否必填">
          <el-switch v-model="fieldForm.is_required" />
        </el-form-item>

        <el-form-item label="字段描述">
          <el-input
            v-model="fieldForm.description"
            type="textarea"
            :rows="2"
            placeholder="请输入字段描述（可选）"
          ></el-input>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="fieldDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitField" :loading="fieldDialog.loading">
          {{ fieldDialog.isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 应用模板结果对话框 -->
    <el-dialog
      v-model="applyDialog.visible"
      title="模板应用结果"
      width="500px"
    >
      <el-result
        :icon="applyDialog.success ? 'success' : 'error'"
        :title="applyDialog.success ? '模板应用成功' : '模板应用失败'"
        :sub-title="applyDialog.message"
      >
        <template #extra>
          <el-button v-if="applyDialog.success" type="primary" @click="downloadGeneratedFile">
            下载文件
          </el-button>
          <el-button @click="applyDialog.visible = false">关闭</el-button>
        </template>
      </el-result>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiService } from '@/services/api'

export default {
  name: 'TemplateDetail',

  setup() {
    // 路由信息
    const route = useRoute()
    const router = useRouter()
    const templateId = computed(() => route.params.id)

    // 数据
    const template = ref({})
    const fields = ref([])
    const projects = ref([])
    const loading = ref(true)

    // 字段对话框
    const fieldFormRef = ref(null)
    const fieldDialog = reactive({
      visible: false,
      isEdit: false,
      editId: null,
      loading: false
    })

    // 字段表单
    const fieldForm = reactive({
      field_name: '',
      field_key: '',
      field_type: 'text',
      placeholder: '',
      is_required: false,
      description: ''
    })

    // 字段表单验证规则
    const fieldRules = {
      field_name: [
        { required: true, message: '请输入字段名称', trigger: 'blur' }
      ],
      field_key: [
        { required: true, message: '请输入字段键名', trigger: 'blur' },
        { pattern: /^[a-zA-Z0-9_]+$/, message: '键名只能包含字母、数字和下划线', trigger: 'blur' }
      ],
      field_type: [
        { required: true, message: '请选择字段类型', trigger: 'change' }
      ]
    }

    // 应用模板表单
    const applyFormRef = ref(null)
    const applyForm = reactive({
      projectId: '',
      fieldValues: {}
    })

    // 应用状态
    const applying = ref(false)

    // 应用结果对话框
    const applyDialog = reactive({
      visible: false,
      success: false,
      message: '',
      downloadUrl: ''
    })

    // 获取模板详情
    const fetchTemplate = async () => {
      loading.value = true
      try {
        const data = await apiService.getTemplate(templateId.value)
        template.value = data
      } catch (error) {
        console.error('获取模板详情失败:', error)
        ElMessage.error('获取模板详情失败')
      } finally {
        loading.value = false
      }
    }

    // 获取模板字段
    const fetchFields = async () => {
      try {
        const data = await apiService.getTemplateFields(templateId.value)
        fields.value = data
      } catch (error) {
        console.error('获取模板字段失败:', error)
        ElMessage.error('获取模板字段失败')
      }
    }

    // 获取项目列表
    const fetchProjects = async () => {
      try {
        const data = await apiService.getProjects()
        projects.value = data
      } catch (error) {
        console.error('获取项目列表失败:', error)
      }
    }

    // 分析模板字段
    const analyzeTemplate = async () => {
      try {
        ElMessageBox.confirm(
          '分析将覆盖当前已有的字段定义，确定要继续吗？',
          '确认操作',
          {
            type: 'warning'
          }
        ).then(async () => {
          loading.value = true
          try {
            const analyzedFields = await apiService.analyzeTemplate(templateId.value)
            fields.value = analyzedFields
            ElMessage.success('模板分析成功')
          } catch (error) {
            console.error('分析模板失败:', error)
            ElMessage.error('分析模板失败')
          } finally {
            loading.value = false
          }
        })
      } catch {
        // 用户取消，不做处理
      }
    }

    // 添加字段
    const addField = () => {
      fieldDialog.isEdit = false
      fieldDialog.editId = null
      resetFieldForm()
      fieldDialog.visible = true
    }

    // 编辑字段
    const editField = (field) => {
      fieldDialog.isEdit = true
      fieldDialog.editId = field.id

      fieldForm.field_name = field.field_name
      fieldForm.field_key = field.field_key
      fieldForm.field_type = field.field_type
      fieldForm.placeholder = field.placeholder
      fieldForm.is_required = field.is_required
      fieldForm.description = field.description || ''

      fieldDialog.visible = true
    }

    // 重置字段表单
    const resetFieldForm = () => {
      fieldForm.field_name = ''
      fieldForm.field_key = ''
      fieldForm.field_type = 'text'
      fieldForm.placeholder = ''
      fieldForm.is_required = false
      fieldForm.description = ''

      if (fieldFormRef.value) {
        fieldFormRef.value.resetFields()
      }
    }

    // 提交字段表单
    const submitField = async () => {
      if (!fieldFormRef.value) return

      await fieldFormRef.value.validate(async (valid) => {
        if (!valid) return

        fieldDialog.loading = true
        try {
          const data = { ...fieldForm }

          if (fieldDialog.isEdit) {
            await apiService.updateTemplateField(fieldDialog.editId, data)
            ElMessage.success('字段更新成功')
          } else {
            await apiService.createTemplateField(templateId.value, data)
            ElMessage.success('字段创建成功')
          }

          fieldDialog.visible = false
          fetchFields()
        } catch (error) {
          console.error('保存字段失败:', error)
          ElMessage.error('保存字段失败')
        } finally {
          fieldDialog.loading = false
        }
      })
    }

    // 删除字段
    const deleteField = (field) => {
      ElMessageBox.confirm(
        `确定要删除字段 "${field.field_name}" 吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await apiService.deleteTemplateField(field.id)
          ElMessage.success('字段删除成功')
          fetchFields()
        } catch (error) {
          console.error('删除字段失败:', error)
          ElMessage.error('删除字段失败')
        }
      }).catch(() => {
        // 用户取消，不做处理
      })
    }

    // 删除模板
    const confirmDelete = () => {
      ElMessageBox.confirm(
        `确定要删除模板 "${template.value.name}" 吗？此操作不可撤销，所有相关的字段也将被删除。`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          await apiService.deleteTemplate(templateId.value)
          ElMessage.success('模板删除成功')
          router.push('/templates')
        } catch (error) {
          console.error('删除模板失败:', error)
          ElMessage.error('删除模板失败')
        }
      }).catch(() => {
        // 用户取消，不做处理
      })
    }

    // 应用模板
    const applyTemplate = async () => {
      if (!applyForm.projectId) {
        ElMessage.warning('请选择项目')
        return
      }

      // 检查必填字段
      const requiredFields = fields.value.filter(f => f.is_required)
      for (const field of requiredFields) {
        if (!applyForm.fieldValues[field.field_key]) {
          ElMessage.warning(`请填写必填字段: ${field.field_name}`)
          return
        }
      }

      applying.value = true
      try {
        const result = await apiService.applyTemplate(
          templateId.value,
          applyForm.projectId,
          applyForm.fieldValues
        )

        applyDialog.success = true
        applyDialog.message = result.message || '模板应用成功'
        applyDialog.downloadUrl = result.download_url
        applyDialog.visible = true
      } catch (error) {
        console.error('应用模板失败:', error)
        applyDialog.success = false
        applyDialog.message = '应用模板失败: ' + (error.response?.data?.detail || error.message || '未知错误')
        applyDialog.visible = true
      } finally {
        applying.value = false
      }
    }

    // 下载生成的文件
    const downloadGeneratedFile = () => {
      if (applyDialog.downloadUrl) {
        window.open(applyDialog.downloadUrl, '_blank')
      }
    }

    // 返回列表
    const goBack = () => {
      router.push('/templates')
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

    // 获取字段类型标签
    const getFieldTypeLabel = (type) => {
      const types = {
        text: '文本',
        date: '日期',
        number: '数字'
      }
      
      return types[type] || type
    }

    // 组件挂载时获取数据
    onMounted(async () => {
      await fetchTemplate()
      await fetchFields()
      await fetchProjects()
    })

    return {
      template,
      fields,
      projects,
      loading,
      fieldFormRef,
      fieldDialog,
      fieldForm,
      fieldRules,
      applyFormRef,
      applyForm,
      applying,
      applyDialog,
      fetchTemplate,
      fetchFields,
      analyzeTemplate,
      addField,
      editField,
      resetFieldForm,
      submitField,
      deleteField,
      confirmDelete,
      applyTemplate,
      downloadGeneratedFile,
      goBack,
      getTemplateTypeLabel,
      getFieldTypeLabel
    }
  }
}
</script>

<style scoped>
.template-detail-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.template-title {
  font-size: 18px;
  font-weight: bold;
  margin-right: 10px;
}

.default-tag {
  margin-left: 8px;
}

.skeleton-content {
  padding: 20px;
}

.template-info-card,
.fields-card,
.apply-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex-center {
  display: flex;
  align-items: center;
}

.field-values-container {
  margin-top: 20px;
}
</style> 