<template>
  <div class="modern-dashboard">
    <!-- 顶部状态栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1 class="dashboard-title">
          <el-icon class="title-icon"><HomeFilled /></el-icon>
          AgriNex 智慧农场
        </h1>
        <div class="weather-widget">
          <el-icon class="weather-icon"><Sunny /></el-icon>
          <span class="weather-temp">22°C</span>
          <span class="weather-desc">晴朗</span>
        </div>
      </div>
      <div class="header-right">
        <div class="time-display">
          <div class="current-time">{{ currentTime }}</div>
          <div class="current-date">{{ currentDate }}</div>
        </div>
        <el-button 
          type="primary" 
          :icon="Refresh" 
          @click="refreshDashboard"
          :loading="isRefreshing"
          class="refresh-btn"
        >
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 关键指标卡片 -->
    <div class="metrics-grid">
      <div class="metric-card primary">
        <div class="metric-header">
          <el-icon class="metric-icon"><Monitor /></el-icon>
          <span class="metric-label">设备总数</span>
        </div>
        <div class="metric-value">{{ dashboardStore.stats.devices?.total || 24 }}</div>
        <div class="metric-trend">
          <el-icon class="trend-icon up"><ArrowUp /></el-icon>
          <span>较昨日 +2</span>
        </div>
      </div>

      <div class="metric-card success">
        <div class="metric-header">
          <el-icon class="metric-icon"><Connection /></el-icon>
          <span class="metric-label">在线设备</span>
        </div>
        <div class="metric-value">{{ dashboardStore.stats.devices?.online || 22 }}</div>
        <div class="metric-trend">
          <el-icon class="trend-icon up"><ArrowUp /></el-icon>
          <span>在线率 92%</span>
        </div>
      </div>

      <div class="metric-card warning">
        <div class="metric-header">
          <el-icon class="metric-icon"><Warning /></el-icon>
          <span class="metric-label">活跃告警</span>
        </div>
        <div class="metric-value">{{ dashboardStore.stats.alarms?.active || 3 }}</div>
        <div class="metric-trend">
          <el-icon class="trend-icon down"><ArrowDown /></el-icon>
          <span>较昨日 -2</span>
        </div>
      </div>

      <div class="metric-card info">
        <div class="metric-header">
          <el-icon class="metric-icon"><DataAnalysis /></el-icon>
          <span class="metric-label">今日数据</span>
        </div>
        <div class="metric-value">{{ formatNumber(dashboardStore.stats.data_points || 12580) }}</div>
        <div class="metric-trend">
          <el-icon class="trend-icon up"><ArrowUp /></el-icon>
          <span>采集正常</span>
        </div>
      </div>

      <div class="metric-card special">
        <div class="metric-header">
          <el-icon class="metric-icon"><MagicStick /></el-icon>
          <span class="metric-label">AI预测</span>
        </div>
        <div class="metric-value">95%</div>
        <div class="metric-trend">
          <el-icon class="trend-icon up"><ArrowUp /></el-icon>
          <span>准确率</span>
        </div>
      </div>

      <div class="metric-card energy">
        <div class="metric-header">
          <el-icon class="metric-icon"><Lightning /></el-icon>
          <span class="metric-label">能耗效率</span>
        </div>
        <div class="metric-value">87%</div>
        <div class="metric-trend">
          <el-icon class="trend-icon up"><ArrowUp /></el-icon>
          <span>优化中</span>
        </div>
      </div>
    </div>

    <!-- 环境实时监控 -->
    <div class="environment-section">
      <div class="section-header">          <h2 class="section-title">
            <el-icon><Timer /></el-icon>
            环境实时监控
          </h2>
        <div class="time-selector">
          <el-radio-group v-model="timeRange" size="small" @change="updateChartData">
            <el-radio-button value="1h">1小时</el-radio-button>
            <el-radio-button value="6h">6小时</el-radio-button>
            <el-radio-button value="24h">24小时</el-radio-button>
            <el-radio-button value="7d">7天</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div class="environment-cards">
        <div class="env-card temperature">
          <div class="env-header">
            <el-icon class="env-icon"><Timer /></el-icon>
            <span class="env-title">温度</span>
          </div>
          <div class="env-value">22.5°C</div>
          <div class="env-status optimal">
            <el-icon><Select /></el-icon>
            <span>适宜</span>
          </div>
          <div class="env-chart">
            <v-chart :option="temperatureSparkline" style="height: 60px;" />
          </div>
        </div>

        <div class="env-card humidity">
          <div class="env-header">
            <el-icon class="env-icon"><Drizzling /></el-icon>
            <span class="env-title">湿度</span>
          </div>
          <div class="env-value">65%</div>
          <div class="env-status optimal">
            <el-icon><Select /></el-icon>
            <span>适宜</span>
          </div>
          <div class="env-chart">
            <v-chart :option="humiditySparkline" style="height: 60px;" />
          </div>
        </div>

        <div class="env-card soil">
          <div class="env-header">
            <el-icon class="env-icon"><GoldMedal /></el-icon>
            <span class="env-title">土壤湿度</span>
          </div>
          <div class="env-value">58%</div>
          <div class="env-status warning">
            <el-icon><Warning /></el-icon>
            <span>偏低</span>
          </div>
          <div class="env-chart">
            <v-chart :option="soilSparkline" style="height: 60px;" />
          </div>
        </div>

        <div class="env-card light">
          <div class="env-header">
            <el-icon class="env-icon"><Sunny /></el-icon>
            <span class="env-title">光照</span>
          </div>
          <div class="env-value">25k Lux</div>
          <div class="env-status optimal">
            <el-icon><Select /></el-icon>
            <span>良好</span>
          </div>
          <div class="env-chart">
            <v-chart :option="lightSparkline" style="height: 60px;" />
          </div>
        </div>
      </div>      </div>
    </div>

    <!-- 主要图表区域 -->
    <div class="charts-section">
      <div class="chart-container large">
        <div class="chart-header">
          <h3 class="chart-title">环境数据趋势分析</h3>
          <div class="chart-controls">
            <el-select v-model="selectedSensors" multiple size="small" style="width: 200px;">
              <el-option label="温度" value="temperature" />
              <el-option label="湿度" value="humidity" />
              <el-option label="土壤湿度" value="soil" />
              <el-option label="光照" value="light" />
            </el-select>
          </div>
        </div>
        <div class="chart-content">
          <v-chart 
            :option="mainTrendChart" 
            :loading="chartLoading"
            style="height: 400px;" 
            @click="onChartClick"
          />
        </div>
      </div>

      <div class="chart-container medium">
        <div class="chart-header">
          <h3 class="chart-title">设备运行状态</h3>
        </div>
        <div class="chart-content">
          <v-chart :option="deviceStatusChart" style="height: 300px;" />
        </div>
      </div>

      <div class="chart-container medium">
        <div class="chart-header">
          <h3 class="chart-title">告警分析</h3>
        </div>
        <div class="chart-content">
          <v-chart :option="alarmAnalysisChart" style="height: 300px;" />
        </div>
      </div>
    </div>

    <!-- 设备状态和告警信息 -->
    <div class="info-section">
      <div class="info-card devices">
        <div class="info-header">
          <h3 class="info-title">
            <el-icon><Monitor /></el-icon>
            设备状态
          </h3>
          <el-button size="small" text @click="refreshDevices">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="info-content">
          <div class="device-list">
            <div class="device-item" v-for="device in mockDevices" :key="device.id">
              <div class="device-info">
                <el-icon class="device-icon" :class="device.status">
                  <Monitor v-if="device.type === 'sensor'" />
                  <Camera v-if="device.type === 'camera'" />
                  <Connection v-if="device.type === 'gateway'" />
                </el-icon>
                <div class="device-details">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-meta">{{ device.location }} • {{ device.lastUpdate }}</div>
                </div>
              </div>
              <el-tag :type="device.status === 'online' ? 'success' : 'danger'" size="small">
                {{ device.status === 'online' ? '在线' : '离线' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <div class="info-card alarms">
        <div class="info-header">
          <h3 class="info-title">
            <el-icon><Warning /></el-icon>
            实时告警
          </h3>
          <el-button size="small" text @click="refreshAlarms">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </div>
        <div class="info-content">
          <div class="alarm-list">
            <div class="alarm-item" v-for="alarm in mockAlarms" :key="alarm.id">
              <div class="alarm-info">
                <el-icon class="alarm-icon" :class="alarm.level">
                  <Warning v-if="alarm.level === 'high'" />
                  <InfoFilled v-if="alarm.level === 'medium'" />
                  <CircleCheck v-if="alarm.level === 'low'" />
                </el-icon>
                <div class="alarm-details">
                  <div class="alarm-title">{{ alarm.title }}</div>
                  <div class="alarm-time">{{ alarm.time }}</div>
                </div>
              </div>
              <el-button size="small" text type="primary">处理</el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="info-card activities">
        <div class="info-header">
          <h3 class="info-title">
            <el-icon><Clock /></el-icon>
            最近活动
          </h3>
        </div>
        <div class="info-content">
          <el-timeline class="activity-timeline">
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.time"
              :type="activity.type"
              size="small"
            >
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-desc">{{ activity.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </div>

    <!-- AI助手快捷操作 -->
    <div class="ai-assistant-section">
      <div class="ai-card">
        <div class="ai-header">
          <div class="ai-avatar">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="ai-info">
            <h3 class="ai-title">AgriNex AI 助手</h3>
            <p class="ai-desc">智能分析 • 预测建议 • 自动优化</p>
          </div>
        </div>
        <div class="ai-insights">
          <div class="insight-item">
            <el-icon class="insight-icon success"><TrendCharts /></el-icon>
            <span>当前环境条件适宜作物生长，预计产量提升 8%</span>
          </div>
          <div class="insight-item">
            <el-icon class="insight-icon warning"><Warning /></el-icon>
            <span>土壤湿度偏低，建议在 2 小时内进行灌溉</span>
          </div>
          <div class="insight-item">
            <el-icon class="insight-icon info"><Opportunity /></el-icon>
            <span>明日天气晴朗，可考虑延长光照时间至 14 小时</span>
          </div>
        </div>
        <div class="ai-actions">
          <el-button type="primary" size="small">
            <el-icon><ChatLineRound /></el-icon>
            智能对话
          </el-button>
          <el-button size="small">
            <el-icon><Document /></el-icon>
            生成报告
          </el-button>
          <el-button size="small">
            <el-icon><Setting /></el-icon>
            自动优化
          </el-button>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue';
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
import { 
  Monitor, Connection, Warning, DataAnalysis, MagicStick, Lightning,
  HomeFilled, Sunny, Refresh, ArrowUp, ArrowDown, Timer,
  Drizzling, GoldMedal, Select, TrendCharts, Opportunity,
  ChatLineRound, Document, Setting, Clock, Camera, InfoFilled,
  CircleCheck
} from '@element-plus/icons-vue';
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

// 响应式状态
const chartTimeRange = ref('24h');
const timeRange = ref('24h');
const selectedSensors = ref(['temperature', 'humidity', 'soil', 'light']);
const chartLoading = ref(false);
const isRefreshing = ref(false);
const currentTime = ref('');
const currentDate = ref('');

// 定时器
let timeTimer: any;

// 格式化数字
const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
};

// 更新时间
const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  currentDate.value = now.toLocaleDateString('zh-CN', { 
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

// 模拟设备数据
const mockDevices = reactive([
  {
    id: 1,
    name: '温室A-温度传感器',
    type: 'sensor',
    status: 'online',
    location: '温室A区',
    lastUpdate: '2分钟前'
  },
  {
    id: 2,
    name: '温室B-摄像头',
    type: 'camera',
    status: 'online',
    location: '温室B区',
    lastUpdate: '1分钟前'
  },
  {
    id: 3,
    name: '中央网关',
    type: 'gateway',
    status: 'offline',
    location: '控制中心',
    lastUpdate: '15分钟前'
  },
  {
    id: 4,
    name: '土壤湿度传感器',
    type: 'sensor',
    status: 'online',
    location: '温室C区',
    lastUpdate: '30秒前'
  }
]);

// 模拟告警数据
const mockAlarms = reactive([
  {
    id: 1,
    title: '土壤湿度过低',
    level: 'high',
    time: '2分钟前'
  },
  {
    id: 2,
    title: '设备离线告警',
    level: 'medium',
    time: '15分钟前'
  },
  {
    id: 3,
    title: '数据采集正常',
    level: 'low',
    time: '1小时前'
  }
]);

// 更新活动数据结构
const recentActivities = reactive([
  {
    id: 1,
    title: '设备状态更新',
    description: '温度传感器#001告警已解决',
    time: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    type: 'success'
  },
  {
    id: 2,
    title: '新设备接入',
    description: '温室监控设备#003已连接',
    time: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    type: 'primary'
  },
  {
    id: 3,
    title: '数据异常',
    description: '湿度传感器#002数据波动',
    time: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    type: 'warning'
  },
  {
    id: 4,
    title: '系统维护',
    description: '自动备份任务完成',
    time: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    type: 'info'
  }
]);

// 生成sparkline数据
const generateSparklineData = (baseValue: number, variance: number) => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push(baseValue + (Math.random() - 0.5) * variance);
  }
  return data;
};

// Sparkline图表配置
const temperatureSparkline = computed(() => ({
  xAxis: { type: 'category', show: false },
  yAxis: { type: 'value', show: false },
  grid: { left: 0, right: 0, top: 0, bottom: 0 },
  series: [{
    type: 'line',
    data: generateSparklineData(22.5, 4),
    smooth: true,
    lineStyle: { color: '#ff6b6b', width: 2 },
    areaStyle: { 
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(255, 107, 107, 0.3)' },
          { offset: 1, color: 'rgba(255, 107, 107, 0.05)' }
        ]
      }
    },
    symbol: 'none'
  }]
}));

