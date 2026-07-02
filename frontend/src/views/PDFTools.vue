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
            <el-select
              v-model="mergeFiles"
              multiple
              filterable
              placeholder="选择 PDF 文件"
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
              :disabled="mergeFiles.length < 2"
              :loading="merging"
              @click="handleMerge"
            >
              <el-icon><DocumentCopy /></el-icon>
              合并 {{ mergeFiles.length }} 个文件
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
            <el-select
              v-model="imageFiles"
              multiple
              filterable
              placeholder="选择图片文件"
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
              :disabled="imageFiles.length === 0"
              :loading="converting"
              @click="handleImagesToPdf"
            >
              <el-icon><Picture /></el-icon>
              转换 {{ imageFiles.length }} 张图片
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
        <el-select
          v-model="extractFile"
          filterable
          placeholder="选择 PDF 文件"
          style="width: 400px;"
        >
          <el-option
            v-for="file in pdfFiles"
            :key="file.id"
            :label="file.filename"
            :value="file.id"
          />
        </el-select>
        <el-button
          type="primary"
          :disabled="!extractFile"
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
import { ref, onMounted } from 'vue'
import { fileApi, pdfApi } from '../services/api'
import { ElMessage } from 'element-plus'
import { DocumentCopy, Picture, Crop } from '@element-plus/icons-vue'

const pdfFiles = ref([])
const imgFiles = ref([])
const mergeFiles = ref([])
const mergeOutputName = ref('merged')
const imageFiles = ref([])
const imageOutputName = ref('output')
const extractFile = ref(null)
const extractResult = ref(null)
const merging = ref(false)
const converting = ref(false)
const extracting = ref(false)

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

const handleMerge = async () => {
  merging.value = true
  try {
    await pdfApi.merge(mergeFiles.value, mergeOutputName.value + '.pdf')
    ElMessage.success('PDF 合并成功')
    mergeFiles.value = []
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
    await pdfApi.imagesToPdf(imageFiles.value, imageOutputName.value + '.pdf')
    ElMessage.success('转换成功')
    imageFiles.value = []
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
    const res = await pdfApi.extractImages(extractFile.value)
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

.extract-content {
  display: flex;
  gap: 12px;
  align-items: center;
}

.extract-result {
  margin-top: 16px;
}
</style>
