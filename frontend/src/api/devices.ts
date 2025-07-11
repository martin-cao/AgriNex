// api/devices.ts
import api from './client';
import type { Device, Sensor, Reading, MediaReading, ApiResponse } from '../types';

export const devicesApi = {
  // 获取设备列表
  getDevices: async (): Promise<ApiResponse<Device[]>> => {
    const response = await api.get('/devices');
    return response.data;
  },

  // 获取设备详情
  getDevice: async (deviceId: number): Promise<ApiResponse<Device>> => {
    const response = await api.get(`/devices/${deviceId}`);
    return response.data;
  },

  // 创建设备
  createDevice: async (device: Omit<Device, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Device>> => {
    const response = await api.post('/devices', device);
    return response.data;
  },

  // 更新设备
  updateDevice: async (deviceId: number, device: Partial<Device>): Promise<ApiResponse<Device>> => {
    const response = await api.put(`/devices/${deviceId}`, device);
    return response.data;
  },

  // 删除设备
  deleteDevice: async (deviceId: number): Promise<ApiResponse<{}>> => {
    const response = await api.delete(`/devices/${deviceId}`);
    return response.data;
  },

  // 获取设备传感器列表
  getDeviceSensors: async (deviceId: number): Promise<ApiResponse<Sensor[]>> => {
    const response = await api.get(`/devices/${deviceId}/sensors`);
    return response.data;
  },

  // 获取设备传感器最新读数
  getDeviceSensorLatest: async (deviceId: number, sensorId: number): Promise<ApiResponse<Reading>> => {
    const response = await api.get(`/devices/${deviceId}/sensors/${sensorId}/latest`);
    return response.data;
  },

  // 获取设备传感器读数历史
  getDeviceSensorReadings: async (
    deviceId: number, 
    sensorId: number, 
    params?: { 
      start_time?: string; 
      end_time?: string; 
      limit?: number; 
    }
  ): Promise<ApiResponse<Reading[]>> => {
    const response = await api.get(`/devices/${deviceId}/sensors/${sensorId}/readings`, { params });
    return response.data;
  },

  // 获取设备健康状态
  getDevicesHealth: async (): Promise<ApiResponse<{ total: number; online: number; offline: number }>> => {
    const response = await api.get('/devices/health');
    return response.data;
  }
};
