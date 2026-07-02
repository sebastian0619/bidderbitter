import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 文件 API
export const fileApi = {
  upload(file, category, description, saveToManager = true) {
    const formData = new FormData()
    formData.append('file', file)
    if (category) formData.append('category', category)
    if (description) formData.append('description', description)
    formData.append('save_to_manager', saveToManager)
    return api.post('/files', formData)
  },
  
  list(params) {
    return api.get('/files', { params })
  },
  
  get(id) {
    return api.get(`/files/${id}`)
  },
  
  update(id, data) {
    return api.put(`/files/${id}`, data)
  },
  
  delete(id) {
    return api.delete(`/files/${id}`)
  },
  
  download(id) {
    return api.get(`/files/${id}/download`, { responseType: 'blob' })
  },
  
  addTags(fileId, tagIds) {
    return api.post(`/files/${fileId}/tags`, tagIds)
  },
  
  removeTag(fileId, tagId) {
    return api.delete(`/files/${fileId}/tags/${tagId}`)
  }
}

// 标签 API
export const tagApi = {
  list() {
    return api.get('/tags')
  },
  
  create(name, color, category) {
    return api.post('/tags', null, { params: { name, color, category } })
  },
  
  update(id, data) {
    return api.put(`/tags/${id}`, null, { params: data })
  },
  
  delete(id) {
    return api.delete(`/tags/${id}`)
  }
}

// PDF API
export const pdfApi = {
  merge(fileIds, outputName) {
    return api.post('/pdf/merge', { files: file_ids, output_name: outputName })
  },
  
  extractImages(fileId) {
    return api.post('/pdf/extract-images', null, { params: { file_id: fileId } })
  },
  
  imagesToPdf(fileIds, outputName) {
    return api.post('/image/to-pdf', { file_ids: fileIds, output_name: outputName })
  }
}

// 项目 API
export const projectApi = {
  list(params) {
    return api.get('/projects', { params })
  },
  
  create(data) {
    return api.post('/projects', null, { params: data })
  },
  
  get(id) {
    return api.get(`/projects/${id}`)
  },
  
  update(id, data) {
    return api.put(`/projects/${id}`, null, { params: data })
  },
  
  delete(id) {
    return api.delete(`/projects/${id}`)
  },
  
  addFiles(projectId, fileIds) {
    return api.post(`/projects/${projectId}/files`, fileIds)
  },
  
  removeFile(projectId, fileId) {
    return api.delete(`/projects/${projectId}/files/${fileId}`)
  },
  
  // 章节管理
  getSections(projectId) {
    return api.get(`/projects/${projectId}/sections`)
  },
  
  addSection(projectId, title, sectionType, description) {
    return api.post(`/projects/${projectId}/sections`, null, { 
      params: { title, section_type: sectionType, description } 
    })
  },
  
  updateSection(projectId, sectionId, title) {
    return api.put(`/projects/${projectId}/sections/${sectionId}`, null, { 
      params: { title } 
    })
  },
  
  deleteSection(projectId, sectionId) {
    return api.delete(`/projects/${projectId}/sections/${sectionId}`)
  },
  
  // 生成投标文档
  generate(projectId) {
    return api.post(`/projects/${projectId}/generate`)
  }
}

// Agent API
export const agentApi = {
  classifyFile(fileId) {
    return api.post(`/files/${fileId}/classify`)
  },
  
  batchClassify(fileIds) {
    return api.post('/files/batch-classify', fileIds)
  }
}

export default api
