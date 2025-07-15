// stores/alarms.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { alarmApi } from '../api';
import type { Alarm } from '../types';

export const useAlarmsStore = defineStore('alarms', () => {
  const alarms = ref<Alarm[]>([]);
  const isLoading = ref(false);

  const fetchAlarms = async (params?: { status?: string; limit?: number; offset?: number }) => {
    isLoading.value = true;
    try {
      const response = await alarmApi.getAlarms(params);
      if (response.success && response.data) {
        alarms.value = response.data;
      }
    } catch (error) {
      console.error('获取告警列表失败:', error);
    } finally {
      isLoading.value = false;
    }
  };

  const resolveAlarm = async (alarmId: number) => {
    try {
      const response = await alarmApi.resolveAlarm(alarmId);
      if (response.success && response.data) {
        const index = alarms.value.findIndex(a => a.id === alarmId);
        if (index !== -1) {
          alarms.value[index] = response.data;
        }
        return response.data;
      }
    } catch (error) {
      console.error('解决告警失败:', error);
      throw error;
    }
  };

  const getActiveAlarms = () => {
    return alarms.value.filter(alarm => alarm.status === 'active');
  };

  const getResolvedAlarms = () => {
    return alarms.value.filter(alarm => alarm.status === 'resolved');
  };

  return {
    alarms,
    isLoading,
    fetchAlarms,
    resolveAlarm,
    getActiveAlarms,
    getResolvedAlarms
  };
});
