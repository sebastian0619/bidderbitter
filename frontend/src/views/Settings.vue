<template>
  <div class="settings-container">
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <el-icon><Setting /></el-icon>
        </div>
        <div class="header-text">
          <h1>系统设置</h1>
          <p>配置AI模型、上传参数和系统功能</p>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-card class="loading-card">
        <el-skeleton :rows="8" animated />
      </el-card>
    </div>

    <!-- 设置内容 -->
    <div v-else class="settings-content">
      <!-- AI设置 -->
      <el-card class="settings-card ai-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon ai-icon">
                <el-icon><Setting /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>AI服务配置</h3>
                <span class="card-subtitle">配置主要的AI文本分析服务</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveAISettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="aiSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="AI服务提供商">
              <el-select v-model="aiSettings.ai_provider" placeholder="选择AI服务提供商" class="full-width">
                <el-option label="OpenAI" value="openai">
                  <div class="option-item">
                    <span class="option-label">OpenAI</span>
                    <span class="option-desc">最先进的GPT模型</span>
                  </div>
                </el-option>
                <el-option label="Azure OpenAI" value="azure">
                  <div class="option-item">
                    <span class="option-label">Azure OpenAI</span>
                    <span class="option-desc">微软Azure托管服务</span>
                  </div>
                </el-option>
                <el-option label="Ollama (本地)" value="ollama">
                  <div class="option-item">
                    <span class="option-label">Ollama (本地)</span>
                    <span class="option-desc">本地部署的开源模型</span>
                  </div>
                </el-option>
                <el-option label="自定义服务" value="custom">
                  <div class="option-item">
                    <span class="option-label">自定义服务</span>
                    <span class="option-desc">兼容OpenAI API的自定义服务</span>
                  </div>
                </el-option>
              </el-select>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                选择AI服务提供商，支持OpenAI、Azure OpenAI、Ollama本地服务或自定义兼容服务
              </div>
            </el-form-item>

            <el-form-item label="文本分析模型">
              <el-input 
                v-model="aiSettings.ai_text_model" 
                placeholder="例如: gpt-4, claude-3-sonnet, llama3.2"
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                用于文档分析和文本理解的AI模型名称
              </div>
            </el-form-item>

            <el-form-item label="API密钥">
              <el-input 
                v-model="aiSettings.ai_api_key" 
                type="password" 
                placeholder="输入API密钥（Ollama可留空）"
                show-password
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Key /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                AI服务的API密钥，Ollama本地服务可以留空
              </div>
            </el-form-item>

            <el-form-item label="API基础URL">
              <el-input 
                v-model="aiSettings.ai_base_url" 
                placeholder="例如: https://api.openai.com/v1 或 http://localhost:11434/v1"
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Link /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                AI服务的API端点地址，Ollama默认: http://localhost:11434/v1
              </div>
            </el-form-item>
          </div>
        </el-form>
      </el-card>

      <!-- 视觉模型配置 -->
      <el-card class="settings-card vision-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon vision-icon">
                <el-icon><View /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>视觉模型配置</h3>
                <span class="card-subtitle">配置图像分析和OCR识别服务</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveVisionSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="visionSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="视觉服务提供商">
              <el-select v-model="visionSettings.vision_provider" placeholder="选择视觉服务提供商" class="full-width">
                <el-option label="使用主AI服务" value="">
                  <div class="option-item">
                    <span class="option-label">使用主AI服务</span>
                    <span class="option-desc">继承上面的AI服务配置</span>
                  </div>
                </el-option>
                <el-option label="OpenAI" value="openai">
                  <div class="option-item">
                    <span class="option-label">OpenAI</span>
                    <span class="option-desc">GPT-4 Vision模型</span>
                  </div>
                </el-option>
                <el-option label="Ollama (本地)" value="ollama">
                  <div class="option-item">
                    <span class="option-label">Ollama (本地)</span>
                    <span class="option-desc">本地LLaVA视觉模型</span>
                  </div>
                </el-option>
                <el-option label="Azure OpenAI" value="azure">
                  <div class="option-item">
                    <span class="option-label">Azure OpenAI</span>
                    <span class="option-desc">Azure托管的视觉模型</span>
                  </div>
                </el-option>
                <el-option label="自定义服务" value="custom">
                  <div class="option-item">
                    <span class="option-label">自定义服务</span>
                    <span class="option-desc">自定义的视觉AI服务</span>
                  </div>
                </el-option>
              </el-select>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                选择"使用主AI服务"将使用上面配置的AI服务进行视觉分析
              </div>
            </el-form-item>

            <!-- 独立视觉配置 -->
            <template v-if="visionSettings.vision_provider">
              <el-form-item label="视觉模型名称">
                <el-input 
                  v-model="aiSettings.ai_vision_model" 
                  :placeholder="getVisionModelPlaceholder()"
                  class="full-width"
                >
                  <template #prefix>
                    <el-icon><View /></el-icon>
                  </template>
                </el-input>
                <div class="form-help">
                  <el-icon><InfoFilled /></el-icon>
                  {{ getVisionModelHelp() }}
                </div>
              </el-form-item>

              <template v-if="visionSettings.vision_provider !== 'ollama'">
                <el-form-item label="视觉API地址">
                  <el-input 
                    v-model="visionSettings.vision_base_url" 
                    :placeholder="getVisionUrlPlaceholder()"
                    class="full-width"
                  >
                    <template #prefix>
                      <el-icon><Link /></el-icon>
                    </template>
                  </el-input>
                  <div class="form-help">
                    <el-icon><InfoFilled /></el-icon>
                    视觉模型的API地址，留空则使用默认地址
                  </div>
                </el-form-item>

                <el-form-item label="视觉API密钥">
                  <el-input 
                    v-model="visionSettings.vision_api_key" 
                    type="password" 
                    placeholder="留空则使用主AI服务密钥"
                    show-password
                    class="full-width"
                  >
                    <template #prefix>
                      <el-icon><Key /></el-icon>
                    </template>
                  </el-input>
                  <div class="form-help">
                    <el-icon><InfoFilled /></el-icon>
                    视觉模型的API密钥，留空则使用主AI服务的密钥
                  </div>
                </el-form-item>
              </template>

              <!-- Ollama 特定配置 -->
              <template v-if="visionSettings.vision_provider === 'ollama'">
                <el-form-item label="Ollama服务地址">
                  <el-input 
                    v-model="visionSettings.ollama_vision_base_url" 
                    placeholder="http://localhost:11434/v1"
                    class="full-width"
                  >
                    <template #prefix>
                      <el-icon><Monitor /></el-icon>
                    </template>
                  </el-input>
                  <div class="form-help">
                    <el-icon><InfoFilled /></el-icon>
                    Ollama视觉模型服务的地址
                  </div>
                </el-form-item>
              </template>
            </template>

            <el-alert
              v-if="!visionSettings.vision_provider"
              title="当前将使用主AI服务进行视觉分析"
              type="info"
              :closable="false"
              show-icon
              class="info-alert"
            />
          </div>
        </el-form>
      </el-card>

      <!-- 上传设置 -->
      <el-card class="settings-card upload-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon upload-icon">
                <el-icon><Upload /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>文件上传配置</h3>
                <span class="card-subtitle">管理文件上传限制和格式支持</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveUploadSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="uploadSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="最大文件大小">
              <el-input 
                v-model="uploadSettings.upload_max_file_size" 
                placeholder="52428800"
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Files /></el-icon>
                </template>
                <template #append>字节</template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                单个文件最大大小，默认50MB (52428800字节)
              </div>
            </el-form-item>

            <el-form-item label="允许的文件类型">
              <el-input 
                v-model="uploadSettings.upload_allowed_types" 
                placeholder="pdf,docx,doc,png,jpg,jpeg"
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                允许上传的文件扩展名，用逗号分隔
              </div>
            </el-form-item>
          </div>
        </el-form>
      </el-card>

      <!-- 截图设置 -->
      <el-card class="settings-card screenshot-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon screenshot-icon">
                <el-icon><Camera /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>网页截图配置</h3>
                <span class="card-subtitle">控制网页截图的性能和质量参数</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveScreenshotSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="screenshotSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="截图超时时间">
              <el-input 
                v-model="screenshotSettings.screenshot_timeout" 
                placeholder="30"
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Timer /></el-icon>
                </template>
                <template #append>秒</template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                单个页面截图的最大等待时间
              </div>
            </el-form-item>

            <el-form-item label="最大截图页数">
              <el-input 
                v-model="screenshotSettings.screenshot_max_pages" 
                placeholder="20"
                class="full-width"
              >
                <template #prefix>
                  <el-icon><Document /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                单个网页最大截图页数
              </div>
            </el-form-item>
          </div>
        </el-form>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button type="success" size="large" @click="saveAllSettings" :loading="saving" class="primary-action">
          <el-icon><Check /></el-icon>
          保存所有设置
        </el-button>
        <el-button type="warning" size="large" @click="initDefaultSettings" :loading="initializing" class="secondary-action">
          <el-icon><RefreshLeft /></el-icon>
          恢复默认设置
        </el-button>
        <el-button size="large" @click="refreshSettings" class="tertiary-action">
          <el-icon><Refresh /></el-icon>
          刷新设置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, Upload, Camera, View, Check, InfoFilled, Document, 
  Key, Link, Monitor, Files, Timer, RefreshLeft, Refresh 
} from '@element-plus/icons-vue'
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

