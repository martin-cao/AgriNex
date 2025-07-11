// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import type { RouteRecordRaw } from 'vue-router';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false, title: '登录' }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true, title: '仪表盘' }
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('../views/Devices.vue'),
    meta: { requiresAuth: true, title: '设备管理' }
  },
  {
    path: '/devices/:id',
    name: 'DeviceDetail',
    component: () => import('../views/DeviceDetail.vue'),
    meta: { requiresAuth: true, title: '设备详情' }
  },
  {
    path: '/sensors',
    name: 'SensorData',
    component: () => import('../views/SensorData.vue'),
    meta: { requiresAuth: true, title: '传感器数据' }
  },
  {
    path: '/sensors/:id',
    name: 'SensorDetail',
    component: () => import('../views/SensorDetail.vue'),
    meta: { requiresAuth: true, title: '传感器详情' }
  },
  {
    path: '/alarms',
    name: 'Alarms',
    component: () => import('../views/Alarms.vue'),
    meta: { requiresAuth: true, title: '告警管理' }
  },
  {
    path: '/predictions',
    name: 'Predictions',
    component: () => import('../views/Predictions.vue'),
    meta: { requiresAuth: true, title: '预测分析' }
  },
  {
    path: '/media',
    name: 'MediaGallery',
    component: () => import('../views/MediaGallery.vue'),
    meta: { requiresAuth: true, title: '媒体库' }
  },
  {
    path: '/chatbot',
    name: 'ChatBot',
    component: () => import('../views/ChatBot.vue'),
    meta: { requiresAuth: true, title: 'AI助手' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true, title: '个人资料' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { requiresAuth: true, title: '系统设置' }
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login');
    return;
  }
  
  // 如果已经登录，不允许访问登录页
  if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard');
    return;
  }
  
  next();
});

export default router;
