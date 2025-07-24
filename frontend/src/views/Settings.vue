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

      <!-- MCP服务配置 -->
      <el-card class="settings-card mcp-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon mcp-icon">
                <el-icon><Grid /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>MCP服务配置</h3>
                <span class="card-subtitle">配置模型上下文协议服务</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveMCPSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="mcpSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="启用MCP服务">
              <el-switch v-model="mcpSettings.mcp_enabled" active-text="启用" inactive-text="禁用" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                启用后AI服务可以调用外部MCP工具
              </div>
            </el-form-item>

            <el-form-item label="MCP服务器URL">
              <el-input 
                v-model="mcpSettings.mcp_server_url"
                placeholder="例如: http://localhost:8000/mcp"
                class="full-width"
                :disabled="!mcpSettings.mcp_enabled"
              >
                <template #prefix>
                  <el-icon><Link /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                MCP服务器的基础URL地址
              </div>
            </el-form-item>

            <el-form-item label="MCP API密钥">
              <el-input 
                v-model="mcpSettings.mcp_api_key"
                type="password"
                placeholder="输入MCP服务的API密钥"
                show-password
                class="full-width"
                :disabled="!mcpSettings.mcp_enabled"
              >
                <template #prefix>
                  <el-icon><Key /></el-icon>
                </template>
              </el-input>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                MCP服务的认证密钥（如需要）
              </div>
            </el-form-item>

            <el-form-item label="请求超时时间">
              <el-input-number 
                v-model="mcpSettings.mcp_timeout"
                :min="5"
                :max="300"
                :step="5"
                :disabled="!mcpSettings.mcp_enabled"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                MCP工具调用的超时时间（秒），默认30秒
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

      <!-- OCR配置 -->
      <el-card class="settings-card ocr-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon ocr-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>OCR文字识别配置</h3>
                <span class="card-subtitle">配置文档OCR识别参数，优化扫描件文字提取</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveOCRSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="ocrSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="启用OCR识别">
              <el-switch v-model="ocrSettings.docling_enable_ocr" active-text="启用" inactive-text="禁用" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                启用后系统将对扫描件PDF进行OCR文字识别
              </div>
            </el-form-item>

            <el-form-item label="强制全页OCR">
              <el-switch v-model="ocrSettings.docling_force_full_page_ocr" active-text="启用" inactive-text="禁用" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                强制对所有PDF页面进行OCR，提高扫描件识别率
              </div>
            </el-form-item>

            <el-form-item label="OCR语言">
              <el-select v-model="ocrSettings.docling_ocr_languages" multiple placeholder="选择OCR识别语言" class="full-width">
                <el-option label="简体中文" value="ch_sim">
                  <div class="option-item">
                    <span class="option-label">简体中文</span>
                    <span class="option-desc">识别简体中文字符</span>
                  </div>
                </el-option>
                <el-option label="英文" value="en">
                  <div class="option-item">
                    <span class="option-label">英文</span>
                    <span class="option-desc">识别英文字符</span>
                  </div>
                </el-option>
              </el-select>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                选择OCR需要识别的语言，支持多语言混合识别
              </div>
            </el-form-item>

            <el-form-item label="置信度阈值">
              <el-slider
                v-model="ocrSettings.docling_confidence_threshold"
                :min="0.1"
                :max="0.9"
                :step="0.05"
                :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                文字识别的置信度阈值，越低识别越多文字但可能包含错误，建议0.2-0.5
              </div>
            </el-form-item>

            <el-form-item label="位图区域阈值">
              <el-slider
                v-model="ocrSettings.docling_bitmap_area_threshold"
                :min="0.01"
                :max="0.1"
                :step="0.01"
                :format-tooltip="(val) => `${(val * 100).toFixed(1)}%`"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                识别的最小区域比例，越小识别越多小文字，建议0.03-0.05
              </div>
            </el-form-item>

            <el-form-item label="图像缩放倍数">
              <el-slider
                v-model="ocrSettings.docling_images_scale"
                :min="1.0"
                :max="5.0"
                :step="0.5"
                :format-tooltip="(val) => `${val}x`"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                OCR处理时的图像放大倍数，越大识别越准确但处理越慢，建议2.0-3.0
              </div>
            </el-form-item>

            <el-form-item label="使用GPU加速">
              <el-switch v-model="ocrSettings.docling_use_gpu" active-text="启用" inactive-text="禁用" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                启用GPU加速可显著提高OCR处理速度（需要CUDA环境）
              </div>
            </el-form-item>

            <el-alert
              title="OCR配置优化建议"
              type="info"
              :closable="false"
              show-icon
              class="info-alert"
            >
              <template #default>
                <p><strong>扫描件优化：</strong>启用强制全页OCR，置信度阈值设为0.2-0.3</p>
                <p><strong>文字质量：</strong>图像缩放倍数设为2.0-3.0，位图阈值设为0.03</p>
                <p><strong>处理速度：</strong>启用GPU加速，降低图像缩放倍数</p>
              </template>
            </el-alert>
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
                单个文件最大大小，默认500MB (524288000字节)
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

      <!-- 分类提示词设置 -->
      <el-card class="settings-card prompt-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon prompt-icon">
                <el-icon><EditPen /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>分类提示词管理</h3>
                <span class="card-subtitle">自定义AI文档分类的提示词模板</span>
              </div>
            </div>
            <el-dropdown @command="handlePromptCommand" class="prompt-actions">
              <el-button type="primary" size="default">
                提示词操作
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="refresh">
                    <el-icon><Refresh /></el-icon>
                    刷新提示词
                  </el-dropdown-item>
                  <el-dropdown-item command="reset-vision" divided>
                    <el-icon><RefreshLeft /></el-icon>
                    重置视觉提示词
                  </el-dropdown-item>
                  <el-dropdown-item command="reset-text">
                    <el-icon><RefreshLeft /></el-icon>
                    重置文本提示词
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>

        <div class="prompt-content">
          <el-tabs v-model="activePromptTab" class="prompt-tabs">
            <!-- 视觉分类提示词 -->
            <el-tab-pane label="视觉分类提示词" name="vision" lazy>
              <div class="prompt-tab-content">
                <div class="prompt-info">
                  <el-alert
                    title="视觉分类提示词用于分析图片类型的文档（如证书、合同扫描件等）"
                    type="info"
                    :closable="false"
                    show-icon
                  />
                </div>
                <div class="prompt-editor">
                  <el-input
                    v-model="classificationPrompts.vision.value"
                    type="textarea"
                    :rows="20"
                    placeholder="编辑视觉分类提示词..."
                    class="prompt-textarea"
                    :disabled="promptLoading"
                  />
                  <div class="prompt-meta">
                    <span class="prompt-updated">
                      <el-icon><Clock /></el-icon>
                      最后更新: {{ formatDate(classificationPrompts.vision.updated_at) }}
                    </span>
                    <div class="prompt-actions">
                      <el-button 
                        type="success" 
                        @click="savePrompt('classification_vision_prompt')"
                        :loading="promptSaving"
                        size="default"
                      >
                        <el-icon><Check /></el-icon>
                        保存并热重载
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- 文本分类提示词 -->
            <el-tab-pane label="文本分类提示词" name="text" lazy>
              <div class="prompt-tab-content">
                <div class="prompt-info">
                  <el-alert
                    title="文本分类提示词用于分析已提取文本内容的文档分类"
                    type="info"
                    :closable="false"
                    show-icon
                  />
                </div>
                <div class="prompt-editor">
                  <el-input
                    v-model="classificationPrompts.text.value"
                    type="textarea"
                    :rows="20"
                    placeholder="编辑文本分类提示词..."
                    class="prompt-textarea"
                    :disabled="promptLoading"
                  />
                  <div class="prompt-meta">
                    <span class="prompt-updated">
                      <el-icon><Clock /></el-icon>
                      最后更新: {{ formatDate(classificationPrompts.text.updated_at) }}
                    </span>
                    <div class="prompt-actions">
                      <el-button 
                        type="success" 
                        @click="savePrompt('classification_text_prompt')"
                        :loading="promptSaving"
                        size="default"
                      >
                        <el-icon><Check /></el-icon>
                        保存并热重载
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-card>

      <!-- Docling OCR设置 -->
      <el-card class="settings-card ocr-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon ocr-icon">
                <el-icon><View /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>智能OCR配置</h3>
                <span class="card-subtitle">基于Docling的文档OCR识别，提升文档分析准确性</span>
              </div>
            </div>
            <div class="ocr-status">
              <el-tag 
                :type="ocrStatus.docling_available ? 'success' : 'danger'"
                class="status-tag"
                size="large"
              >
                <el-icon><CircleCheckFilled v-if="ocrStatus.docling_available" /><CircleCloseFilled v-else /></el-icon>
                {{ ocrStatus.docling_available ? 'Docling可用' : 'Docling不可用' }}
              </el-tag>
              <el-button 
                type="primary" 
                size="default"
                @click="refreshOCRStatus"
                :loading="ocrStatusLoading"
                class="refresh-btn"
              >
                <el-icon><Refresh /></el-icon>
                刷新状态
              </el-button>
            </div>
          </div>
        </template>

        <div v-if="!ocrStatus.docling_available" class="ocr-unavailable">
          <el-result
            icon="warning"
            title="Docling不可用"
            sub-title="Docling库未安装或配置错误，请检查Docker容器环境配置"
          >
            <template #extra>
              <el-button type="primary" @click="refreshOCRStatus">
                <el-icon><Refresh /></el-icon>
                重新检测
              </el-button>
            </template>
          </el-result>
        </div>

        <el-form v-else :model="ocrSettings" label-width="140px" class="settings-form">
          <div class="form-group">
            <el-form-item label="启用智能OCR">
              <div class="ocr-enable-section">
                <el-switch
                  v-model="ocrSettings.easyocr_enable"
                  active-text="启用EasyOCR"
                  inactive-text="使用Tesseract"
                  size="large"
                  @change="handleOCRToggle"
                  :loading="ocrToggleLoading"
                />
                <div class="ocr-comparison">
                  <div class="ocr-option">
                    <div class="option-header">
                      <el-tag type="info" size="small">传统OCR</el-tag>
                      <span class="option-name">Tesseract</span>
                    </div>
                    <ul class="option-features">
                      <li>✓ 轻量级，启动快</li>
                      <li>✓ 无需下载额外模型</li>
                      <li>⚠ 精度相对较低</li>
                    </ul>
                  </div>
                  <div class="ocr-option">
                    <div class="option-header">
                      <el-tag type="success" size="small">智能OCR</el-tag>
                      <span class="option-name">EasyOCR</span>
                    </div>
                    <ul class="option-features">
                      <li>✓ 高精度识别</li>
                      <li>✓ 支持多种语言</li>
                      <li>⚠ 需要下载模型文件</li>
                    </ul>
                  </div>
                </div>
              </div>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                启用EasyOCR可显著提高文档识别准确性，特别适合律师执业证等重要文档的解析
              </div>
            </el-form-item>

            <template v-if="ocrSettings.easyocr_enable">
              <el-form-item label="模型存储路径">
                <el-input 
                  v-model="ocrSettings.easyocr_model_path" 
                  placeholder="/app/easyocr_models"
                  class="full-width"
                >
                  <template #prefix>
                    <el-icon><Folder /></el-icon>
                  </template>
                </el-input>
                <div class="form-help">
                  <el-icon><InfoFilled /></el-icon>
                  EasyOCR模型文件的存储目录
                </div>
              </el-form-item>

              <el-form-item label="下载代理">
                <el-input 
                  v-model="ocrSettings.easyocr_download_proxy" 
                  placeholder="http://proxy.example.com:8080"
                  class="full-width"
                >
                  <template #prefix>
                    <el-icon><Link /></el-icon>
                  </template>
                </el-input>
                <div class="form-help">
                  <el-icon><InfoFilled /></el-icon>
                  下载模型时使用的代理地址，留空则直连
                </div>
              </el-form-item>

              <el-form-item label="支持语言">
                <el-select 
                  v-model="ocrSettings.easyocr_languages" 
                  multiple 
                  placeholder="选择支持的语言"
                  class="full-width"
                >
                  <el-option label="简体中文" value="ch_sim" />
                  <el-option label="繁体中文" value="ch_tra" />
                  <el-option label="英语" value="en" />
                  <el-option label="日语" value="ja" />
                  <el-option label="韩语" value="ko" />
                </el-select>
                <div class="form-help">
                  <el-icon><InfoFilled /></el-icon>
                  选择需要识别的语言，将下载对应的模型文件
                </div>
              </el-form-item>

              <el-form-item label="GPU加速">
                <el-switch
                  v-model="ocrSettings.easyocr_use_gpu"
                  active-text="启用"
                  inactive-text="禁用"
                />
                <div class="form-help">
                  <el-icon><InfoFilled /></el-icon>
                  使用GPU加速OCR处理（需要CUDA支持）
                </div>
              </el-form-item>

              <el-form-item label="状态信息">
                <div class="ocr-status-info">
                  <div class="status-item">
                    <span class="status-label">模型初始化:</span>
                    <el-tag :type="ocrStatus.reader_initialized ? 'success' : 'warning'">
                      {{ ocrStatus.reader_initialized ? '已初始化' : '未初始化' }}
                    </el-tag>
                  </div>
                  <div class="status-item">
                    <span class="status-label">支持语言:</span>
                    <span class="status-value">{{ Array.isArray(ocrStatus.languages) ? ocrStatus.languages.join(', ') : ocrStatus.languages }}</span>
                  </div>
                  <div class="status-item">
                    <span class="status-label">GPU模式:</span>
                    <el-tag :type="ocrStatus.use_gpu ? 'success' : 'info'">
                      {{ ocrStatus.use_gpu ? '已启用' : '未启用' }}
                    </el-tag>
                  </div>
                </div>
              </el-form-item>

              <el-form-item label="模型管理">
                <div class="model-management">
                  <div class="model-status-card">
                    <div class="status-header">
                      <el-icon class="status-icon"><FolderOpened /></el-icon>
                      <span class="status-title">模型状态</span>
                    </div>
                    <div class="status-grid">
                      <div class="status-item">
                        <span class="status-label">初始化状态:</span>
                        <el-tag :type="ocrStatus.reader_initialized ? 'success' : 'warning'">
                          {{ ocrStatus.reader_initialized ? '已就绪' : '未初始化' }}
                        </el-tag>
                      </div>
                      <div class="status-item">
                        <span class="status-label">支持语言:</span>
                        <el-tag 
                          v-for="lang in formatLanguages(ocrStatus.languages)" 
                          :key="lang" 
                          type="info" 
                          size="small"
                          class="lang-tag"
                        >
                          {{ lang }}
                        </el-tag>
                      </div>
                      <div class="status-item">
                        <span class="status-label">GPU加速:</span>
                        <el-tag :type="ocrStatus.use_gpu ? 'success' : 'info'">
                          {{ ocrStatus.use_gpu ? '已启用' : '未启用' }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                  
                  <div class="model-actions">
                    <el-button 
                      type="primary" 
                      @click="downloadModels"
                      :loading="modelDownloading"
                      class="action-btn"
                    >
                      <el-icon><Download /></el-icon>
                      {{ ocrStatus.reader_initialized ? '更新模型' : '下载模型' }}
                    </el-button>
                    <el-button 
                      type="default" 
                      @click="reloadOCR"
                      :loading="ocrReloading"
                      class="action-btn"
                    >
                      <el-icon><RefreshLeft /></el-icon>
                      重新加载
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="saveOCRSettings"
                      :loading="saving"
                      class="action-btn"
                    >
                      <el-icon><Check /></el-icon>
                      保存配置
                    </el-button>
                  </div>
                </div>
              </el-form-item>
            </template>
          </div>
        </el-form>
      </el-card>

      <!-- AI分析高级设置 -->
      <el-card class="settings-card ai-analysis-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon ai-analysis-icon">
                <el-icon><Setting /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>AI分析高级配置</h3>
                <span class="card-subtitle">配置文档分析时的详细功能选项</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveAIAnalysisSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="aiAnalysisSettings" label-width="180px" class="settings-form">
          <div class="form-group">
            <el-form-item label="启用表格结构分析">
              <el-switch v-model="aiAnalysisSettings.ai_analysis_enable_table_structure" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                分析文档中的表格结构，提取表格数据（可能影响处理速度）
              </div>
            </el-form-item>

            <el-form-item label="启用图片分类">
              <el-switch v-model="aiAnalysisSettings.ai_analysis_enable_picture_classification" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                对文档中的图片进行分类识别（如印章、签名、图表等）
              </div>
            </el-form-item>

            <el-form-item label="启用图片描述">
              <el-switch v-model="aiAnalysisSettings.ai_analysis_enable_picture_description" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                生成文档中图片的详细描述（需要AI视觉模型支持）
              </div>
            </el-form-item>

            <el-form-item label="生成页面图片">
              <el-switch v-model="aiAnalysisSettings.ai_analysis_generate_page_images" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                为每个页面生成独立的图片文件（增加存储空间使用）
              </div>
            </el-form-item>

            <el-form-item label="生成图片文件">
              <el-switch v-model="aiAnalysisSettings.ai_analysis_generate_picture_images" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                提取文档中的图片并保存为独立文件（增加存储空间使用）
              </div>
            </el-form-item>
          </div>
        </el-form>
      </el-card>

      <!-- OCR精度优化设置 -->
      <el-card class="settings-card ocr-advanced-card">
        <template #header>
          <div class="card-header">
            <div class="card-title-wrapper">
              <div class="card-icon ocr-advanced-icon">
                <el-icon><View /></el-icon>
              </div>
              <div class="card-title-text">
                <h3>OCR精度优化配置</h3>
                <span class="card-subtitle">调整OCR识别参数以提高文本提取准确性</span>
              </div>
            </div>
            <el-button 
              type="primary" 
              size="default"
              @click="saveOCRAdvancedSettings"
              :loading="saving"
              class="save-btn"
            >
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <el-form :model="ocrAdvancedSettings" label-width="180px" class="settings-form">
          <div class="form-group">
            <el-form-item label="置信度阈值">
              <el-slider 
                v-model="ocrAdvancedSettings.docling_confidence_threshold"
                :min="0.1"
                :max="1.0"
                :step="0.05"
                :format-tooltip="(val) => `${(val * 100).toFixed(0)}%`"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                控制OCR识别的置信度阈值，较低值可能提高召回率但降低精度
              </div>
            </el-form-item>

            <el-form-item label="位图区域阈值">
              <el-slider 
                v-model="ocrAdvancedSettings.docling_bitmap_area_threshold"
                :min="0.01"
                :max="0.1"
                :step="0.01"
                :format-tooltip="(val) => `${(val * 100).toFixed(1)}%`"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                控制位图区域的最小面积阈值，影响小文本的识别
              </div>
            </el-form-item>

            <el-form-item label="强制全页OCR">
              <el-switch v-model="ocrAdvancedSettings.docling_force_full_page_ocr" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                强制对所有页面进行OCR，可能提高漏行检测但增加处理时间
              </div>
            </el-form-item>

            <el-form-item label="识别网络类型">
              <el-select v-model="ocrAdvancedSettings.docling_recog_network" class="full-width">
                <el-option label="标准模式 (standard)" value="standard">
                  <div class="option-item">
                    <span class="option-label">标准模式</span>
                    <span class="option-desc">平衡精度和速度，推荐使用</span>
                  </div>
                </el-option>
                <el-option label="快速模式 (fast)" value="fast">
                  <div class="option-item">
                    <span class="option-label">快速模式</span>
                    <span class="option-desc">处理速度更快，但精度可能略低</span>
                  </div>
                </el-option>
              </el-select>
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                选择OCR识别网络类型，影响识别精度和处理速度
              </div>
            </el-form-item>

            <el-form-item label="GPU加速">
              <el-switch v-model="ocrAdvancedSettings.docling_use_gpu" />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                使用GPU加速OCR处理（需要CUDA支持）
              </div>
            </el-form-item>

            <el-form-item label="图像缩放比例">
              <el-slider 
                v-model="ocrAdvancedSettings.docling_images_scale"
                :min="1.0"
                :max="3.0"
                :step="0.1"
                :format-tooltip="(val) => `${val.toFixed(1)}x`"
                class="full-width"
              />
              <div class="form-help">
                <el-icon><InfoFilled /></el-icon>
                处理前对图像进行缩放，较高值可能提高小文本识别但增加内存使用
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
  Key, Link, Monitor, Files, Timer, RefreshLeft, Refresh,
  EditPen, ArrowDown, Clock, Folder, Download, FolderOpened,
  CircleCheckFilled, CircleCloseFilled
} from '@element-plus/icons-vue'
import apiService from '@/services/api'

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

