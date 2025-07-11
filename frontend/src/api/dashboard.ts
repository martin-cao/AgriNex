// api/dashboard.ts
import api from './client';
import type { DashboardStats, ApiResponse } from '../types';

export const dashboardApi = {
  // 获取仪表板统计数据
  getDashboardStats: async (): Promise<ApiResponse<DashboardStats>> => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // 获取系统状态
  getSystemStatus: async (): Promise<ApiResponse<{
    database: boolean;
    mqtt: boolean;
    storage: boolean;
    prediction: boolean;
  }>> => {
    const response = await api.get('/status');
    return response.data;
  },

  // 获取健康检查
  getHealthCheck: async (): Promise<ApiResponse<{
    status: string;
    timestamp: string;
    uptime: number;
  }>> => {
    const response = await api.get('/health');
    return response.data;
  }
};
