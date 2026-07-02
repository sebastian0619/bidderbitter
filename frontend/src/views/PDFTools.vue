<template>
  <div class="pdf-tools">
    <div class="page-header">
      <div>
        <h1 class="page-title">PDF 工具</h1>
        <p class="page-subtitle">处理 PDF 和图片文件</p>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- PDF 合并 -->
      <el-col :span="12">
        <el-card class="tool-card" shadow="hover">
          <template #header>
            <div class="tool-header">
              <div class="tool-icon" style="background: var(--primary-50); color: var(--primary-600);">
                <el-icon :size="20"><DocumentCopy /></el-icon>
              </div>
              <div>
                <div class="tool-title">PDF 合并</div>
                <div class="tool-desc">将多个 PDF 文件合并为一个</div>
              </div>
            </div>
          </template>
          <div class="tool-content">
            <!-- 上传区域 -->
            <el-upload
              ref="mergeUploadRef"
              :auto-upload="false"
              :on-change="handleMergeFileChange"
              :file-list="mergeUploadedFiles"
              multiple
              accept=".pdf"
              drag
              class="upload-area"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽文件到此处或<em>点击上传</em></div>
              <div class="upload-hint">支持多个 PDF 文件</div>
            </el-upload>

            <!-- 存入文件管理选项 -->
            <el-checkbox v-model="mergeSaveToManager" class="save-checkbox">
              存入文件管理
            </el-checkbox>

            <!-- 或选择已有文件 -->
            <div class="divider-text">或选择已有文件</div>
            <el-select
              v-model="mergeFiles"
              multiple
              filterable
              placeholder="选择已有 PDF 文件"
              style="width: 100%;"
            >
              <el-option
                v-for="file in pdfFiles"
                :key="file.id"
                :label="file.filename"
                :value="file.id"
              />
            </el-select>

            <el-input
              v-model="mergeOutputName"
              placeholder="输出文件名"
              style="margin-top: 12px;"
            >
              <template #append>.pdf</template>
            </el-input>
            <el-button
              type="primary"
              style="margin-top: 16px; width: 100%;"
              :disabled="!canMerge"
              :loading="merging"
              @click="handleMerge"
            >
              <el-icon><DocumentCopy /></el-icon>
              合并文件
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 图片转 PDF -->
      <el-col :span="12">
        <el-card class="tool-card" shadow="hover">
          <template #header>
            <div class="tool-header">
              <div class="tool-icon" style="background: #ecfdf5; color: var(--success);">
                <el-icon :size="20"><Picture /></el-icon>
              </div>
              <div>
                <div class="tool-title">图片转 PDF</div>
                <div class="tool-desc">将多张图片合并为 PDF</div>
              </div>
            </div>
          </template>
          <div class="tool-content">
            <!-- 上传区域 -->
            <el-upload
              ref="imageUploadRef"
              :auto-upload="false"
              :on-change="handleImageFileChange"
              :file-list="imageUploadedFiles"
              multiple
              accept=".jpg,.jpeg,.png,.gif,.bmp"
              drag
              class="upload-area"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽图片到此处或<em>点击上传</em></div>
              <div class="upload-hint">支持 JPG、PNG、GIF、BMP</div>
            </el-upload>

            <!-- 存入文件管理选项 -->
            <el-checkbox v-model="imageSaveToManager" class="save-checkbox">
              存入文件管理
            </el-checkbox>

            <!-- 或选择已有文件 -->
            <div class="divider-text">或选择已有文件</div>
            <el-select
              v-model="imageFiles"
              multiple
              filterable
              placeholder="选择已有图片文件"
              style="width: 100%;"
            >
              <el-option
                v-for="file in imgFiles"
                :key="file.id"
                :label="file.filename"
                :value="file.id"
              />
            </el-select>

            <el-input
              v-model="imageOutputName"
              placeholder="输出文件名"
              style="margin-top: 12px;"
            >
              <template #append>.pdf</template>
            </el-input>
            <el-button
              type="success"
              style="margin-top: 16px; width: 100%;"
              :disabled="!canConvert"
              :loading="converting"
              @click="handleImagesToPdf"
            >
              <el-icon><Picture /></el-icon>
              转换为 PDF
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- PDF 图片提取 -->
    <el-card class="tool-card extract-card" shadow="hover" style="margin-top: 16px;">
      <template #header>
        <div class="tool-header">
          <div class="tool-icon" style="background: #f5f3ff; color: var(--info);">
            <el-icon :size="20"><Crop /></el-icon>
          </div>
          <div>
            <div class="tool-title">PDF 图片提取</div>
            <div class="tool-desc">从 PDF 文件中提取所有图片</div>
          </div>
        </div>
      </template>
      <div class="extract-content">
        <!-- 上传区域 -->
        <el-upload
          ref="extractUploadRef"
          :auto-upload="false"
          :on-change="handleExtractFileChange"
          :file-list="extractUploadedFiles"
          accept=".pdf"
          :limit="1"
          class="extract-upload"
        >
          <el-button type="primary" plain>
            <el-icon><Upload /></el-icon>
            上传 PDF
          </el-button>
        </el-upload>

        <span class="extract-or">或</span>

        <el-select
          v-model="extractFile"
          filterable
          placeholder="选择已有 PDF 文件"
          style="width: 300px;"
        >
          <el-option
            v-for="file in pdfFiles"
            :key="file.id"
            :label="file.filename"
            :value="file.id"
          />
        </el-select>

        <!-- 存入文件管理选项 -->
        <el-checkbox v-model="extractSaveToManager" class="save-checkbox">
          存入文件管理
        </el-checkbox>

        <el-button
          type="primary"
          :disabled="!canExtract"
          :loading="extracting"
          @click="handleExtract"
        >
          <el-icon><Crop /></el-icon>
          提取图片
        </el-button>
      </div>
      <div v-if="extractResult" class="extract-result">
        <el-alert
          :title="`成功提取 ${extractResult.extracted_count} 张图片`"
          type="success"
          show-icon
          :closable="false"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fileApi, pdfApi } from '../services/api'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Picture, Crop, UploadFilled, Upload } from '@element-plus/icons-vue'

