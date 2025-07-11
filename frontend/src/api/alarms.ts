// api/alarms.ts
import api from './client';
import type { Alarm, ApiResponse } from '../types';

export const alarmsApi = {
  // 获取告警列表
  getAlarms: async (params?: { 
    status?: string; 
    limit?: number; 
    offset?: number; 
  }): Promise<ApiResponse<Alarm[]>> => {
    const response = await api.get('/alarms', { params });
    return response.data;
  },

  // 获取告警详情
  getAlarm: async (alarmId: number): Promise<ApiResponse<Alarm>> => {
    const response = await api.get(`/alarms/${alarmId}`);
    return response.data;
  },

  // 解决告警
  resolveAlarm: async (alarmId: number): Promise<ApiResponse<Alarm>> => {
    const response = await api.post(`/alarms/${alarmId}/resolve`);
    return response.data;
  },

  // 获取告警统计
  getAlarmStatistics: async (): Promise<ApiResponse<{
    total: number;
    active: number;
    resolved: number;
    critical: number;
    warning: number;
    info: number;
  }>> => {
    const response = await api.get('/alarms/statistics');
    return response.data;
  }
};
