<template>
  <div class="alarms-page">
    <div class="page-header">
      <h2>告警管理</h2>
      <div class="header-actions">
        <el-select
          v-model="statusFilter"
          placeholder="告警状态"
          style="width: 120px; margin-right: 10px"
          @change="onStatusFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="活跃" value="active" />
          <el-option label="已解决" value="resolved" />
        </el-select>
        <el-button @click="refreshAlarms">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 告警统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#F56C6C"><Warning /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ alarmStats.active }}</div>
              <div class="stats-label">活跃告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ alarmStats.resolved }}</div>
              <div class="stats-label">已解决</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#E6A23C"><Clock /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ alarmStats.total }}</div>
              <div class="stats-label">总告警数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6" :lg="6" :xl="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon color="#F56C6C"><WarnTriangleFilled /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-number">{{ alarmStats.critical }}</div>
              <div class="stats-label">严重告警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警列表 -->
    <el-card class="alarms-card">
      <template #header>
        <div class="card-header">
          <span>告警列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索告警"
              style="width: 200px; margin-right: 10px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="batchResolve" :disabled="!selectedAlarms.length">
              <el-icon><Check /></el-icon>
              批量解决
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredAlarms"
        :loading="alarmsStore.isLoading"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="告警类型" width="120">
          <template #default="scope">
            <el-tag :type="getAlarmLevelType(scope.row.alarm_type)" size="small">
              {{ getAlarmLevelText(scope.row.alarm_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警消息" min-width="200" />
        <el-table-column label="传感器" width="120">
          <template #default="scope">
            传感器#{{ scope.row.sensor_id }}
          </template>
        </el-table-column>
        <el-table-column label="阈值" width="120">
          <template #default="scope">
            {{ formatNumber(scope.row.threshold_value) }}
          </template>
        </el-table-column>
        <el-table-column label="当前值" width="120">
          <template #default="scope">
            {{ formatNumber(scope.row.current_value) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'danger' : 'success'" size="small">
              {{ scope.row.status === 'active' ? '活跃' : '已解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="resolved_at" label="解决时间" width="180">
          <template #default="scope">
            {{ scope.row.resolved_at ? formatDateTime(scope.row.resolved_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'active'"
              type="success"
              size="small"
              @click="resolveAlarm(scope.row)"
            >
              解决
            </el-button>
            <el-button
              v-else
              type="info"
              size="small"
              disabled
            >
              已解决
            </el-button>
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

    <!-- 告警趋势图 -->
    <el-card class="trend-card">
      <template #header>
        <div class="card-header">
          <span>告警趋势</span>
          <el-radio-group v-model="trendTimeRange" @change="refreshTrendData">
            <el-radio-button value="24h">24小时</el-radio-button>
            <el-radio-button value="7d">7天</el-radio-button>
            <el-radio-button value="30d">30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div class="chart-container">
        <v-chart
          :option="trendChartOption"
          :loading="trendLoading"
          style="height: 300px;"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { use } from 'echarts/core';
import { LineChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useAlarmsStore } from '../stores/alarms';
import { formatDateTime, formatNumber, getAlarmLevelColor, getAlarmLevelText } from '../utils';
import type { Alarm } from '../types';

// 注册ECharts组件
use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  LineChart,
  BarChart,
  CanvasRenderer
]);

const alarmsStore = useAlarmsStore();

const searchQuery = ref('');
const statusFilter = ref('');
const currentPage = ref(1);
const pageSize = ref(50);
const totalCount = ref(0);
const selectedAlarms = ref<Alarm[]>([]);
const trendTimeRange = ref('7d');
const trendLoading = ref(false);

// 告警统计数据
const alarmStats = reactive({
  total: 0,
  active: 0,
  resolved: 0,
  critical: 0,
  warning: 0,
  info: 0
});

// 趋势数据
const trendData = reactive({
  dates: [] as string[],
  critical: [] as number[],
  warning: [] as number[],
  info: [] as number[]
});

// 过滤后的告警列表
const filteredAlarms = computed(() => {
  let alarms = alarmsStore.alarms;

  // 状态过滤
  if (statusFilter.value) {
    alarms = alarms.filter(alarm => alarm.status === statusFilter.value);
  }

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    alarms = alarms.filter(alarm =>
      alarm.message.toLowerCase().includes(query) ||
      alarm.alarm_type.toLowerCase().includes(query)
    );
  }

  return alarms;
});

// 告警趋势图配置
const trendChartOption = computed(() => ({
  title: {
    text: '告警趋势',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'cross'
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
    boundaryGap: false,
    data: trendData.dates
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '严重',
      type: 'line',
      data: trendData.critical,
      lineStyle: { color: '#F56C6C' },
      areaStyle: { color: 'rgba(245, 108, 108, 0.1)' }
    },
    {
      name: '警告',
      type: 'line',
      data: trendData.warning,
      lineStyle: { color: '#E6A23C' },
      areaStyle: { color: 'rgba(230, 162, 60, 0.1)' }
    },
    {
      name: '信息',
      type: 'line',
      data: trendData.info,
      lineStyle: { color: '#409EFF' },
      areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
    }
  ]
}));

// 获取告警级别类型
const getAlarmLevelType = (level: string) => {
  switch (level.toLowerCase()) {
    case 'critical':
      return 'danger';
    case 'warning':
      return 'warning';
    case 'info':
      return 'info';
    default:
      return '';
  }
};

// 状态过滤改变
const onStatusFilterChange = () => {
  currentPage.value = 1;
  // 这里可以重新获取数据
};

// 处理选择改变
const handleSelectionChange = (selection: Alarm[]) => {
  selectedAlarms.value = selection;
};

// 页面大小改变
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  refreshAlarms();
};

// 当前页改变
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  refreshAlarms();
};

// 解决告警
const resolveAlarm = async (alarm: Alarm) => {
  try {
    await ElMessageBox.confirm(
      `确定要解决告警 "${alarm.message}" 吗？`,
      '确认解决',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await alarmsStore.resolveAlarm(alarm.id);
    ElMessage.success('告警已解决');
    
    // 更新统计数据
    updateAlarmStats();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '解决告警失败');
    }
  }
};

// 批量解决告警
const batchResolve = async () => {
  if (selectedAlarms.value.length === 0) {
    ElMessage.warning('请选择要解决的告警');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要解决选中的 ${selectedAlarms.value.length} 个告警吗？`,
      '确认批量解决',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    // 批量解决告警
    for (const alarm of selectedAlarms.value) {
      if (alarm.status === 'active') {
        await alarmsStore.resolveAlarm(alarm.id);
      }
    }

    ElMessage.success('批量解决告警成功');
    selectedAlarms.value = [];
    
    // 更新统计数据
    updateAlarmStats();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量解决告警失败');
    }
  }
};

// 刷新告警
const refreshAlarms = async () => {
  await alarmsStore.fetchAlarms({
    limit: pageSize.value,
    offset: (currentPage.value - 1) * pageSize.value
  });
  updateAlarmStats();
};

// 更新告警统计
const updateAlarmStats = () => {
  const alarms = alarmsStore.alarms;
  alarmStats.total = alarms.length;
  alarmStats.active = alarms.filter(a => a.status === 'active').length;
  alarmStats.resolved = alarms.filter(a => a.status === 'resolved').length;
  alarmStats.critical = alarms.filter(a => a.alarm_type === 'critical').length;
  alarmStats.warning = alarms.filter(a => a.alarm_type === 'warning').length;
  alarmStats.info = alarms.filter(a => a.alarm_type === 'info').length;
};

// 刷新趋势数据
const refreshTrendData = async () => {
  trendLoading.value = true;
  try {
    // 生成模拟数据
    const days = trendTimeRange.value === '24h' ? 1 : 
                  trendTimeRange.value === '7d' ? 7 : 30;
    
    trendData.dates = [];
    trendData.critical = [];
    trendData.warning = [];
    trendData.info = [];

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      if (trendTimeRange.value === '24h') {
        date.setHours(date.getHours() - i);
        trendData.dates.push(date.getHours() + ':00');
      } else {
        trendData.dates.push(date.toISOString().split('T')[0]);
      }
      
      trendData.critical.push(Math.floor(Math.random() * 5));
      trendData.warning.push(Math.floor(Math.random() * 10));
      trendData.info.push(Math.floor(Math.random() * 15));
    }
  } catch (error) {
    console.error('刷新趋势数据失败:', error);
  } finally {
    trendLoading.value = false;
  }
};

// 页面加载时获取数据
onMounted(async () => {
  await refreshAlarms();
  await refreshTrendData();
});
</script>

<style scoped>
.alarms-page {
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
  color: #333;
  margin-bottom: 5px;
}

.stats-label {
  font-size: 14px;
  color: #666;
}

.alarms-card,
.trend-card {
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

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.chart-container {
  height: 300px;
}

@media (max-width: 768px) {
  .alarms-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .stats-content {
    flex-direction: column;
    text-align: center;
  }
  
  .stats-icon {
    margin-right: 0;
    margin-bottom: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }
  
  .header-actions .el-input {
    width: 100% !important;
  }
}
</style>
