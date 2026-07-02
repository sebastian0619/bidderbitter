<template>
  <div class="tag-manager">
    <div class="page-header">
      <div>
        <h1 class="page-title">标签管理</h1>
        <p class="page-subtitle">管理文件标签</p>
      </div>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        新建标签
      </el-button>
    </div>

    <el-card>
      <div class="tag-grid">
        <div
          v-for="tag in tags"
          :key="tag.id"
          class="tag-card"
        >
          <div class="tag-card-header">
            <div class="tag-color" :style="{ background: tag.color }" />
            <span class="tag-name">{{ tag.name }}</span>
            <el-tag v-if="tag.category" size="small" type="info">{{ tag.category }}</el-tag>
          </div>
          <div class="tag-card-actions">
            <el-button text size="small" @click="editTag(tag)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text size="small" type="danger" @click="deleteTag(tag)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <el-empty v-if="tags.length === 0" description="暂无标签" />
    </el-card>

    <!-- 新建/编辑标签对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingTag ? '编辑标签' : '新建标签'"
      width="420px"
    >
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="标签名" required>
          <el-input v-model="tagForm.name" placeholder="请输入标签名" />
        </el-form-item>
        <el-form-item label="颜色">
          <div class="color-picker">
            <el-color-picker v-model="tagForm.color" show-alpha />
            <div class="preset-colors">
              <div
                v-for="color in presetColors"
                :key="color"
                class="preset-color"
                :style="{ background: color }"
                @click="tagForm.color = color"
              />
            </div>
          </div>
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="tagForm.category" placeholder="可选，如：业务类型、项目等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTag" :disabled="!tagForm.name">
          {{ editingTag ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tagApi } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'

const tags = ref([])
const showAddDialog = ref(false)
const editingTag = ref(null)
const tagForm = ref({
  name: '',
  color: '#3b82f6',
  category: ''
})

const presetColors = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
]

const loadTags = async () => {
  try {
    const res = await tagApi.list()
    tags.value = res.data
  } catch (error) {
    ElMessage.error('加载标签失败')
  }
}

const editTag = (tag) => {
  editingTag.value = tag
  tagForm.value = {
    name: tag.name,
    color: tag.color || '#3b82f6',
    category: tag.category || ''
  }
  showAddDialog.value = true
}

const saveTag = async () => {
  try {
    if (editingTag.value) {
      await tagApi.update(editingTag.value.id, tagForm.value)
      ElMessage.success('更新成功')
    } else {
      await tagApi.create(tagForm.value.name, tagForm.value.color, tagForm.value.category)
      ElMessage.success('创建成功')
    }
    showAddDialog.value = false
    editingTag.value = null
    tagForm.value = { name: '', color: '#3b82f6', category: '' }
    loadTags()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deleteTag = async (tag) => {
  try {
    await ElMessageBox.confirm(`确定删除标签 "${tag.name}"？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    await tagApi.delete(tag.id)
    ElMessage.success('删除成功')
    loadTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(loadTags)
</script>

<style scoped>
.tag-manager {
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

.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.tag-card {
  background: var(--header-bg);
  border: 1px solid var(--neutral-200);
  border-radius: var(--radius-lg);
  padding: 16px;
  transition: all 0.2s ease;
}

.tag-card:hover {
  border-color: var(--primary-300);
  box-shadow: var(--shadow-sm);
}

.tag-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.tag-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--neutral-800);
  flex: 1;
}

.tag-card-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.tag-card:hover .tag-card-actions {
  opacity: 1;
}

.color-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preset-colors {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.preset-color:hover {
  transform: scale(1.1);
}
</style>
