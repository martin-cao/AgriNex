// api/sensors.ts
import { http } from './http';
import type { Sensor, Reading, ApiResponse, PaginatedResponse } from '@/types';

export const sensorsApi = {
  // 获取传感器列表
  getSensors: async (): Promise<ApiResponse<Sensor[]>> => {
    const response = await http.get('/api/sensors');
    return response.data;
  },

  // 获取传感器详情
  getSensor: async (sensorId: number): Promise<ApiResponse<Sensor>> => {
    const response = await http.get(`/api/sensors/${sensorId}`);
    return response.data;
  },

  // 创建传感器
  createSensor: async (sensor: Omit<Sensor, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Sensor>> => {
    const response = await http.post('/api/sensors', sensor);
    return response.data;
  },

  // 更新传感器
  updateSensor: async (sensorId: number, sensor: Partial<Sensor>): Promise<ApiResponse<Sensor>> => {
    const response = await http.put(`/api/sensors/${sensorId}`, sensor);
    return response.data;
  },

  // 删除传感器
  deleteSensor: async (sensorId: number): Promise<ApiResponse<{}>> => {
    const response = await http.delete(`/api/sensors/${sensorId}`);
    return response.data;
  },

  // 获取传感器读数
  getSensorReadings: async (
    sensorId: number, 
    params?: { 
      start_time?: string; 
      end_time?: string; 
      per_page?: number;
      page?: number;
    }
  ): Promise<ApiResponse<Reading[]>> => {
    const response = await http.get(`/api/sensors/${sensorId}/readings`, { params });
    return response.data;
  },

  // 添加传感器读数
  addSensorReading: async (
    sensorId: number, 
    reading: { value: number; timestamp?: string }
  ): Promise<ApiResponse<Reading>> => {
    const response = await http.post(`/api/sensors/${sensorId}/readings`, reading);
    return response.data;
  },

  // 获取传感器最新读数
  getSensorLatest: async (sensorId: number): Promise<ApiResponse<Reading>> => {
    const response = await http.get(`/api/sensors/${sensorId}/readings/latest`);
    return response.data;
  },

  // 获取传感器统计信息
  getSensorStatistics: async (
    sensorId: number, 
    params?: { 
      start_time?: string; 
      end_time?: string; 
    }
  ): Promise<ApiResponse<{
    count: number;
    avg: number;
    min: number;
    max: number;
    std: number;
  }>> => {
    const response = await http.get(`/api/sensors/${sensorId}/statistics`, { params });
    return response.data;
  }
};
