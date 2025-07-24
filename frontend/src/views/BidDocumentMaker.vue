<template>
  <div class="bid-document-maker">
    <el-page-header @back="goBack" title="投标文件制作">
      <template #content>
        <span class="page-title">投标文件制作</span>
      </template>
    </el-page-header>

    <el-card class="main-card">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success" class="steps">
        <el-step title="项目初始化" description="创建项目并上传招标文件"></el-step>
        <el-step title="信息提取" description="AI提取招标关键信息"></el-step>
        <el-step title="模板选择" description="选择投标文件模板"></el-step>
        <el-step title="内容配置" description="配置投标文件内容"></el-step>
        <el-step title="生成文档" description="生成最终投标文件"></el-step>
      </el-steps>

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 项目初始化 -->
        <div v-if="currentStep === 0" class="step-panel">
          <h3>项目初始化</h3>
          <el-form :model="projectForm" :rules="projectRules" ref="projectFormRef" label-width="120px">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="projectForm.name" placeholder="请输入项目名称"></el-input>
            </el-form-item>
            
            <el-form-item label="招标文件">
              <el-upload
                ref="tenderFileUpload"
                class="tender-file-uploader"
                drag
                :action="`/api/bid-documents/upload-tender-file`"
                :auto-upload="false"
                :on-change="handleTenderFileChange"
                :on-success="handleTenderFileSuccess"
                :on-error="handleTenderFileError"
                :file-list="tenderFileList"
                accept=".pdf,.doc,.docx"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">拖拽招标文件到此处或 <em>点击上传</em></div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持PDF、Word格式的招标文件，文件大小不超过50MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="createProject" :loading="creating">
                创建项目
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤2: 信息提取 -->
        <div v-if="currentStep === 1" class="step-panel">
          <h3>招标信息提取</h3>
          <div v-if="extracting" class="extracting-status">
            <el-progress type="circle" :percentage="extractProgress" :status="extractStatus"></el-progress>
            <p>{{ extractMessage }}</p>
          </div>
          
          <div v-else-if="extractedInfo" class="extracted-info">
            <el-alert
              title="AI已成功提取招标信息"
              type="success"
              :closable="false"
              show-icon
            />
            
            <el-form :model="extractedInfo" label-width="120px" class="info-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="招标人">
                    <el-input v-model="extractedInfo.tender_company" placeholder="招标人名称"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="招标代理">
                    <el-input v-model="extractedInfo.tender_agency" placeholder="招标代理机构"></el-input>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="投标人">
                    <el-input v-model="extractedInfo.bidder_name" placeholder="投标人名称"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="投标截止时间">
                    <el-date-picker
                      v-model="extractedInfo.deadline"
                      type="datetime"
                      placeholder="选择投标截止时间"
                      format="YYYY-MM-DD HH:mm:ss"
                      value-format="YYYY-MM-DD HH:mm:ss"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="法定代表人">
                    <el-input v-model="extractedInfo.legal_representative" placeholder="法定代表人"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="授权代表">
                    <el-input v-model="extractedInfo.authorized_representative" placeholder="授权代表"></el-input>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="项目名称">
                <el-input v-model="extractedInfo.project_name" placeholder="项目名称"></el-input>
              </el-form-item>
              
              <el-form-item label="项目预算">
                <el-input v-model="extractedInfo.project_budget" placeholder="项目预算金额"></el-input>
              </el-form-item>
              
              <el-form-item label="业务范围">
                <el-input
                  v-model="extractedInfo.business_scope"
                  type="textarea"
                  :rows="3"
                  placeholder="业务范围描述"
                ></el-input>
              </el-form-item>
            </el-form>
            
            <div class="action-buttons">
              <el-button @click="currentStep = 0">上一步</el-button>
              <el-button type="primary" @click="saveProjectInfo">保存并继续</el-button>
            </div>
          </div>
        </div>

        <!-- 步骤3: 模板选择 -->
        <div v-if="currentStep === 2" class="step-panel">
          <h3>选择投标文件模板</h3>
          <div class="template-selection">
            <el-radio-group v-model="selectedTemplateId" class="template-group">
              <el-card
                v-for="template in templates"
                :key="template.id"
                class="template-card"
                :class="{ 'selected': selectedTemplateId === template.id }"
                @click="selectedTemplateId = template.id"
              >
                <div class="template-info">
                  <h4>{{ template.name }}</h4>
                  <p>{{ template.description || '暂无描述' }}</p>
                  <el-tag v-if="template.is_default" type="success" size="small">默认模板</el-tag>
                </div>
              </el-card>
            </el-radio-group>
            
            <div class="action-buttons">
              <el-button @click="currentStep = 1">上一步</el-button>
              <el-button type="primary" @click="nextStep" :disabled="!selectedTemplateId">
                下一步
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤4: 内容配置 -->
        <div v-if="currentStep === 3" class="step-panel">
          <h3>配置投标文件内容</h3>
          <div class="content-config">
            <el-form :model="contentConfig" label-width="120px">
              <el-form-item label="包含内容">
                <el-checkbox-group v-model="contentConfig.includeItems">
                  <el-checkbox label="awards">获奖信息</el-checkbox>
                  <el-checkbox label="performances">业绩案例</el-checkbox>
                  <el-checkbox label="lawyers">律师团队</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
              
              <el-form-item label="数据筛选">
                <el-collapse v-model="activeFilters">
                  <el-collapse-item title="获奖信息筛选" name="awards">
                    <el-form-item label="年份范围">
                      <el-date-picker
                        v-model="contentConfig.awardYearRange"
                        type="yearrange"
                        range-separator="至"
                        start-placeholder="开始年份"
                        end-placeholder="结束年份"
                      />
                    </el-form-item>
                    <el-form-item label="业务领域">
                      <el-select v-model="contentConfig.awardBusinessFields" multiple placeholder="选择业务领域">
                        <el-option label="知识产权" value="知识产权"></el-option>
                        <el-option label="公司并购" value="公司并购"></el-option>
                        <el-option label="金融证券" value="金融证券"></el-option>
                        <el-option label="房地产" value="房地产"></el-option>
                      </el-select>
                    </el-form-item>
                  </el-collapse-item>
                  
                  <el-collapse-item title="业绩案例筛选" name="performances">
                    <el-form-item label="项目类型">
                      <el-select v-model="contentConfig.performanceTypes" multiple placeholder="选择项目类型">
                        <el-option label="长期顾问" value="长期顾问"></el-option>
                        <el-option label="重大个案" value="重大个案"></el-option>
                      </el-select>
                    </el-form-item>
                    <el-form-item label="金额范围">
                      <el-input-number
                        v-model="contentConfig.minAmount"
                        placeholder="最小金额"
                        :min="0"
                      />
                      <span class="range-separator">至</span>
                      <el-input-number
                        v-model="contentConfig.maxAmount"
                        placeholder="最大金额"
                        :min="0"
                      />
                    </el-form-item>
                  </el-collapse-item>
                  
                  <el-collapse-item title="律师团队筛选" name="lawyers">
                    <el-form-item label="职位">
                      <el-select v-model="contentConfig.lawyerPositions" multiple placeholder="选择职位">
                        <el-option label="合伙人" value="合伙人"></el-option>
                        <el-option label="律师" value="律师"></el-option>
                      </el-select>
                    </el-form-item>
                  </el-collapse-item>
                </el-collapse>
              </el-form-item>
            </el-form>
            
            <div class="action-buttons">
              <el-button @click="currentStep = 2">上一步</el-button>
              <el-button type="primary" @click="nextStep">下一步</el-button>
            </div>
          </div>
        </div>

        <!-- 步骤5: 生成文档 -->
        <div v-if="currentStep === 4" class="step-panel">
          <h3>生成投标文件</h3>
          <div class="generation-panel">
            <div v-if="generating" class="generating-status">
              <el-progress type="circle" :percentage="generateProgress" :status="generateStatus"></el-progress>
              <p>{{ generateMessage }}</p>
            </div>
            
            <div v-else-if="generatedDocument" class="generation-result">
              <el-result
                icon="success"
                title="投标文件生成成功"
                sub-title="您的投标文件已生成完成，可以下载使用"
              >
                <template #extra>
                  <el-button type="primary" @click="downloadDocument">下载文档</el-button>
                  <el-button @click="previewDocument">预览文档</el-button>
                  <el-button @click="resetProcess">重新开始</el-button>
                </template>
              </el-result>
            </div>
            
            <div v-else class="generation-start">
              <el-alert
                title="准备生成投标文件"
                type="info"
                :closable="false"
                show-icon
              >
                <template #default>
                  <p>系统将根据您配置的信息生成完整的投标文件，包含：</p>
                  <ul>
                    <li>项目基本信息</li>
                    <li v-if="contentConfig.includeItems.includes('awards')">获奖情况</li>
                    <li v-if="contentConfig.includeItems.includes('performances')">业绩案例</li>
                    <li v-if="contentConfig.includeItems.includes('lawyers')">律师团队</li>
                  </ul>
                </template>
              </el-alert>
              
              <div class="action-buttons">
                <el-button @click="currentStep = 3">上一步</el-button>
                <el-button type="primary" @click="generateDocument" :loading="generating">
                  开始生成
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 文档预览对话框 -->
    <el-dialog
      v-model="previewDialog.visible"
      title="文档预览"
      width="80%"
      :fullscreen="true"
    >
      <div class="document-preview">
        <iframe
          v-if="previewDialog.url"
          :src="previewDialog.url"
          width="100%"
          height="600px"
          frameborder="0"
        ></iframe>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiService } from '@/services/api'

