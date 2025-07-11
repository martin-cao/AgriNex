import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import pinia from './stores';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import { useAuthStore } from './stores/auth';

// 创建应用实例
const app = createApp(App);

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// 使用插件
app.use(pinia);
app.use(router);
app.use(ElementPlus);

// 初始化认证状态
const authStore = useAuthStore();
authStore.initializeAuth();

// 挂载应用
app.mount('#app');
