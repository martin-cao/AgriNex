<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#409EFF"><Monitor /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">
                {{ dashboardStore.stats.total_devices || 0 }}
              </div>
              <div class="stats-label">总设备数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#67C23A"><Connection /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">
                {{ dashboardStore.stats.online_devices || 0 }}
              </div>
              <div class="stats-label">在线设备</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#F56C6C"><Warning /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">
                {{ dashboardStore.stats.active_alerts || 0 }}
              </div>
              <div class="stats-label">活跃告警</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#E6A23C"><DataAnalysis /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">
                {{ dashboardStore.stats.today_data_points || 0 }}
              </div>
              <div class="stats-label">今日数据点</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <!-- 环境数据趋势图 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>环境数据趋势</span>
              <el-button-group size="small">
                <el-button
                  :type="chartTimeRange === '1h' ? 'primary' : ''"
                  @click="changeTimeRange('1h')"
                >
                  1小时
                </el-button>
                <el-button
                  :type="chartTimeRange === '24h' ? 'primary' : ''"
                  @click="changeTimeRange('24h')"
                >
                  24小时
                </el-button>
                <el-button
                  :type="chartTimeRange === '7d' ? 'primary' : ''"
                  @click="changeTimeRange('7d')"
                >
                  7天
                </el-button>
              </el-button-group>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              :option="trendChartOption" 
              :loading="chartLoading"
              style="height: 300px;"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 设备状态分布 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>设备状态分布</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              :option="deviceStatusChartOption" 
              style="height: 300px;"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 告警统计 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>告警统计</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              :option="alarmChartOption" 
              style="height: 300px;"
            />
          </div>
        </el-card>
      </el-col>

      <!-- 最近活动 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
            </div>
          </template>
          <div class="activity-list">
            <el-timeline>
              <el-timeline-item
                v-for="activity in recentActivities"
                :key="activity.id"
                :timestamp="formatDateTime(activity.timestamp)"
                :type="activity.type"
              >
                {{ activity.message }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统状态 -->
    <el-row :gutter="20" class="system-status-row">
      <el-col :span="24">
        <el-card class="system-status-card">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
              <el-button size="small" @click="refreshSystemStatus">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <div class="system-status-content">
            <div class="status-item">
              <div class="status-label">数据库</div>
              <div class="status-indicator">
                <el-tag :type="dashboardStore.systemStatus.database ? 'success' : 'danger'">
                  {{ dashboardStore.systemStatus.database ? '正常' : '异常' }}
                </el-tag>
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">MQTT服务</div>
              <div class="status-indicator">
                <el-tag :type="dashboardStore.systemStatus.mqtt ? 'success' : 'danger'">
                  {{ dashboardStore.systemStatus.mqtt ? '正常' : '异常' }}
                </el-tag>
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">存储服务</div>
              <div class="status-indicator">
                <el-tag :type="dashboardStore.systemStatus.storage ? 'success' : 'danger'">
                  {{ dashboardStore.systemStatus.storage ? '正常' : '异常' }}
                </el-tag>
              </div>
            </div>
            <div class="status-item">
              <div class="status-label">预测服务</div>
              <div class="status-indicator">
                <el-tag :type="dashboardStore.systemStatus.prediction ? 'success' : 'danger'">
                  {{ dashboardStore.systemStatus.prediction ? '正常' : '异常' }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { use } from 'echarts/core';
import { LineChart, PieChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';
import { useDashboardStore } from '../stores/dashboard';
import { useAlarmsStore } from '../stores/alarms';
import { useDevicesStore } from '../stores/devices';
import { formatDateTime } from '../utils';

// 注册ECharts组件
use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  LineChart,
  PieChart,
  BarChart,
  CanvasRenderer
]);

const dashboardStore = useDashboardStore();
const alarmsStore = useAlarmsStore();
const devicesStore = useDevicesStore();

const chartTimeRange = ref('24h');
const chartLoading = ref(false);

// 最近活动数据
const recentActivities = reactive([
  {
    id: 1,
    message: '设备温度传感器#001告警已解决',
    timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    type: 'success'
  },
  {
    id: 2,
    message: '新增设备：温室监控设备#003',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    type: 'primary'
  },
  {
    id: 3,
    message: '湿度传感器#002数据异常',
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    type: 'warning'
  },
  {
    id: 4,
    message: '系统自动备份完成',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    type: 'info'
  }
]);

// 环境数据趋势图配置
const trendChartOption = computed(() => ({
  title: {
    text: '环境数据趋势',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    }
  },
  legend: {
    data: ['温度', '湿度', '光照强度'],
    top: 30
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: generateTimeData()
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '温度',
      type: 'line',
      data: generateTemperatureData(),
      smooth: true,
      lineStyle: {
        color: '#409EFF'
      }
    },
    {
      name: '湿度',
      type: 'line',
      data: generateHumidityData(),
      smooth: true,
      lineStyle: {
        color: '#67C23A'
      }
    },
    {
      name: '光照强度',
      type: 'line',
      data: generateLightData(),
      smooth: true,
      lineStyle: {
        color: '#E6A23C'
      }
    }
  ]
}));

