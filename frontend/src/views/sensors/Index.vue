<template>
  <div class="sensors-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>传感器数据</h1>
      <p class="page-description">监控农业环境传感器实时数据与历史趋势</p>
    </div>

    <!-- 空状态显示 -->
    <div v-if="!loading && devices.length === 0" style="text-align: center; padding: 60px 0;">
      <a-empty description="暂无设备数据">
        <template #description>
          <p>请先<router-link to="/devices">添加设备</router-link>，然后才能查看传感器数据</p>
        </template>
      </a-empty>
    </div>

    <!-- 设备选择器 -->
    <a-card class="device-selector" size="small" v-if="devices.length > 0">
      <a-row :gutter="16" align="middle">
        <a-col :span="4">
          <!-- <span>选择地点:</span> -->
          <a-select
            v-model:value="selectedLocation"
            placeholder="请选择地点"
            style="width: 100%; margin-left: 8px;"
            allow-clear
            @change="handleLocationChange"
          >
            <a-select-option value="">全部地点</a-select-option>
            <a-select-option
              v-for="location in availableLocations"
              :key="location"
              :value="location"
            >
              {{ location }}
            </a-select-option>
          </a-select>
        </a-col>
        
        <a-col :span="5">
          <!-- <span>选择设备:</span> -->
          <a-select
            v-model:value="selectedDevice"
            placeholder="请选择设备"
            style="width: 100%; margin-left: 8px;"
            @change="handleDeviceChange"
          >
            <a-select-option
              v-for="device in filteredDevices"
              :key="device.id"
              :value="device.id"
            >
              {{ device.name }} ({{ device.location }})
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="5">
          <!-- <span>选择传感器:</span> -->
          <a-select
            v-model:value="selectedSensor"
            placeholder="请选择传感器"
            style="width: 100%; margin-left: 8px;"
            :disabled="!selectedDevice"
            @change="handleSensorChange"
          >
            <a-select-option
              v-for="sensor in sensors"
              :key="sensor.id"
              :value="sensor.id"
            >
              {{ sensor.name }} ({{ sensor.sensor_type }})
            </a-select-option>
          </a-select>
        </a-col>

        <a-col :span="5">
          <!-- <span>时间范围:</span> -->
          <a-select
            v-model:value="timeRange"
            style="width: 100%; margin-left: 8px;"
            @change="handleTimeRangeChange"
          >
            <a-select-option value="1h">最近1小时</a-select-option>
            <a-select-option value="6h">最近6小时</a-select-option>
            <a-select-option value="24h">最近24小时</a-select-option>
            <a-select-option value="7d">最近7天</a-select-option>
            <a-select-option value="30d">最近30天</a-select-option>
          </a-select>
        </a-col>

        <a-col :span="5">
          <a-space>
            <a-button type="primary" @click="refreshData" :loading="loading">
              <reload-outlined />
              刷新数据
            </a-button>
            <a-button @click="exportData" :disabled="!selectedSensor">
              <download-outlined />
              导出数据
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 实时数据卡片 -->
    <a-row :gutter="[16, 16]" v-if="selectedSensor" class="realtime-cards">
      <a-col :xs="24" :sm="8">
        <StatisticCard
          title="当前值"
          :value="currentData.value ?? '--'"
          :suffix="currentData.unit"
          :precision="2"
          icon="dashboard-outlined"
          icon-color="#1890ff"
          :loading="loading"
        />
      </a-col>
      <a-col :xs="24" :sm="8">
        <StatisticCard
          title="平均值"
          :value="currentData.average ?? '--'"
          :suffix="currentData.unit"
          :precision="2"
          icon="line-chart-outlined"
          icon-color="#52c41a"
          :loading="loading"
        />
      </a-col>
      <a-col :xs="24" :sm="8">
        <StatisticCard
          title="变化趋势"
          :value="Math.abs(currentData.change)"
          :suffix="currentData.unit"
          :precision="2"
          icon="rise-outlined"
          :icon-color="currentData.change >= 0 ? '#52c41a' : '#ff4d4f'"
          :trend="`${currentData.change >= 0 ? '+' : ''}${currentData.change.toFixed(2)}`"
          :trend-type="currentData.change >= 0 ? 'up' : 'down'"
          :loading="loading"
        />
      </a-col>
    </a-row>

    <!-- 图表区域 -->
    <a-row :gutter="[16, 16]" v-if="selectedSensor">
      <!-- 时序图表 -->
      <a-col :span="24">
        <ChartContainer
          title="传感器数据趋势"
          :option="trendChartOption"
          :height="400"
          :loading="chartLoading"
          @refresh="refreshChartData"
        >
          <template #actions>
            <a-space>
              <a-tooltip title="实时更新">
                <a-switch
                  v-model:checked="autoRefresh"
                  checked-children="自动"
                  un-checked-children="手动"
                  @change="handleAutoRefreshChange"
                />
              </a-tooltip>
              <a-button type="text" @click="refreshChartData">
                <reload-outlined />
              </a-button>
            </a-space>
          </template>
        </ChartContainer>
      </a-col>
    </a-row>

    <!-- 统计信息和阈值设置 -->
    <a-row :gutter="[16, 16]" v-if="selectedSensor">
      <!-- 数据统计 -->
      <a-col :xs="24" :lg="12">
        <a-card title="数据统计" :loading="loading">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="最大值">
              {{ statistics.max }} {{ currentData.unit }}
            </a-descriptions-item>
            <a-descriptions-item label="最小值">
              {{ statistics.min }} {{ currentData.unit }}
            </a-descriptions-item>
            <a-descriptions-item label="平均值">
              {{ statistics.avg }} {{ currentData.unit }}
            </a-descriptions-item>
            <a-descriptions-item label="标准差">
              {{ statistics.std }} {{ currentData.unit }}
            </a-descriptions-item>
            <a-descriptions-item label="数据点数">
              {{ statistics.count }} 个
            </a-descriptions-item>
            <a-descriptions-item label="更新时间">
              {{ formatTime(statistics.lastUpdate) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>

      <!-- 阈值设置 -->
      <a-col :xs="24" :lg="12">
        <a-card title="阈值设置" :loading="loading">
          <a-form layout="vertical" size="small">
            <a-form-item label="最大阈值">
              <a-input-number
                v-model:value="thresholds.max"
                style="width: 100%"
                :precision="2"
                @change="handleThresholdChange"
              />
            </a-form-item>
            <a-form-item label="最小阈值">
              <a-input-number
                v-model:value="thresholds.min"
                style="width: 100%"
                :precision="2"
                @change="handleThresholdChange"
              />
            </a-form-item>
            <a-form-item>
              <a-space>
                <a-button type="primary" size="small" @click="saveThresholds">
                  保存设置
                </a-button>
                <a-button size="small" @click="resetThresholds">
                  重置
                </a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
    </a-row>

    <!-- 空状态 -->
    <a-card v-if="!selectedSensor" class="empty-state">
      <a-empty description="请选择设备和传感器来查看数据">
        <a-button type="primary" @click="refreshDevices">
          <reload-outlined />
          刷新设备列表
        </a-button>
      </a-empty>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import StatisticCard from '@/components/ui/StatisticCard.vue';
import ChartContainer from '@/components/charts/ChartContainer.vue';
import { sensorsApi } from '@/api/sensors';
import { deviceApi } from '@/api/device';
import type { SensorData, Sensor, Device } from '@/types';
import dayjs from 'dayjs';

const router = useRouter();

// 响应式数据
const loading = ref(true);
const chartLoading = ref(false);
const selectedLocation = ref<string>('');
const selectedDevice = ref<string | null>(null);
const selectedSensor = ref<number | null>(null);
const timeRange = ref('24h');
const autoRefresh = ref(false);
const devices = ref<Device[]>([]);
const sensors = ref<Sensor[]>([]);
const sensorData = ref<SensorData[]>([]);

const currentData = reactive({
  value: null as number | null,
  unit: '',
  average: null as number | null,
  change: 0
});

const statistics = reactive({
  max: 0,
  min: 0,
  avg: 0,
  std: 0,
  count: 0,
  lastUpdate: ''
});

const thresholds = reactive({
  max: null,
  min: null
});

let refreshInterval: number | null = null;

// 计算属性
const availableLocations = computed(() => {
  const locations = new Set<string>();
  devices.value.forEach(device => {
    if (device.location) {
      locations.add(device.location);
    }
  });
  return Array.from(locations).sort();
});

const filteredDevices = computed(() => {
  if (!selectedLocation.value) {
    return devices.value;
  }
  return devices.value.filter(device => device.location === selectedLocation.value);
});

const trendChartOption = computed(() => {
  if (!sensorData.value.length) {
    return {
      title: {
        text: '暂无数据',
        left: 'center'
      },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: []
      },
      yAxis: {
        type: 'value',
        name: currentData.unit
      },
      series: [{
        name: '传感器数值',
        type: 'line',
        data: []
      }]
    };
  }

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const data = params[0];
        return `
          <div>
            <div>时间: ${dayjs(data.axisValue).format('MM-DD HH:mm')}</div>
            <div style="color: ${data.color}">
              值: ${data.value} ${currentData.unit}
            </div>
          </div>
        `;
      }
    },
    legend: {
      data: ['传感器数值', '最大阈值', '最小阈值']
    },
    xAxis: {
      type: 'category',
      data: sensorData.value.map(item => dayjs(item.timestamp).format('MM-DD HH:mm'))
    },
    yAxis: {
      type: 'value',
      name: currentData.unit,
      axisLabel: {
        formatter: '{value} ' + currentData.unit
      }
    },
    series: [
      {
        name: '传感器数值',
        type: 'line',
        data: sensorData.value.map(item => item.value),
        smooth: true,
        lineStyle: {
          color: '#1890ff',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.1)' }
            ]
          }
        }
      },
      // 阈值线
      ...(thresholds.max !== null ? [{
        name: '最大阈值',
        type: 'line',
        data: sensorData.value.map(() => thresholds.max),
        lineStyle: {
          color: '#ff4d4f',
          type: 'dashed'
        },
        symbol: 'none'
      }] : []),
      ...(thresholds.min !== null ? [{
        name: '最小阈值',
        type: 'line',
        data: sensorData.value.map(() => thresholds.min),
        lineStyle: {
          color: '#faad14',
          type: 'dashed'
        },
        symbol: 'none'
      }] : [])
    ]
  };
});