const mcpSettings = ref({
  mcp_enabled: false,
  mcp_server_url: '',
  mcp_api_key: '',
  mcp_timeout: 30
})

const uploadSettings = ref({
  upload_max_file_size: '524288000',
  upload_allowed_types: 'pdf,docx,doc,png,jpg,jpeg'
})

const screenshotSettings = ref({
  screenshot_timeout: '30',
  screenshot_max_pages: '20'
})

// 分类提示词相关
const activePromptTab = ref('vision')
const promptLoading = ref(false)
const promptSaving = ref(false)
const classificationPrompts = ref({
  vision: {
    value: '',
    description: '',
    updated_at: null
  },
  text: {
    value: '',
    description: '',
    updated_at: null
  }
})

// EasyOCR相关
const ocrStatusLoading = ref(false)
const modelDownloading = ref(false)
const ocrReloading = ref(false)
const ocrStatus = ref({
  docling_available: false,
  available: false,
  enabled: false,
  reader_initialized: false,
  model_path: '',
  languages: [],
  use_gpu: false,
  proxy: ''
})

const ocrSettings = ref({
  docling_enable_ocr: true,
  docling_force_full_page_ocr: true,
  docling_ocr_languages: ['ch_sim', 'en'],
  docling_confidence_threshold: 0.2,
  docling_bitmap_area_threshold: 0.03,
  docling_images_scale: 3.0,
  docling_use_gpu: false
})

