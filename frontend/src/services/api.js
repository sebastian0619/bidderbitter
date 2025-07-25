import axios from 'axios'
import { ElMessage } from 'element-plus'

// 修正baseURL配置 - 避免重复的/api路径
const baseURL = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api'

// 创建axios实例
const api = axios.create({
  baseURL,
  timeout: 0, // 移除超时限制，允许处理大文件
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 如果是文件上传，修改Content-Type
    if (config.data instanceof FormData) {
      config.headers['Content-Type'] = 'multipart/form-data'
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API请求错误:', error)
    
    let message = '请求失败'
    
    if (error.response) {
      // 服务器响应了错误状态码
      const status = error.response.status
      const data = error.response.data
      
      switch (status) {
        case 400:
          message = data.detail || '请求参数错误'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = data.detail || '服务器内部错误'
          break
        default:
          message = data.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      // 请求发出但没有收到响应
      message = '网络连接失败，请检查网络'
    } else {
      // 其他错误
      message = error.message || '未知错误'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API服务对象
export const apiService = {
  // ==================== 配置相关 ====================
  
  // 获取厂牌列表
  getBrands() {
    return api.get('/config/brands')
  },
  
  // 获取业务领域列表
  getBusinessFields() {
    return api.get('/config/business-fields')
  },
  
  // ==================== 文件上传 ====================
  
  // 上传文档
  uploadDocument(file, documentType) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', documentType)
    
    return api.post('/upload/document', formData)
  },
  
  // 处理网页截图
  processScreenshot(urls, awardId = null) {
    return api.post('/process/screenshot', {
      urls,
      award_id: awardId
    })
  },
  
  // ==================== 获奖管理 ====================
  
  // 获取获奖列表
  getAwards(params = {}) {
    return api.get('/awards', { params })
  },
  
  // 创建获奖记录
  createAward(data) {
    return api.post('/awards', data)
  },
  
  // 更新获奖记录
  updateAward(id, data) {
    return api.put(`/awards/${id}`, data)
  },
  
  // 删除获奖记录
  deleteAward(id) {
    return api.delete(`/awards/${id}`)
  },
  
  // ==================== 业绩管理 ====================
  
  // 获取业绩列表
  getPerformances(params = {}) {
    return api.get('/performances', { params })
  },
  
  // 创建业绩记录
  createPerformance(data) {
    return api.post('/performances', data)
  },
  
  // 更新业绩记录
  updatePerformance(id, data) {
    return api.put(`/performances/${id}`, data)
  },
  
  // 删除业绩记录
  deletePerformance(id) {
    return api.delete(`/performances/${id}`)
  },
  
  // ==================== 文档生成 ====================
  
  // 生成文档
  generateDocument(data) {
    return api.post('/generate/document', data)
  },
  
  // 下载文件
  downloadFile(filename) {
    return api.get(`/download/${filename}`, {
      responseType: 'blob'
    })
  },
  
  // ==================== 项目管理 ====================

  // 获取项目列表
  getProjects(params = {}) {
    return api.get('/projects', { params })
  },

  // 获取项目详情
  getProject(id) {
    return api.get(`/projects/${id}`)
  },

  // 创建项目
  createProject(data) {
    return api.post('/projects', data).then(response => {
      // 确保返回结构一致
      if (response && response.id) {
        return { success: true, data: response }
      }
      return response
    })
  },

  // 更新项目
  updateProject(id, data) {
    return api.put(`/projects/${id}`, data)
  },

  // 删除项目
  deleteProject(id) {
    return api.delete(`/projects/${id}`)
  },

  // ==================== 章节管理 ====================

  // 获取章节列表
  getSections(projectId) {
    return api.get(`/projects/${projectId}/sections`)
  },

  // 创建章节
  createSection(projectId, data) {
    return api.post(`/projects/${projectId}/sections`, data)
  },

  // 更新章节
  updateSection(sectionId, data) {
    return api.put(`/projects/sections/${sectionId}`, data)
  },

  // 删除章节
  deleteSection(sectionId) {
    return api.delete(`/projects/sections/${sectionId}`)
  },

  // 重新排序章节
  reorderSections(items) {
    return api.put('/projects/sections/reorder', { items })
  },

  // ==================== 文档管理 ====================

  // 获取章节文档列表
  getSectionDocuments(sectionId) {
    return api.get(`/projects/sections/${sectionId}/documents`)
  },

  // 上传章节文档
  uploadSectionDocument(sectionId, file, order = 0) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('order', order)
    
    return api.post(`/projects/sections/${sectionId}/documents`, formData)
  },

  // 删除文档
  deleteDocument(documentId) {
    return api.delete(`/projects/documents/${documentId}`)
  },

  // 重新排序文档
  reorderDocuments(items) {
    return api.put('/projects/documents/reorder', { items })
  },

  // 生成项目文档
  generateProjectDocument(projectId) {
    return api.post(`/projects/${projectId}/generate`)
  },

  // ==================== 投标文档管理 ====================

  // 分析招标文件
  analyzeTenderDocument(file, projectId = null) {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) {
      formData.append('project_id', projectId)
    }
    return api.post('/bid-documents/analyze-tender-document', formData)
  },

  // 获取投标文档模板
  getBidTemplates(templateType = null) {
    const params = templateType ? { template_type: templateType } : {}
    return api.get('/bid-documents/templates', { params })
  },

  // 生成投标文档
  generateBidDocument(generationConfig) {
    return api.post('/bid-documents/generate', generationConfig)
  },

  // 获取项目章节
  getProjectSections(projectId) {
    return api.get(`/bid-documents/projects/${projectId}/sections`)
  },

  // 创建投标章节
  createBidSection(projectId, sectionData) {
    return api.post(`/bid-documents/projects/${projectId}/sections`, sectionData)
  },

  // 预览投标文档
  previewBidDocument(projectId) {
    return api.get(`/bid-documents/projects/${projectId}/preview`)
  },

  // 下载投标文档
  downloadBidDocument(documentId) {
    return api.get(`/bid-documents/download/${documentId}`, {
      responseType: 'blob'
    })
  },

  // ==================== 模板管理 ====================

  // 获取模板列表
  getTemplates(params = {}) {
    return api.get('/templates', { params })
  },

  // 获取模板详情
  getTemplate(id) {
    return api.get(`/templates/${id}`)
  },

  // 上传模板
  uploadTemplate(data) {
    const formData = new FormData()
    Object.keys(data).forEach(key => {
      if (key === 'file') {
        formData.append('file', data[key])
      } else {
        formData.append(key, data[key])
      }
    })
    
    return api.post('/templates', formData)
  },

  // 分析模板
  analyzeTemplate(templateId) {
    return api.post(`/templates/${templateId}/analyze`)
  },

  // 获取模板字段
  getTemplateFields(templateId) {
    return api.get(`/templates/${templateId}/fields`)
  },

  // 应用模板
  applyTemplate(templateId, projectId, fieldValues, outputFilename = null) {
    return api.post('/templates/apply', {
      template_id: templateId,
      project_id: projectId,
      field_values: fieldValues,
      output_filename: outputFilename
    })
  },

  // 获取项目字段映射
  getProjectMappings(projectId) {
    return api.get(`/templates/projects/${projectId}/mappings`)
  },
  
  // ==================== 健康检查 ====================
  
  // 健康检查
  healthCheck() {
    return api.get('/health')
  },
  
  // 获取业绩统计
  getPerformanceStats() {
    return api.get('/stats/performances')
  },
  
  // 系统设置相关
  getSettings(category = null) {
    const params = category ? { category } : {}
    return api.get('/settings', { params })
  },
  
  updateSettings(settingsData) {
    return api.post('/settings', settingsData)
  },
  
  initDefaultSettings() {
    return api.post('/settings/init-defaults')
  },
  
  // 获取业绩统计
  getAwardStats() {
    return api.get('/stats/awards')
  },

  // 通用POST方法
  post(url, data, config) {
    return api.post(url, data, config)
  },
  // 通用GET方法
  get(url, config) {
    return api.get(url, config)
  },
  // 通用PUT方法
  put(url, data, config) {
    return api.put(url, data, config)
  },
  // 通用DELETE方法
  delete(url, config) {
    return api.delete(url, config)
  },

  // ==================== 文件管理 ====================
  
  // 获取文件列表
  getFiles(params = {}) {
    return api.get('/files/list', { params })
  },
  
  // 获取文件详情
  getFileInfo(fileId) {
    return api.get(`/files/${fileId}`)
  },
  
  // 更新文件信息
  updateFileInfo(fileId, data) {
    return api.put(`/files/${fileId}`, data)
  },
  
  // 删除文件
  deleteFile(fileId, force = false) {
    return api.delete(`/files/${fileId}`, { params: { force } })
  },
  
  // 下载文件
  downloadFileById(fileId) {
    return api.get(`/files/${fileId}/download`, { responseType: 'blob' })
  },
  
  // 上传常驻文件
  uploadPermanentFile(formData) {
    return api.post('/files/upload/permanent', formData)
  },
  
  // 上传临时文件
  uploadTemporaryFile(formData) {
    return api.post('/files/upload/temporary', formData)
  },
  
  // AI分析文档
  analyzeDocument(fileId, enableVision = true, forceReanalyze = false) {
    return api.post('/files/analyze-document', {
      file_id: fileId,
      enable_vision: enableVision,
      force_reanalyze: forceReanalyze
    })
  },
  
  // 批量分析文档
  batchAnalyzeDocuments(fileIds, enableVision = true, updateRecords = false) {
    return api.post('/files/batch-analyze', {
      file_ids: fileIds,
      enable_vision: enableVision,
      update_records: updateRecords
    })
  },
  
  // 获取文件分类建议
  getCategorySuggestions() {
    return api.get('/files/categories/suggestions')
  },
  
  // 获取文件统计信息
  getFileStats() {
    return api.get('/files/stats')
  },
}

// 文件上传辅助函数
export const uploadHelper = {
  // 检查文件类型
  checkFileType(file, allowedTypes) {
    const fileType = file.type
    const fileName = file.name.toLowerCase()
    
    // 检查MIME类型
    if (allowedTypes.some(type => fileType.includes(type))) {
      return true
    }
    
    // 检查文件扩展名
    const allowedExtensions = {
      'pdf': ['.pdf'],
      'word': ['.doc', '.docx'],
      'image': ['.jpg', '.jpeg', '.png', '.gif']
    }
    
    for (const [type, extensions] of Object.entries(allowedExtensions)) {
      if (allowedTypes.includes(type) && extensions.some(ext => fileName.endsWith(ext))) {
        return true
      }
    }
    
    return false
  },
  
  // 检查文件大小
  checkFileSize(file, maxSize = 50 * 1024 * 1024) { // 默认50MB
    return file.size <= maxSize
  },
  
  // 格式化文件大小
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}

// 导出默认实例
export default api 