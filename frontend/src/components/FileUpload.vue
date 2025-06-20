<!-- 通用文件上传组件 -->
<template>
  <div class="file-upload-container">
    <div
      class="upload-area"
      :class="{ dragover: dragOver }"
      @click="handleClick"
      @dragover.prevent="handleDragOver"
      @dragenter.prevent="handleDragEnter"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <div class="upload-icon">
        <el-icon><UploadFilled /></el-icon>
      </div>
      <div class="upload-text">
        <span v-if="!uploading">点击上传或拖拽文件到此处</span>
        <span v-else>正在上传...</span>
      </div>
      <div class="upload-hint">
        支持的文件类型：{{ acceptText }}，最大文件大小：{{ maxSizeText }}
      </div>
    </div>
    
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      :multiple="multiple"
      style="display: none"
      @change="handleFileSelect"
    />
    
    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list">
      <div
        v-for="(file, index) in fileList"
        :key="index"
        class="file-item"
      >
        <el-icon class="file-icon">
          <Document v-if="isDocumentFile(file)" />
          <Picture v-else-if="isImageFile(file)" />
          <Files v-else />
        </el-icon>
        
        <div class="file-info">
          <div class="file-name">{{ file.name }}</div>
          <div class="file-size">{{ formatFileSize(file.size) }}</div>
          <el-progress
            v-if="file.uploading"
            :percentage="file.progress || 0"
            :show-text="false"
            size="small"
          />
        </div>
        
        <div class="file-actions">
          <el-button
            v-if="!file.uploading"
            type="danger"
            size="small"
            text
            @click="removeFile(index)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Picture, Files, Delete } from '@element-plus/icons-vue'
import { uploadHelper } from '@/services/api'

const props = defineProps({
  // 接受的文件类型
  accept: {
    type: String,
    default: '.pdf,.doc,.docx,.jpg,.jpeg,.png'
  },
  // 是否允许多文件上传
  multiple: {
    type: Boolean,
    default: false
  },
  // 最大文件大小（字节）
  maxSize: {
    type: Number,
    default: 50 * 1024 * 1024 // 50MB
  },
  // 允许的文件类型数组
  allowedTypes: {
    type: Array,
    default: () => ['pdf', 'word', 'image']
  }
})

const emit = defineEmits(['upload', 'remove', 'change'])

const fileInput = ref(null)
const dragOver = ref(false)
const uploading = ref(false)
const fileList = ref([])

// 计算属性
const acceptText = computed(() => {
  const types = []
  if (props.allowedTypes.includes('pdf')) types.push('PDF')
  if (props.allowedTypes.includes('word')) types.push('Word')
  if (props.allowedTypes.includes('image')) types.push('图片')
  return types.join('、')
})

const maxSizeText = computed(() => {
  return uploadHelper.formatFileSize(props.maxSize)
})

// 方法
const handleClick = () => {
  if (!uploading.value) {
    fileInput.value?.click()
  }
}

const handleDragOver = () => {
  dragOver.value = true
}

const handleDragEnter = () => {
  dragOver.value = true
}

const handleDragLeave = (e) => {
  if (!e.currentTarget.contains(e.relatedTarget)) {
    dragOver.value = false
  }
}

const handleDrop = (e) => {
  dragOver.value = false
  const files = Array.from(e.dataTransfer.files)
  handleFiles(files)
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  handleFiles(files)
  // 清空input
  e.target.value = ''
}

const handleFiles = (files) => {
  if (!props.multiple && files.length > 1) {
    ElMessage.warning('只能上传一个文件')
    return
  }
  
  const validFiles = []
  
  for (const file of files) {
    // 检查文件类型
    if (!uploadHelper.checkFileType(file, props.allowedTypes)) {
      ElMessage.error(`文件 ${file.name} 类型不支持`)
      continue
    }
    
    // 检查文件大小
    if (!uploadHelper.checkFileSize(file, props.maxSize)) {
      ElMessage.error(`文件 ${file.name} 大小超过限制`)
      continue
    }
    
    validFiles.push(file)
  }
  
  if (validFiles.length > 0) {
    if (!props.multiple) {
      fileList.value = []
    }
    
    validFiles.forEach(file => {
      fileList.value.push({
        ...file,
        uploading: false,
        progress: 0
      })
    })
    
    emit('change', fileList.value)
    emit('upload', validFiles)
  }
}

const removeFile = (index) => {
  fileList.value.splice(index, 1)
  emit('change', fileList.value)
  emit('remove', index)
}

const isDocumentFile = (file) => {
  return file.type?.includes('pdf') || file.type?.includes('word') || 
         file.name?.toLowerCase().endsWith('.pdf') ||
         file.name?.toLowerCase().endsWith('.doc') ||
         file.name?.toLowerCase().endsWith('.docx')
}

const isImageFile = (file) => {
  return file.type?.startsWith('image/') ||
         file.name?.toLowerCase().match(/\.(jpg|jpeg|png|gif)$/)
}

const formatFileSize = (bytes) => {
  return uploadHelper.formatFileSize(bytes)
}

// 暴露方法给父组件
const setUploading = (index, uploading, progress = 0) => {
  if (fileList.value[index]) {
    fileList.value[index].uploading = uploading
    fileList.value[index].progress = progress
  }
}

const clearFiles = () => {
  fileList.value = []
  emit('change', [])
}

defineExpose({
  setUploading,
  clearFiles,
  fileList
})
</script>

<style lang="scss" scoped>
.file-upload-container {
  .upload-area {
    border: 2px dashed var(--el-border-color);
    border-radius: 8px;
    padding: 40px 20px;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    
    &:hover {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-9);
    }
    
    &.dragover {
      border-color: var(--el-color-primary);
      background-color: var(--el-color-primary-light-8);
    }
  }
  
  .upload-icon {
    font-size: 48px;
    color: var(--el-text-color-placeholder);
    margin-bottom: 16px;
  }
  
  .upload-text {
    color: var(--el-text-color-regular);
    margin-bottom: 8px;
    font-size: 16px;
  }
  
  .upload-hint {
    color: var(--el-text-color-placeholder);
    font-size: 14px;
  }
  
  .file-list {
    margin-top: 16px;
  }
  
  .file-item {
    display: flex;
    align-items: center;
    padding: 12px;
    background: var(--el-fill-color-extra-light);
    border-radius: 6px;
    margin-bottom: 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .file-icon {
    margin-right: 12px;
    color: var(--el-color-primary);
    font-size: 20px;
  }
  
  .file-info {
    flex: 1;
  }
  
  .file-name {
    font-weight: 500;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
  }
  
  .file-size {
    font-size: 12px;
    color: var(--el-text-color-regular);
    margin-bottom: 4px;
  }
  
  .file-actions {
    display: flex;
    gap: 8px;
  }
}
</style> 