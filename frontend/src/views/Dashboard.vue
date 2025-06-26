<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">数据管理</h1>
    <p class="text-gray-600 mb-6">这里展示了所有已录入的奖项和业绩数据。</p>

    <!-- 奖项数据 -->
    <div class="mb-8">
      <div class="flex justify-between items-center mb-3">
        <h2 class="text-xl font-semibold">奖项数据</h2>
        <router-link
          to="/awards/new"
          class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
        >
          新增奖项
        </router-link>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <table class="min-w-full">
          <thead>
            <tr>
              <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">奖项名称</th>
              <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">评选品牌</th>
              <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">业务类型</th>
              <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">年份</th>
              <th class="px-6 py-3 border-b-2 border-gray-300 text-left text-xs leading-4 font-medium text-gray-500 uppercase tracking-wider">已核实</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in awards" :key="item.id">
              <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.title }}</td>
              <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.brand }}</td>
              <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.business_type }}</td>
              <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">{{ item.year }}</td>
              <td class="px-6 py-4 whitespace-no-wrap border-b border-gray-200">
                <span :class="item.is_verified ? 'text-green-600' : 'text-red-600'">{{ item.is_verified ? '是' : '否' }}</span>
              </td>
            </tr>
            <tr v-if="awardsLoading">
              <td colspan="5" class="text-center py-4">加载中...</td>
            </tr>
            <tr v-if="!awardsLoading && awards.length === 0">
              <td colspan="5" class="text-center py-4">没有奖项数据。</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const awards = ref([])
const awardsLoading = ref(true)

const fetchAwards = async () => {
  awardsLoading.value = true
  try {
    const response = await api.get('/awards')
    if (response.data.success) {
      awards.value = response.data.awards
    } else {
      console.error('获取奖项数据失败:', response.data.message)
    }
  } catch (error) {
    console.error('请求奖项数据出错:', error)
  } finally {
    awardsLoading.value = false
  }
}

onMounted(() => {
  fetchAwards()
})
</script>