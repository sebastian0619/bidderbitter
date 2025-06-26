<template>
  <div class="ai-assistant">
    <el-card class="assistant-card">
      <template #header>
        <div class="card-header">
          <h2>🤖 AI智能助手</h2>
          <el-tag :type="connectionStatus.type">{{ connectionStatus.text }}</el-tag>
        </div>
      </template>

      <!-- 工具状态面板 -->
      <el-collapse v-model="activeTools" class="tools-panel">
        <el-collapse-item title="🛠️ 可用工具" name="tools">
          <div class="tools-grid">
            <el-card 
              v-for="tool in availableTools" 
              :key="tool.name"
              class="tool-card"
              shadow="hover"
            >
              <template #header>
                <div class="tool-header">
                  <span class="tool-name">{{ tool.name }}</span>
                  <el-tag size="small" type="success">可用</el-tag>
                </div>
              </template>
              <p class="tool-description">{{ tool.description }}</p>
              <div class="tool-params" v-if="tool.parameters">
                <small>参数：</small>
                <el-tag 
                  v-for="(param, key) in tool.parameters" 
                  :key="key"
                  size="small"
                  class="param-tag"
                >
                  {{ key }}
                </el-tag>
              </div>
            </el-card>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 对话区域 -->
      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            :class="['message', message.role]"
          >
            <div class="message-avatar">
              <el-avatar :icon="message.role === 'user' ? 'User' : 'Service'" />
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.content)"></div>
              
              <!-- 工具调用结果 -->
              <div v-if="message.tools_used && message.tools_used.length > 0" class="tools-used">
                <el-divider content-position="left">使用的工具</el-divider>
                <div 
                  v-for="(tool, toolIndex) in message.tools_used" 
                  :key="toolIndex"
                  class="tool-result"
                >
                  <el-tag type="info" size="small">{{ tool.tool_name }}</el-tag>
                  <div class="tool-args">
                    <small>参数：{{ JSON.stringify(tool.arguments) }}</small>
                  </div>
                  <div class="tool-output">
                    <el-button 
                      size="small" 
                      @click="toggleToolResult(toolIndex)"
                      type="text"
                    >
                      {{ toolResultVisible[toolIndex] ? '隐藏' : '显示' }}结果
                    </el-button>
                    <div v-if="toolResultVisible[toolIndex]" class="tool-result-content">
                      <pre>{{ JSON.stringify(tool.result, null, 2) }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            placeholder="请输入您的问题，AI助手将自动调用相关工具来帮助您..."
            @keydown.ctrl.enter="sendMessage"
          />
          <div class="input-actions">
            <el-button 
              type="primary" 
              @click="sendMessage"
              :loading="isLoading"
              :disabled="!userInput.trim()"
            >
              发送 (Ctrl+Enter)
            </el-button>
            <el-button @click="clearChat">清空对话</el-button>
          </div>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <el-divider content-position="left">快捷操作</el-divider>
        <div class="quick-buttons">
          <el-button 
            v-for="action in quickActions" 
            :key="action.name"
            @click="executeQuickAction(action)"
            size="small"
          >
            {{ action.label }}
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/services/api'

export default {
  name: 'AIAssistant',
  setup() {
    const messages = ref([])
    const userInput = ref('')
    const isLoading = ref(false)
    const availableTools = ref([])
    const connectionStatus = ref({ type: 'warning', text: '检查中...' })
    const activeTools = ref(['tools'])
    const toolResultVisible = ref({})

    // 快捷操作
    const quickActions = ref([
      {
        name: 'search_awards',
        label: '🔍 搜索奖项',
        action: () => {
          userInput.value = '请帮我搜索"金杜律师事务所"在2023年的获奖情况'
        }
      },
      {
        name: 'search_performance',
        label: '📊 查询业绩',
        action: () => {
          userInput.value = '请帮我查询"中伦律师事务所"的业绩信息'
        }
      },
      {
        name: 'analyze_document',
        label: '📄 分析文档',
        action: () => {
          userInput.value = '请帮我分析上传的文档，提取奖项信息'
        }
      },
      {
        name: 'get_statistics',
        label: '📈 数据统计',
        action: () => {
          userInput.value = '请帮我获取数据库的统计信息'
        }
      },
      {
        name: 'web_search',
        label: '🌐 网页搜索',
        action: () => {
          userInput.value = '请帮我搜索钱伯斯网站上的法律评级信息'
        }
      }
    ])

    const messagesContainer = ref(null)

    // 获取可用工具
    const loadTools = async () => {
      try {
        const response = await api.get('/ai-tools/tools')
        if (response.data.success) {
          availableTools.value = response.data.tools
          connectionStatus.value = { type: 'success', text: '已连接' }
        }
      } catch (error) {
        console.error('加载工具失败:', error)
        connectionStatus.value = { type: 'error', text: '连接失败' }
        ElMessage.error('加载工具失败')
      }
    }

    // 发送消息
    const sendMessage = async () => {
      if (!userInput.value.trim() || isLoading.value) return

      const userMessage = userInput.value.trim()
      
      // 添加用户消息
      messages.value.push({
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      })

      userInput.value = ''
      isLoading.value = true

      try {
        // 调用AI助手API
        const response = await api.post('/ai-tools/ai-assistant', {
          user_message: userMessage
        })

        if (response.data.success) {
          // 添加AI回复
          messages.value.push({
            role: 'assistant',
            content: response.data.response,
            tools_used: response.data.tools_used || [],
            timestamp: new Date()
          })

          // 初始化工具结果可见性
          if (response.data.tools_used) {
            response.data.tools_used.forEach((_, index) => {
              toolResultVisible.value[messages.value.length - 1 + '_' + index] = false
            })
          }
        } else {
          throw new Error(response.data.error || 'AI助手响应失败')
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        ElMessage.error('发送消息失败: ' + error.message)
        
        // 添加错误消息
        messages.value.push({
          role: 'assistant',
          content: '抱歉，我遇到了一些问题。请稍后重试。',
          timestamp: new Date()
        })
      } finally {
        isLoading.value = false
        await nextTick()
        scrollToBottom()
      }
    }

    // 清空对话
    const clearChat = async () => {
      try {
        await ElMessageBox.confirm('确定要清空所有对话记录吗？', '确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        messages.value = []
        toolResultVisible.value = {}
      } catch {
        // 用户取消
      }
    }

    // 执行快捷操作
    const executeQuickAction = (action) => {
      action.action()
    }

    // 切换工具结果可见性
    const toggleToolResult = (toolIndex) => {
      toolResultVisible.value[toolIndex] = !toolResultVisible.value[toolIndex]
    }

    // 格式化消息内容
    const formatMessage = (content) => {
      // 简单的markdown格式化
      return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>')
    }

    // 滚动到底部
    const scrollToBottom = () => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }

    onMounted(() => {
      loadTools()
    })

    return {
      messages,
      userInput,
      isLoading,
      availableTools,
      connectionStatus,
      activeTools,
      toolResultVisible,
      quickActions,
      messagesContainer,
      sendMessage,
      clearChat,
      executeQuickAction,
      toggleToolResult,
      formatMessage
    }
  }
}
</script>

<style scoped>
.ai-assistant {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.assistant-card {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #409eff;
}

.tools-panel {
  margin-bottom: 20px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.tool-card {
  border: 1px solid #e4e7ed;
}

.tool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-name {
  font-weight: bold;
  color: #409eff;
}

.tool-description {
  color: #606266;
  margin: 10px 0;
  font-size: 14px;
}

.tool-params {
  margin-top: 10px;
}

.param-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
  max-height: 400px;
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 10px;
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  line-height: 1.5;
}

.message.user .message-text {
  background: #409eff;
  color: white;
}

.tools-used {
  margin-top: 15px;
}

.tool-result {
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 6px;
  padding: 10px;
  margin: 10px 0;
}

.tool-args {
  margin: 8px 0;
  color: #606266;
}

.tool-result-content {
  margin-top: 10px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}

.tool-result-content pre {
  margin: 0;
  font-size: 12px;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-all;
}

.chat-input {
  margin-bottom: 20px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  gap: 10px;
}

.quick-actions {
  margin-top: 20px;
}

.quick-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-buttons .el-button {
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-assistant {
    padding: 10px;
  }
  
  .tools-grid {
    grid-template-columns: 1fr;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .quick-buttons {
    flex-direction: column;
  }
}
</style> 