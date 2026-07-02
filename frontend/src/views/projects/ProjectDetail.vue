<template>
  <div class="project-detail" v-if="project">
    <div class="page-header">
      <div>
        <el-button text @click="$router.push('/projects')">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h1 class="page-title">{{ project.name }}</h1>
        <el-tag :type="getStatusType(project.status)" size="small">
          {{ getStatusLabel(project.status) }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button @click="showAddFilesDialog = true">
          <el-icon><Plus /></el-icon>
          添加文件
        </el-button>
        <el-button type="primary" @click="generateDocument">
          <el-icon><Document /></el-icon>
          生成投标文件
        </el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 项目信息 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span class="card-title">项目信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="招标人">{{ project.tender_company || '-' }}</el-descriptions-item>
            <el-descriptions-item label="招标代理">{{ project.tender_agency || '-' }}</el-descriptions-item>
            <el-descriptions-item label="投标人">{{ project.bidder_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="截止日期">
              <span :class="{ 'text-danger': isDeadlineSoon(project.deadline) }">
                {{ formatDate(project.deadline) }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="描述">{{ project.description || '-' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <!-- 章节管理 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">投标文件章节</span>
              <el-button size="small" @click="addSection">
                <el-icon><Plus /></el-icon>
                添加章节
              </el-button>
            </div>
          </template>
          
          <div class="sections-list">
            <div v-for="section in project.sections" :key="section.id" class="section-item">
              <div class="section-header">
                <div class="section-info">
                  <el-icon><Document /></el-icon>
                  <span class="section-title">{{ section.title }}</span>
                  <el-tag size="small" type="info">{{ section.section_type }}</el-tag>
                </div>
                <div class="section-actions">
                  <el-button text size="small" @click="editSection(section)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button text size="small" type="danger" @click="deleteSection(section)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
            <el-empty v-if="!project.sections?.length" description="暂无章节" />
          </div>
        </el-card>

        <!-- 项目文件 -->
        <el-card style="margin-top: 16px;">
          <template #header>
            <div class="card-header">
              <span class="card-title">项目文件 ({{ project.files?.length || 0 }})</span>
            </div>
          </template>
          
          <div class="files-list">
            <div v-for="file in project.files" :key="file.id" class="file-item">
              <div class="file-icon" :class="file.file_type">
                <el-icon :size="16">
                  <Document v-if="file.file_type === 'pdf'" />
                  <Picture v-else-if="file.file_type === 'image'" />
                  <Files v-else />
                </el-icon>
              </div>
              <div class="file-info">
                <div class="file-name">{{ file.filename }}</div>
                <div class="file-category">{{ file.category || '未分类' }}</div>
              </div>
              <el-button text size="small" type="danger" @click="removeFile(file)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-empty v-if="!project.files?.length" description="暂无文件" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 添加文件对话框 -->
    <el-dialog v-model="showAddFilesDialog" title="添加文件到项目" width="800px">
      <div class="add-files-content">
        <el-transfer
          v-model="selectedFileIds"
          :data="availableFiles"
          :titles="['可用文件', '已选择']"
          :props="{ key: 'id', label: 'filename' }"
        />
      </div>
      <template #footer>
        <el-button @click="showAddFilesDialog = false">取消</el-button>
        <el-button type="primary" @click="addFilesToProject" :disabled="selectedFileIds.length === 0">
          添加 {{ selectedFileIds.length }} 个文件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectApi, fileApi } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Document, Edit, Delete, Picture, Files } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const showAddFilesDialog = ref(false)
const selectedFileIds = ref([])
const availableFiles = ref([])

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

const loadProject = async () => {
  try {
    const res = await projectApi.get(route.params.id)
    project.value = res.data
  } catch (error) {
    ElMessage.error('加载项目失败')
    router.push('/projects')
  }
}

const loadAvailableFiles = async () => {
  try {
    const res = await fileApi.list({ page_size: 100 })
    availableFiles.value = res.data.files.map(f => ({
      id: f.id,
      filename: f.filename
    }))
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

const addFilesToProject = async () => {
  try {
    await projectApi.addFiles(project.value.id, selectedFileIds.value)
    ElMessage.success('添加成功')
    showAddFilesDialog.value = false
    selectedFileIds.value = []
    loadProject()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

const removeFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确定移除文件 "${file.filename}"？`, '确认移除', {
      type: 'warning'
    })
    await projectApi.removeFile(project.value.id, file.id)
    ElMessage.success('移除成功')
    loadProject()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

const addSection = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入章节名称', '添加章节', {
      inputPlaceholder: '例如: 业绩证明材料',
      confirmButtonText: '添加',
      cancelButtonText: '取消'
    })
    if (value) {
      await projectApi.addSection(project.value.id, value)
      ElMessage.success('章节添加成功')
      loadProject()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('添加失败')
    }
  }
}

const editSection = async (section) => {
  try {
    const { value } = await ElMessageBox.prompt('修改章节名称', '编辑章节', {
      inputValue: section.title,
      confirmButtonText: '保存',
      cancelButtonText: '取消'
    })
    if (value) {
      await projectApi.updateSection(project.value.id, section.id, value)
      ElMessage.success('章节更新成功')
      loadProject()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('更新失败')
    }
  }
}

const deleteSection = async (section) => {
  try {
    await ElMessageBox.confirm(`确定删除章节 "${section.title}"？`, '确认删除', {
      type: 'warning'
    })
    await projectApi.deleteSection(project.value.id, section.id)
    ElMessage.success('章节删除成功')
    loadProject()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const generating = ref(false)

const generateDocument = async () => {
  generating.value = true
  try {
    const res = await projectApi.generate(project.value.id)
    if (res.data.success) {
      ElMessage.success('投标文档生成成功')
      // 下载文件
      window.open(res.data.download_url, '_blank')
    } else {
      ElMessage.error(res.data.error || '生成失败')
    }
  } catch (error) {
    ElMessage.error('生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  loadProject()
  loadAvailableFiles()
})
</script>

<style scoped>
.project-detail {
  max-width: 1400px;
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
  margin-top: 8px;
  margin-bottom: 8px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--neutral-800);
}

.sections-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-item {
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-md);
  padding: 12px 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title {
  font-weight: 500;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-md);
}

.file-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-icon.pdf {
  background: #fef2f2;
  color: var(--danger);
}

.file-icon.image {
  background: #ecfdf5;
  color: var(--success);
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
}

.file-category {
  font-size: 12px;
  color: var(--neutral-400);
}

.text-danger {
  color: var(--danger);
  font-weight: 600;
}

.add-files-content {
  height: 400px;
}
</style>
