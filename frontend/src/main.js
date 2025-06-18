import { createApp, h } from 'vue'

console.log('Vue main.js loaded')

const app = createApp({
  render() {
    return h('div', { style: 'padding: 20px; text-align: center; color: red; font-size: 24px;' }, [
      h('h1', 'Vue应用正常工作!'),
      h('p', '这是使用渲染函数创建的内容'),
      h('button', { 
        onClick: () => alert('按钮点击成功!'),
        style: 'padding: 10px 20px; margin: 10px; font-size: 16px;'
      }, '点击测试')
    ])
  },
  mounted() {
    console.log('Vue app mounted successfully')
    document.title = 'Vue App Working!'
  }
})

console.log('About to mount Vue app')
app.mount('#app')
console.log('Vue app mount attempted') 