<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">投标软件系统</h1>
      <p class="page-description">法律行业投标资料管理和文档生成系统</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon awards">
            <el-icon><Trophy /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalAwards }}</div>
            <div class="stat-label">获奖记录</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon performances">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalPerformances }}</div>
            <div class="stat-label">业绩记录</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon verified">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.verifiedCount }}</div>
            <div class="stat-label">已验证记录</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon documents">
            <el-icon><DocumentAdd /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats.generatedDocs }}</div>
            <div class="stat-label">生成文档</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 主要内容标签页 -->
    <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
      <!-- 获奖管理 -->
      <el-tab-pane label="获奖管理" name="awards">
        <div class="tab-content">
          <DataTable
            :data="awards"
            :columns="awardColumns"
            :loading="loadingAwards"
            :total-count="awardTotal"
            @refresh="loadAwards"
            @edit="editAward"
            @delete="deleteAward"
            @page-change="onAwardsPageChange"
          >
            <template #toolbar-right>
              <el-button type="primary" @click="showAddAward = true">
                <el-icon><Plus /></el-icon>
                添加获奖
              </el-button>
              <el-button @click="showUploadAward = true">
                <el-icon><Upload /></el-icon>
                上传文档
              </el-button>
            </template>
            
            <template #brand="{ row }">
              <el-tag :type="getBrandTagType(row.brand)" size="small">
                {{ row.brand }}
              </el-tag>
            </template>
            
            <template #verified="{ row }">
              <el-icon v-if="row.verified" color="#67c23a"><CircleCheck /></el-icon>
              <el-icon v-else color="#f56c6c"><CircleClose /></el-icon>
            </template>
            
            <template #screenshot="{ row }">
              <el-button
                v-if="row.screenshot_url"
                size="small"
                text
                @click="previewImage(row.screenshot_url)"
              >
                查看截图
              </el-button>
              <span v-else class="text-muted">无截图</span>
            </template>
          </DataTable>
        </div>
      </el-tab-pane>
      
      <!-- 业绩管理 -->
      <el-tab-pane label="业绩管理" name="performances">
        <div class="tab-content">
          <DataTable
            :data="performances"
            :columns="performanceColumns"
            :loading="loadingPerformances"
            :total-count="performanceTotal"
            @refresh="loadPerformances"
            @edit="editPerformance"
            @delete="deletePerformance"
            @page-change="onPerformancesPageChange"
          >
            <template #toolbar-right>
              <el-button type="primary" @click="showAddPerformance = true">
                <el-icon><Plus /></el-icon>
                添加业绩
              </el-button>
              <el-button @click="showUploadPerformance = true">
                <el-icon><Upload /></el-icon>
                上传文档
              </el-button>
            </template>
            
            <template #type="{ row }">
              <el-tag :type="row.type === 'advisor' ? 'success' : 'warning'" size="small">
                {{ row.type === 'advisor' ? '长期顾问' : '重大个案' }}
              </el-tag>
            </template>
            
            <template #amount="{ row }">
              <span v-if="row.amount">{{ formatAmount(row.amount) }}</span>
              <span v-else class="text-muted">未填写</span>
            </template>
          </DataTable>
        </div>
      </el-tab-pane>
      
      <!-- 文档生成 -->
      <el-tab-pane label="文档生成" name="generate">
        <div class="tab-content">
          <el-row :gutter="20">
            <el-col :md="12">
              <div class="card">
                <div class="card-header">
                  <h3 class="card-title">
                    <el-icon><DocumentAdd /></el-icon>
                    快速生成
                  </h3>
                </div>
                <div class="card-body">
                  <el-form :model="generateForm" label-width="100px">
                    <el-form-item label="文档类型">
                      <el-radio-group v-model="generateForm.type">
                        <el-radio-button label="award">获奖文档</el-radio-button>
                        <el-radio-button label="performance">业绩文档</el-radio-button>
                        <el-radio-button label="combined">综合文档</el-radio-button>
                      </el-radio-group>
                    </el-form-item>
                    
                    <el-form-item label="厂牌筛选" v-if="generateForm.type !== 'performance'">
                      <el-select
                        v-model="generateForm.brands"
                        multiple
                        placeholder="选择厂牌"
                        style="width: 100%"
                      >
                        <el-option
                          v-for="brand in appStore.brandOptions"
                          :key="brand.value"
                          :label="brand.label"
                          :value="brand.value"
                        />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="业务领域">
                      <el-select
                        v-model="generateForm.businessFields"
                        multiple
                        placeholder="选择业务领域"
                        style="width: 100%"
                      >
                        <el-option
                          v-for="field in appStore.businessFieldOptions"
                          :key="field.value"
                          :label="field.label"
                          :value="field.value"
                        />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="年份范围">
                      <el-select
                        v-model="generateForm.years"
                        multiple
                        placeholder="选择年份"
                        style="width: 100%"
                      >
                        <el-option
                          v-for="year in yearOptions"
                          :key="year"
                          :label="year"
                          :value="year"
                        />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button 
                        type="primary" 
                        @click="quickGenerate" 
                        :loading="generating"
                        style="width: 100%"
                      >
                        生成文档
                      </el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </el-col>
            
            <el-col :md="12">
              <div class="card">
                <div class="card-header">
                  <h3 class="card-title">
                    <el-icon><Clock /></el-icon>
                    生成历史
                  </h3>
                </div>
                <div class="card-body">
                  <el-timeline v-if="generateHistory.length > 0">
                    <el-timeline-item
                      v-for="item in generateHistory"
                      :key="item.id"
                      :timestamp="item.timestamp"
                      :type="item.status === 'success' ? 'success' : 'danger'"
                    >
                      <div class="history-item">
                        <strong>{{ item.name }}</strong>
                        <p>{{ item.description }}</p>
                        <el-button
                          v-if="item.status === 'success'"
                          size="small"
                          text
                          @click="downloadFile(item.filename)"
                        >
                          下载文件
                        </el-button>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                  <el-empty v-else description="暂无生成记录" />
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加获奖对话框 -->
    <el-dialog v-model="showAddAward" title="添加获奖记录" width="600px">
      <el-form :model="awardForm" :rules="awardRules" ref="awardFormRef" label-width="100px">
        <el-form-item label="厂牌" prop="brand">
          <el-select v-model="awardForm.brand" placeholder="选择厂牌" style="width: 100%">
            <el-option
              v-for="brand in appStore.brandOptions"
              :key="brand.value"
              :label="brand.label"
              :value="brand.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="获奖年份" prop="year">
          <el-select v-model="awardForm.year" placeholder="选择年份" style="width: 100%">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year"
              :value="year"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="业务领域" prop="business_field">
          <el-select v-model="awardForm.business_field" placeholder="选择业务领域" style="width: 100%">
            <el-option
              v-for="field in appStore.businessFieldOptions"
              :key="field.value"
              :label="field.label"
              :value="field.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="排名" prop="ranking">
          <el-input v-model="awardForm.ranking" placeholder="如：Band 1, Tier 1, 推荐等" />
        </el-form-item>
        
        <el-form-item label="网页链接">
          <el-input v-model="awardForm.source_url" placeholder="输入网页链接，可自动截图" />
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input v-model="awardForm.notes" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddAward = false">取消</el-button>
        <el-button type="primary" @click="submitAward" :loading="submittingAward">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传获奖文档对话框 -->
    <el-dialog v-model="showUploadAward" title="上传获奖文档" width="600px">
      <FileUpload
        ref="awardUploadRef"
        :allowed-types="['pdf', 'word', 'image']"
        :multiple="true"
        @upload="handleAwardUpload"
      />
      
      <template #footer>
        <el-button @click="showUploadAward = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加业绩对话框 -->
    <el-dialog v-model="showAddPerformance" title="添加业绩记录" width="600px">
      <el-form :model="performanceForm" :rules="performanceRules" ref="performanceFormRef" label-width="100px">
        <el-form-item label="业绩类型" prop="type">
          <el-radio-group v-model="performanceForm.type">
            <el-radio-button label="advisor">长期顾问</el-radio-button>
            <el-radio-button label="case">重大个案</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="客户名称" prop="client_name">
          <el-input v-model="performanceForm.client_name" placeholder="输入客户名称" />
        </el-form-item>
        
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="performanceForm.project_name" placeholder="输入项目名称" />
        </el-form-item>
        
        <el-form-item label="业务领域" prop="business_field">
          <el-select v-model="performanceForm.business_field" placeholder="选择业务领域" style="width: 100%">
            <el-option
              v-for="field in appStore.businessFieldOptions"
              :key="field.value"
              :label="field.label"
              :value="field.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="项目金额">
          <el-input
            v-model="performanceForm.amount"
            placeholder="输入金额"
            type="number"
          >
            <template #append>万元</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="项目年份" prop="year">
          <el-select v-model="performanceForm.year" placeholder="选择年份" style="width: 100%">
            <el-option
              v-for="year in yearOptions"
              :key="year"
              :label="year"
              :value="year"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="项目描述">
          <el-input v-model="performanceForm.description" type="textarea" rows="4" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddPerformance = false">取消</el-button>
        <el-button type="primary" @click="submitPerformance" :loading="submittingPerformance">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 上传业绩文档对话框 -->
    <el-dialog v-model="showUploadPerformance" title="上传业绩文档" width="600px">
      <FileUpload
        ref="performanceUploadRef"
        :allowed-types="['pdf', 'word', 'image']"
        :multiple="true"
        @upload="handlePerformanceUpload"
      />
      
      <template #footer>
        <el-button @click="showUploadPerformance = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 图片预览对话框 -->
    <el-dialog v-model="showImagePreview" title="截图预览" width="800px">
      <div class="image-preview">
        <el-image
          :src="previewImageUrl"
          fit="contain"
          style="width: 100%; max-height: 500px"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { apiService } from '@/services/api'
