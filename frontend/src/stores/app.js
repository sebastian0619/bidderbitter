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
    
    try {
      setLoading(true, '正在初始化应用...')
      
      // 并行加载配置数据
      const [brandsResult, fieldsResult] = await Promise.all([
        apiService.getBrands(),
        apiService.getBusinessFields()
      ])
      
      if (brandsResult.success) {
        brands.value = brandsResult.brands
      }
      
      if (fieldsResult.success) {
        businessFields.value = fieldsResult.business_fields
      }
      
      initialized.value = true
      
    } catch (error) {
      console.error('应用初始化失败:', error)
      showMessage('应用初始化失败，请刷新页面重试', 'error')
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
      
      if (brandsResult.success) {
        brands.value = brandsResult.brands
      }
      
      if (fieldsResult.success) {
        businessFields.value = fieldsResult.business_fields
      }
      
      showMessage('配置数据已更新')
      
    } catch (error) {
      console.error('刷新配置失败:', error)
      showMessage('刷新配置失败', 'error')
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