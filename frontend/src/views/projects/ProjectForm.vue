<template>
  <div class="project-form-container">
    <el-page-header @back="goBack" :title="isEdit ? '编辑项目' : '新建项目'">
    </el-page-header>

    <el-card class="form-card">
      <el-form 
        ref="formRef" 
        :model="form" 
        :rules="rules" 
        label-position="top"
        status-icon
        v-loading="loading"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入投标项目名称"></el-input>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="招标人" prop="tender_company">
              <el-input v-model="form.tender_company" placeholder="请输入招标人名称"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="招标代理机构" prop="tender_agency">
              <el-input v-model="form.tender_agency" placeholder="请输入招标代理机构名称"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="投标人全称" prop="bidder_name">
          <el-input v-model="form.bidder_name" placeholder="请输入投标人全称"></el-input>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="投标截止日期" prop="deadline">
              <el-date-picker
                v-model="form.deadline"
                type="datetime"
                placeholder="请选择投标截止日期"
                style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择项目状态" style="width: 100%">
                <el-option label="草稿" value="draft"></el-option>
                <el-option label="进行中" value="in_progress"></el-option>
                <el-option label="已完成" value="completed"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述信息"
          ></el-input>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="submitForm">{{ isEdit ? '保存修改' : '创建项目' }}</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'

export default {
  name: 'ProjectForm',

  setup() {
    // 获取路由信息
    const route = useRoute()
    const router = useRouter()
    const projectId = computed(() => route.params.id)
    const isEdit = computed(() => route.meta.mode === 'edit')

    // 表单引用
    const formRef = ref(null)
    const loading = ref(false)

    // 表单数据
    const form = reactive({
      name: '',
      tender_company: '',
      tender_agency: '',
      bidder_name: '',
      deadline: '',
      status: 'draft',
      description: ''
    })

    // 表单校验规则
    const rules = {
      name: [
        { required: true, message: '请输入项目名称', trigger: 'blur' },
        { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
      ],
      bidder_name: [
        { required: true, message: '请输入投标人名称', trigger: 'blur' }
      ],
      tender_company: [
        { required: true, message: '请输入招标人名称', trigger: 'blur' }
      ]
    }

    // 获取项目详情
    const fetchProject = async () => {
      if (!isEdit.value || !projectId.value) return

      loading.value = true
      try {
        const response = await apiService.getProject(projectId.value)
        Object.assign(form, response)

        // 处理日期
        if (form.deadline) {
          form.deadline = new Date(form.deadline)
        }

      } catch (error) {
        console.error('获取项目详情失败:', error)
        ElMessage.error('获取项目详情失败')
      } finally {
        loading.value = false
      }
    }

    // 提交表单
    const submitForm = async () => {
      if (!formRef.value) return

      await formRef.value.validate(async (valid) => {
        if (!valid) return

        loading.value = true
        try {
          const data = { ...form }
          
          // 处理日期格式
          if (data.deadline && data.deadline instanceof Date) {
            data.deadline = data.deadline.toISOString()
          }

          // 编辑或创建
          if (isEdit.value) {
            await apiService.updateProject(projectId.value, data)
            ElMessage.success('项目更新成功')
          } else {
            await apiService.createProject(data)
            ElMessage.success('项目创建成功')
          }

          // 返回列表
          router.push('/projects')
        } catch (error) {
          console.error('保存项目失败:', error)
          ElMessage.error('保存项目失败')
        } finally {
          loading.value = false
        }
      })
    }

    // 返回列表
    const goBack = () => {
      router.push('/projects')
    }

    // 组件挂载时，如果是编辑模式，获取项目详情
    onMounted(() => {
      if (isEdit.value) {
        fetchProject()
      }
    })

    return {
      formRef,
      form,
      rules,
      loading,
      isEdit,
      submitForm,
      goBack
    }
  }
}
</script>

<style scoped>
.project-form-container {
  padding: 20px;
}

.form-card {
  margin-top: 20px;
}
</style> 