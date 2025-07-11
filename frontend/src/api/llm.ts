// api/llm.ts
import api from './client';
import type { 
  LLMRequest, 
  LLMResponse, 
  ApiResponse, 
  ChatMessage,
  QuickAction,
  SystemDiagnosis,
  AgriculturalAdvice,
  ReportData
} from '../types';

export const llmApi = {
  // 聊天机器人对话
  chatWithBot: async (data: { 
    message: string; 
    context?: string; 
    sensor_id?: number; 
  }): Promise<ApiResponse<{ 
    response: string; 
    context: string; 
    timestamp: string; 
    confidence: number;
  }>> => {
    const response = await api.post('/llm/chat', data);
    return response.data;
  },

  // 获取传感器数据分析和建议
  getSensorAnalysis: async (request: LLMRequest): Promise<ApiResponse<LLMResponse & {
    data_points: number;
    analysis_period: string;
    recommendations: string[];
  }>> => {
    const response = await api.post('/llm/sensor-analysis', request);
    return response.data;
  },

  // 获取农业建议
  getAgriculturalAdvice: async (data: { 
    crop_type?: string; 
    weather_condition?: string; 
    soil_moisture?: number; 
    temperature?: number; 
    humidity?: number; 
  }): Promise<ApiResponse<AgriculturalAdvice>> => {
    const response = await api.post('/llm/agricultural-advice', data);
    return response.data;
  },

  // 生成报告
  generateReport: async (data: { 
    sensor_ids: number[]; 
    start_date: string; 
    end_date: string; 
    report_type: string; 
  }): Promise<ApiResponse<ReportData>> => {
    const response = await api.post('/llm/generate-report', data);
    return response.data;
  },

  // 系统诊断
  getSystemDiagnosis: async (): Promise<ApiResponse<SystemDiagnosis>> => {
    const response = await api.post('/llm/system-diagnosis');
    return response.data;
  },

  // 获取快捷操作
  getQuickActions: async (): Promise<ApiResponse<{ 
    actions: QuickAction[];
    timestamp: string;
  }>> => {
    const response = await api.get('/llm/quick-actions');
    return response.data;
  }
};
