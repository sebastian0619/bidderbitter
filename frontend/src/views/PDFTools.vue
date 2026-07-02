<template>
  <div class="pdf-tools">
    <el-row :gutter="20">
      <!-- PDF 合并 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>PDF 合并</span>
              <el-icon><Document /></el-icon>
            </div>
          </template>
          <div class="tool-content">
            <p>选择多个 PDF 文件合并为一个</p>
            <el-select
              v-model="mergeFiles"
              multiple
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
              style="margin-top: 10px;"
            />
            <el-button
              type="primary"
              style="margin-top: 10px; width: 100%;"
              :disabled="mergeFiles.length < 2"
              @click="handleMerge"
            >
              合并 PDF
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 图片转 PDF -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>图片转 PDF</span>
              <el-icon><Picture /></el-icon>
            </div>
          </template>
          <div class="tool-content">
            <p>选择多张图片合并为 PDF</p>
            <el-select
              v-model="imageFiles"
              multiple
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
              style="margin-top: 10px;"
            />
            <el-button
              type="primary"
              style="margin-top: 10px; width: 100%;"
              :disabled="imageFiles.length === 0"
              @click="handleImagesToPdf"
            >
              转换为 PDF
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- PDF 图片提取 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>PDF 图片提取</span>
          <el-icon><Picture /></el-icon>
        </div>
      </template>
      <div class="tool-content">
        <p>从 PDF 文件中提取所有图片</p>
        <el-select
          v-model="extractFile"
          placeholder="选择 PDF 文件"
          style="width: 300px;"
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
          style="margin-left: 10px;"
          :disabled="!extractFile"
          @click="handleExtract"
        >
          提取图片
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fileApi, pdfApi } from '../services/api'
import { ElMessage } from 'element-plus'
import { Document, Picture } from '@element-plus/icons-vue'

const pdfFiles = ref([])
const imgFiles = ref([])
const mergeFiles = ref([])
const mergeOutputName = ref('merged.pdf')
const imageFiles = ref([])
const imageOutputName = ref('output.pdf')
const extractFile = ref(null)

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
  try {
    await pdfApi.merge(mergeFiles.value, mergeOutputName.value)
    ElMessage.success('PDF 合并成功')
    loadFiles()
  } catch (error) {
    ElMessage.error('合并失败')
  }
}

const handleImagesToPdf = async () => {
  try {
    await pdfApi.imagesToPdf(imageFiles.value, imageOutputName.value)
    ElMessage.success('转换成功')
    loadFiles()
  } catch (error) {
    ElMessage.error('转换失败')
  }
}

const handleExtract = async () => {
  try {
    const res = await pdfApi.extractImages(extractFile.value)
    ElMessage.success(`提取了 ${res.data.extracted_count} 张图片`)
  } catch (error) {
    ElMessage.error('提取失败')
  }
}

onMounted(loadFiles)
</script>

<style scoped>
.pdf-tools {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tool-content {
  display: flex;
  flex-direction: column;
}

.tool-content p {
  color: #666;
  margin-bottom: 15px;
}
</style>