export default {
  name: 'BidDocumentMaker',
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const currentStep = ref(0)
    const creating = ref(false)
    const extracting = ref(false)
    const generating = ref(false)
    const extractProgress = ref(0)
    const generateProgress = ref(0)
    const extractStatus = ref('')
    const generateStatus = ref('')
    const extractMessage = ref('')
    const generateMessage = ref('')
    
    const projectForm = reactive({
      name: '',
      description: ''
    })
    
    const projectRules = {
      name: [
        { required: true, message: '请输入项目名称', trigger: 'blur' }
      ]
    }
    
    const tenderFileList = ref([])
    const extractedInfo = ref(null)
    const templates = ref([])
    const selectedTemplateId = ref(null)
    const contentConfig = reactive({
      includeItems: ['awards', 'performances', 'lawyers'],
      awardYearRange: null,
      awardBusinessFields: [],
      performanceTypes: [],
      minAmount: null,
      maxAmount: null,
      lawyerPositions: []
    })
    
    const activeFilters = ref(['awards'])
    const generatedDocument = ref(null)
    const previewDialog = reactive({
      visible: false,
      url: ''
    })
    
    const projectFormRef = ref()
    const projectId = ref(null)
    
    // 方法
    const goBack = () => {
      router.push('/projects')
    }
    
    const handleTenderFileChange = (file) => {
      console.log('招标文件选择:', file)
    }
    
    const handleTenderFileSuccess = (response) => {
      ElMessage.success('招标文件上传成功')
    }
    
    const handleTenderFileError = (error) => {
      ElMessage.error('招标文件上传失败')
    }
    
    const createProject = async () => {
      try {
        await projectFormRef.value.validate()
        
        if (tenderFileList.value.length === 0) {
          ElMessage.warning('请先上传招标文件')
          return
        }
        
        creating.value = true
        
        // 创建项目
        const projectData = {
          name: projectForm.name,
          description: projectForm.description
        }
        
        const projectResponse = await apiService.createProject(projectData)
        
        if (projectResponse.success) {
          projectId.value = projectResponse.id
          // 分析招标文件
          const analysisResponse = await apiService.analyzeTenderDocument(
            tenderFileList.value[0].raw,
            projectId.value
          )
          
          if (analysisResponse.success) {
            ElMessage.success('项目创建成功')
            currentStep.value = 1
            await extractTenderInfo(analysisResponse.data.file_path)
          }
        }
      } catch (error) {
        ElMessage.error('创建项目失败: ' + error.message)
      } finally {
        creating.value = false
      }
    }
    
    const extractTenderInfo = async (filePath) => {
      try {
        extracting.value = true
        extractProgress.value = 0
        extractMessage.value = '正在分析招标文件...'
        
        // 模拟进度
        const progressInterval = setInterval(() => {
          if (extractProgress.value < 90) {
            extractProgress.value += 10
          }
        }, 500)
        
        const response = await apiService.analyzeTenderDocument(tenderFileList.value[0].raw, projectId.value)
        
        clearInterval(progressInterval)
        extractProgress.value = 100
        extractMessage.value = '信息提取完成'
        
        if (response.success) {
          extractedInfo.value = response.data.extracted_info
          ElMessage.success('招标信息提取成功')
        } else {
          ElMessage.error('信息提取失败: ' + response.error)
        }
      } catch (error) {
        ElMessage.error('信息提取失败: ' + error.message)
      } finally {
        extracting.value = false
      }
    }
    
    const saveProjectInfo = async () => {
      try {
        const response = await apiService.updateProject(projectId.value, extractedInfo.value)
        
        if (response.success) {
          ElMessage.success('项目信息保存成功')
          await loadTemplates()
          currentStep.value = 2
        }
      } catch (error) {
        ElMessage.error('保存项目信息失败: ' + error.message)
      }
    }
    
    const loadTemplates = async () => {
      try {
        const response = await apiService.getBidTemplates('bid_document')
        if (response.success) {
          templates.value = response.data
          if (templates.value.length > 0) {
            const defaultTemplate = templates.value.find(t => t.is_default)
            selectedTemplateId.value = defaultTemplate ? defaultTemplate.id : templates.value[0].id
          }
        }
      } catch (error) {
        ElMessage.error('加载模板失败: ' + error.message)
      }
    }
    
    const nextStep = () => {
      currentStep.value++
    }
    
    const generateDocument = async () => {
      try {
        generating.value = true
        generateProgress.value = 0
        generateMessage.value = '正在生成投标文件...'
        
        // 模拟进度
        const progressInterval = setInterval(() => {
          if (generateProgress.value < 90) {
            generateProgress.value += 10
          }
        }, 1000)
        
        const response = await apiService.generateBidDocument({
          project_id: projectId.value,
          template_id: selectedTemplateId.value,
          sections: [],
          field_mappings: {},
          include_attachments: true,
          auto_fill_data: true
        })
        
        clearInterval(progressInterval)
        generateProgress.value = 100
        generateMessage.value = '文档生成完成'
        
        if (response.success) {
          generatedDocument.value = response.data
          ElMessage.success('投标文件生成成功')
        } else {
          ElMessage.error('文档生成失败: ' + response.error)
        }
      } catch (error) {
        ElMessage.error('文档生成失败: ' + error.message)
      } finally {
        generating.value = false
      }
    }
    
    const downloadDocument = () => {
      if (generatedDocument.value) {
        window.open(`/api/bid-documents/download/${generatedDocument.value.document_id}`, '_blank')
      }
    }
    
    const previewDocument = () => {
      if (generatedDocument.value) {
        previewDialog.url = `/api/bid-documents/preview/${generatedDocument.value.document_id}`
        previewDialog.visible = true
      }
    }
    
    const resetProcess = () => {
      currentStep.value = 0
      extractedInfo.value = null
      generatedDocument.value = null
      tenderFileList.value = []
      projectForm.name = ''
      projectForm.description = ''
    }
    
    // 生命周期
    onMounted(() => {
      // 初始化
    })
    
    return {
      currentStep,
      creating,
      extracting,
      generating,
      extractProgress,
      generateProgress,
      extractStatus,
      generateStatus,
      extractMessage,
      generateMessage,
      projectForm,
      projectRules,
      tenderFileList,
      extractedInfo,
      templates,
      selectedTemplateId,
      contentConfig,
      activeFilters,
      generatedDocument,
      previewDialog,
      projectFormRef,
      projectId,
      goBack,
      handleTenderFileChange,
      handleTenderFileSuccess,
      handleTenderFileError,
      createProject,
      saveProjectInfo,
      nextStep,
      generateDocument,
      downloadDocument,
      previewDocument,
      resetProcess
    }
  }
}
</script>