// AI分析高级设置
const aiAnalysisSettings = ref({
  ai_analysis_enable_table_structure: false,
  ai_analysis_enable_picture_classification: false,
  ai_analysis_enable_picture_description: false,
  ai_analysis_generate_page_images: false,
  ai_analysis_generate_picture_images: false
})

// OCR精度优化设置
const ocrAdvancedSettings = ref({
  docling_confidence_threshold: 0.5,
  docling_bitmap_area_threshold: 0.05,
  docling_force_full_page_ocr: false,
  docling_recog_network: 'standard',
  docling_use_gpu: false,
  docling_images_scale: 2.0
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

      // 填充MCP设置
      Object.keys(mcpSettings.value).forEach(key => {
        if (settings[key]) {
          if (key === 'mcp_enabled') {
            mcpSettings.value[key] = settings[key].value === 'true'
          } else if (key === 'mcp_timeout') {
            mcpSettings.value[key] = parseInt(settings[key].value) || 30
          } else {
            mcpSettings.value[key] = settings[key].value
          }
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
      
      // 填充OCR设置
      Object.keys(ocrSettings.value).forEach(key => {
        if (settings[key]) {
          if (key === 'docling_ocr_languages' || key === 'easyocr_languages') {
            // 处理语言数组
            let value = settings[key].value
            if (typeof value === 'string') {
              try {
                value = JSON.parse(value)
              } catch {
                value = ['ch_sim', 'en']
              }
            }
            ocrSettings.value[key] = Array.isArray(value) ? value : ['ch_sim', 'en']
          } else if (key === 'easyocr_enable' || key === 'enable_docling_ocr' || key === 'easyocr_use_gpu') {
            // 处理布尔值
            let value = settings[key].value
            if (typeof value === 'string') {
              value = value.toLowerCase() === 'true'
            }
            ocrSettings.value[key] = Boolean(value)
          } else {
            ocrSettings.value[key] = settings[key].value
          }
        }
      })
      
      // 填充AI分析高级设置
      Object.keys(aiAnalysisSettings.value).forEach(key => {
        if (settings[key]) {
          let value = settings[key].value
          if (typeof value === 'string') {
            value = value.toLowerCase() === 'true'
          }
          aiAnalysisSettings.value[key] = Boolean(value)
        }
      })
      
      // 填充OCR高级设置
      Object.keys(ocrAdvancedSettings.value).forEach(key => {
        if (settings[key]) {
          let value = settings[key].value
          if (key === 'docling_confidence_threshold' || key === 'docling_bitmap_area_threshold' || key === 'docling_images_scale') {
            value = parseFloat(value) || 0.5
          } else if (key === 'docling_force_full_page_ocr' || key === 'docling_use_gpu') {
            value = value.toLowerCase() === 'true'
          }
          ocrAdvancedSettings.value[key] = value
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
    console.log('🔧 开始保存AI设置:', aiSettings.value)
    console.log('🌐 当前API baseURL:', apiService.defaults?.baseURL || 'axios实例获取中...')
    
    const response = await apiService.updateSettings(aiSettings.value)
    console.log('✅ AI设置保存响应:', response)
    
    const data = response?.data || response;
    if (data && data.success) {
      ElMessage.success({
        message: `AI设置保存成功！更新了 ${data.updated_settings?.length || 0} 个设置`,
        duration: 3000
      })
      console.log('🔄 重新加载设置以确保同步...')
      // 重新加载设置以确保同步
      await loadSettings()
    } else {
      console.error('❌ 保存响应失败:', data)
      ElMessage.error(data?.message || 'AI设置保存失败')
    }
  } catch (error) {
    console.error('❌ 保存AI设置失败:', error)
    console.error('错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      config: error.config
    })
    const errorMsg = error.response?.data?.detail || error.message || '保存AI设置失败'
    ElMessage.error({
      message: `保存失败: ${errorMsg}`,
      duration: 5000
    })
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

const saveMCPSettings = async () => {
  try {
    saving.value = true
    const response = await apiService.updateSettings(mcpSettings.value)
    
    if (response.success) {
      ElMessage.success('MCP服务配置保存成功')
    }
  } catch (error) {
    console.error('保存MCP设置失败:', error)
    ElMessage.error('保存MCP设置失败')
  } finally {
    saving.value = false
  }
}

const saveOCRSettings = async () => {
  try {
    saving.value = true
    const response = await apiService.updateSettings(ocrSettings.value)
    if (response.success) {
      ElMessage.success('OCR设置保存成功')
      await loadSettings()
    } else {
      ElMessage.error(response.message || 'OCR设置保存失败')
    }
  } catch (error) {
    ElMessage.error('保存OCR设置失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const saveAIAnalysisSettings = async () => {
  try {
    saving.value = true
    console.log('🔧 开始保存AI分析设置:', aiAnalysisSettings.value)
    
    const response = await apiService.updateSettings(aiAnalysisSettings.value)
    
    if (response.success) {
      ElMessage.success('AI分析设置保存成功')
      await loadSettings() // 重新加载设置
    } else {
      ElMessage.error('AI分析设置保存失败')
    }
  } catch (error) {
    console.error('保存AI分析设置失败:', error)
    ElMessage.error('保存AI分析设置失败')
  } finally {
    saving.value = false
  }
}

const saveOCRAdvancedSettings = async () => {
  try {
    saving.value = true
    console.log('🔧 开始保存OCR高级设置:', ocrAdvancedSettings.value)
    
    const response = await apiService.updateSettings(ocrAdvancedSettings.value)
    
    if (response.success) {
      ElMessage.success('OCR高级设置保存成功')
      await loadSettings() // 重新加载设置
    } else {
      ElMessage.error('OCR高级设置保存失败')
    }
  } catch (error) {
    console.error('保存OCR高级设置失败:', error)
    ElMessage.error('保存OCR高级设置失败')
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
      ...screenshotSettings.value,
      ...ocrSettings.value  // 添加OCR设置
    }
    
    // 处理OCR语言数组的序列化（与saveOCRSettings保持一致）
    if (Array.isArray(allSettings.docling_ocr_languages)) {
      allSettings.docling_ocr_languages = JSON.stringify(allSettings.docling_ocr_languages)
    }
    if (Array.isArray(allSettings.easyocr_languages)) {
      allSettings.easyocr_languages = JSON.stringify(allSettings.easyocr_languages)
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
    
    console.log('保存所有设置:', allSettings)
    
    const response = await apiService.updateSettings(allSettings)
    console.log('保存响应:', response)
    
    if (response && response.success) {
      ElMessage.success(`所有设置保存成功！更新了 ${response.updated_settings?.length || 0} 个设置`)
      // 重新加载设置以确保同步
      await loadSettings()
      // 重新加载OCR状态
      await refreshOCRStatus()
    } else {
      console.error('保存响应失败:', response)
      ElMessage.error(response?.message || '保存设置失败')
    }
  } catch (error) {
    console.error('保存设置失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '保存设置失败'
    ElMessage.error(errorMsg)
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

// 新增方法
// 加载分类提示词
const loadClassificationPrompts = async () => {
  try {
    promptLoading.value = true
    const response = await apiService.get('/settings/classification-prompts')
    
    if (response.success) {
      const prompts = response.prompts
      if (prompts.classification_vision_prompt) {
        classificationPrompts.value.vision = {
          value: prompts.classification_vision_prompt.value,
          description: prompts.classification_vision_prompt.description,
          updated_at: prompts.classification_vision_prompt.updated_at
        }
      }
      if (prompts.classification_text_prompt) {
        classificationPrompts.value.text = {
          value: prompts.classification_text_prompt.value,
          description: prompts.classification_text_prompt.description,
          updated_at: prompts.classification_text_prompt.updated_at
        }
      }
    }
  } catch (error) {
    console.error('加载分类提示词失败:', error)
    ElMessage.error('加载分类提示词失败: ' + (error.message || '未知错误'))
  } finally {
    promptLoading.value = false
  }
}

// 保存提示词
const savePrompt = async (promptKey) => {
  try {
    promptSaving.value = true
    const promptType = promptKey === 'classification_vision_prompt' ? 'vision' : 'text'
    const promptValue = classificationPrompts.value[promptType].value
    
    if (!promptValue.trim()) {
      ElMessage.error('提示词内容不能为空')
      return
    }
    
    const response = await apiService.put(`/settings/classification-prompts/${promptKey}`, {
      value: promptValue
    })
    
    if (response.success) {
      ElMessage.success('提示词保存成功，AI服务已热重载')
      classificationPrompts.value[promptType].updated_at = response.updated_at
    }
  } catch (error) {
    console.error('保存提示词失败:', error)
    ElMessage.error('保存提示词失败: ' + (error.message || '未知错误'))
  } finally {
    promptSaving.value = false
  }
}

// 处理提示词命令
const handlePromptCommand = async (command) => {
  switch (command) {
    case 'refresh':
      await loadClassificationPrompts()
      ElMessage.success('提示词已刷新')
      break
    case 'reset-vision':
      await resetPrompt('classification_vision_prompt')
      break
    case 'reset-text':
      await resetPrompt('classification_text_prompt')
      break
  }
}

// 重置提示词
const resetPrompt = async (promptKey) => {
  try {
    await ElMessageBox.confirm(
      '此操作将恢复提示词为默认值，是否继续？',
      '确认重置提示词',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    promptSaving.value = true
    const response = await apiService.post(`/settings/classification-prompts/reset/${promptKey}`)
    
    if (response.success) {
      ElMessage.success('提示词重置成功')
      await loadClassificationPrompts()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重置提示词失败:', error)
      ElMessage.error('重置提示词失败: ' + (error.message || '未知错误'))
    }
  } finally {
    promptSaving.value = false
  }
}

// 刷新OCR状态
const refreshOCRStatus = async () => {
  try {
    ocrStatusLoading.value = true
    
    // 同时获取Docling和EasyOCR状态
    const [doclingResponse, easyocrResponse] = await Promise.all([
      apiService.get('/ocr/docling/status'),
      apiService.get('/ocr/easyocr/status')
    ])
    
    if (doclingResponse.success && easyocrResponse.success) {
      ocrStatus.value = {
        docling_available: doclingResponse.docling_available,
        ocr_enabled: doclingResponse.ocr_enabled,
        converter_initialized: doclingResponse.converter_initialized,
        languages: doclingResponse.languages,
        reader_initialized: easyocrResponse.initialized,
        easyocr_models: easyocrResponse.existing_models || [],
        easyocr_model_path: easyocrResponse.model_path,
        use_gpu: false  // 从其他地方获取
      }
    }
  } catch (error) {
    console.error('获取OCR状态失败:', error)
    ElMessage.error('获取OCR状态失败: ' + (error.message || '未知错误'))
  } finally {
    ocrStatusLoading.value = false
  }
}

// 下载EasyOCR模型
const downloadModels = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将下载EasyOCR模型文件，可能需要较长时间，是否继续？',
      '确认下载模型',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    modelDownloading.value = true
    const response = await apiService.post('/ocr/easyocr/download-models')
    
    if (response.success) {
      ElMessage.success('EasyOCR模型下载成功')
      await refreshOCRStatus()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('下载模型失败:', error)
      ElMessage.error('下载模型失败: ' + (error.message || '未知错误'))
    }
  } finally {
    modelDownloading.value = false
  }
}

// 重新加载OCR配置
const reloadOCR = async () => {
  try {
    ocrReloading.value = true
    const response = await apiService.post('/ocr/docling/reload')
    
    if (response.success) {
      ElMessage.success('OCR配置重新加载成功')
      await refreshOCRStatus()
    }
  } catch (error) {
    console.error('重新加载OCR配置失败:', error)
    ElMessage.error('重新加载OCR配置失败: ' + (error.message || '未知错误'))
  } finally {
    ocrReloading.value = false
  }
}

// OCR切换处理
const ocrToggleLoading = ref(false)

const handleOCRToggle = async (enabled) => {
  try {
    ocrToggleLoading.value = true
    await saveOCRSettings()
    if (enabled) {
      ElMessage.info('EasyOCR已启用，建议下载/更新模型以获得最佳效果')
    } else {
      ElMessage.info('已切换到Tesseract OCR模式')
    }
  } catch (error) {
    // 切换失败时回退状态
    ocrSettings.value.easyocr_enable = !enabled
  } finally {
    ocrToggleLoading.value = false
  }
}

const formatLanguages = (languages) => {
  if (!languages) return []
  if (typeof languages === 'string') {
    try {
      languages = JSON.parse(languages)
    } catch {
      return [languages]
    }
  }
  if (Array.isArray(languages)) {
    return languages.map(lang => {
      switch(lang) {
        case 'ch_sim': return '简体中文'
        case 'ch_tra': return '繁体中文'  
        case 'en': return '英语'
        case 'ja': return '日语'
        case 'ko': return '韩语'
        default: return lang
      }
    })
  }
  return []
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch (e) {
    return '未知'
  }
}

// 生命周期
onMounted(async () => {
  await loadSettings()
  await loadClassificationPrompts()
  await refreshOCRStatus()
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

/* 分类提示词样式 */
.prompt-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: white;
}

.prompt-icon {
  background: rgba(255, 255, 255, 0.2) !important;
}

/* OCR样式 */
.ocr-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #6190e8 0%, #a7bfe8 100%);
  color: white;
}

.ocr-icon {
  background: rgba(255, 255, 255, 0.2) !important;
}

.ocr-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
}

.ocr-enable-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ocr-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 12px;
}

.ocr-option {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.option-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.option-name {
  font-weight: 600;
  color: #303133;
}

.option-features {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  color: #666;
}

.option-features li {
  padding: 4px 0;
  line-height: 1.4;
}

.model-management {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-status-card {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.status-icon {
  color: #409eff;
}

.status-title {
  font-weight: 600;
  color: #303133;
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.status-label {
  font-weight: 500;
  color: #606266;
  min-width: 100px;
}

.lang-tag {
  margin-left: 4px;
}

.model-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  min-width: 120px;
}

.ocr-status-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.ocr-status-info .status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #e9ecef;
}

.ocr-status-info .status-item:last-child {
  border-bottom: none;
}

.status-value {
  color: #606266;
  font-size: 14px;
}

.prompt-actions {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.prompt-content {
  padding: 24px;
}

.prompt-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.prompt-tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.prompt-info {
  margin-bottom: 16px;
}

.prompt-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompt-textarea :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  border-radius: 8px;
  border: 2px solid #e4e7ed;
  transition: border-color 0.3s ease;
}

.prompt-textarea :deep(.el-textarea__inner:focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.prompt-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.prompt-updated {
  color: #909399;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.prompt-actions {
  display: flex;
  gap: 12px;
}

/* EasyOCR样式 */
.ocr-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ocr-icon {
  background: rgba(255, 255, 255, 0.2) !important;
}

.ocr-status {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-tag {
  font-weight: 600;
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
}

.ocr-unavailable {
  padding: 20px;
}

.ocr-status-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-label {
  font-weight: 600;
  color: #495057;
  min-width: 100px;
}

.status-value {
  color: #6c757d;
  font-family: monospace;
}

.model-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.model-actions .el-button {
  flex: 1;
  min-width: 140px;
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
  
  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .prompt-meta {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .model-actions {
    flex-direction: column;
  }
  
  .model-actions .el-button {
    flex: none;
    width: 100%;
  }
  
  .ocr-status {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}
</style>