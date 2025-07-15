import { http } from './http';
import type { ApiResponse } from '@/types';

export const dashboardApi = {
  // 获取仪表盘统计数据
  getStats: (): Promise<ApiResponse<{
    devices: {
      total: number;
      online: number;
      offline: number;
      error: number;
    };
    sensors: {
      total: number;
      active: number;
      inactive: number;
      error: number;
    };
    alarms: {
      total: number;
      active: number;
      resolved: number;
      critical: number;
    };
    data_points: number;
  }>> => {
    return http.get('/api/dashboard/stats');
  },

  // 获取实时数据
  getRealTimeData: (): Promise<ApiResponse<{
    timestamp: string;
    temperature: number;
    humidity: number;
    soil_moisture: number;
    light_intensity: number;
    ph_value: number;
  }>> => {
    return http.get('/api/dashboard/realtime');
  },

  // 获取图表数据
  getChartData: (params: {
    type: 'temperature' | 'humidity' | 'soil_moisture' | 'light_intensity' | 'ph_value';
    period: '1h' | '6h' | '24h' | '7d' | '30d';
    sensor_id?: string;
  }): Promise<ApiResponse<Array<{
    timestamp: string;
    value: number;
    sensor_id?: string;
    sensor_name?: string;
  }>>> => {
    return http.get('/api/dashboard/chart-data', { params });
  },

  // 获取设备状态分布
  getDeviceStatusDistribution: (): Promise<ApiResponse<Array<{
    status: string;
    count: number;
    percentage: number;
  }>>> => {
    return http.get('/api/dashboard/device-status-distribution');
  },

  // 获取报警趋势
  getAlarmTrend: (period: '7d' | '30d' | '90d' = '7d'): Promise<ApiResponse<Array<{
    date: string;
    count: number;
    level_distribution: Record<string, number>;
  }>>> => {
    return http.get('/api/dashboard/alarm-trend', {
      params: { period }
    });
  },

  // 获取系统健康状态
  getSystemHealth: (): Promise<ApiResponse<{
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    network_status: 'good' | 'warning' | 'error';
    database_status: 'connected' | 'disconnected';
    mqtt_status: 'connected' | 'disconnected';
    api_response_time: number;
  }>> => {
    return http.get('/api/dashboard/system-health');
  },

  // 获取最近活动
  getRecentActivities: (limit: number = 10): Promise<ApiResponse<Array<{
    id: string;
    type: 'device' | 'sensor' | 'alarm' | 'user';
    action: string;
    description: string;
    timestamp: string;
    user?: string;
    device_id?: string;
    sensor_id?: string;
  }>>> => {
    return http.get('/api/dashboard/recent-activities', {
      params: { limit }
    });
  },

  // 获取最近报警
  getRecentAlarms: (): Promise<ApiResponse<Array<{
    id: string;
    title: string;
    level: string;
    status: string;
    triggered_at: string;
  }>>> => {
    return http.get('/api/dashboard/recent-alarms');
  },

  // 获取设备概览
  getDeviceOverview: (): Promise<ApiResponse<Array<{
    status: string;
    count: number;
  }>>> => {
    return http.get('/api/dashboard/device-overview');
  },

  // 获取趋势数据
  getTrendData: (timeRange: string): Promise<ApiResponse<Array<{
    time: string;
    temperature: number;
    humidity: number;
    light: number;
  }>>> => {
    return http.get('/api/dashboard/trend-data', {
      params: { time_range: timeRange }
    });
  },

  // 获取状态数据
  getStatusData: (): Promise<ApiResponse<Array<{
    status: string;
    count: number;
  }>>> => {
    return http.get('/api/dashboard/status-data');
  }
};
