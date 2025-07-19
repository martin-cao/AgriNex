<template>
  <div class="media-page">
    <div class="page-header">
      <h1>媒体数据</h1>
      <p class="page-description">浏览传感器上传的图片和视频</p>
    </div>

    <a-card class="filter-card" size="small">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-select v-model:value="selectedLocation" allow-clear placeholder="选择地点" @change="onLocationChange">
            <a-select-option v-for="loc in availableLocations" :key="loc" :value="loc">{{ loc }}</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="selectedDevice" allow-clear placeholder="选择设备" @change="onDeviceChange">
            <a-select-option v-for="dev in filteredDevices" :key="dev.id" :value="dev.id">{{ dev.name }}</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="selectedSensor" allow-clear placeholder="选择传感器" :disabled="!selectedDevice" @change="fetchMedia">
            <a-select-option v-for="s in sensors" :key="s.id" :value="s.id">{{ s.name }} ({{ s.sensor_type }})</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-button type="primary" @click="fetchMedia" :disabled="!selectedSensor" :loading="loading">刷新</a-button>
        </a-col>
      </a-row>
    </a-card>

    <a-spin :spinning="loading" style="width:100%">
      <a-row v-if="mediaList.length" :gutter="[16,16]" class="media-grid">
        <a-col v-for="item in mediaList" :key="item.id" :xs="24" :sm="12" :md="8" :lg="6" :xl="4">
          <a-card :hoverable="true">
            <template #cover>
              <img v-if="item.data_type==='image'" :src="item.object_url" style="width:100%" />
              <video v-else controls :src="item.object_url" style="width:100%" />
            </template>
            <a-card-meta :title="formatDate(item.timestamp)">
              <template #description>
                <a-space>
                  <a-button type="link" size="small" @click="download(item)">下载</a-button>
                  <a-button type="link" size="small" @click="share(item)">分享</a-button>
                </a-space>
              </template>
            </a-card-meta>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-else description="暂无媒体数据" style="margin-top:40px" />
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { formatDate } from '@/utils';
import { deviceApi, sensorsApi, mediaApi } from '@/api';
import type { Device, Sensor, MediaReading } from '@/types';

const loading = ref(false);
const devices = ref<Device[]>([]);
const sensors = ref<Sensor[]>([]);
const mediaList = ref<MediaReading[]>([]);

const selectedLocation = ref<string>('');
const selectedDevice = ref<number | null>(null);
const selectedSensor = ref<number | null>(null);

const availableLocations = computed(() => {
  const set = new Set<string>();
  devices.value.forEach(d => { if (d.location) set.add(d.location); });
  return Array.from(set);
});

const filteredDevices = computed(() => {
  if (!selectedLocation.value) return devices.value;
  return devices.value.filter(d => d.location === selectedLocation.value);
});

const onLocationChange = () => {
  selectedDevice.value = null;
  selectedSensor.value = null;
  sensors.value = [];
};

const onDeviceChange = async () => {
  selectedSensor.value = null;
  sensors.value = [];
  if (!selectedDevice.value) return;
  try {
    const res = await deviceApi.getDeviceSensors(Number(selectedDevice.value));
    sensors.value = res.data || [];
  } catch (e) {
    message.error('获取传感器失败');
  }
};

const fetchDevices = async () => {
  try {
    loading.value = true;
    const res = await deviceApi.getDevices();
    devices.value = res.data || [];
  } catch (e) {
    message.error('获取设备列表失败');
  } finally {
    loading.value = false;
  }
};

const fetchMedia = async () => {
  if (!selectedSensor.value) return;
  try {
    loading.value = true;
    const res = await mediaApi.getMediaReadings(Number(selectedSensor.value), { per_page: 100 });
    const data = res.data || [];
    mediaList.value = data.filter(r => r.data_type === 'image' || r.data_type === 'video');
  } catch (e) {
    message.error('获取媒体数据失败');
  } finally {
    loading.value = false;
  }
};

const download = (item: MediaReading) => {
  if (!item.object_url) return;
  const link = document.createElement('a');
  link.href = item.object_url;
  link.download = item.object_key || 'media';
  link.click();
};

const share = async (item: MediaReading) => {
  if (!item.object_url) return;
  try {
    await navigator.clipboard.writeText(item.object_url);
    message.success('已复制分享链接');
  } catch (e) {
    message.error('复制失败');
  }
};

onMounted(() => {
  fetchDevices();
});
</script>

<style scoped>
.media-grid {
  margin-top: 16px;
}
</style>