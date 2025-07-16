import { http } from './http';
import type { Device, DeviceStatus, ApiResponse, PaginatedResponse } from '@/types';

export const deviceApi = {
  // 获取设备列表
  getDevices: (params?: {
    page?: number;
    per_page?: number;
    status?: DeviceStatus;
    type?: string;
    search?: string;
  }): Promise<PaginatedResponse<Device>> => {
    return http.get('/api/devices', { params });
  },

  // 获取设备详情
  getDevice: (id: string): Promise<ApiResponse<Device>> => {
    return http.get(`/api/devices/${id}`);
  },

  // 创建设备
  createDevice: (data: Partial<Device>): Promise<ApiResponse<Device>> => {
    return http.post('/api/devices', data);
  },

  // 更新设备
  updateDevice: (id: string, data: Partial<Device>): Promise<ApiResponse<Device>> => {
    return http.put(`/api/devices/${id}`, data);
  },

  // 删除设备
  deleteDevice: (id: string): Promise<ApiResponse<void>> => {
    return http.delete(`/api/devices/${id}`);
  },

  // 批量操作设备
  batchOperation: (operation: 'start' | 'stop' | 'restart', deviceIds: string[]): Promise<ApiResponse<void>> => {
    return http.post('/api/devices/batch', {
      operation,
      device_ids: deviceIds
    });
  },

  // 获取设备统计信息
  getDeviceStats: (): Promise<ApiResponse<{
    total: number;
    online: number;
    offline: number;
    error: number;
    by_type: Record<string, number>;
  }>> => {
    return http.get('/api/devices/stats');
  },

  // 获取设备类型列表
  getDeviceTypes: (): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    description?: string;
  }>>> => {
    return http.get('/api/devices/types');
  },

  // 控制设备
  controlDevice: (id: string, action: string, params?: any): Promise<ApiResponse<any>> => {
    return http.post(`/api/devices/${id}/control`, {
      action,
      params
    });
  }
};
