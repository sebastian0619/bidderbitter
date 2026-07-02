import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 文件 API
export const fileApi = {
  upload(file, category, description) {
    const formData = new FormData()
    formData.append('file', file)
    if (category) formData.append('category', category)
    if (description) formData.append('description', description)
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

export default api
