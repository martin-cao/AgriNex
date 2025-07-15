// api/deviceTemplates.ts
import { http } from './http';
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
  getDeviceTemplates: (): Promise<ApiResponse<DeviceTemplate[]>> => {
    return http.get('/api/device-templates');
  },

  // 获取设备模板详情
  getDeviceTemplate: (deviceType: string): Promise<ApiResponse<DeviceTemplate>> => {
    return http.get(`/api/device-templates/${deviceType}`);
  },

  // 创建设备模板
  createDeviceTemplate: (template: Omit<DeviceTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<DeviceTemplate>> => {
    return http.post('/api/device-templates', template);
  },

  // 更新设备模板
  updateDeviceTemplate: (deviceType: string, template: Partial<DeviceTemplate>): Promise<ApiResponse<DeviceTemplate>> => {
    return http.put(`/api/device-templates/${deviceType}`, template);
  },

  // 删除设备模板
  deleteDeviceTemplate: (deviceType: string): Promise<ApiResponse<{}>> => {
    return http.delete(`/api/device-templates/${deviceType}`);
  },

  // 获取模板传感器配置
  getTemplateSensors: (deviceType: string): Promise<ApiResponse<{
    data: SensorConfig[];
    total: number;
    required_sensors: number;
  }>> => {
    return http.get(`/api/device-templates/${deviceType}/sensors`);
  },

  // 验证传感器类型
  validateSensorType: (deviceType: string, sensorType: string): Promise<ApiResponse<{
    valid: boolean;
    sensor_config?: SensorConfig;
    allowed_types?: string[];
    message: string;
  }>> => {
    return http.post(`/api/device-templates/${deviceType}/validate`, {
      sensor_type: sensorType
    });
  }
};
