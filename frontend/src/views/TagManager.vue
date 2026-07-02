<template>
  <div class="tag-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            新建标签
          </el-button>
        </div>
      </template>

      <el-table :data="tags" style="width: 100%;">
        <el-table-column prop="name" label="标签名" />
        <el-table-column prop="color" label="颜色" width="120">
          <template #default="{ row }">
            <div
              :style="{
                width: '24px',
                height: '24px',
                backgroundColor: row.color,
                borderRadius: '4px'
              }"
            />
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="150" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editTag(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteTag(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑标签对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingTag ? '编辑标签' : '新建标签'"
      width="400px"
    >
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="标签名">
          <el-input v-model="tagForm.name" placeholder="请输入标签名" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="tagForm.color" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="tagForm.category" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTag">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tagApi } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const tags = ref([])
const showAddDialog = ref(false)
const editingTag = ref(null)
const tagForm = ref({
  name: '',
  color: '#409EFF',
  category: ''
})

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
    color: tag.color,
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
    tagForm.value = { name: '', color: '#409EFF', category: '' }
    loadTags()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deleteTag = async (tag) => {
  try {
    await ElMessageBox.confirm('确定删除该标签？', '提示', {
      type: 'warning'
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
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