const humiditySparkline = computed(() => ({
  xAxis: { type: 'category', show: false },
  yAxis: { type: 'value', show: false },
  grid: { left: 0, right: 0, top: 0, bottom: 0 },
  series: [{
    type: 'line',
    data: generateSparklineData(65, 10),
    smooth: true,
    lineStyle: { color: '#4ecdc4', width: 2 },
    areaStyle: { 
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(78, 205, 196, 0.3)' },
          { offset: 1, color: 'rgba(78, 205, 196, 0.05)' }
        ]
      }
    },
    symbol: 'none'
  }]
}));

const soilSparkline = computed(() => ({
  xAxis: { type: 'category', show: false },
  yAxis: { type: 'value', show: false },
  grid: { left: 0, right: 0, top: 0, bottom: 0 },
  series: [{
    type: 'line',
    data: generateSparklineData(58, 8),
    smooth: true,
    lineStyle: { color: '#f7b731', width: 2 },
    areaStyle: { 
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(247, 183, 49, 0.3)' },
          { offset: 1, color: 'rgba(247, 183, 49, 0.05)' }
        ]
      }
    },
    symbol: 'none'
  }]
}));

const lightSparkline = computed(() => ({
  xAxis: { type: 'category', show: false },
  yAxis: { type: 'value', show: false },
  grid: { left: 0, right: 0, top: 0, bottom: 0 },
  series: [{
    type: 'line',
    data: generateSparklineData(25000, 5000),
    smooth: true,
    lineStyle: { color: '#ffa726', width: 2 },
    areaStyle: { 
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(255, 167, 38, 0.3)' },
          { offset: 1, color: 'rgba(255, 167, 38, 0.05)' }
        ]
      }
    },
    symbol: 'none'
  }]
}));

