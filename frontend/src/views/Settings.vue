<template>
  <div class="settings-container">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>管理系统配置和AI模型设置</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 设置内容 -->
    <div v-else class="settings-content">
      <!-- AI设置 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Setting /></el-icon>
              AI服务配置
            </span>
            <el-button 
              type="primary" 
              size="small"
              @click="saveAISettings"
              :loading="saving"
            >
              保存AI设置
            </el-button>
          </div>
        </template>

        <el-form :model="aiSettings" label-width="140px" class="settings-form">
          <el-form-item label="AI服务提供商">
            <el-select v-model="aiSettings.ai_provider" placeholder="选择AI服务提供商">
              <el-option label="OpenAI" value="openai" />
              <el-option label="Azure OpenAI" value="azure" />
              <el-option label="自定义服务" value="custom" />
            </el-select>
            <div class="form-help">选择AI服务提供商，支持OpenAI、Azure OpenAI或自定义兼容服务</div>
          </el-form-item>

          <el-form-item label="文本分析模型">
            <el-input 
              v-model="aiSettings.ai_text_model" 
              placeholder="例如: gpt-4, claude-3-sonnet, llama-2-7b-chat"
            />
            <div class="form-help">用于文档分析和文本理解的AI模型名称</div>
          </el-form-item>

          <el-form-item label="图像分析模型">
            <el-input 
              v-model="aiSettings.ai_vision_model" 
              placeholder="例如: gpt-4-vision-preview, llava-1.5-7b"
            />
            <div class="form-help">用于图像识别和分析的AI模型名称</div>
          </el-form-item>

          <el-form-item label="API密钥">
            <el-input 
              v-model="aiSettings.ai_api_key" 
              type="password" 
              placeholder="输入API密钥"
              show-password
            />
            <div class="form-help">AI服务的API密钥，将安全存储</div>
          </el-form-item>

          <el-form-item label="API基础URL">
            <el-input 
              v-model="aiSettings.ai_base_url" 
              placeholder="例如: https://api.openai.com/v1"
            />
            <div class="form-help">AI服务的API端点地址，大多数服务需要包含 /v1 路径</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 上传设置 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Upload /></el-icon>
              文件上传配置
            </span>
            <el-button 
              type="primary" 
              size="small"
              @click="saveUploadSettings"
              :loading="saving"
            >
              保存上传设置
            </el-button>
          </div>
        </template>

        <el-form :model="uploadSettings" label-width="140px" class="settings-form">
          <el-form-item label="最大文件大小">
            <el-input 
              v-model="uploadSettings.upload_max_file_size" 
              placeholder="52428800"
            >
              <template #append>字节</template>
            </el-input>
            <div class="form-help">单个文件最大大小，默认50MB (52428800字节)</div>
          </el-form-item>

          <el-form-item label="允许的文件类型">
            <el-input 
              v-model="uploadSettings.upload_allowed_types" 
              placeholder="pdf,docx,doc,png,jpg,jpeg"
            />
            <div class="form-help">允许上传的文件扩展名，用逗号分隔</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 截图设置 -->
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Camera /></el-icon>
              网页截图配置
            </span>
            <el-button 
              type="primary" 
              size="small"
              @click="saveScreenshotSettings"
              :loading="saving"
            >
              保存截图设置
            </el-button>
          </div>
        </template>

        <el-form :model="screenshotSettings" label-width="140px" class="settings-form">
          <el-form-item label="截图超时时间">
            <el-input 
              v-model="screenshotSettings.screenshot_timeout" 
              placeholder="30"
            >
              <template #append>秒</template>
            </el-input>
            <div class="form-help">单个页面截图的最大等待时间</div>
          </el-form-item>

          <el-form-item label="最大截图页数">
            <el-input 
              v-model="screenshotSettings.screenshot_max_pages" 
              placeholder="20"
            />
            <div class="form-help">单个网页最大截图页数</div>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="success" @click="saveAllSettings" :loading="saving">
          保存所有设置
        </el-button>
        <el-button type="info" @click="initDefaultSettings" :loading="initializing">
          恢复默认设置
        </el-button>
        <el-button @click="refreshSettings">
          刷新设置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, Upload, Camera } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