const pdfFiles = ref([])
const imgFiles = ref([])

// PDF 合并
const mergeFiles = ref([])
const mergeUploadedFiles = ref([])
const mergeOutputName = ref('merged')
const mergeSaveToManager = ref(true)
const merging = ref(false)

// 图片转 PDF
const imageFiles = ref([])
const imageUploadedFiles = ref([])
const imageOutputName = ref('output')
const imageSaveToManager = ref(true)
const converting = ref(false)

// PDF 图片提取
const extractFile = ref(null)
const extractUploadedFiles = ref([])
const extractSaveToManager = ref(true)
const extractResult = ref(null)
const extracting = ref(false)

// 计算属性
const canMerge = computed(() => {
  return mergeFiles.value.length >= 2 || mergeUploadedFiles.value.length >= 2
})

const canConvert = computed(() => {
  return imageFiles.value.length > 0 || imageUploadedFiles.value.length > 0
})

const canExtract = computed(() => {
  return extractFile.value || extractUploadedFiles.value.length > 0
})

const loadFiles = async () => {
  try {
    const res = await fileApi.list({ page_size: 100 })
    const allFiles = res.data.files
    pdfFiles.value = allFiles.filter(f => f.file_type === 'pdf')
    imgFiles.value = allFiles.filter(f => f.file_type === 'image')
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  }
}

// 上传文件处理
const handleMergeFileChange = (file, fileList) => {
  mergeUploadedFiles.value = fileList
}

const handleImageFileChange = (file, fileList) => {
  imageUploadedFiles.value = fileList
}

const handleExtractFileChange = (file, fileList) => {
  extractUploadedFiles.value = fileList
}