// 主趋势图表
const mainTrendChart = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' }
  },
  legend: {
    data: ['温度', '湿度', '土壤湿度', '光照'],
    bottom: 10
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '15%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: generateTimeData()
  },
  yAxis: [
    {
      type: 'value',
      name: '温度/湿度',
      position: 'left',
      axisLabel: { formatter: '{value}' }
    },
    {
      type: 'value',
      name: '光照',
      position: 'right',
      axisLabel: { formatter: '{value}' }
    }
  ],
  series: [
    {
      name: '温度',
      type: 'line',
      data: generateTemperatureData(),
      smooth: true,
      lineStyle: { color: '#ff6b6b' }
    },
    {
      name: '湿度',
      type: 'line',
      data: generateHumidityData(),
      smooth: true,
      lineStyle: { color: '#4ecdc4' }
    },
    {
      name: '土壤湿度',
      type: 'line',
      data: generateSoilData(),
      smooth: true,
      lineStyle: { color: '#f7b731' }
    },
    {
      name: '光照',
      type: 'line',
      yAxisIndex: 1,
      data: generateLightData(),
      smooth: true,
      lineStyle: { color: '#ffa726' }
    }
  ]
}));

// 设备状态图表
const deviceStatusChart = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [
    {
      name: '设备状态',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      data: [
        { value: dashboardStore.stats.devices?.online || 22, name: '在线', itemStyle: { color: '#67C23A' } },
        { value: dashboardStore.stats.devices?.offline || 2, name: '离线', itemStyle: { color: '#F56C6C' } },
        { value: dashboardStore.stats.devices?.maintenance || 1, name: '维护', itemStyle: { color: '#E6A23C' } }
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

// 告警分析图表
const alarmAnalysisChart = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' }
  },
  legend: {
    data: ['严重', '警告', '信息']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['今日', '昨日', '本周', '上周']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '严重',
      type: 'bar',
      data: [3, 5, 12, 8],
      itemStyle: { color: '#F56C6C' }
    },
    {
      name: '警告',
      type: 'bar',
      data: [8, 12, 25, 20],
      itemStyle: { color: '#E6A23C' }
    },
    {
      name: '信息',
      type: 'bar',
      data: [15, 20, 45, 35],
      itemStyle: { color: '#409EFF' }
    }
  ]
}));

