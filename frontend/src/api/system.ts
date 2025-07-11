// api/system.ts
import HttpUtil from '../utils/http';
import type { ApiResponse } from '../types';

export const systemApi = {
  // 系统健康检查
  healthCheck: async (): Promise<ApiResponse<{ status: string; timestamp: string }>> => {
    return HttpUtil.get('/health');
  },

  // 获取系统信息
  getSystemInfo: async (): Promise<ApiResponse<any>> => {
    return HttpUtil.get('/system/info');
  },

  // 获取系统状态
  getSystemStatus: async (): Promise<ApiResponse<any>> => {
    return HttpUtil.get('/system/status');
  },

  // 获取API版本信息
  getVersion: async (): Promise<ApiResponse<{ version: string; build: string }>> => {
    return HttpUtil.get('/version');
  },

  // 获取服务器时间
  getServerTime: async (): Promise<ApiResponse<{ timestamp: string; timezone: string }>> => {
    return HttpUtil.get('/time');
  }
};
