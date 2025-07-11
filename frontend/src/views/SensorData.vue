<template>
  <div class="sensor-data-page">
    <div class="page-header">
      <h2>传感器数据</h2>
      <div class="header-actions">
        <el-select
          v-model="selectedSensor"
          placeholder="选择传感器"
          style="width: 200px; margin-right: 10px"
          @change="onSensorChange"
        >
          <el-option
            v-for="sensor in sensorsStore.sensors"
            :key="sensor.id"
            :label="sensor.name"
            :value="sensor.id"
          />
        </el-select>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div v-if="selectedSensor" class="sensor-content">
      <!-- 传感器信息 -->
      <el-card class="sensor-info-card">
        <template #header>
          <div class="card-header">
            <span>传感器信息</span>
          </div>
        </template>

        <div v-if="currentSensor" class="sensor-info">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="6">
              <div class="info-item">
                <span class="label">传感器名称：</span>
                <span class="value">{{ currentSensor.name }}</span>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <div class="info-item">
                <span class="label">类型：</span>
                <span class="value">{{ currentSensor.sensor_type }}</span>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <div class="info-item">
                <span class="label">单位：</span>
                <span class="value">{{ currentSensor.unit }}</span>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <div class="info-item">
                <span class="label">状态：</span>
                <el-tag :type="currentSensor.is_active ? 'success' : 'danger'" size="small">
                  {{ currentSensor.is_active ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 实时数据 -->
      <el-card class="realtime-card">
        <template #header>
          <div class="card-header">
            <span>实时数据</span>
            <el-button size="small" @click="refreshLatestData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div class="realtime-content">
          <div class="realtime-value">
            <div class="value">{{ latestValue || '--' }}</div>
            <div class="unit">{{ currentSensor?.unit || '' }}</div>
          </div>
          <div class="realtime-info">
            <div class="time">{{ latestTime || '暂无数据' }}</div>
            <div class="status">
              <el-tag :type="getValueStatus(latestValue)" size="small">
                {{ getValueStatusText(latestValue) }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 数据图表 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>数据趋势</span>
            <div class="time-range-selector">
              <el-radio-group v-model="timeRange" @change="onTimeRangeChange">
                <el-radio-button value="1h">1小时</el-radio-button>
                <el-radio-button value="6h">6小时</el-radio-button>
                <el-radio-button value="24h">24小时</el-radio-button>
                <el-radio-button value="7d">7天</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>

        <div class="chart-container">
          <v-chart
            :option="chartOption"
            :loading="chartLoading"
            style="height: 400px;"
          />
        </div>
      </el-card>

      <!-- 数据表格 -->
      <el-card class="data-table-card">
        <template #header>
          <div class="card-header">
            <span>历史数据</span>
            <div class="header-actions">
              <el-button size="small" @click="exportData">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button size="small" @click="showAddDataDialog = true">
                <el-icon><Plus /></el-icon>
                添加数据
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="sensorsStore.sensorReadings"
          :loading="sensorsStore.isLoading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="value" label="数值" width="120">
            <template #default="scope">
              {{ formatNumber(scope.row.value) }} {{ currentSensor?.unit }}
            </template>
          </el-table-column>
          <el-table-column prop="timestamp" label="时间戳" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getValueStatus(scope.row.value)" size="small">
                {{ getValueStatusText(scope.row.value) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100, 200]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>

      <!-- 数据统计 -->
      <el-card class="statistics-card">
        <template #header>
          <div class="card-header">
            <span>数据统计</span>
            <el-button size="small" @click="refreshStatistics">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div class="statistics-content">
          <div class="stat-item">
            <div class="stat-label">总数据量</div>
            <div class="stat-value">{{ statistics.count || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">平均值</div>
            <div class="stat-value">{{ formatNumber(statistics.avg || 0) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">最小值</div>
            <div class="stat-value">{{ formatNumber(statistics.min || 0) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">最大值</div>
            <div class="stat-value">{{ formatNumber(statistics.max || 0) }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">标准差</div>
            <div class="stat-value">{{ formatNumber(statistics.std || 0) }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 未选择传感器 -->
    <div v-else class="no-sensor-selected">
      <el-empty description="请选择一个传感器查看数据" />
    </div>

    <!-- 添加数据对话框 -->
    <el-dialog
      v-model="showAddDataDialog"
      title="添加数据"
      width="500px"
      @close="resetDataForm"
    >
      <el-form
        ref="dataFormRef"
        :model="dataForm"
        :rules="dataRules"
        label-width="80px"
      >
        <el-form-item label="数值" prop="value">
          <el-input-number
            v-model="dataForm.value"
            :precision="2"
            style="width: 100%"
            placeholder="请输入数值"
          />
        </el-form-item>
        <el-form-item label="时间戳" prop="timestamp">
          <el-date-picker
            v-model="dataForm.timestamp"
            type="datetime"
            placeholder="选择时间"
            style="width: 100%"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDataDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="submitData"
          >
            添加
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { use } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { useSensorsStore } from '../stores/sensors';
import { formatDateTime, formatNumber } from '../utils';
import type { Sensor } from '../types';

// 注册ECharts组件
use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  LineChart,
  CanvasRenderer
]);

const sensorsStore = useSensorsStore();

const selectedSensor = ref<number | null>(null);
const timeRange = ref('24h');
const currentPage = ref(1);
const pageSize = ref(50);
const totalCount = ref(0);
const chartLoading = ref(false);
const showAddDataDialog = ref(false);
const submitLoading = ref(false);
const dataFormRef = ref<FormInstance>();

// 当前传感器信息
const currentSensor = ref<Sensor | null>(null);
const latestValue = ref<number | null>(null);
const latestTime = ref<string | null>(null);

// 数据统计
const statistics = reactive({
  count: 0,
  avg: 0,
  min: 0,
  max: 0,
  std: 0
});

// 添加数据表单
const dataForm = reactive({
  value: null as number | null,
  timestamp: ''
});

// 数据表单验证规则
const dataRules: FormRules = {
  value: [
    { required: true, message: '请输入数值', trigger: 'blur' }
  ]
};

// 图表配置
const chartOption = computed(() => ({
  title: {
    text: `${currentSensor.value?.name || '传感器'} 数据趋势`,
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
    },
    formatter: (params: any) => {
      const param = params[0];
      return `${param.name}<br/>${param.seriesName}: ${param.value} ${currentSensor.value?.unit || ''}`;
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'time',
    boundaryGap: false
  },
  yAxis: {
    type: 'value',
    name: currentSensor.value?.unit || ''
  },
  dataZoom: [
    {
      type: 'slider',
      start: 0,
      end: 100
    }
  ],
  series: [
    {
      name: currentSensor.value?.name || '数值',
      type: 'line',
      data: sensorsStore.sensorReadings.map(reading => [
        reading.timestamp,
        reading.value
      ]),
      smooth: true,
      lineStyle: {
        color: '#409EFF'
      },
      areaStyle: {
        color: 'rgba(64, 158, 255, 0.1)'
      }
    }
  ]
}));

// 获取数值状态
const getValueStatus = (value: number | null) => {
  if (value === null || value === undefined) return 'info';
  if (!currentSensor.value) return 'info';
  
  const { min_value, max_value } = currentSensor.value;
  
  if (min_value !== null && min_value !== undefined && value < min_value) {
    return 'danger';
  }
  if (max_value !== null && max_value !== undefined && value > max_value) {
    return 'danger';
  }
  
  return 'success';
};

// 获取数值状态文本
const getValueStatusText = (value: number | null) => {
  if (value === null || value === undefined) return '无数据';
  
  const status = getValueStatus(value);
  switch (status) {
    case 'success':
      return '正常';
    case 'danger':
      return '异常';
    default:
      return '未知';
  }
};

// 传感器改变
const onSensorChange = async (sensorId: number) => {
  await loadSensorData(sensorId);
};

// 时间范围改变
const onTimeRangeChange = async () => {
  if (selectedSensor.value) {
    await loadSensorReadings(selectedSensor.value);
  }
};

// 页面大小改变
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  if (selectedSensor.value) {
    loadSensorReadings(selectedSensor.value);
  }
};

// 当前页改变
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  if (selectedSensor.value) {
    loadSensorReadings(selectedSensor.value);
  }
};

// 加载传感器数据
const loadSensorData = async (sensorId: number) => {
  try {
    // 获取传感器详情
    const sensor = await sensorsStore.fetchSensor(sensorId);
    currentSensor.value = sensor || null;
    
    // 获取最新数据
    await refreshLatestData();
    
    // 获取历史数据
    await loadSensorReadings(sensorId);
    
    // 获取统计数据
    await refreshStatistics();
  } catch (error) {
    console.error('加载传感器数据失败:', error);
  }
};

// 加载传感器读数
const loadSensorReadings = async (sensorId: number) => {
  chartLoading.value = true;
  try {
    const params = {
      limit: pageSize.value,
      // 根据时间范围设置开始时间
      start_time: getStartTime(),
      end_time: new Date().toISOString()
    };
    
    await sensorsStore.fetchSensorReadings(sensorId, params);
  } catch (error) {
    console.error('加载传感器读数失败:', error);
  } finally {
    chartLoading.value = false;
  }
};

// 获取开始时间
const getStartTime = () => {
  const now = new Date();
  switch (timeRange.value) {
    case '1h':
      return new Date(now.getTime() - 60 * 60 * 1000).toISOString();
    case '6h':
      return new Date(now.getTime() - 6 * 60 * 60 * 1000).toISOString();
    case '24h':
      return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    case '7d':
      return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
    default:
      return new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
  }
};

// 刷新数据
const refreshData = async () => {
  if (selectedSensor.value) {
    await loadSensorData(selectedSensor.value);
  }
};

// 刷新最新数据
const refreshLatestData = async () => {
  if (!selectedSensor.value) return;
  
  try {
    // 这里应该调用获取最新数据的API
    // 暂时从读数列表获取最新数据
    const readings = sensorsStore.sensorReadings;
    if (readings.length > 0) {
      const latest = readings[0];
      latestValue.value = latest.value;
      latestTime.value = formatDateTime(latest.timestamp);
    }
  } catch (error) {
    console.error('刷新最新数据失败:', error);
  }
};

// 刷新统计数据
const refreshStatistics = async () => {
  if (!selectedSensor.value) return;
  
  try {
    // 这里应该调用获取统计数据的API
    // 暂时从读数列表计算统计数据
    const readings = sensorsStore.sensorReadings;
    if (readings.length > 0) {
      const values = readings.map(r => r.value);
      statistics.count = values.length;
      statistics.avg = values.reduce((a, b) => a + b, 0) / values.length;
      statistics.min = Math.min(...values);
      statistics.max = Math.max(...values);
      
      // 计算标准差
      const mean = statistics.avg;
      const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
      statistics.std = Math.sqrt(variance);
    }
  } catch (error) {
    console.error('刷新统计数据失败:', error);
  }
};

// 导出数据
const exportData = () => {
  // 实现数据导出逻辑
  ElMessage.info('导出功能开发中...');
};

// 提交数据
const submitData = async () => {
  if (!dataFormRef.value || !selectedSensor.value) return;
  
  try {
    await dataFormRef.value.validate();
    submitLoading.value = true;
    
    const readingData = {
      value: dataForm.value!,
      timestamp: dataForm.timestamp || new Date().toISOString()
    };
    
    await sensorsStore.addSensorReading(selectedSensor.value, readingData);
    ElMessage.success('数据添加成功');
    
    showAddDataDialog.value = false;
    resetDataForm();
    
    // 刷新数据
    await refreshData();
  } catch (error: any) {
    ElMessage.error(error.message || '添加数据失败');
  } finally {
    submitLoading.value = false;
  }
};

// 重置数据表单
const resetDataForm = () => {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
  }
  
  dataForm.value = null;
  dataForm.timestamp = '';
};

// 页面加载时获取传感器列表
onMounted(async () => {
  await sensorsStore.fetchSensors();
  
  // 如果有传感器，默认选择第一个
  if (sensorsStore.sensors.length > 0) {
    selectedSensor.value = sensorsStore.sensors[0].id;
    await loadSensorData(selectedSensor.value);
  }
});
</script>

<style scoped>
.sensor-data-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
}

.sensor-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sensor-info-card,
.realtime-card,
.chart-card,
.data-table-card,
.statistics-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.info-item .label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.info-item .value {
  color: #333;
  flex: 1;
}

.realtime-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
}

.realtime-value {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.realtime-value .value {
  font-size: 48px;
  font-weight: bold;
  color: #409EFF;
}

.realtime-value .unit {
  font-size: 18px;
  color: #666;
}

.realtime-info {
  text-align: right;
}

.realtime-info .time {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.time-range-selector {
  display: flex;
  align-items: center;
}

.chart-container {
  height: 400px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.statistics-content {
  display: flex;
  justify-content: space-around;
  padding: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.no-sensor-selected {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 768px) {
  .sensor-data-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }
  
  .header-actions .el-select {
    width: 100% !important;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .realtime-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .realtime-info {
    text-align: center;
  }
  
  .statistics-content {
    flex-direction: column;
    gap: 20px;
  }
}
</style>