// 数据生成函数
const generateTimeData = () => {
  const data = [];
  const now = new Date();
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push(time.getHours() + ':00');
  }
  return data;
};

const generateTemperatureData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((20 + Math.random() * 10).toFixed(1));
  }
  return data;
};

const generateHumidityData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((50 + Math.random() * 30).toFixed(1));
  }
  return data;
};

const generateSoilData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((45 + Math.random() * 25).toFixed(1));
  }
  return data;
};

const generateLightData = () => {
  const data = [];
  for (let i = 0; i < 24; i++) {
    data.push((15000 + Math.random() * 20000).toFixed(0));
  }
  return data;
};

// 方法
const updateChartData = () => {
  console.log('时间范围改变:', timeRange.value);
  // 这里可以根据时间范围重新获取数据
};

const onChartClick = (params: any) => {
  console.log('图表点击:', params);
};

const refreshDashboard = async () => {
  isRefreshing.value = true;
  try {
    await dashboardStore.refreshDashboard();
  } finally {
    isRefreshing.value = false;
  }
};

const refreshDevices = async () => {
  await devicesStore.fetchDevices();
};

const refreshAlarms = async () => {
  await alarmsStore.fetchAlarms();
};

// 更改时间范围
const changeTimeRange = (range: string) => {
  chartTimeRange.value = range;
  console.log('时间范围改变:', range);
};

