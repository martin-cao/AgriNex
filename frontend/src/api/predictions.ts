// api/predictions.ts
import api from './client';
import type { Prediction, ApiResponse } from '../types';

export const predictionsApi = {
  // 获取预测结果
  getPredictions: async (params?: { 
    sensor_id?: number; 
    start_time?: string; 
    end_time?: string; 
    limit?: number; 
  }): Promise<ApiResponse<Prediction[]>> => {
    const response = await api.get('/predictions', { params });
    return response.data;
  },

  // 触发预测
  triggerPrediction: async (data: { 
    sensor_id: number; 
    periods?: number; 
    freq?: string; 
  }): Promise<ApiResponse<{ 
    status: string; 
    message: string; 
    predictions_count: number; 
  }>> => {
    const response = await api.post('/predictions/trigger', data);
    return response.data;
  },

  // 获取预测统计
  getPredictionStatistics: async (): Promise<ApiResponse<{
    total_predictions: number;
    sensors_with_predictions: number;
    last_prediction_time: string;
  }>> => {
    const response = await api.get('/predictions/statistics');
    return response.data;
  }
};
