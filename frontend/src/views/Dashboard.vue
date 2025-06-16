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

    <!-- 主要功能区 -->
    <el-row :gutter="20" class="main-section">
      <el-col :md="12">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <el-icon><Upload /></el-icon>
              快速上传
            </h3>
          </div>
          <div class="card-body">
            <p>上传Word或PDF文档，AI自动提取获奖和业绩信息</p>
            <div class="upload-buttons">
              <el-button 
                type="primary" 
                icon="Trophy"
                @click="goToUpload('awards')"
                class="upload-btn"
              >
                上传获奖文档
              </el-button>
              <el-button 
                type="success" 
                icon="Document"
                @click="goToUpload('performances')"
                class="upload-btn"
              >
                上传业绩文档
              </el-button>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :md="12">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <el-icon><DocumentAdd /></el-icon>
              快速生成
            </h3>
          </div>
          <div class="card-body">
            <p>根据筛选条件快速生成投标文档</p>
            <div class="generate-buttons">
              <el-button 
                type="warning" 
                icon="Document"
                @click="goToGenerate('combined')"
                class="generate-btn"
              >
                生成综合文档
              </el-button>
              <el-button 
                type="info" 
                icon="Setting"
                @click="showQuickGenerate = true"
                class="generate-btn"
              >
                自定义生成
              </el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          <el-icon><Clock /></el-icon>
          最近活动
        </h3>
        <el-button text @click="refreshActivities">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      <div class="card-body">
        <el-timeline v-if="recentActivities.length > 0">
          <el-timeline-item
            v-for="activity in recentActivities"
            :key="activity.id"
            :timestamp="activity.timestamp"
            :type="activity.type"
          >
            <div class="activity-content">
              <strong>{{ activity.title }}</strong>
              <p>{{ activity.description }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无活动记录" />
      </div>
    </div>

    <!-- 快速生成对话框 -->
    <el-dialog
      v-model="showQuickGenerate"
      title="快速生成文档"
      width="600px"
    >
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
      </el-form>
      
      <template #footer>
        <el-button @click="showQuickGenerate = false">取消</el-button>
        <el-button type="primary" @click="quickGenerate" :loading="generating">
          生成文档
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { apiService } from '@/services/api'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const stats = ref({
  totalAwards: 0,
  totalPerformances: 0,
  verifiedCount: 0,
  generatedDocs: 0
})

const recentActivities = ref([])
const showQuickGenerate = ref(false)
const generating = ref(false)

const generateForm = ref({
  type: 'combined',
  brands: [],
  businessFields: [],
  years: []
})

// 计算属性
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= currentYear - 10; i--) {
    years.push(i)
  }
  return years
})

// 方法
const loadStats = async () => {
  try {
    // 这里应该调用实际的统计API
    // 暂时使用模拟数据
    stats.value = {
      totalAwards: 128,
      totalPerformances: 245,
      verifiedCount: 89,
      generatedDocs: 34
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadRecentActivities = async () => {
  try {
    // 模拟最近活动数据
    recentActivities.value = [
      {
        id: 1,
        title: '新增获奖记录',
        description: 'Chambers 2024年度银行与金融领域排名',
        timestamp: '2024-01-15 14:30',
        type: 'success'
      },
      {
        id: 2,
        title: '业绩文档上传',
        description: '某银行并购项目法律服务合同',
        timestamp: '2024-01-15 10:15',
        type: 'primary'
      },
      {
        id: 3,
        title: '生成投标文档',
        description: '银行与金融领域综合投标文档',
        timestamp: '2024-01-14 16:45',
        type: 'warning'
      }
    ]
  } catch (error) {
    console.error('加载活动记录失败:', error)
  }
}

const goToUpload = (type) => {
  if (type === 'awards') {
    router.push('/awards/upload')
  } else {
    router.push('/performances/upload')
  }
}

const goToGenerate = (type) => {
  router.push(`/generate/${type}`)
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
      showQuickGenerate.value = false
    }
    
  } catch (error) {
    console.error('生成文档失败:', error)
    appStore.showMessage('生成文档失败', 'error')
  } finally {
    generating.value = false
  }
}

const refreshActivities = async () => {
  await loadRecentActivities()
  appStore.showMessage('活动记录已刷新')
}

// 页面加载时初始化数据
onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadRecentActivities()
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

.main-section {
  margin-bottom: 24px;
}

.upload-buttons,
.generate-buttons {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.upload-btn,
.generate-btn {
  flex: 1;
}

.activity-content {
  strong {
    color: var(--el-text-color-primary);
    font-size: 14px;
  }
  
  p {
    margin: 4px 0 0 0;
    color: var(--el-text-color-regular);
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .upload-buttons,
  .generate-buttons {
    flex-direction: column;
  }
}
</style> 