// 上传文件到服务器
const uploadFiles = async (files, saveToManager) => {
  const uploadedIds = []
  for (const file of files) {
    try {
      const res = await fileApi.upload(file.raw, saveToManager ? 'uploaded' : 'temp', '', saveToManager)
      uploadedIds.push(res.data.id)
    } catch (error) {
      console.error('上传失败:', error)
    }
  }
  return uploadedIds
}

const handleMerge = async () => {
  merging.value = true
  try {
    let fileIds = [...mergeFiles.value]
    
    // 上传新文件
    if (mergeUploadedFiles.value.length > 0) {
      const uploadedIds = await uploadFiles(mergeUploadedFiles.value, mergeSaveToManager.value)
      fileIds = [...fileIds, ...uploadedIds]
    }
    
    await pdfApi.merge(fileIds, mergeOutputName.value + '.pdf')
    ElMessage.success('PDF 合并成功')
    mergeFiles.value = []
    mergeUploadedFiles.value = []
    loadFiles()
  } catch (error) {
    ElMessage.error('合并失败')
  } finally {
    merging.value = false
  }
}

const handleImagesToPdf = async () => {
  converting.value = true
  try {
    let fileIds = [...imageFiles.value]
    
    // 上传新文件
    if (imageUploadedFiles.value.length > 0) {
      const uploadedIds = await uploadFiles(imageUploadedFiles.value, imageSaveToManager.value)
      fileIds = [...fileIds, ...uploadedIds]
    }
    
    await pdfApi.imagesToPdf(fileIds, imageOutputName.value + '.pdf')
    ElMessage.success('转换成功')
    imageFiles.value = []
    imageUploadedFiles.value = []
    loadFiles()
  } catch (error) {
    ElMessage.error('转换失败')
  } finally {
    converting.value = false
  }
}

const handleExtract = async () => {
  extracting.value = true
  extractResult.value = null
  
  try {
    let fileId = extractFile.value
    
    // 上传新文件
    if (!fileId && extractUploadedFiles.value.length > 0) {
      const uploadedIds = await uploadFiles(extractUploadedFiles.value, extractSaveToManager.value)
      fileId = uploadedIds[0]
    }
    
    const res = await pdfApi.extractImages(fileId)
    extractResult.value = res.data
    ElMessage.success(`提取了 ${res.data.extracted_count} 张图片`)
  } catch (error) {
    ElMessage.error('提取失败')
  } finally {
    extracting.value = false
  }
}

onMounted(loadFiles)
</script>

<style scoped>
.pdf-tools {
  max-width: 1200px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--neutral-900);
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 14px;
  color: var(--neutral-500);
  margin-top: 4px;
}

.tool-card {
  transition: all 0.2s ease;
}

.tool-card:hover {
  transform: translateY(-1px);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--neutral-800);
}

.tool-desc {
  font-size: 12px;
  color: var(--neutral-500);
  margin-top: 2px;
}

.tool-content {
  display: flex;
  flex-direction: column;
}

.upload-area {
  margin-bottom: 12px;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 24px;
  border-radius: var(--radius-md);
}

.upload-icon {
  font-size: 48px;
  color: var(--neutral-300);
  margin-bottom: 8px;
}

.upload-text {
  font-size: 14px;
  color: var(--neutral-600);
}

.upload-text em {
  color: var(--primary-600);
  font-style: normal;
}

.upload-hint {
  font-size: 12px;
  color: var(--neutral-400);
  margin-top: 4px;
}

.save-checkbox {
  margin: 12px 0;
}

.divider-text {
  font-size: 12px;
  color: var(--neutral-400);
  text-align: center;
  margin: 12px 0;
  position: relative;
}

.divider-text::before,
.divider-text::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 40%;
  height: 1px;
  background: var(--neutral-200);
}

.divider-text::before {
  left: 0;
}

.divider-text::after {
  right: 0;
}

.extract-content {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.extract-upload {
  flex-shrink: 0;
}

.extract-or {
  font-size: 13px;
  color: var(--neutral-400);
}

.extract-result {
  margin-top: 16px;
}
</style>