const visionSettings = ref({
  vision_provider: 'openai',
  vision_base_url: '',
  vision_api_key: '',
  ollama_vision_base_url: 'http://localhost:11434/v1',
  ollama_vision_model: 'llava:latest'
})

const uploadSettings = ref({
  upload_max_file_size: '52428800',
  upload_allowed_types: 'pdf,docx,doc,png,jpg,jpeg'
})

const screenshotSettings = ref({
  screenshot_timeout: '30',
  screenshot_max_pages: '20'
})

// 动态帮助函数
const getVisionModelPlaceholder = () => {
  const provider = visionSettings.value.vision_provider
  switch (provider) {
    case 'ollama':
      return 'llava:latest, llava:13b, llava:7b'
    case 'openai':
      return 'gpt-4-vision-preview, gpt-4o'
    case 'azure':
      return 'gpt-4-vision'
    default:
      return 'gpt-4-vision-preview, llava:latest'
  }
}

const getVisionModelHelp = () => {
  const provider = visionSettings.value.vision_provider
  switch (provider) {
    case 'ollama':
      return 'Ollama中安装的视觉模型名称'
    case 'openai':
      return 'OpenAI的视觉模型名称'
    case 'azure':
      return 'Azure OpenAI的视觉模型部署名称'
    default:
      return '视觉模型名称'
  }
}