// 刷新系统状态
const refreshSystemStatus = async () => {
  await dashboardStore.fetchSystemStatus();
};

// 页面加载时获取数据
onMounted(async () => {
  updateTime();
  timeTimer = setInterval(updateTime, 1000);
  
  await dashboardStore.refreshDashboard();
  await alarmsStore.fetchAlarms();
  await devicesStore.fetchDevices();
});

onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer);
  }
});
</script>

<style scoped>
/* 现代化Dashboard样式 */
.modern-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 顶部头部 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 20px 30px;
  margin-bottom: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 30px;
}

.dashboard-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title-icon {
  font-size: 32px;
  color: #667eea;
}

.weather-widget {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(103, 194, 58, 0.1);
  border-radius: 20px;
  border: 1px solid rgba(103, 194, 58, 0.2);
}

.weather-icon {
  color: #ffa726;
  font-size: 20px;
}

.weather-temp {
  font-weight: 600;
  font-size: 16px;
  color: #333;
}

.weather-desc {
  color: #666;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.time-display {
  text-align: right;
}

.current-time {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  font-family: 'SF Mono', Consolas, monospace;
}

.current-date {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.refresh-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
}

/* 指标卡片网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.metric-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  border-radius: 20px 20px 0 0;
}

.metric-card.primary::before {
  background: linear-gradient(90deg, #409EFF, #67C23A);
}

.metric-card.success::before {
  background: linear-gradient(90deg, #67C23A, #85ce61);
}

.metric-card.warning::before {
  background: linear-gradient(90deg, #E6A23C, #f56c6c);
}

.metric-card.info::before {
  background: linear-gradient(90deg, #909399, #409EFF);
}

.metric-card.special::before {
  background: linear-gradient(90deg, #c084fc, #7c3aed);
}

.metric-card.energy::before {
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
}

.metric-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.metric-icon {
  font-size: 20px;
  color: #667eea;
}

.metric-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.metric-value {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 12px;
  font-family: 'SF Mono', Consolas, monospace;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.trend-icon {
  font-size: 14px;
}

.trend-icon.up {
  color: #67C23A;
}

.trend-icon.down {
  color: #F56C6C;
}

/* 环境监控区域 */
.environment-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin: 0;
}

