import { createApp } from 'vue'

console.log('Vue main.js loaded')

const app = createApp({
  template: '<h1>Vue应用正常工作!</h1>',
  mounted() {
    console.log('Vue app mounted successfully')
  }
})

console.log('About to mount Vue app')
app.mount('#app')
console.log('Vue app mount attempted') 