// 设备状态分布图配置
const deviceStatusChartOption = computed(() => ({
  title: {
    text: '设备状态分布',
    left: 'center'
  },
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    top: 'middle'
  },
  series: [
    {
      name: '设备状态',
      type: 'pie',
      radius: '50%',
      center: ['50%', '50%'],
      data: [
        { value: dashboardStore.stats.online_devices, name: '在线', itemStyle: { color: '#67C23A' } },
        { value: dashboardStore.stats.total_devices - dashboardStore.stats.online_devices, name: '离线', itemStyle: { color: '#F56C6C' } }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
}));

// 告警统计图配置
const alarmChartOption = computed(() => ({
  title: {
    text: '告警统计',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  legend: {
    data: ['严重', '警告', '信息'],
    top: 30
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['本周', '上周', '本月']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '严重',
      type: 'bar',
      data: [5, 3, 8],
      itemStyle: { color: '#F56C6C' }
    },
    {
      name: '警告',
      type: 'bar',
      data: [12, 8, 15],
      itemStyle: { color: '#E6A23C' }
    },
    {
      name: '信息',
      type: 'bar',
      data: [20, 15, 25],
      itemStyle: { color: '#409EFF' }
    }
  ]
}));

// 生成时间数据
const generateTimeData = () => {
  const data = [];
  const now = new Date();
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push(time.getHours() + ':00');
  }
  return data;
};

// 生成温度数据
const generateTemperatureData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((20 + Math.random() * 10).toFixed(1));
  }
  return data;
};

// 生成湿度数据
const generateHumidityData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((50 + Math.random() * 30).toFixed(1));
  }
  return data;
};

// 生成光照数据
const generateLightData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((1000 + Math.random() * 5000).toFixed(0));
  }
  return data;
};

// 更改时间范围
const changeTimeRange = (range: string) => {
  chartTimeRange.value = range;
  // 这里可以根据时间范围重新获取数据
  console.log('时间范围改变:', range);
};

// 刷新系统状态
const refreshSystemStatus = async () => {
  await dashboardStore.fetchSystemStatus();
};

// 页面加载时获取数据
onMounted(async () => {
  await dashboardStore.refreshDashboard();
  await alarmsStore.fetchAlarms();
  await devicesStore.fetchDevices();
});
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.stats-content {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stats-icon {
  font-size: 32px;
  margin-right: 15px;
}

.stats-info {
  flex: 1;
}

.stats-number {
  font-size: 24px;
  font-weight: bold;
  color: var(--agrinex-text-primary);
  margin-bottom: 5px;
}

.stats-label {
  font-size: 14px;
  color: var(--agrinex-text-secondary);
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.chart-container {
  height: 300px;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
}

.system-status-row {
  margin-bottom: 20px;
}

.system-status-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.system-status-content {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 20px;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.status-label {
  font-size: 14px;
  color: var(--agrinex-text-secondary);
  margin-bottom: 10px;
}

.status-indicator {
  font-size: 12px;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 10px;
  }
  
  .stats-content {
    flex-direction: column;
    text-align: center;
  }
  
  .stats-icon {
    margin-right: 0;
    margin-bottom: 10px;
  }
  
  .system-status-content {
    flex-direction: column;
    gap: 15px;
  }
}
</style>
