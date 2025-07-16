import { http } from './http';
import type { Alarm, ApiResponse, PaginatedResponse } from '@/types';

export const alarmApi = {
  // 获取报警列表
  getAlarms: (params?: {
    page?: number;
    per_page?: number;
    status?: 'active' | 'resolved' | 'ignored';
    level?: 'low' | 'medium' | 'high' | 'critical';
    start_time?: string;
    end_time?: string;
    device_id?: string;
    sensor_id?: string;
  }): Promise<PaginatedResponse<Alarm>> => {
    return http.get('/api/alarms', { params });
  },

  // 获取报警详情
  getAlarm: (id: string): Promise<ApiResponse<Alarm>> => {
    return http.get(`/api/alarms/${id}`);
  },

  // 处理报警
  resolveAlarm: (id: string, note?: string): Promise<ApiResponse<void>> => {
    return http.post(`/api/alarms/${id}/resolve`, { note });
  },

  // 忽略报警
  ignoreAlarm: (id: string, note?: string): Promise<ApiResponse<void>> => {
    return http.post(`/api/alarms/${id}/ignore`, { note });
  },

  // 批量处理报警
  batchResolveAlarms: (alarmIds: string[], note?: string): Promise<ApiResponse<void>> => {
    return http.post('/api/alarms/batch/resolve', {
      alarm_ids: alarmIds,
      note
    });
  },

  // 获取报警统计
  getAlarmStats: (period?: '24h' | '7d' | '30d'): Promise<ApiResponse<{
    total: number;
    active: number;
    resolved: number;
    by_level: Record<string, number>;
    by_type: Record<string, number>;
    timeline: Array<{
      date: string;
      count: number;
    }>;
  }>> => {
    return http.get('/api/alarms/stats', {
      params: period ? { period } : undefined
    });
  },

  // 获取报警规则
  getAlarmRules: (): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    condition: string;
    level: string;
    enabled: boolean;
    description?: string;
  }>>> => {
    return http.get('/api/alarms/rules');
  },

  // 创建报警规则
  createAlarmRule: (data: {
    name: string;
    description?: string;
    sensor_id: number;
    rule_type: 'threshold' | 'change_rate' | 'pattern';
    condition: '>' | '<' | '>=' | '<=' | '==' | '!=';
    threshold_value: number;
    consecutive_count?: number;
    severity?: 'low' | 'medium' | 'high';
    is_active?: boolean;
    email_enabled?: boolean;
    webhook_enabled?: boolean;
    webhook_url?: string | null;
  }): Promise<ApiResponse<any>> => {
    return http.post('/api/alarms/rules', data);
  },

  // 更新报警规则
  updateAlarmRule: (id: string, data: any): Promise<ApiResponse<any>> => {
    return http.put(`/api/alarms/rules/${id}`, data);
  },

  // 删除报警规则
  deleteAlarmRule: (id: string): Promise<ApiResponse<void>> => {
    return http.delete(`/api/alarms/rules/${id}`);
  }
};
