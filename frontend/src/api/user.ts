import { http } from './http';
import type { User, ApiResponse } from '@/types';

export const userApi = {
  // 用户登录
  login: (username: string, password: string): Promise<{
    access_token: string;
    refresh_token: string;
    user: User;
  }> => {
    return http.post('/api/auth/login', {
      username,
      password
    });
  },

  // 用户注册
  register: (data: {
    username: string;
    password: string;
    email: string;
    phone?: string;
    full_name?: string;
  }): Promise<ApiResponse<User>> => {
    console.log('发送注册请求:', data);
    return http.post('/api/auth/register', data);
  },

  // 获取当前用户信息
  getCurrentUser: (): Promise<ApiResponse<User>> => {
    return http.get('/api/auth/profile');
  },

  // 更新用户信息
  updateUser: (data: Partial<User>): Promise<ApiResponse<User>> => {
    return http.put('/api/auth/profile', data);
  },

  // 用户登出
  logout: (): Promise<ApiResponse<void>> => {
    return http.post('/api/auth/logout');
  },

  // 获取用户统计信息（模拟数据，因为后端暂无此接口）
  getUserStats: (): Promise<ApiResponse<{
    loginCount: number;
    lastLoginTime: string;
    deviceCount: number;
    alertCount: number;
  }>> => {
    // 返回模拟数据
    return Promise.resolve({
      success: true,
      data: {
        loginCount: 42,
        lastLoginTime: new Date().toISOString(),
        deviceCount: 8,
        alertCount: 3
      }
    });
  },

  // 获取登录历史（模拟数据，因为后端暂无此接口）
  getLoginHistory: (): Promise<ApiResponse<Array<{
    id: number;
    loginTime: string;
    ip: string;
    userAgent: string;
    location: string;
  }>>> => {
    // 返回模拟数据
    return Promise.resolve({
      success: true,
      data: [
        {
          id: 1,
          loginTime: new Date().toISOString(),
          ip: '192.168.1.100',
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
          location: '本地网络'
        },
        {
          id: 2,
          loginTime: new Date(Date.now() - 86400000).toISOString(),
          ip: '192.168.1.100',
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
          location: '本地网络'
        }
      ]
    });
  },

  // 获取用户活动记录（模拟数据，因为后端暂无此接口）
  getUserActivities: (): Promise<ApiResponse<Array<{
    id: number;
    action: string;
    timestamp: string;
    details: string;
  }>>> => {
    // 返回模拟数据
    return Promise.resolve({
      success: true,
      data: [
        {
          id: 1,
          action: '登录系统',
          timestamp: new Date().toISOString(),
          details: '用户成功登录系统'
        },
        {
          id: 2,
          action: '查看设备',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          details: '查看设备列表'
        },
        {
          id: 3,
          action: '处理告警',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          details: '处理温度超限告警'
        }
      ]
    });
  }
};
