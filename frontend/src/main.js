import { createApp } from 'vue'

const app = createApp({
  template: `
    <div style="padding: 20px; text-align: center;">
      <h1>投标文件制作系统</h1>
      <p>系统正在初始化中...</p>
      <div style="margin: 20px 0;">
        <button @click="testApi" style="padding: 10px 20px; margin: 5px;">测试API连接</button>
      </div>
      <div v-if="apiResult" style="margin-top: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;">
        <h3>API测试结果：</h3>
        <pre>{{ apiResult }}</pre>
      </div>
    </div>
  `,
  data() {
    return {
      apiResult: null
    }
  },
  methods: {
    async testApi() {
      try {
        const response = await fetch('/api/health')
        const data = await response.json()
        this.apiResult = JSON.stringify(data, null, 2)
      } catch (error) {
        this.apiResult = '错误: ' + error.message
      }
    }
  }
})

app.mount('#app') 