import DataTable from '@/components/DataTable.vue'
import FileUpload from '@/components/FileUpload.vue'
import {
  Trophy,
  Document,
  CircleCheck,
  CircleClose,
  DocumentAdd,
  Upload,
  Clock,
  Plus,
  Refresh
} from '@element-plus/icons-vue'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const activeTab = ref('awards')
const stats = ref({
  totalAwards: 0,
  totalPerformances: 0,
  verifiedCount: 0,
  generatedDocs: 0
})

// 获奖相关数据
const awards = ref([])
const loadingAwards = ref(false)
const awardTotal = ref(0)
const showAddAward = ref(false)
const showUploadAward = ref(false)
const submittingAward = ref(false)

// 业绩相关数据
const performances = ref([])
const loadingPerformances = ref(false)
const performanceTotal = ref(0)
const showAddPerformance = ref(false)
const showUploadPerformance = ref(false)
const submittingPerformance = ref(false)

// 生成相关数据
const generating = ref(false)
const generateHistory = ref([])

// 图片预览
const showImagePreview = ref(false)
const previewImageUrl = ref('')

// 表单数据
const awardForm = ref({
  brand: '',
  year: new Date().getFullYear(),
  business_field: '',
  ranking: '',
  source_url: '',
  notes: ''
})

const performanceForm = ref({
  type: 'advisor',
  client_name: '',
  project_name: '',
  business_field: '',
  amount: '',
  year: new Date().getFullYear(),
  description: ''
})