<style scoped>
.bid-document-maker {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.main-card {
  margin-top: 20px;
}

.steps {
  margin-bottom: 30px;
}

.step-content {
  min-height: 400px;
}

.step-panel {
  padding: 20px 0;
}

.step-panel h3 {
  margin-bottom: 20px;
  color: #303133;
}

.tender-file-uploader {
  width: 100%;
}

.extracting-status,
.generating-status {
  text-align: center;
  padding: 40px 0;
}

.extracting-status p,
.generating-status p {
  margin-top: 20px;
  color: #606266;
}

.extracted-info {
  margin-top: 20px;
}

.info-form {
  margin-top: 20px;
}

.template-selection {
  margin-top: 20px;
}

.template-group {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.template-card {
  width: 300px;
  cursor: pointer;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.template-card.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.template-info h4 {
  margin: 0 0 10px 0;
  color: #303133;
}

.template-info p {
  margin: 0 0 10px 0;
  color: #606266;
  font-size: 14px;
}

.content-config {
  margin-top: 20px;
}

.range-separator {
  margin: 0 10px;
  color: #606266;
}

.generation-panel {
  text-align: center;
  padding: 40px 0;
}

.generation-start {
  max-width: 600px;
  margin: 0 auto;
}

.generation-start ul {
  text-align: left;
  margin: 10px 0;
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}

.document-preview {
  height: 600px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}
</style> 