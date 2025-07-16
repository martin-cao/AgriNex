import { http } from './http';
import type { SensorData, Sensor, ApiResponse, PaginatedResponse } from '@/types';

export const sensorApi = {
  // 获取传感器列表
  getSensors: (params?: {
    page?: number;
    per_page?: number;
    status?: 'active' | 'inactive' | 'error';
    type?: string;
    search?: string;
  }): Promise<PaginatedResponse<Sensor>> => {
    return http.get('/api/sensors', { params });
  },

  // 获取传感器详情
  getSensor: (id: string): Promise<ApiResponse<Sensor>> => {
    return http.get(`/api/sensors/${id}`);
  },

  // 获取传感器数据
  getSensorData: (params: {
    sensor_id?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
    data_type?: string;
  }): Promise<ApiResponse<SensorData[]>> => {
    return http.get('/api/sensor-data', { params });
  },

  // 获取最新传感器数据
  getLatestSensorData: (sensorId?: string): Promise<ApiResponse<SensorData[]>> => {
    return http.get('/api/sensor-data/latest', {
      params: sensorId ? { sensor_id: sensorId } : undefined
    });
  },

  // 获取传感器统计信息
  getSensorStats: (): Promise<ApiResponse<{
    total: number;
    active: number;
    inactive: number;
    error: number;
    by_type: Record<string, number>;
  }>> => {
    return http.get('/api/sensors/stats');
  },

  // 获取传感器类型列表
  getSensorTypes: (): Promise<ApiResponse<Array<{
    id: string;
    name: string;
    unit?: string;
    description?: string;
  }>>> => {
    return http.get('/api/sensors/types');
  },

  // 校准传感器
  calibrateSensor: (id: string, calibrationData: any): Promise<ApiResponse<void>> => {
    return http.post(`/api/sensors/${id}/calibrate`, calibrationData);
  },

  // 重置传感器
  resetSensor: (id: string): Promise<ApiResponse<void>> => {
    return http.post(`/api/sensors/${id}/reset`);
  }
};
