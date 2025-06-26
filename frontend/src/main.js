import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 全局样式
import './styles/index.scss'

console.log('Vue main.js loaded')

// 动态设置网页标题、副标题和favicon
async function setAppInfo() {
  try {
    const res = await fetch('/api/app-info');
    if (res.ok) {
      const info = await res.json();
      document.title = `${info.app_name || '投标苦'} - ${info.subtitle || '法律人的投标自救工具'}`;
      setFavicon(info.favicon || '/favicon.ico');
      window.__APP_NAME__ = info.app_name || '投标苦';
      window.__APP_SUBTITLE__ = info.subtitle || '法律人的投标自救工具';
    }
  } catch (e) {
    document.title = '投标苦 - 法律人的投标自救工具';
    setFavicon('/favicon.ico');
    window.__APP_NAME__ = '投标苦';
    window.__APP_SUBTITLE__ = '法律人的投标自救工具';
  }
}
function setFavicon(url) {
  let link = document.querySelector("link[rel~='icon']");
  if (!link) {
    link = document.createElement('link');
    link.rel = 'icon';
    document.head.appendChild(link);
  }
  link.href = url;
}
setAppInfo();

const app = createApp(App)

// 安装插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局配置
app.config.globalProperties.$ELEMENT = {
  size: 'default',
  zIndex: 3000
}

console.log('About to mount Vue app')
app.mount('#app')
console.log('Vue app mounted successfully') 