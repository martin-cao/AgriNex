// stores/dashboard.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { dashboardApi } from '../api';
import type { DashboardStats, SystemHealth } from '../types';

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats>({
    devices: {
      total: 0,
      online: 0,
      offline: 0,
      error: 0,
    },
    sensors: {
      total: 0,
      active: 0,
      inactive: 0,
      error: 0,
    },
    alarms: {
      total: 0,
      active: 0,
      resolved: 0,
      critical: 0,
    },
    data_points: 0,
    last_updated: '',
  });
  const systemStatus = ref<SystemHealth>({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    network_status: 'good',
    database_status: 'disconnected',
    mqtt_status: 'disconnected',
    api_response_time: 0,
    last_updated: '',
  });
  const isLoading = ref(false);

  const fetchDashboardStats = async () => {
    isLoading.value = true;
    try {
      const response = await dashboardApi.getStats();
      if (response.success && response.data) {
        stats.value = response.data;
      }
    } catch (error) {
      console.error('获取仪表板统计数据失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const response = await dashboardApi.getSystemHealth();
      if (response.success && response.data) {
        systemStatus.value = response.data;
      }
    } catch (error) {
      console.error('获取系统状态失败:', error);
    }
  };

  const refreshDashboard = async () => {
    await Promise.all([
      fetchDashboardStats(),
      fetchSystemStatus()
    ]);
  };

  return {
    stats,
    systemStatus,
    isLoading,
    fetchDashboardStats,
    fetchSystemStatus,
    refreshDashboard
  };
});
