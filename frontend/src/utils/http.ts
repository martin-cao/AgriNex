// utils/http.ts
import api from '@/api/client';
import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse } from '@/types';

/**
 * HTTP工具类，进一步封装axios
 */
export class HttpUtil {
  /**
   * GET请求
   */
  static async get<T = any>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response: AxiosResponse<ApiResponse<T>> = await api.get(url, config);
    return response.data;
  }

  /**
   * POST请求
   */
  static async post<T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response: AxiosResponse<ApiResponse<T>> = await api.post(url, data, config);
    return response.data;
  }

  /**
   * PUT请求
   */
  static async put<T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response: AxiosResponse<ApiResponse<T>> = await api.put(url, data, config);
    return response.data;
  }

  /**
   * PATCH请求
   */
  static async patch<T = any>(
    url: string, 
    data?: any, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response: AxiosResponse<ApiResponse<T>> = await api.patch(url, data, config);
    return response.data;
  }

  /**
   * DELETE请求
   */
  static async delete<T = any>(
    url: string, 
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response: AxiosResponse<ApiResponse<T>> = await api.delete(url, config);
    return response.data;
  }

  /**
   * 文件上传
   */
  static async upload<T = any>(
    url: string, 
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    };

    const response: AxiosResponse<ApiResponse<T>> = await api.post(url, formData, config);
    return response.data;
  }

  /**
   * 文件下载
   */
  static async download(
    url: string, 
    filename?: string, 
    config?: AxiosRequestConfig
  ): Promise<void> {
    const response = await api.get(url, {
      ...config,
      responseType: 'blob',
    });

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * 批量请求
   */
  static async batch<T = any>(
    requests: Array<() => Promise<ApiResponse<T>>>
  ): Promise<ApiResponse<T>[]> {
    return Promise.all(requests.map(request => request()));
  }

  /**
   * 重试请求
   */
  static async retry<T = any>(
    requestFn: () => Promise<ApiResponse<T>>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<ApiResponse<T>> {
    let lastError: any;
    
    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error;
        if (i < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
        }
      }
    }
    
    throw lastError;
  }
}

export default HttpUtil;
