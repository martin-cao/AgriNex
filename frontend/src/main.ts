import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import pinia from './stores';
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import * as antIcons from '@ant-design/icons-vue';
import { useAuthStore } from './stores/auth';
import './assets/styles/global.less';

// 创建应用实例
const app = createApp(App);

// 注册 Ant Design Vue 图标
Object.keys(antIcons).forEach(key => {
  app.component(key, antIcons[key as keyof typeof antIcons]);
});

// 使用插件
app.use(pinia);
app.use(router);
app.use(Antd);

// 初始化认证状态
const authStore = useAuthStore();
authStore.initializeAuth();

// 挂载应用
app.mount('#app');
