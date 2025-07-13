// api/deviceTemplates.ts
import api from './client';
import type { ApiResponse } from '../types';

export interface DeviceTemplate {
  id: number;
  device_type: string;
  name: string;
  description?: string;
  manufacturer?: string;
  model?: string;
  sensor_configs: SensorConfig[];
  default_config: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SensorConfig {
  type: string;
  name: string;
  unit: string;
  description?: string;
  is_required: boolean;
  default_config?: Record<string, any>;
  validation_rules?: Record<string, any>;
}

export const deviceTemplatesApi = {
  // 获取设备模板列表
  getDeviceTemplates: async (): Promise<ApiResponse<DeviceTemplate[]>> => {
    const response = await api.get('/device-templates/');
    return response.data;
  },

  // 获取设备模板详情
  getDeviceTemplate: async (deviceType: string): Promise<ApiResponse<DeviceTemplate>> => {
    const response = await api.get(`/device-templates/${deviceType}`);
    return response.data;
  },

  // 创建设备模板
  createDeviceTemplate: async (template: Omit<DeviceTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<DeviceTemplate>> => {
    const response = await api.post('/device-templates/', template);
    return response.data;
  },

  // 更新设备模板
  updateDeviceTemplate: async (deviceType: string, template: Partial<DeviceTemplate>): Promise<ApiResponse<DeviceTemplate>> => {
    const response = await api.put(`/device-templates/${deviceType}`, template);
    return response.data;
  },

  // 删除设备模板
  deleteDeviceTemplate: async (deviceType: string): Promise<ApiResponse<{}>> => {
    const response = await api.delete(`/device-templates/${deviceType}`);
    return response.data;
  },

  // 获取模板传感器配置
  getTemplateSensors: async (deviceType: string): Promise<ApiResponse<{
    data: SensorConfig[];
    total: number;
    required_sensors: number;
  }>> => {
    const response = await api.get(`/device-templates/${deviceType}/sensors`);
    return response.data;
  },

  // 验证传感器类型
  validateSensorType: async (deviceType: string, sensorType: string): Promise<ApiResponse<{
    valid: boolean;
    sensor_config?: SensorConfig;
    allowed_types?: string[];
    message: string;
  }>> => {
    const response = await api.post(`/device-templates/${deviceType}/validate`, {
      sensor_type: sensorType
    });
    return response.data;
  }
};
