import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios';
import { message } from 'ant-design-vue';
import router from '@/router';

// 创建 axios 实例
const http: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
http.interceptors.request.use(
  (config) => {
    // 添加认证 token
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
http.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response;
    
    // 如果返回的数据表示成功，直接返回数据
    if (data.success || data.code === 200 || response.status === 200) {
      return response.data;
    }
    
    // 处理业务错误
    const errorMessage = data.message || '请求失败';
    message.error(errorMessage);
    return Promise.reject(new Error(errorMessage));
  },
  (error) => {
    // 处理 HTTP 错误
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          message.error('登录已过期，请重新登录');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          router.push('/login');
          break;
        case 403:
          message.error('没有权限访问该资源');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器内部错误');
          break;
        default:
          const errorMessage = data?.message || error.message || '网络错误';
          message.error(errorMessage);
      }
    } else if (error.request) {
      message.error('网络连接失败，请检查网络设置');
    } else {
      message.error('请求配置错误');
    }
    
    return Promise.reject(error);
  }
);

export { http };

// 封装常用的请求方法
export const request = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return http.get(url, config);
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return http.post(url, data, config);
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return http.put(url, data, config);
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return http.delete(url, config);
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return http.patch(url, data, config);
  }
};
