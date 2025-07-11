// stores/devices.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { devicesApi } from '../api';
import type { Device, Sensor } from '../types';

export const useDevicesStore = defineStore('devices', () => {
  const devices = ref<Device[]>([]);
  const currentDevice = ref<Device | null>(null);
  const deviceSensors = ref<Sensor[]>([]);
  const isLoading = ref(false);

  const fetchDevices = async () => {
    isLoading.value = true;
    try {
      const response = await devicesApi.getDevices();
      if (response.success && response.data) {
        devices.value = response.data;
      }
    } catch (error) {
      console.error('获取设备列表失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const fetchDevice = async (deviceId: number) => {
    isLoading.value = true;
    try {
      const response = await devicesApi.getDevice(deviceId);
      if (response.success && response.data) {
        currentDevice.value = response.data;
        return response.data;
      }
    } catch (error) {
      console.error('获取设备详情失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const createDevice = async (device: Omit<Device, 'id' | 'created_at' | 'updated_at'>) => {
    isLoading.value = true;
    try {
      const response = await devicesApi.createDevice(device);
      if (response.success && response.data) {
        devices.value.push(response.data);
        return response.data;
      }
    } catch (error) {
      console.error('创建设备失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const updateDevice = async (deviceId: number, device: Partial<Device>) => {
    isLoading.value = true;
    try {
      const response = await devicesApi.updateDevice(deviceId, device);
      if (response.success && response.data) {
        const index = devices.value.findIndex(d => d.id === deviceId);
        if (index !== -1) {
          devices.value[index] = response.data;
        }
        if (currentDevice.value?.id === deviceId) {
          currentDevice.value = response.data;
        }
        return response.data;
      }
    } catch (error) {
      console.error('更新设备失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const deleteDevice = async (deviceId: number) => {
    isLoading.value = true;
    try {
      const response = await devicesApi.deleteDevice(deviceId);
      if (response.success) {
        devices.value = devices.value.filter(d => d.id !== deviceId);
        if (currentDevice.value?.id === deviceId) {
          currentDevice.value = null;
        }
      }
    } catch (error) {
      console.error('删除设备失败:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchDeviceSensors = async (deviceId: number) => {
    isLoading.value = true;
    try {
      const response = await devicesApi.getDeviceSensors(deviceId);
      if (response.success && response.data) {
        deviceSensors.value = response.data;
        return response.data;
      }
    } catch (error) {
      console.error('获取设备传感器失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  return {
    devices,
    currentDevice,
    deviceSensors,
    isLoading,
    fetchDevices,
    fetchDevice,
    createDevice,
    updateDevice,
    deleteDevice,
    fetchDeviceSensors
  };
});