// 响应式数据
const loading = ref(true)
const saving = ref(false)
const initializing = ref(false)

// 设置数据
const aiSettings = ref({
  ai_provider: 'openai',
  ai_text_model: 'gpt-4',
  ai_vision_model: 'gpt-4-vision-preview',
  ai_api_key: '',
  ai_base_url: 'https://api.openai.com/v1'
})

const uploadSettings = ref({
  upload_max_file_size: '52428800',
  upload_allowed_types: 'pdf,docx,doc,png,jpg,jpeg'
})

const screenshotSettings = ref({
  screenshot_timeout: '30',
  screenshot_max_pages: '20'
})

// 方法
const loadSettings = async () => {
  try {
    loading.value = true
    const response = await apiService.getSettings()
    
    if (response.success) {
      const settings = response.settings
      
      // 填充AI设置
      Object.keys(aiSettings.value).forEach(key => {
        if (settings[key]) {
          aiSettings.value[key] = settings[key].value
        }
      })
      
      // 填充上传设置
      Object.keys(uploadSettings.value).forEach(key => {
        if (settings[key]) {
          uploadSettings.value[key] = settings[key].value
        }
      })
      
      // 填充截图设置
      Object.keys(screenshotSettings.value).forEach(key => {
        if (settings[key]) {
          screenshotSettings.value[key] = settings[key].value
        }
      })
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

const saveAISettings = async () => {
  try {
    saving.value = true
    const response = await apiService.updateSettings(aiSettings.value)
    
    if (response.success) {
      ElMessage.success('AI设置保存成功')
    }
  } catch (error) {
    console.error('保存AI设置失败:', error)
    ElMessage.error('保存AI设置失败')
  } finally {
    saving.value = false
  }
}

const saveUploadSettings = async () => {
  try {
    saving.value = true
    const response = await apiService.updateSettings(uploadSettings.value)
    
    if (response.success) {
      ElMessage.success('上传设置保存成功')
    }
  } catch (error) {
    console.error('保存上传设置失败:', error)
    ElMessage.error('保存上传设置失败')
  } finally {
    saving.value = false
  }
}

const saveScreenshotSettings = async () => {
  try {
    saving.value = true
    const response = await apiService.updateSettings(screenshotSettings.value)
    
    if (response.success) {
      ElMessage.success('截图设置保存成功')
    }
  } catch (error) {
    console.error('保存截图设置失败:', error)
    ElMessage.error('保存截图设置失败')
  } finally {
    saving.value = false
  }
}

const saveAllSettings = async () => {
  try {
    saving.value = true
    const allSettings = {
      ...aiSettings.value,
      ...uploadSettings.value,
      ...screenshotSettings.value
    }
    
    const response = await apiService.updateSettings(allSettings)
    
    if (response.success) {
      ElMessage.success('所有设置保存成功')
    }
  } catch (error) {
    console.error('保存设置失败:', error)
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
  }
}

const initDefaultSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将恢复所有设置为默认值，是否继续？',
      '确认恢复默认设置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    initializing.value = true
    const response = await apiService.initDefaultSettings()
    
    if (response.success) {
      ElMessage.success('默认设置恢复成功')
      await loadSettings()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复默认设置失败:', error)
      ElMessage.error('恢复默认设置失败')
    }
  } finally {
    initializing.value = false
  }
}

const refreshSettings = () => {
  loadSettings()
}

// 生命周期
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #909399;
  margin: 0;
  font-size: 14px;
}

.loading-wrapper {
  padding: 20px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}

.settings-form {
  padding: 20px 0;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 20px 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-card__header) {
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-input-group__append) {
  background-color: #f5f7fa;
  border-color: #dcdfe6;
  color: #909399;
}
</style> 