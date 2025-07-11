// api/auth.ts
import api from './client';
import type { User, LoginForm, RegisterForm, ApiResponse } from '../types';

export const authApi = {
  // 登录
  login: async (loginForm: LoginForm): Promise<{ data: { access_token: string; user: User } }> => {
    const response = await api.post('/auth/login', loginForm);
    return { data: response.data };
  },

  // 注册
  register: async (registerForm: Omit<RegisterForm, 'confirmPassword'>): Promise<{ data: { access_token: string; user: User } }> => {
    const response = await api.post('/auth/register', registerForm);
    return { data: response.data };
  },

  // 获取用户信息
  getProfile: async (): Promise<ApiResponse<User>> => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  // 刷新token
  refreshToken: async (): Promise<ApiResponse<{ token: string }>> => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  // 登出
  logout: async (): Promise<ApiResponse<{}>> => {
    const response = await api.post('/auth/logout');
    return response.data;
  }
};