.time-selector .el-radio-group {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 4px;
}

.environment-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.env-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.env-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.env-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.env-icon {
  font-size: 18px;
}

.env-title {
  font-weight: 600;
  color: #333;
}

.env-value {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 8px;
  font-family: 'SF Mono', Consolas, monospace;
}

.env-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin-bottom: 16px;
  padding: 4px 8px;
  border-radius: 12px;
  width: fit-content;
}

.env-status.optimal {
  background: rgba(103, 194, 58, 0.1);
  color: #67C23A;
  border: 1px solid rgba(103, 194, 58, 0.2);
}

.env-status.warning {
  background: rgba(230, 162, 60, 0.1);
  color: #E6A23C;
  border: 1px solid rgba(230, 162, 60, 0.2);
}

.env-chart {
  height: 60px;
}

/* 图表区域 */
.charts-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  grid-template-rows: auto auto;
  gap: 20px;
  margin-bottom: 30px;
}

.chart-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-container.large {
  grid-row: span 2;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.chart-controls {
  display: flex;
  gap: 12px;
}

.chart-content {
  padding: 0 24px 24px;
}

/* 信息卡片区域 */
.info-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.info-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.info-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.info-content {
  padding: 0 24px 24px;
}

.device-list, .alarm-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-item, .alarm-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.device-item:hover, .alarm-item:hover {
  background: rgba(0, 0, 0, 0.04);
  transform: translateX(4px);
}

.device-info, .alarm-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-icon, .alarm-icon {
  font-size: 18px;
}

.device-icon.online, .alarm-icon.low {
  color: #67C23A;
}

.device-icon.offline, .alarm-icon.high {
  color: #F56C6C;
}

.alarm-icon.medium {
  color: #E6A23C;
}

.device-details, .alarm-details {
  display: flex;
  flex-direction: column;
}

.device-name, .alarm-title {
  font-weight: 600;
  color: #1a1a1a;
  font-size: 14px;
}

.device-meta, .alarm-time {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.activity-timeline {
  padding: 16px 0;
}

.activity-content {
  padding-left: 8px;
}

.activity-title {
  font-weight: 600;
  color: #1a1a1a;
  font-size: 14px;
  margin-bottom: 4px;
}

.activity-desc {
  font-size: 12px;
  color: #666;
}

/* AI助手区域 */
.ai-assistant-section {
  margin-bottom: 30px;
}

.ai-card {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1), rgba(192, 132, 252, 0.1));
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(124, 58, 237, 0.2);
  box-shadow: 0 8px 32px rgba(124, 58, 237, 0.1);
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.ai-avatar {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #c084fc, #7c3aed);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.ai-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 4px 0;
}

.ai-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.ai-insights {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-size: 14px;
  line-height: 1.5;
}

.insight-icon {
  font-size: 16px;
  margin-top: 2px;
  flex-shrink: 0;
}

.insight-icon.success {
  color: #67C23A;
}

.insight-icon.warning {
  color: #E6A23C;
}

.insight-icon.info {
  color: #409EFF;
}

.ai-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.ai-actions .el-button {
  border-radius: 12px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-section {
    grid-template-columns: 1fr;
  }
  
  .chart-container.large {
    grid-row: span 1;
  }
}

@media (max-width: 768px) {
  .modern-dashboard {
    padding: 10px;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .header-left {
    flex-direction: column;
    gap: 15px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
  
  .environment-cards {
    grid-template-columns: 1fr;
  }
  
  .info-section {
    grid-template-columns: 1fr;
  }
  
  .ai-actions {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .dashboard-title {
    font-size: 24px;
  }
  
  .metric-value {
    font-size: 28px;
  }
  
  .env-value {
    font-size: 24px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.metric-card, .env-card, .chart-container, .info-card, .ai-card {
  animation: fadeInUp 0.6s ease-out;
}

.metric-card:nth-child(1) { animation-delay: 0.1s; }
.metric-card:nth-child(2) { animation-delay: 0.2s; }
.metric-card:nth-child(3) { animation-delay: 0.3s; }
.metric-card:nth-child(4) { animation-delay: 0.4s; }
.metric-card:nth-child(5) { animation-delay: 0.5s; }
.metric-card:nth-child(6) { animation-delay: 0.6s; }
</style>