const getVisionUrlPlaceholder = () => {
  const provider = visionSettings.value.vision_provider
  switch (provider) {
    case 'openai':
      return 'https://api.openai.com/v1'
    case 'azure':
      return 'https://your-resource.openai.azure.com'
    case 'custom':
      return 'http://your-custom-api.com/v1'
    default:
      return ''
  }
}

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
      
      // 填充视觉模型设置
      Object.keys(visionSettings.value).forEach(key => {
        if (settings[key]) {
          visionSettings.value[key] = settings[key].value
        }
      })
      
      // 如果没有独立的视觉提供商配置，设为空字符串表示使用主AI服务
      if (!settings.vision_provider || settings.vision_provider.value === aiSettings.value.ai_provider) {
        visionSettings.value.vision_provider = ''
      }
      
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

const saveVisionSettings = async () => {
  try {
    saving.value = true
    
    let settingsToSave = {
      ai_vision_model: aiSettings.value.ai_vision_model
    }
    
    if (visionSettings.value.vision_provider) {
      // 保存独立的视觉配置
      settingsToSave = { 
        ...settingsToSave,
        ...visionSettings.value 
      }
    } else {
      // 使用主AI服务，清空独立配置
      settingsToSave = {
        ...settingsToSave,
        vision_provider: aiSettings.value.ai_provider,
        vision_base_url: '',
        vision_api_key: ''
      }
    }
    
    const response = await apiService.updateSettings(settingsToSave)
    
    if (response.success) {
      ElMessage.success('视觉设置保存成功')
    }
  } catch (error) {
    console.error('保存视觉设置失败:', error)
    ElMessage.error('保存视觉设置失败')
  } finally {
    saving.value = false
  }
}

