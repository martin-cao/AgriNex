// api/media.ts
import api from './client';
import type { ApiResponse } from '../types';

export interface MediaFile {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  mime_type: string;
  url: string;
  thumbnail_url?: string;
  device_id?: number;
  sensor_id?: number;
  created_at: string;
  updated_at: string;
}

export const mediaApi = {
  // 获取媒体文件列表
  getMediaFiles: async (params?: {
    file_type?: string;
    device_id?: number;
    sensor_id?: number;
    start_date?: string;
    end_date?: string;
    page?: number;
    per_page?: number;
  }): Promise<ApiResponse<MediaFile[]>> => {
    try {
      const response = await api.get('/media/', { params });
      return response.data;
    } catch (error: any) {
      // 如果API不存在，返回空数据
      if (error.response?.status === 404) {
        return {
          success: true,
          data: []
        };
      }
      throw error;
    }
  },

  // 获取媒体文件详情
  getMediaFile: async (mediaId: number): Promise<ApiResponse<MediaFile>> => {
    const response = await api.get(`/media/${mediaId}/`);
    return response.data;
  },

  // 上传媒体文件
  uploadMediaFile: async (formData: FormData): Promise<ApiResponse<MediaFile>> => {
    const response = await api.post('/media/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 删除媒体文件
  deleteMediaFile: async (mediaId: number): Promise<ApiResponse<{}>> => {
    const response = await api.delete(`/media/${mediaId}/`);
    return response.data;
  },

  // 获取预签名上传URL（如果使用MinIO直接上传）
  getUploadUrl: async (filename: string, contentType: string): Promise<ApiResponse<{
    upload_url: string;
    file_url: string;
  }>> => {
    const response = await api.post('/media/upload-url/', {
      filename,
      content_type: contentType
    });
    return response.data;
  }
};
