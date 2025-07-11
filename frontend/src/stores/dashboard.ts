// stores/dashboard.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { dashboardApi } from '../api';
import type { DashboardStats } from '../types';

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats>({
    total_devices: 0,
    online_devices: 0,
    active_alerts: 0,
    today_data_points: 0
  });
  const systemStatus = ref({
    database: false,
    mqtt: false,
    storage: false,
    prediction: false
  });
  const isLoading = ref(false);

  const fetchDashboardStats = async () => {
    isLoading.value = true;
    try {
      const response = await dashboardApi.getDashboardStats();
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
      const response = await dashboardApi.getSystemStatus();
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
