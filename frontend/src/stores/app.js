import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { apiService } from '@/services/api'

export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const loadingText = ref('正在处理...')
  const brands = ref([])
  const businessFields = ref([])
  const initialized = ref(false)

  // 默认数据
  const defaultBrands = [
    { name: 'Chambers', full_name: 'Chambers and Partners' },
    { name: 'Legal500', full_name: 'The Legal 500' },
    { name: 'IFLR1000', full_name: 'IFLR1000' },
    { name: 'ALB', full_name: 'Asian Legal Business' },
    { name: 'LegalBand', full_name: 'Legal Band' }
  ]

  const defaultBusinessFields = [
    { name: '银行与金融' },
    { name: '公司法律服务' },
    { name: '并购重组' },
    { name: '资本市场' },
    { name: '争议解决' },
    { name: '知识产权' },
    { name: '国际贸易' },
    { name: '房地产建设' },
    { name: '劳动法' },
    { name: '税务法' }
  ]

  // 计算属性
  const brandOptions = computed(() => 
    brands.value.map(brand => ({
      label: brand.full_name || brand.name,
      value: brand.name
    }))
  )

  const businessFieldOptions = computed(() => 
    businessFields.value.map(field => ({
      label: field.name,
      value: field.name
    }))
  )

  // 方法
  const setLoading = (isLoading, text = '正在处理...') => {
    loading.value = isLoading
    loadingText.value = text
  }

  const showMessage = (message, type = 'success') => {
    ElMessage({
      message,
      type,
      duration: 3000
    })
  }

  const showNotification = (title, message, type = 'success') => {
    ElNotification({
      title,
      message,
      type,
      duration: 4000
    })
  }

  const initApp = async () => {
    if (initialized.value) return
    
    console.log('开始初始化应用...')
    
    try {
      setLoading(true, '正在初始化应用...')
      
      // 设置较短的超时时间用于初始化
      const initTimeout = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('初始化超时')), 5000)
      )
      
      try {
        // 并行加载配置数据，但有超时保护
        const apiPromise = Promise.all([
          apiService.getBrands(),
          apiService.getBusinessFields()
        ])
        
        const [brandsResult, fieldsResult] = await Promise.race([
          apiPromise,
          initTimeout
        ])
        
        console.log('API数据加载成功')
        
        if (brandsResult && brandsResult.brands) {
          brands.value = brandsResult.brands
        } else {
          brands.value = defaultBrands
        }
        
        if (fieldsResult && fieldsResult.business_fields) {
          businessFields.value = fieldsResult.business_fields
        } else {
          businessFields.value = defaultBusinessFields
        }
        
      } catch (apiError) {
        console.warn('API数据加载失败，使用默认数据:', apiError.message)
        
        // 使用默认数据
        brands.value = defaultBrands
        businessFields.value = defaultBusinessFields
        
        // 只在开发模式下显示警告
        if (process.env.NODE_ENV === 'development') {
          showMessage('后端服务未连接，使用默认数据', 'warning')
        }
      }
      
      initialized.value = true
      console.log('应用初始化完成')
      
    } catch (error) {
      console.error('应用初始化失败:', error)
      
      // 即使出错也要设置默认数据并标记为已初始化
      brands.value = defaultBrands
      businessFields.value = defaultBusinessFields
      initialized.value = true
      
      showMessage('应用启动完成（离线模式）', 'info')
    } finally {
      setLoading(false)
    }
  }

  const refreshConfig = async () => {
    try {
      const [brandsResult, fieldsResult] = await Promise.all([
        apiService.getBrands(),
        apiService.getBusinessFields()
      ])
      
      if (brandsResult && brandsResult.brands) {
        brands.value = brandsResult.brands
      }
      
      if (fieldsResult && fieldsResult.business_fields) {
        businessFields.value = fieldsResult.business_fields
      }
      
      showMessage('配置数据已更新')
      
    } catch (error) {
      console.error('刷新配置失败:', error)
      showMessage('刷新配置失败，请检查网络连接', 'error')
    }
  }

  return {
    // 状态
    loading,
    loadingText,
    brands,
    businessFields,
    initialized,
    
    // 计算属性
    brandOptions,
    businessFieldOptions,
    
    // 方法
    setLoading,
    showMessage,
    showNotification,
    initApp,
    refreshConfig
  }
}) 