// api/client.ts
import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig } from 'axios';
import { ElMessage } from 'element-plus';

// 创建 axios 实例
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.VITE_APP_ENV === 'production' ? '/api' : 'http://localhost:8000/api'),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API 响应错误:', error.config?.url, error.response?.status, error.response?.data);
    
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          // 清除token并跳转到登录页
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          ElMessage.error('认证失效，请重新登录');
          break;
        case 403:
          ElMessage.error('没有权限访问该资源');
          break;
        case 404:
          ElMessage.error('请求的资源不存在');
          break;
        case 500:
          ElMessage.error('服务器内部错误');
          break;
        default:
          ElMessage.error(data?.message || data?.error || '请求失败');
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络设置');
    } else {
      ElMessage.error('请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

export default api;
