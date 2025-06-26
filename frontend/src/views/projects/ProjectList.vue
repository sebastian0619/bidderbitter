<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">投标项目管理</h1>

    <div class="mb-4">
      <router-link
        to="/projects/new"
        class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
      >
        新增项目
      </router-link>
    </div>

    <div class="bg-white shadow rounded-lg p-4">
      <table class="min-w-full">
        <thead>
          <tr>
            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">项目名称</th>
            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">客户名称</th>
            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">业务领域</th>
            <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">年份</th>
            <th class="px-6 py-3 border-b-2 border-gray-300"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in performances" :key="item.id">
            <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.project_name }}</td>
            <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.client_name }}</td>
            <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.business_field }}</td>
            <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.year }}</td>
            <td class="px-6 py-4 whitespace-no-wrap text-right border-b border-gray-200 text-sm leading-5 font-medium">
              <router-link :to="{ name: 'ProjectDetail', params: { id: item.id } }" class="text-indigo-600 hover:text-indigo-900">查看</router-link>
            </td>
          </tr>
          <tr v-if="loading">
            <td colspan="5" class="text-center py-4">加载中...</td>
          </tr>
          <tr v-if="!loading && performances.length === 0">
            <td colspan="5" class="text-center py-4">没有项目数据。</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const performances = ref([])
const loading = ref(true)

const fetchPerformances = async () => {
  loading.value = true
  try {
    const response = await api.get('/performances')
    if (response.data.success) {
      performances.value = response.data.performances
    } else {
      console.error('获取业绩数据失败:', response.data.message)
    }
  } catch (error) {
    console.error('请求业绩数据出错:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchPerformances)
</script>