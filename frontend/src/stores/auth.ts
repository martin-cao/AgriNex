// stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authApi } from '../api';
import type { User, LoginForm, RegisterForm } from '../types';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('token'));
  const isLoading = ref(false);

  const isAuthenticated = computed(() => {
    return !!token.value && !!user.value;
  });

  const login = async (loginForm: LoginForm) => {
    isLoading.value = true;
    try {
      const response = await authApi.login(loginForm);
      console.log('登录响应:', response);
      console.log('响应数据:', response.data);
      
      // 后端直接返回数据，不包装在ApiResponse中
      if (response.data && response.data.access_token) {
        token.value = response.data.access_token;
        user.value = response.data.user;
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        console.log('登录成功，token和用户信息已保存');
        console.log('设置的用户信息:', user.value);
        console.log('设置的token:', token.value);
        return response;
      }
      console.error('登录响应格式不正确:', response);
      throw new Error('登录失败：无效的响应格式');
    } catch (error) {
      console.error('登录失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const register = async (registerForm: Omit<RegisterForm, 'confirmPassword'>) => {
    isLoading.value = true;
    try {
      const response = await authApi.register(registerForm);
      // 后端直接返回数据，不包装在ApiResponse中
      if (response.data && response.data.access_token) {
        token.value = response.data.access_token;
        user.value = response.data.user;
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response;
      }
      throw new Error('注册失败：无效的响应格式');
    } catch (error) {
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // 忽略登出错误
    }
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const getProfile = async () => {
    if (!token.value) return;
    
    try {
      const response = await authApi.getProfile();
      if (response.success && response.data) {
        user.value = response.data;
        localStorage.setItem('user', JSON.stringify(response.data));
      }
    } catch (error) {
      // 如果获取用户信息失败，清除认证状态
      await logout();
    }
  };

  const initializeAuth = () => {
    const savedUser = localStorage.getItem('user');
    const savedToken = localStorage.getItem('token');
    
    if (savedUser && savedToken) {
      try {
        user.value = JSON.parse(savedUser);
        token.value = savedToken;
      } catch (error) {
        // 如果解析失败，清除本地存储
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
  };

  return {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    getProfile,
    initializeAuth
  };
});
