<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">创建新奖项</h1>
    <div class="bg-white shadow rounded-lg p-6">
      <form @submit.prevent="submitForm">
        <!-- 奖项标题 -->
        <div class="mb-4">
          <label for="title" class="block text-gray-700 font-bold mb-2">奖项标题</label>
          <input
            type="text"
            id="title"
            v-model="form.title"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          />
        </div>

        <!-- 评选品牌 -->
        <div class="mb-4">
          <label for="brand" class="block text-gray-700 font-bold mb-2">评选品牌</label>
          <select
            id="brand"
            v-model="form.brand"
            class="shadow bg-white border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          >
            <option disabled value="">请选择一个品牌</option>
            <option v-for="brand in brands" :key="brand.name" :value="brand.name">
              {{ brand.name }}
            </option>
          </select>
        </div>

        <!-- 业务类型 -->
        <div class="mb-4">
          <label for="business_type" class="block text-gray-700 font-bold mb-2">业务类型</label>
          <select
            id="business_type"
            v-model="form.business_type"
            class="shadow bg-white border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            required
          >
            <option disabled value="">请选择一个业务类型</option>
            <option v-for="field in businessFields" :key="field.name" :value="field.name">
              {{ field.name }}
            </option>
          </select>
        </div>

        <!-- 年份 -->
        <div class="mb-6">
          <label for="year" class="block text-gray-700 font-bold mb-2">年份</label>
          <input
            type="number"
            id="year"
            v-model="form.year"
            class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
            placeholder="例如: 2023"
            required
          />
        </div>

        <!-- 提交按钮 -->
        <div class="flex items-center justify-end">
          <button
            type="submit"
            :disabled="submitting"
            class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
          >
            {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

const router = useRouter();

const form = reactive({
  title: '',
  brand: '',
  business_type: '',
  year: new Date().getFullYear(),
});

const brands = ref([]);
const businessFields = ref([]);
const submitting = ref(false);

const fetchOptions = async () => {
  try {
    const [brandsRes, fieldsRes] = await Promise.all([
      api.get('/config/brands'),
      api.get('/config/business-fields'),
    ]);
    if (brandsRes.data.success) {
      brands.value = brandsRes.data.brands;
    }
    if (fieldsRes.data.success) {
      businessFields.value = fieldsRes.data.business_fields;
    }
  } catch (error) {
    console.error('获取配置选项失败:', error);
    // 在这里可以添加用户提示
  }
};

const submitForm = async () => {
  submitting.value = true;
  try {
    const response = await api.post('/awards', form);
    if (response.data.success) {
      // 可以在这里添加成功提示
      router.push('/dashboard'); // 成功后返回数据管理页面
    } else {
      console.error('创建奖项失败:', response.data.message);
      // 在这里可以添加用户提示
    }
  } catch (error) {
    console.error('提交奖项出错:', error);
    // 在这里可以添加用户提示
  } finally {
    submitting.value = false;
  }
};

onMounted(fetchOptions);
</script> 