const saveAllSettings = async () => {
  try {
    saving.value = true
    
    let allSettings = {
      ...aiSettings.value,
      ...uploadSettings.value,
      ...screenshotSettings.value
    }
    
    // 添加视觉模型配置
    allSettings.ai_vision_model = aiSettings.value.ai_vision_model
    
    // 如果有独立视觉配置，包含视觉设置
    if (visionSettings.value.vision_provider) {
      allSettings = { ...allSettings, ...visionSettings.value }
    } else {
      // 否则确保视觉提供商与主AI提供商一致
      allSettings.vision_provider = aiSettings.value.ai_provider
      allSettings.vision_base_url = ''
      allSettings.vision_api_key = ''
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  color: white;
}

.header-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  backdrop-filter: blur(10px);
  font-size: 28px;
}

.header-text h1 {
  font-size: 32px;
  margin: 0 0 8px 0;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-text p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.loading-wrapper {
  padding: 24px;
}

.loading-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-card {
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: none;
  overflow: hidden;
  transition: all 0.3s ease;
}

.settings-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
}

.ai-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.vision-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.upload-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.screenshot-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.card-title-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 20px;
  backdrop-filter: blur(10px);
}

.card-title-text h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
}

.card-subtitle {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.save-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.save-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
}

.settings-form {
  padding: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.full-width {
  width: 100%;
}

.form-help {
  font-size: 13px;
  color: #666;
  margin-top: 6px;
  line-height: 1.5;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-label {
  font-weight: 500;
  color: #303133;
}

.option-desc {
  font-size: 12px;
  color: #909399;
}

.info-alert {
  margin-top: 16px;
  border-radius: 8px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 32px 0;
  margin-top: 24px;
}

.primary-action {
  background: linear-gradient(135deg, #67b26f 0%, #4ca2cd 100%);
  border: none;
  padding: 12px 32px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(103, 178, 111, 0.3);
  transition: all 0.3s ease;
}

.primary-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(103, 178, 111, 0.4);
}

.secondary-action {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  border: none;
  color: #8b4513;
  padding: 12px 32px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(252, 182, 159, 0.3);
  transition: all 0.3s ease;
}

.secondary-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(252, 182, 159, 0.4);
  color: #8b4513;
}

.tertiary-action {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
  border: none;
  color: #666;
  padding: 12px 32px;
  border-radius: 12px;
  font-weight: 600;
  box-shadow: 0 4px 16px rgba(168, 237, 234, 0.3);
  transition: all 0.3s ease;
}

.tertiary-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(168, 237, 234, 0.4);
  color: #666;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #303133;
}

:deep(.el-card__body) {
  padding: 0;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-input-group__append) {
  background-color: #f5f7fa;
  border-color: #dcdfe6;
  color: #909399;
  border-radius: 0 8px 8px 0;
}

:deep(.el-form-item__content) {
  display: flex;
  flex-direction: column;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }
  
  .header-text h1 {
    font-size: 24px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .primary-action,
  .secondary-action,
  .tertiary-action {
    width: 100%;
    max-width: 300px;
  }
}
</style> 