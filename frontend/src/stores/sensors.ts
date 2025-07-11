// stores/sensors.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { sensorsApi } from '../api';
import type { Sensor, Reading } from '../types';

export const useSensorsStore = defineStore('sensors', () => {
  const sensors = ref<Sensor[]>([]);
  const currentSensor = ref<Sensor | null>(null);
  const sensorReadings = ref<Reading[]>([]);
  const isLoading = ref(false);

  const fetchSensors = async () => {
    isLoading.value = true;
    try {
      const response = await sensorsApi.getSensors();
      if (response.success && response.data) {
        sensors.value = response.data;
      }
    } catch (error) {
      console.error('获取传感器列表失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const fetchSensor = async (sensorId: number) => {
    isLoading.value = true;
    try {
      const response = await sensorsApi.getSensor(sensorId);
      if (response.success && response.data) {
        currentSensor.value = response.data;
        return response.data;
      }
    } catch (error) {
      console.error('获取传感器详情失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const createSensor = async (sensor: Omit<Sensor, 'id' | 'created_at' | 'updated_at'>) => {
    isLoading.value = true;
    try {
      const response = await sensorsApi.createSensor(sensor);
      if (response.success && response.data) {
        sensors.value.push(response.data);
        return response.data;
      }
    } catch (error) {
      console.error('创建传感器失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const updateSensor = async (sensorId: number, sensor: Partial<Sensor>) => {
    isLoading.value = true;
    try {
      const response = await sensorsApi.updateSensor(sensorId, sensor);
      if (response.success && response.data) {
        const index = sensors.value.findIndex(s => s.id === sensorId);
        if (index !== -1) {
          sensors.value[index] = response.data;
        }
        if (currentSensor.value?.id === sensorId) {
          currentSensor.value = response.data;
        }
        return response.data;
      }
    } catch (error) {
      console.error('更新传感器失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const deleteSensor = async (sensorId: number) => {
    isLoading.value = true;
    try {
      const response = await sensorsApi.deleteSensor(sensorId);
      if (response.success) {
        sensors.value = sensors.value.filter(s => s.id !== sensorId);
        if (currentSensor.value?.id === sensorId) {
          currentSensor.value = null;
        }
      }
    } catch (error) {
      console.error('删除传感器失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchSensorReadings = async (
    sensorId: number,
    params?: { start_time?: string; end_time?: string; per_page?: number; page?: number }
  ) => {
    isLoading.value = true;
    try {
      const response = await sensorsApi.getSensorReadings(sensorId, params);
      if (response.success) {
        // 处理分页响应
        if (response.data) {
          sensorReadings.value = Array.isArray(response.data) ? response.data : [];
          return {
            data: sensorReadings.value,
            pagination: response.pagination
          };
        }
      }
      return { data: [], pagination: null };
    } catch (error) {
      console.error('获取传感器读数失败:', error);
      // 如果API返回404或无数据，返回空数组而不是错误
      sensorReadings.value = [];
      return { data: [], pagination: null };
    } finally {
      isLoading.value = false;
    }
  };

  const addSensorReading = async (sensorId: number, reading: { value: number; timestamp?: string }) => {
    try {
      const response = await sensorsApi.addSensorReading(sensorId, reading);
      if (response.success && response.data) {
        sensorReadings.value.unshift(response.data);
        return response.data;
      }
    } catch (error) {
      console.error('添加传感器读数失败:', error);
      throw error;
    }
  };

  return {
    sensors,
    currentSensor,
    sensorReadings,
    isLoading,
    fetchSensors,
    fetchSensor,
    createSensor,
    updateSensor,
    deleteSensor,
    fetchSensorReadings,
    addSensorReading
  };
});
