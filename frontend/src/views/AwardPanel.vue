<template>
  <div class="award-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <div class="header-left">
        <h2>
          <el-icon><Trophy /></el-icon>
          奖项管理
        </h2>
        <p>管理荣誉奖项，支持AI自动检索和手动浏览器操作</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showUploadDialog = true">
          <el-icon><Upload /></el-icon>
          上传奖项文件
        </el-button>
        <el-button type="success" @click="showBrowserDialog = true">
          <el-icon><Monitor /></el-icon>
          实时浏览器
        </el-button>
        <el-button type="warning" @click="showAutoSearchDialog = true">
          <el-icon><Search /></el-icon>
          AI自动检索
        </el-button>
        <el-button @click="refreshAwards">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索奖项名称、品牌、业务领域..."
          @input="searchAwards"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select 
          v-model="selectedBrand" 
          placeholder="选择品牌" 
          @change="searchAwards"
          clearable
        >
          <el-option 
            v-for="brand in brands" 
            :key="brand" 
            :label="brand" 
            :value="brand"
          />
        </el-select>
      </div>
    </div>

    <!-- 奖项列表 -->
    <div class="award-table-container">
      <el-table 
        :data="awards" 
        v-loading="awardsLoading" 
        class="award-table"
      >
        <el-table-column prop="title" label="奖项名称" min-width="250">
          <template #default="scope">
            <div class="award-info">
              <div class="award-title">{{ scope.row.title }}</div>
              <div class="award-meta">
                <el-tag size="small" type="primary">{{ scope.row.brand }}</el-tag>
                <span class="year">{{ scope.row.year }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="business_type" label="业务领域" width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.business_type" size="small" type="info">
              {{ scope.row.business_type }}
            </el-tag>
            <span v-else class="text-placeholder">未分类</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_verified" label="验证状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_verified ? 'success' : 'warning'" size="small">
              {{ scope.row.is_verified ? '已验证' : '待验证' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
              <el-button size="mini" circle @click="viewAward(scope.row)">
                <el-icon><View /></el-icon>
              </el-button>
              
              <el-button size="mini" type="primary" circle @click="editAward(scope.row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              
              <el-button size="mini" type="danger" circle @click="deleteAward(scope.row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传奖项文件" width="600px">
      <p>上传功能开发中...</p>
      <template #footer>
        <el-button @click="showUploadDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 浏览器对话框 -->
    <el-dialog v-model="showBrowserDialog" title="实时浏览器" width="90%">
      <div class="browser-container">
        <div class="browser-toolbar">
          <el-input 
            v-model="browserUrl" 
            placeholder="输入网址，如：https://chambers.com"
            class="url-input"
          >
            <template #prepend>
              <el-button @click="loadUrl" type="primary">访问</el-button>
            </template>
          </el-input>
          
          <el-button @click="takeScreenshot" type="success">截图</el-button>
          <el-button @click="saveToSystem" type="primary">录入系统</el-button>
        </div>
        <div class="browser-placeholder">
          <el-empty description="浏览器功能开发中" />
        </div>
      </div>
      <template #footer>
        <el-button @click="showBrowserDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- AI检索对话框 -->
    <el-dialog v-model="showAutoSearchDialog" title="AI自动检索" width="600px">
      <p>AI自动检索功能开发中...</p>
      <template #footer>
        <el-button @click="showAutoSearchDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Trophy, Upload, Monitor, Search, Refresh, View, Edit, Delete
} from '@element-plus/icons-vue'

// 响应式数据
const awards = ref([])
const awardsLoading = ref(false)
const brands = ref(['Chambers', 'Legal 500', 'IFLR1000', 'ALB', 'Best Lawyers'])

// 搜索筛选
const searchQuery = ref('')
const selectedBrand = ref('')

// 对话框状态
const showUploadDialog = ref(false)
const showBrowserDialog = ref(false)
const showAutoSearchDialog = ref(false)

// 浏览器相关
const browserUrl = ref('https://chambers.com')

// 方法
const refreshAwards = async () => {
  awardsLoading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    awards.value = [
      {
        id: 1,
        title: 'Chambers Asia-Pacific 2024 - Banking & Finance',
        brand: 'Chambers',
        business_type: '银行金融',
        year: 2024,
        is_verified: true
      },
      {
        id: 2,
        title: 'Legal 500 China 2023 - Corporate M&A',
        brand: 'Legal 500',
        business_type: '公司并购',
        year: 2023,
        is_verified: false
      }
    ]
  } catch (error) {
    ElMessage.error('获取奖项列表失败')
  } finally {
    awardsLoading.value = false
  }
}

const searchAwards = () => {
  console.log('搜索奖项:', searchQuery.value, selectedBrand.value)
}

const loadUrl = () => {
  ElMessage.info('浏览器功能开发中')
}

const takeScreenshot = () => {
  ElMessage.info('截图功能开发中')
}

const saveToSystem = () => {
  ElMessage.info('录入系统功能开发中')
}

const viewAward = (award) => {
  ElMessage.info(`查看奖项: ${award.title}`)
}

const editAward = (award) => {
  ElMessage.info(`编辑奖项: ${award.title}`)
}

const deleteAward = (award) => {
  ElMessage.info(`删除奖项: ${award.title}`)
}

// 组件挂载
onMounted(() => {
  refreshAwards()
})
</script>

<style lang="scss" scoped>
.award-panel {
  padding: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  
  .header-left h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 700;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 12px;
    
    .el-icon {
      font-size: 28px;
      color: #f59e0b;
    }
  }
  
  .header-left p {
    margin: 0;
    color: #64748b;
    font-size: 16px;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.search-section {
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  gap: 16px;
  align-items: center;
  
  .search-input {
    min-width: 320px;
  }
}

.award-table-container {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.award-info {
  .award-title {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 4px;
  }
  
  .award-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .year {
      color: #64748b;
      font-size: 13px;
    }
  }
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
  
  .el-button.is-circle {
    width: 28px;
    height: 28px;
    padding: 0;
  }
}

.browser-container {
  height: 60vh;
  display: flex;
  flex-direction: column;
}

.browser-toolbar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  align-items: center;
  
  .url-input {
    flex: 1;
  }
}

.browser-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.text-placeholder {
  color: #9ca3af;
  font-style: italic;
}
</style> 