const generateForm = ref({
  type: 'combined',
  brands: [],
  businessFields: [],
  years: []
})

// 表单验证规则
const awardRules = {
  brand: [{ required: true, message: '请选择厂牌', trigger: 'change' }],
  year: [{ required: true, message: '请选择年份', trigger: 'change' }],
  business_field: [{ required: true, message: '请选择业务领域', trigger: 'change' }],
  ranking: [{ required: true, message: '请输入排名', trigger: 'blur' }]
}

const performanceRules = {
  type: [{ required: true, message: '请选择业绩类型', trigger: 'change' }],
  client_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  project_name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  business_field: [{ required: true, message: '请选择业务领域', trigger: 'change' }],
  year: [{ required: true, message: '请选择年份', trigger: 'change' }]
}

// 表格列配置
const awardColumns = [
  { prop: 'brand', label: '厂牌', slot: 'brand', width: 120 },
  { prop: 'year', label: '年份', width: 80 },
  { prop: 'business_field', label: '业务领域', minWidth: 150 },
  { prop: 'ranking', label: '排名', width: 120 },
  { prop: 'verified', label: '验证状态', slot: 'verified', width: 100 },
  { prop: 'screenshot_url', label: '截图', slot: 'screenshot', width: 100 },
  { prop: 'created_at', label: '创建时间', width: 150, formatter: formatDate }
]

const performanceColumns = [
  { prop: 'type', label: '类型', slot: 'type', width: 100 },
  { prop: 'client_name', label: '客户名称', minWidth: 150 },
  { prop: 'project_name', label: '项目名称', minWidth: 200 },
  { prop: 'business_field', label: '业务领域', minWidth: 150 },
  { prop: 'amount', label: '项目金额', slot: 'amount', width: 120 },
  { prop: 'year', label: '年份', width: 80 },
  { prop: 'created_at', label: '创建时间', width: 150, formatter: formatDate }
]

// 计算属性
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= currentYear - 10; i--) {
    years.push(i)
  }
  return years
})

