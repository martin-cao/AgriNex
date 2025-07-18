// src/api/predictions.ts
import { http } from './http';

export interface PredictionOption {
  key: string;
  description: string;
  periods: number;
  frequency: string;
}

export interface PredictionRequest {
  field?: string;
  period?: string;
}

export interface PredictionPoint {
  timestamp: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

export interface PredictionResponse {
  success: boolean;
  message?: string;
  sensor_id?: number;
  device_id?: number;
  field?: string;
  period?: string;
  period_description?: string;
  forecast?: PredictionPoint[];
  forecast_count?: number;
  status?: string;
}

export interface ForecastOptionsResponse {
  success: boolean;
  periods: string[];
  period_configs: Record<string, PredictionOption>;
}

export interface PredictionHistoryResponse {
  success: boolean;
  data: Array<{
    id: number;
    sensor_id: number;
    predict_ts: string;
    yhat: number;
    yhat_lower: number;
    yhat_upper: number;
    metric_type: string;
    generated_at: string;
  }>;
  pagination?: {
    page: number;
    per_page: number;
    total: number;
    pages: number;
  };
}

export const predictionsApi = {
  // 获取预测选项
  getForecastOptions(): Promise<ForecastOptionsResponse> {
    return http.get('/api/forecasts/options');
  },

  // 获取可预测字段
  getFields(): Promise<{ fields: string[] }> {
    return http.get('/api/forecasts/fields');
  },

  // 触发传感器预测
  triggerSensorPrediction(sensorId: number, request: PredictionRequest): Promise<PredictionResponse> {
    return http.post(`/api/forecasts/sensors/${sensorId}`, request);
  },

  // 获取传感器预测历史
  getSensorPredictions(sensorId: number, page = 1, perPage = 50): Promise<PredictionHistoryResponse> {
    return http.get(`/api/forecasts/sensors/${sensorId}`, {
      params: { page, per_page: perPage }
    });
  },

  // 获取传感器最新预测
  getLatestSensorPredictions(sensorId: number): Promise<PredictionHistoryResponse> {
    return http.get(`/api/forecasts/sensors/${sensorId}/latest`);
  },

  // 获取预测历史
  getPredictionHistory(params?: { page?: number; per_page?: number }): Promise<PredictionHistoryResponse> {
    return http.get('/api/forecasts/history', { params });
  },

  // 设备预测
  predictDevice(deviceId: number, field = 'numeric_value', period = '24h'): Promise<PredictionResponse> {
    return http.get(`/api/forecasts/${deviceId}`, {
      params: { field, period }
    });
  }
};