// 方法
const checkAuth = () => {
  const token = localStorage.getItem('token');
  console.log('检查认证状态，token:', token ? '存在' : '不存在');
  if (token) {
    console.log('Token前10个字符:', token.substring(0, 10));
  }
  if (!token) {
    message.warning('请先登录后访问传感器数据');
    router.push('/login');
    return false;
  }
  return true;
};

const fetchDevices = async () => {
  if (!checkAuth()) return;
  
  try {
    loading.value = true;
    console.log('开始获取设备列表...');
    const response = await deviceApi.getDevices();
    
    let deviceList: any[] = [];
    if (response && response.success && response.data) {
      deviceList = Array.isArray(response.data) ? response.data : [];
    } else if (Array.isArray(response)) {
      deviceList = response;
    } else if (response && response.data && Array.isArray(response.data)) {
      deviceList = response.data;
    } else {
      console.warn('设备响应格式异常:', response);
      deviceList = [];
    }
    
    devices.value = deviceList;
    console.log('获取设备成功:', devices.value);
    console.log('设备数量:', devices.value.length);
    
    // 如果没有设备，在开发模式下创建测试设备
    if (devices.value.length === 0 && import.meta.env.DEV) {
      console.log('没有设备，创建测试设备');
      devices.value = [
        {
          id: '111',
          name: 'TEST_DEVICE',
          type: 'sensor_device',
          location: '测试区域',
          status: 'online' as const,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
      message.info('使用测试设备数据');
    }
  } catch (error) {
    console.error('获取设备列表失败:', error);
    if ((error as any).response?.status === 401) {
      message.error('登录已过期，请重新登录');
      router.push('/login');
    } else {
      message.error('获取设备列表失败，请检查网络连接');
      
      // 在开发模式下提供测试数据
      if (import.meta.env.DEV) {
        console.log('API失败，使用测试设备数据');
        devices.value = [
          {
            id: '111',
            name: 'TEST_DEVICE',
            type: 'sensor_device',
            location: '测试区域',
            status: 'online' as const,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ];
        message.info('网络连接失败，使用测试设备数据');
      }
    }
  } finally {
    loading.value = false;
  }
};

const fetchSensors = async (deviceId: string) => {
  if (!checkAuth()) return;
  
  try {
    console.log('开始获取传感器列表，设备ID:', deviceId);
    console.log('API调用前的token检查...');
    const token = localStorage.getItem('token');
    console.log('当前token:', token ? '存在' : '不存在');
    
    const response = await sensorsApi.getSensors();
    console.log('传感器API响应状态成功');
    console.log('传感器API原始响应:', response);
    console.log('响应类型:', typeof response);
    console.log('是否为数组:', Array.isArray(response));
    
    // 检查响应数据结构 - 修复：直接使用response或response.data
    let allSensors = [];
    if (Array.isArray(response)) {
      // 如果response直接是数组
      allSensors = response;
      console.log('响应直接是传感器数组');
    } else if (response && response.data && Array.isArray(response.data)) {
      // 如果response.data是数组
      allSensors = response.data;
      console.log('响应的data字段是传感器数组');
    } else if (response && response.success && response.data && Array.isArray(response.data)) {
      // 如果是标准API响应格式
      allSensors = response.data;
      console.log('标准API响应格式');
    } else {
      console.error('无法识别的响应格式:', response);
      // 如果获取不到真实数据，创建一些测试数据
      message.info('无法获取传感器数据，使用测试数据');
      allSensors = [
        {
          id: 1,
          name: 'TEST_DEVICE (111)',
          device_id: parseInt(deviceId),
          sensor_type: 'soil_temperature',
          unit: '°C',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
    }
    
    console.log('所有传感器数量:', allSensors.length);
    console.log('传感器示例(前3个):', allSensors.slice(0, 3));
    
    // 检查传感器的device_id字段
    if (allSensors.length > 0) {
      console.log('第一个传感器的完整数据:', allSensors[0]);
      console.log('第一个传感器的device_id:', allSensors[0].device_id, '类型:', typeof allSensors[0].device_id);
    }
    
    sensors.value = allSensors.filter(sensor => {
      const deviceIdNum = parseInt(deviceId);
      const match = sensor.device_id === deviceIdNum;
      console.log(`传感器 ${sensor.id} (${sensor.name}) device_id:${sensor.device_id}(${typeof sensor.device_id}) vs 目标:${deviceIdNum}(${typeof deviceIdNum}) = ${match}`);
      return match;
    });
    
    console.log('过滤后的传感器:', sensors.value);
    console.log(`设备 ${deviceId} 的传感器数量:`, sensors.value.length);
    
    // 如果没有找到传感器，给出提示
    if (sensors.value.length === 0) {
      message.warning('该设备暂无传感器数据');
    }
  } catch (error) {
    console.error('获取传感器列表失败 - 详细错误:', error);
    message.error('获取传感器列表失败，请检查网络连接或重新登录');
    
    // 如果API调用失败，可以创建一些测试数据进行测试
    if (import.meta.env.DEV) {
      console.log('开发模式：创建测试传感器数据');
      sensors.value = [
        {
          id: 1,
          name: 'TEST_DEVICE (111)',
          device_id: parseInt(deviceId),
          sensor_type: 'soil_temperature',
          unit: '°C',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
      message.info('使用测试传感器数据');
    }
  }
};

const fetchSensorData = async () => {
  if (!selectedSensor.value) {
    console.log('没有选择传感器，跳过数据获取');
    return;
  }

  try {
    chartLoading.value = true;
    console.log('开始获取传感器数据，传感器ID:', selectedSensor.value);
    
    // 计算时间范围
    const endTime = dayjs();
    let startTime = dayjs();
    
    switch (timeRange.value) {
      case '1h':
        startTime = endTime.subtract(1, 'hour');
        break;
      case '6h':
        startTime = endTime.subtract(6, 'hour');
        break;
      case '24h':
        startTime = endTime.subtract(24, 'hour');
        break;
      case '7d':
        startTime = endTime.subtract(7, 'day');
        break;
      case '30d':
        startTime = endTime.subtract(30, 'day');
        break;
    }
    
    const params = {
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      per_page: 1000 // 获取足够多的数据点
    };
    
    console.log('请求参数:', params);
    const response = await sensorsApi.getSensorReadings(selectedSensor.value, params);
    console.log('传感器数据API响应:', response);
    
    // 处理API响应数据
    let readings: any[] = [];
    if (response && response.success && response.data) {
      readings = Array.isArray(response.data) ? response.data : [];
    } else if (Array.isArray(response)) {
      readings = response;
    } else {
      console.warn('传感器数据响应格式异常:', response);
      readings = [];
    }
    
    console.log('处理后的传感器读数:', readings);
    console.log('读数数量:', readings.length);
    
    // 确保数据格式正确，转换为SensorData格式
    sensorData.value = readings.map(item => ({
      id: item.id || 0,
      sensor_id: item.sensor_id || selectedSensor.value || 0,
      value: Number(item.value) || 0,
      timestamp: item.timestamp || new Date().toISOString(),
      data_type: item.data_type || 'sensor_reading',
      unit: item.unit || '',
      created_at: item.created_at || new Date().toISOString()
    }));
    
    console.log('格式化后的传感器数据:', sensorData.value);
    
    // 更新当前数据
    if (sensorData.value.length > 0) {
      const latest = sensorData.value[sensorData.value.length - 1];
      const values = sensorData.value.map(item => Number(item.value) || 0);
      
      currentData.value = latest.value;
      currentData.unit = latest.unit || '';
      currentData.average = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
      
      if (sensorData.value.length > 1) {
        const previous = sensorData.value[sensorData.value.length - 2];
        currentData.change = latest.value - previous.value;
      } else {
        currentData.change = 0;
      }
      
      // 更新统计数据
      statistics.max = values.length > 0 ? Math.max(...values) : 0;
      statistics.min = values.length > 0 ? Math.min(...values) : 0;
      statistics.avg = currentData.average;
      statistics.std = values.length > 1 ? Math.sqrt(
        values.reduce((acc, val) => acc + Math.pow(val - statistics.avg, 2), 0) / values.length
      ) : 0;
      statistics.count = values.length;
      statistics.lastUpdate = latest.timestamp;
      
      console.log('更新后的当前数据:', currentData);
      console.log('更新后的统计数据:', statistics);
    } else {
      console.log('没有传感器数据，重置为初始状态');
      // 重置数据
      currentData.value = null;
      currentData.unit = '';
      currentData.average = null;
      currentData.change = 0;
      
      statistics.max = 0;
      statistics.min = 0;
      statistics.avg = 0;
      statistics.std = 0;
      statistics.count = 0;
      statistics.lastUpdate = '';
    }
  } catch (error) {
    console.error('获取传感器数据失败 - 详细错误:', error);
    message.error('获取传感器数据失败，请检查网络连接');
    
    // 在开发模式下，如果API调用失败，生成一些测试数据
    if (import.meta.env.DEV) {
      console.log('开发模式：生成测试传感器数据');
      const now = dayjs();
      const testData = [];
      
      // 生成最近24小时的测试数据
      for (let i = 0; i < 24; i++) {
        const timestamp = now.subtract(i, 'hour').toISOString();
        const value = 20 + Math.random() * 10; // 20-30之间的随机值
        testData.unshift({
          id: i + 1,
          sensor_id: selectedSensor.value || 1,
          value: Number(value.toFixed(2)),
          timestamp: timestamp,
          data_type: 'sensor_reading',
          unit: '°C',
          created_at: timestamp
        });
      }
      
      sensorData.value = testData;
      
      // 更新当前数据
      if (sensorData.value.length > 0) {
        const latest = sensorData.value[sensorData.value.length - 1];
        const values = sensorData.value.map(item => Number(item.value) || 0);
        
        currentData.value = latest.value;
        currentData.unit = latest.unit || '°C';
        currentData.average = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
        
        if (sensorData.value.length > 1) {
          const previous = sensorData.value[sensorData.value.length - 2];
          currentData.change = latest.value - previous.value;
        } else {
          currentData.change = 0;
        }
        
        // 更新统计数据
        statistics.max = values.length > 0 ? Math.max(...values) : 0;
        statistics.min = values.length > 0 ? Math.min(...values) : 0;
        statistics.avg = currentData.average;
        statistics.std = values.length > 1 ? Math.sqrt(
          values.reduce((acc, val) => acc + Math.pow(val - statistics.avg, 2), 0) / values.length
        ) : 0;
        statistics.count = values.length;
        statistics.lastUpdate = latest.timestamp;
      }
      
      message.info('使用测试数据');
    } else {
      // 重置数据
      sensorData.value = [];
      currentData.value = null;
      currentData.unit = '';
      currentData.average = null;
      currentData.change = 0;
    }
  } finally {
    chartLoading.value = false;
  }
};

const handleLocationChange = (location: string) => {
  console.log('地点选择改变:', location);
  selectedDevice.value = null;
  selectedSensor.value = null;
  sensors.value = [];
  sensorData.value = [];
  
  // 清空当前数据
  currentData.value = null;
  currentData.unit = '';
  currentData.average = null;
  currentData.change = 0;
};

const handleDeviceChange = (deviceId: string) => {
  console.log('设备选择改变:', deviceId);
  selectedSensor.value = null;
  sensors.value = [];
  sensorData.value = [];
  
  // 清空当前数据
  currentData.value = null;
  currentData.unit = '';
  currentData.average = null;
  currentData.change = 0;
  
  if (deviceId) {
    fetchSensors(deviceId);
  }
};

const handleSensorChange = () => {
  console.log('传感器选择改变，选中的传感器ID:', selectedSensor.value);
  if (selectedSensor.value) {
    fetchSensorData();
    fetchThresholds();
  } else {
    // 清空数据
    sensorData.value = [];
    currentData.value = null;
    currentData.unit = '';
    currentData.average = null;
    currentData.change = 0;
  }
};

const handleTimeRangeChange = () => {
  fetchSensorData();
};

const handleAutoRefreshChange = (checked: boolean) => {
  if (checked) {
    refreshInterval = setInterval(() => {
      fetchSensorData();
    }, 30000); // 30秒刷新一次
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }
  }
};

const refreshData = () => {
  if (selectedSensor.value) {
    fetchSensorData();
  }
};

const refreshChartData = () => {
  fetchSensorData();
};

const refreshDevices = () => {
  fetchDevices();
};

const exportData = () => {
  if (!sensorData.value.length) {
    message.warning('暂无数据可导出');
    return;
  }

  const csvContent = [
    ['时间', '数值', '单位'],
    ...sensorData.value.map(item => [
      dayjs(item.timestamp).format('YYYY-MM-DD HH:mm:ss'),
      item.value,
      item.unit || ''
    ])
  ].map(row => row.join(',')).join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `sensor_data_${selectedSensor.value}_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;
  link.click();
  
  message.success('数据导出成功');
};

const fetchThresholds = async () => {
  if (!selectedSensor.value) return;

  try {
    // 阈值功能暂时注释
    // const response = await sensorApi.getSensorThresholds(selectedSensor.value);
    // Object.assign(thresholds, response.data);
  } catch (error) {
    console.error('获取阈值设置失败:', error);
  }
};

const handleThresholdChange = () => {
  // 阈值变化时的处理
};

const saveThresholds = async () => {
  if (!selectedSensor.value) return;

  try {
    // await sensorApi.updateSensorThresholds(selectedSensor.value, thresholds);
    message.success('阈值设置保存成功');
  } catch (error) {
    message.error('阈值设置保存失败');
  }
};

const resetThresholds = () => {
  thresholds.max = null;
  thresholds.min = null;
};

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

// 生命周期
onMounted(() => {
  fetchDevices();
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<style lang="less" scoped>
.sensors-page {
  .page-header {
    margin-bottom: 16px;
    
    h1 {
      margin: 0;
      font-size: 24px;
      color: #262626;
    }
    
    .page-description {
      margin: 4px 0 0 0;
      color: #8c8c8c;
    }
  }

  .device-selector {
    margin-bottom: 16px;
  }

  .realtime-cards {
    margin-bottom: 16px;
  }

  .empty-state {
    margin-top: 40px;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .sensors-page {
    .device-selector {
      :deep(.ant-row) {
        flex-direction: column;
        gap: 12px;
        
        .ant-col {
          width: 100% !important;
          flex: none !important;
        }
      }
    }
  }
}
</style>