// 方法实现
const loadStats = async () => {
  try {
    const [awardStats, performanceStats] = await Promise.all([
      apiService.getAwardStats(),
      apiService.getPerformanceStats()
    ])
    
    stats.value = {
      totalAwards: awardStats.total || 0,
      totalPerformances: performanceStats.total || 0,
      verifiedCount: awardStats.verified || 0,
      generatedDocs: 34 // 暂时硬编码
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadAwards = async (params = {}) => {
  try {
    loadingAwards.value = true
    const result = await apiService.getAwards(params)
    if (result) {
      awards.value = result.awards || []
      awardTotal.value = result.total || 0
    }
  } catch (error) {
    console.error('加载获奖数据失败:', error)
  } finally {
    loadingAwards.value = false
  }
}

const loadPerformances = async (params = {}) => {
  try {
    loadingPerformances.value = true
    const result = await apiService.getPerformances(params)
    if (result) {
      performances.value = result.performances || []
      performanceTotal.value = result.total || 0
    }
  } catch (error) {
    console.error('加载业绩数据失败:', error)
  } finally {
    loadingPerformances.value = false
  }
}

// 其他方法
const getBrandTagType = (brand) => {
  const types = ['', 'success', 'info', 'warning', 'danger']
  return types[brand.length % types.length]
}

const formatDate = (row, column, cellValue) => {
  if (!cellValue) return ''
  return new Date(cellValue).toLocaleDateString()
}

const formatAmount = (amount) => {
  if (!amount) return ''
  return `${Number(amount).toLocaleString()} 万元`
}

const previewImage = (url) => {
  previewImageUrl.value = url
  showImagePreview.value = true
}

const editAward = (row) => {
  // 编辑获奖记录
  Object.assign(awardForm.value, row)
  showAddAward.value = true
}

const deleteAward = async (row) => {
  try {
    await apiService.deleteAward(row.id)
    appStore.showMessage('删除成功')
    loadAwards()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const editPerformance = (row) => {
  // 编辑业绩记录
  Object.assign(performanceForm.value, row)
  showAddPerformance.value = true
}

const deletePerformance = async (row) => {
  try {
    await apiService.deletePerformance(row.id)
    appStore.showMessage('删除成功')
    loadPerformances()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const submitAward = async () => {
  try {
    submittingAward.value = true
    await apiService.createAward(awardForm.value)
    appStore.showMessage('添加成功')
    showAddAward.value = false
    loadAwards()
  } catch (error) {
    console.error('添加失败:', error)
  } finally {
    submittingAward.value = false
  }
}

const submitPerformance = async () => {
  try {
    submittingPerformance.value = true
    await apiService.createPerformance(performanceForm.value)
    appStore.showMessage('添加成功')
    showAddPerformance.value = false
    loadPerformances()
  } catch (error) {
    console.error('添加失败:', error)
  } finally {
    submittingPerformance.value = false
  }
}

const handleAwardUpload = async (files) => {
  try {
    for (const file of files) {
      await apiService.uploadDocument(file, 'award')
    }
    appStore.showMessage('上传成功')
    loadAwards()
  } catch (error) {
    console.error('上传失败:', error)
  }
}

const handlePerformanceUpload = async (files) => {
  try {
    for (const file of files) {
      await apiService.uploadDocument(file, 'performance')
    }
    appStore.showMessage('上传成功')
    loadPerformances()
  } catch (error) {
    console.error('上传失败:', error)
  }
}

const quickGenerate = async () => {
  try {
    generating.value = true
    const result = await apiService.generateDocument({
      type: generateForm.value.type,
      filters: {
        brands: generateForm.value.brands,
        business_fields: generateForm.value.businessFields,
        years: generateForm.value.years
      }
    })
    
    if (result.success) {
      appStore.showMessage('文档生成成功', 'success')
      // 下载文件
      window.open(result.download_url, '_blank')
    }
  } catch (error) {
    console.error('生成文档失败:', error)
  } finally {
    generating.value = false
  }
}

const downloadFile = (filename) => {
  window.open(`/api/download/${filename}`, '_blank')
}

const onAwardsPageChange = (params) => {
  loadAwards({ page: params.page, size: params.size })
}

const onPerformancesPageChange = (params) => {
  loadPerformances({ page: params.page, size: params.size })
}

// 页面加载时初始化数据
onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadAwards(),
    loadPerformances()
  ])
})
</script>

<style lang="scss" scoped>
.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  
  &:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
  
  &.awards {
    background: linear-gradient(135deg, #f6d55c, #f39c12);
  }
  
  &.performances {
    background: linear-gradient(135deg, #3498db, #2980b9);
  }
  
  &.verified {
    background: linear-gradient(135deg, #2ecc71, #27ae60);
  }
  
  &.documents {
    background: linear-gradient(135deg, #9b59b6, #8e44ad);
  }
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.main-tabs {
  margin-top: 0;
  
  .tab-content {
    padding: 0;
  }
}

.text-muted {
  color: var(--el-text-color-placeholder);
}

.image-preview {
  text-align: center;
}

.history-item {
  strong {
    color: var(--el-text-color-primary);
    font-size: 14px;
  }
  
  p {
    margin: 4px 0;
    color: var(--el-text-color-regular);
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .stats-row {
    margin-bottom: 16px;
  }
  
  .stat-card {
    margin-bottom: 12px;
    padding: 16px;
  }
}
</style> 