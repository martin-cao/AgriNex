<template>
  <div class="sensor-detail">
    <el-card class="header-card">
      <div class="header-content">
        <h2>📊 传感器详情</h2>
        <el-button @click="$router.go(-1)" type="primary">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
    </el-card>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <div v-else-if="sensor" class="sensor-content">
      <!-- 传感器基本信息 -->
      <el-card class="info-card">
        <template #header>
          <span>传感器信息</span>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="传感器名称">
            {{ sensor.name }}
          </el-descriptions-item>
          <el-descriptions-item label="传感器类型">
            <el-tag :type="getSensorTypeColor(sensor.sensor_type)">
              {{ sensor.sensor_type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="测量单位">
            {{ sensor.unit }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="sensor.status === 'active' ? 'success' : 'danger'">
              {{ sensor.status === 'active' ? '在线' : '离线' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="数值范围">
            {{ sensor.min_value ?? '无' }} - {{ sensor.max_value ?? '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(sensor.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 实时数据 -->
      <el-card class="data-card">
        <template #header>        <div class="card-header">
          <span>实时数据</span>
          <div class="header-actions">
            <el-button @click="getAIAnalysis" type="success" size="small" :loading="loadingAnalysis">
              <el-icon><Star /></el-icon>
              AI分析
            </el-button>
            <el-button @click="fetchReadings" :loading="loadingReadings">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
        </template>
        
        <div class="current-value">
          <div class="value-display">
            <span class="value">{{ latestReading?.value?.toFixed(2) || '--' }}</span>
            <span class="unit">{{ sensor.unit }}</span>
          </div>
          <div class="value-time">
            最后更新: {{ latestReading ? formatDate(latestReading.timestamp) : '无数据' }}
          </div>
        </div>
      </el-card>

      <!-- 历史数据图表 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>历史数据</span>
            <el-radio-group v-model="timeRange" @change="fetchReadings">
              <el-radio-button label="1h">1小时</el-radio-button>
              <el-radio-button label="6h">6小时</el-radio-button>
              <el-radio-button label="1d">1天</el-radio-button>
              <el-radio-button label="7d">7天</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        
        <div class="chart-container">
          <v-chart
            :option="chartOption"
            :style="{ height: '400px', width: '100%' }"
            autoresize
          />
        </div>
      </el-card>

      <!-- 数据统计 -->
      <el-card class="stats-card">
        <template #header>
          <span>数据统计</span>
        </template>
        
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="平均值" :value="stats.average" :precision="2" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最大值" :value="stats.max" :precision="2" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="最小值" :value="stats.min" :precision="2" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="数据点数" :value="stats.count" />
          </el-col>
        </el-row>
      </el-card>

      <!-- 数据表格 -->
      <el-card class="table-card">
        <template #header>
          <span>数据记录</span>
        </template>
        
        <el-table :data="readings" style="width: 100%" max-height="400">
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column prop="value" label="数值" width="120">
            <template #default="scope">
              {{ scope.row.value.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="unit" label="单位" width="80">
            <template #default>
              {{ sensor.unit }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getValueStatus(scope.row.value)">
                {{ getValueStatusText(scope.row.value) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <div v-else class="error-state">
      <el-empty description="传感器不存在" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Refresh, Star } from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { sensorsApi } from '@/api'
import { formatDate } from '@/utils'
import type { Sensor, Reading } from '@/types'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const route = useRoute()
const sensorId = parseInt(route.params.id as string)

const loading = ref(true)
const loadingReadings = ref(false)
const loadingAnalysis = ref(false)
const sensor = ref<Sensor | null>(null)
const readings = ref<Reading[]>([])
const timeRange = ref('1d')

const latestReading = computed(() => {
  return readings.value.length > 0 ? readings.value[0] : null
})

const stats = computed(() => {
  if (readings.value.length === 0) {
    return { average: 0, max: 0, min: 0, count: 0 }
  }

  const values = readings.value.map(r => r.value)
  return {
    average: values.reduce((sum, val) => sum + val, 0) / values.length,
    max: Math.max(...values),
    min: Math.min(...values),
    count: values.length
  }
})

const chartOption = computed(() => {
  const data = readings.value.map(r => [r.timestamp, r.value])

  return {
    title: {
      text: `${sensor.value?.name} 历史数据`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const time = formatDate(params[0].axisValue)
        const value = params[0].value[1]
        return `${time}<br/>${sensor.value?.name}: ${value.toFixed(2)} ${sensor.value?.unit}`
      }
    },
    grid: {
      top: 60,
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: sensor.value?.unit || ''
    },
    series: [
      {
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2
        },
        areaStyle: {
          opacity: 0.1
        }
      }
    ]
  }
})

const fetchSensor = async () => {
  try {
    const response = await sensorsApi.getSensor(sensorId)
    sensor.value = response.data || null
  } catch (error) {
    ElMessage.error('获取传感器信息失败')
  }
}

const fetchReadings = async () => {
  if (!sensor.value) return
  
  loadingReadings.value = true
  try {
    const response = await sensorsApi.getSensorReadings(sensorId, {
      per_page: 1000
    })
    readings.value = response.data || []
  } catch (error) {
    ElMessage.error('获取传感器数据失败')
  } finally {
    loadingReadings.value = false
  }
}

const getSensorTypeColor = (type: string) => {
  const typeMap: Record<string, string> = {
    'temperature': 'danger',
    'humidity': 'primary',
    'pressure': 'warning',
    'light': 'success'
  }
  return typeMap[type] || 'info'
}

const getValueStatus = (value: number) => {
  if (!sensor.value) return 'info'
  
  if (sensor.value.min_value !== undefined && sensor.value.min_value !== null && value < sensor.value.min_value) {
    return 'danger'
  }
  if (sensor.value.max_value !== undefined && sensor.value.max_value !== null && value > sensor.value.max_value) {
    return 'danger'
  }
  return 'success'
}

const getValueStatusText = (value: number) => {
  if (!sensor.value) return '正常'
  
  if (sensor.value.min_value !== undefined && sensor.value.min_value !== null && value < sensor.value.min_value) {
    return '偏低'
  }
  if (sensor.value.max_value !== undefined && sensor.value.max_value !== null && value > sensor.value.max_value) {
    return '偏高'
  }
  return '正常'
}

const getAIAnalysis = async () => {
  if (!sensor.value) return
  
  loadingAnalysis.value = true
  try {
    const { llmApi } = await import('@/api')
    const response = await llmApi.getSensorAnalysis({
      sensor_id: sensorId,
      minutes: 60
    })
    
    if (response.success && response.data) {
      ElMessage({
        type: 'success',
        message: '分析完成！',
        duration: 2000
      })
      
      // 显示分析结果
      ElMessageBox.alert(response.data.advice, 'AI 分析结果', {
        dangerouslyUseHTMLString: true,
        customClass: 'ai-analysis-dialog'
      })
    } else {
      ElMessage.error(response.error || 'AI分析失败')
    }
  } catch (error) {
    console.error('AI Analysis error:', error)
    ElMessage.error('AI分析失败，请稍后重试')
  } finally {
    loadingAnalysis.value = false
  }
}

onMounted(async () => {
  loading.value = true
  await fetchSensor()
  await fetchReadings()
  loading.value = false
})
</script>

<style scoped>
.sensor-detail {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  color: var(--agrinex-text-primary);
}

.loading-container {
  padding: 20px;
}

.sensor-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.data-card,
.chart-card,
.stats-card,
.table-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.current-value {
  text-align: center;
  padding: 20px;
}

.value-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 10px;
}

.value {
  font-size: 3rem;
  font-weight: bold;
  color: #409eff;
}

.unit {
  font-size: 1.2rem;
  color: var(--agrinex-text-secondary);
}

.value-time {
  margin-top: 10px;
  color: var(--agrinex-text-tertiary);
}

.chart-container {
  width: 100%;
  height: 400px;
}

.error-state {
  padding: 60px;
  text-align: center;
}

.el-statistic {
  text-align: center;
}
</style>
