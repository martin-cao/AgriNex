<template>
  <div class="predictions-container">
    <el-card class="header-card">
      <div class="header-content">
        <h2>📊 时序预测</h2>
        <p>基于 Prophet 模型进行农业数据时序预测</p>
      </div>
    </el-card>

    <!-- 预测配置 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>预测配置</span>
        </div>
      </template>
      
      <el-form :model="predictionForm" :rules="rules" ref="formRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="选择地点" prop="location">
              <el-select v-model="predictionForm.location" placeholder="请选择地点" @change="onLocationChange" clearable>
                <el-option label="全部地点" value="" />
                <el-option
                  v-for="location in availableLocations"
                  :key="location"
                  :label="location"
                  :value="location"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="6">
            <el-form-item label="选择设备" prop="deviceId">
              <el-select v-model="predictionForm.deviceId" placeholder="请选择设备" @change="onDeviceChange" :disabled="!filteredDevices.length">
                <el-option
                  v-for="device in filteredDevices"
                  :key="device.id"
                  :label="`${device.name} (${device.location})`"
                  :value="device.id"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="6">
            <el-form-item label="选择传感器" prop="sensorId">
              <el-select v-model="predictionForm.sensorId" placeholder="请选择传感器" @change="onSensorChange" :disabled="!deviceSensors.length">
                <el-option
                  v-for="sensor in deviceSensors"
                  :key="sensor.id"
                  :label="`${sensor.name} (${sensor.sensor_type})`"
                  :value="sensor.id"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="6">
            <el-form-item label="预测时长" prop="period">
              <el-select v-model="predictionForm.period" placeholder="选择预测时长">
                <el-option
                  v-for="(config, key) in forecastOptions"
                  :key="key"
                  :label="config.description"
                  :value="key"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" @click="generatePrediction" :loading="loading">
            <el-icon><TrendCharts /></el-icon>
            生成预测
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button type="success" @click="goToHistory">
            <el-icon><Refresh /></el-icon>
            查看历史预测
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预测结果图表 -->
    <el-card v-if="predictionResults.length > 0" class="results-card">
      <template #header>
        <div class="card-header">
          <span>预测结果图表</span>
          <div>
            <el-tag type="success">{{ predictionInfo.period_description }}</el-tag>
            <el-button type="text" @click="refreshCurrentPrediction">
              <el-icon><Refresh /></el-icon>
              刷新本次预测
            </el-button>
          </div>
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

    <!-- 预测数据表格 -->
    <el-card v-if="predictionResults.length > 0" class="data-table-card">
      <template #header>
        <div class="card-header">
          <span>预测数据详情 (共 {{ predictionResults.length }} 个预测点)</span>
          <el-button type="primary" size="small" @click="exportPredictionData">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
      </template>
      
      <el-table :data="paginatedResults" style="width: 100%">
        <el-table-column prop="timestamp" label="预测时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="yhat" label="预测值" width="120">
          <template #default="scope">
            <el-tag type="primary">{{ scope.row.yhat.toFixed(3) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信区间" width="200">
          <template #default="scope">
            <span class="confidence-interval">
              {{ scope.row.yhat_lower.toFixed(3) }} ~ {{ scope.row.yhat_upper.toFixed(3) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="120">
          <template #default="scope">
            <el-progress
              :percentage="calculateConfidence(scope.row)"
              :stroke-width="8"
              :show-text="false"
            />
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="predictionResults.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Refresh, TrendCharts, Download } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { predictionsApi, type PredictionOption, type PredictionPoint } from '@/api/predictions'
import { deviceApi } from '@/api'
import { useThemeStore } from '@/stores/theme'
import dayjs from 'dayjs'
import type { Device } from '@/types'

// 注册 ECharts 组件
use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

// 路由和主题
const router = useRouter()
const themeStore = useThemeStore()

// 定义预测相关接口
interface PredictionForm {
  location: string
  deviceId: number | null
  sensorId: number | null
  period: string
}

interface PredictionResult {
  timestamp: string
  yhat: number
  yhat_lower: number
  yhat_upper: number
}

interface PredictionResponse {
  forecast?: PredictionResult[]
  period_description: string
  sensor_id: number
}

interface ForecastOption {
  description: string
  periods: number
  frequency: string
}

interface Sensor {
  id: number
  name: string
  sensor_type: string
  device_id: number
  device_name?: string
  location?: string
}

// 响应式数据
const loading = ref(false)
const devices = ref<Device[]>([])
const sensors = ref<Sensor[]>([])
const predictionResults = ref<PredictionResult[]>([])
const forecastOptions = ref<Record<string, ForecastOption>>({})
const predictionInfo = ref<Partial<PredictionResponse>>({})
const formRef = ref<FormInstance>()

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)

const predictionForm: PredictionForm = reactive({
  location: '',
  deviceId: null,
  sensorId: null,
  period: '24h'
})

// 表单验证规则
const rules = {
  sensorId: [{ required: true, message: '请选择传感器', trigger: 'change' }],
  period: [{ required: true, message: '请选择预测时长', trigger: 'change' }]
}

// 可用字段
const availableFields = ref<string[]>(['numeric_value', 'temperature', 'humidity', 'soil_moisture', 'ph', 'light_intensity'])

// 计算属性 - 层次筛选
const availableLocations = computed(() => {
  const locations = devices.value.map(device => device.location).filter(Boolean)
  return [...new Set(locations)]
})

const filteredDevices = computed(() => {
  if (!predictionForm.location) {
    return devices.value
  }
  return devices.value.filter(device => device.location === predictionForm.location)
})

const deviceSensors = computed(() => {
  if (!predictionForm.deviceId) {
    return []
  }
  return sensors.value.filter(sensor => sensor.device_id === predictionForm.deviceId)
})

// 计算属性
const paginatedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return predictionResults.value.slice(start, end)
})

// 图表选项
const chartOption = computed(() => {
  if (predictionResults.value.length === 0) {
    return {}
  }
  
  const data = predictionResults.value.map(p => [p.timestamp, p.yhat])
  const upperBand = predictionResults.value.map(p => [p.timestamp, p.yhat_upper])
  const lowerBand = predictionResults.value.map(p => [p.timestamp, p.yhat_lower])
  
  // 获取选中传感器的信息用于图表标题
  const selectedSensor = sensors.value.find(s => s.id === predictionForm.sensorId)
  const sensorName = selectedSensor?.name || '传感器'
  
  // 根据主题设置颜色
  const isDark = themeStore.isDark
  const textColor = isDark ? 'rgba(255, 255, 255, 0.85)' : '#262626'
  const backgroundColor = isDark ? '#1f1f1f' : '#ffffff'
  const borderColor = isDark ? '#434343' : '#d9d9d9'
  const primaryColor = '#409EFF'
  
  return {
    backgroundColor: backgroundColor,
    title: {
      text: `${sensorName} 预测结果`,
      left: 'center',
      textStyle: {
        color: textColor
      }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? 'rgba(50, 50, 50, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: borderColor,
      textStyle: {
        color: textColor
      },
      formatter: (params: any) => {
        const point = params[0]
        const prediction = predictionResults.value.find(p => p.timestamp === point.data[0])
        if (prediction) {
          return `
            时间: ${dayjs(point.data[0]).format('YYYY-MM-DD HH:mm:ss')}<br/>
            预测值: ${prediction.yhat.toFixed(3)}<br/>
            置信区间: ${prediction.yhat_lower.toFixed(3)} ~ ${prediction.yhat_upper.toFixed(3)}
          `
        }
        return `时间: ${dayjs(point.data[0]).format('YYYY-MM-DD HH:mm:ss')}<br/>预测值: ${point.data[1].toFixed(3)}`
      }
    },
    legend: {
      data: ['预测值', '置信区间'],
      top: 30,
      textStyle: {
        color: textColor
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
      borderColor: borderColor
    },
    xAxis: {
      type: 'time',
      name: '时间',
      nameTextStyle: {
        color: textColor
      },
      axisLabel: {
        color: textColor,
        formatter: (value: any) => dayjs(value).format('MM-DD HH:mm')
      },
      axisLine: {
        lineStyle: {
          color: borderColor
        }
      },
      splitLine: {
        lineStyle: {
          color: borderColor
        }
      }
    },
    yAxis: {
      type: 'value',
      name: selectedSensor?.sensor_type || '预测值',
      nameTextStyle: {
        color: textColor
      },
      axisLabel: {
        color: textColor
      },
      axisLine: {
        lineStyle: {
          color: borderColor
        }
      },
      splitLine: {
        lineStyle: {
          color: borderColor
        }
      }
    },
    series: [
      {
        name: '置信区间',
        type: 'line',
        data: upperBand,
        lineStyle: {
          opacity: 0
        },
        stack: 'confidence-band',
        symbol: 'none',
        areaStyle: {
          color: isDark ? 'rgba(64, 158, 255, 0.15)' : 'rgba(64, 158, 255, 0.1)'
        }
      },
      {
        name: '置信区间下界',
        type: 'line',
        data: lowerBand,
        lineStyle: {
          opacity: 0
        },
        stack: 'confidence-band',
        symbol: 'none',
        areaStyle: {
          color: isDark ? 'rgba(64, 158, 255, 0.15)' : 'rgba(64, 158, 255, 0.1)'
        }
      },
      {
        name: '预测值',
        type: 'line',
        data: data,
        smooth: true,
        lineStyle: {
          color: primaryColor,
          width: 2
        },
        symbol: 'circle',
        symbolSize: 4,
        itemStyle: {
          color: primaryColor
        }
      }
    ]
  }
})

// 方法
const loadDevices = async () => {
  try {
    const response = await deviceApi.getDevices()
    devices.value = response.data || []
    console.log('设备加载成功:', devices.value.length, '个设备')
  } catch (error: any) {
    console.error('加载设备失败:', error)
    if (error.response?.status === 401) {
      ElMessage.error('认证已过期，请重新登录')
    } else {
      ElMessage.error('加载设备列表失败: ' + (error.message || '未知错误'))
    }
    devices.value = []
  }
}

const loadSensors = async () => {
  try {
    const allSensors: Sensor[] = []
    for (const device of devices.value) {
      try {
        const response = await deviceApi.getDeviceSensors(Number(device.id))
        if (response.data) {
          const deviceSensors = response.data.map((sensor: any) => ({
            ...sensor,
            device_id: device.id,
            device_name: device.name,
            location: device.location
          }))
          allSensors.push(...deviceSensors)
        }
      } catch (error: any) {
        console.error(`加载设备 ${device.id} 的传感器失败:`, error)
        if (error.response?.status !== 404) {
          // 404是正常的，说明该设备没有传感器
          console.warn(`设备 ${device.name} 可能没有传感器`)
        }
      }
    }
    sensors.value = allSensors
    console.log('传感器加载成功:', sensors.value.length, '个传感器')
  } catch (error: any) {
    console.error('加载传感器失败:', error)
    ElMessage.error('加载传感器列表失败: ' + (error.message || '未知错误'))
    sensors.value = []
  }
}

const loadForecastOptions = async () => {
  try {
    const response = await predictionsApi.getForecastOptions()
    if (response.success && response.period_configs) {
      forecastOptions.value = response.period_configs
    } else {
      // 使用默认选项
      forecastOptions.value = {
        '30min': { description: '未来30分钟（每分钟一个预测点）', periods: 30, frequency: '1T' },
        '1h': { description: '未来1小时（每分钟一个预测点）', periods: 60, frequency: '2T' },
        '2h': { description: '未来2小时（每5分钟一个预测点）', periods: 120, frequency: '5T' },
        '6h': { description: '未来6小时（每10分钟一个预测点）', periods: 360, frequency: '15T' },
        '12h': { description: '未来12小时（每15分钟一个预测点）', periods: 720, frequency: '30T' },
        '24h': { description: '未来24小时（每30分钟一个预测点）', periods: 1440, frequency: '1H' },
        '2d': { description: '未来2天（每小时一个预测点）', periods: 2880, frequency: '2H' },
        '5d': { description: '未来5天（每2小时一个预测点）', periods: 7200, frequency: '6H' },
        '7d': { description: '未来7天（每2小时一个预测点）', periods: 10080, frequency: '12H' }
      }
    }
  } catch (error) {
    console.error('加载预测选项失败:', error)
    // 使用默认选项
    forecastOptions.value = {
      '30min': { description: '未来30分钟（每分钟一个预测点）', periods: 30, frequency: '1T' },
      '1h': { description: '未来1小时（每分钟一个预测点）', periods: 60, frequency: '2T' },
      '2h': { description: '未来2小时（每5分钟一个预测点）', periods: 120, frequency: '5T' },
      '6h': { description: '未来6小时（每10分钟一个预测点）', periods: 360, frequency: '15T' },
      '12h': { description: '未来12小时（每15分钟一个预测点）', periods: 720, frequency: '30T' },
      '24h': { description: '未来24小时（每30分钟一个预测点）', periods: 1440, frequency: '1H' },
      '2d': { description: '未来2天（每小时一个预测点）', periods: 2880, frequency: '2H' },
      '5d': { description: '未来5天（每2小时一个预测点）', periods: 7200, frequency: '6H' },
      '7d': { description: '未来7天（每2小时一个预测点）', periods: 10080, frequency: '12H' }
    }
  }
}

// 层次筛选的处理函数
const onLocationChange = () => {
  predictionForm.deviceId = null
  predictionForm.sensorId = null
}

const onDeviceChange = () => {
  predictionForm.sensorId = null
}

const onSensorChange = (sensorId: number) => {
  console.log('选择传感器:', sensorId)
}

const generatePrediction = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
  } catch (error) {
    return
  }

  loading.value = true
  try {
    const response = await predictionsApi.triggerSensorPrediction(predictionForm.sensorId!, {
      field: 'numeric_value', // 固定使用 numeric_value 字段
      period: predictionForm.period
    })
    
    if (response.success) {
      ElMessage.success(response.message || '预测任务已提交')
      // 等待一段时间后获取预测结果
      setTimeout(async () => {
        try {
          const latestResponse = await predictionsApi.getLatestSensorPredictions(predictionForm.sensorId!)
          if (latestResponse.success && latestResponse.data) {
            predictionResults.value = latestResponse.data.map(item => ({
              timestamp: item.predict_ts,
              yhat: item.yhat,
              yhat_lower: item.yhat_lower,
              yhat_upper: item.yhat_upper
            }))
            
            // 获取选中传感器的信息
            const selectedSensor = sensors.value.find(s => s.id === predictionForm.sensorId)
            predictionInfo.value = {
              period_description: response.period || predictionForm.period,
              sensor_id: predictionForm.sensorId!
            }
            currentPage.value = 1
            ElMessage.success('预测结果已加载')
          }
        } catch (error) {
          console.error('获取预测结果失败:', error)
          ElMessage.warning('预测任务已提交，请稍后刷新查看结果')
        }
      }, 3000)
    }
  } catch (error: any) {
    console.error('预测生成错误:', error)
    ElMessage.error(error.response?.data?.message || '预测生成失败')
  } finally {
    loading.value = false
  }
}

const goToHistory = () => {
  router.push('/predictions/history')
}

const refreshCurrentPrediction = () => {
  if (predictionForm.sensorId && predictionForm.period) {
    generatePrediction()
  }
}

const exportPredictionData = () => {
  try {
    const data = predictionResults.value.map(p => ({
      时间: formatDateTime(p.timestamp),
      预测值: p.yhat.toFixed(3),
      下界: p.yhat_lower.toFixed(3),
      上界: p.yhat_upper.toFixed(3)
    }))
    
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `prediction_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('数据导出失败')
  }
}

const calculateConfidence = (prediction: PredictionResult): number => {
  const range = prediction.yhat_upper - prediction.yhat_lower
  const confidence = Math.max(0, Math.min(100, 100 - (range / prediction.yhat) * 100))
  return Math.round(confidence)
}

const formatDateTime = (dateTime: string): string => {
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

const resetForm = () => {
  predictionForm.location = ''
  predictionForm.deviceId = null
  predictionForm.sensorId = null
  predictionForm.period = '24h'
  predictionResults.value = []
  predictionInfo.value = {}
  currentPage.value = 1
}

// 组件挂载时初始化
onMounted(async () => {
  // 检查认证状态
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.error('请先登录')
    return
  }
  
  try {
    await loadDevices()
    await loadSensors()
    loadForecastOptions()
  } catch (error) {
    console.error('初始化失败:', error)
    ElMessage.error('页面初始化失败，请刷新重试')
  }
})
</script>

<style scoped>
.predictions-container {
  padding: 20px;
  background: var(--agrinex-bg-primary);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.header-card {
  margin-bottom: 20px;
  background: var(--agrinex-bg-card);
  border-color: var(--agrinex-border-color-split);
}

.header-content {
  text-align: center;
}

.header-content h2 {
  margin: 0 0 10px 0;
  color: var(--agrinex-primary);
  transition: color 0.3s ease;
}

.header-content p {
  margin: 0;
  color: var(--agrinex-text-secondary);
  transition: color 0.3s ease;
}

.config-card,
.results-card,
.data-table-card,
.history-card {
  margin-bottom: 20px;
  background: var(--agrinex-bg-card);
  border-color: var(--agrinex-border-color-split);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--agrinex-text-primary);
}

.chart-container {
  margin: 20px 0;
}

.confidence-interval {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  background: var(--agrinex-bg-secondary);
  color: var(--agrinex-text-primary);
  padding: 2px 6px;
  border-radius: 3px;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* Element Plus 暗色主题适配 - 针对本页面的深度样式 */
:deep(.el-card) {
  background: var(--agrinex-bg-card);
  border-color: var(--agrinex-border-color-split);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

:deep(.el-card__header) {
  background: var(--agrinex-bg-card);
  border-bottom-color: var(--agrinex-border-color-split);
  color: var(--agrinex-text-primary);
}

:deep(.el-form-item__label) {
  color: var(--agrinex-text-primary);
}

:deep(.el-select .el-input__wrapper) {
  background: var(--agrinex-bg-card);
  border-color: var(--agrinex-border-color);
  box-shadow: 0 0 0 1px var(--agrinex-border-color) inset;
}

:deep(.el-select .el-input__inner) {
  color: var(--agrinex-text-primary);
  background: transparent;
}

:deep(.el-button) {
  border-color: var(--agrinex-border-color);
  color: var(--agrinex-text-primary);
  background: var(--agrinex-bg-card);
  transition: all 0.3s ease;
}

:deep(.el-button:hover) {
  background: var(--agrinex-bg-hover);
}

:deep(.el-button--primary) {
  background: var(--agrinex-primary);
  border-color: var(--agrinex-primary);
  color: #ffffff;
}

:deep(.el-button--success) {
  background: var(--agrinex-success);
  border-color: var(--agrinex-success);
  color: #ffffff;
}

:deep(.el-table) {
  background: var(--agrinex-bg-card);
  color: var(--agrinex-text-primary);
}

:deep(.el-table th.el-table__cell) {
  background: var(--agrinex-bg-secondary);
  color: var(--agrinex-text-primary);
  border-bottom-color: var(--agrinex-border-color-split);
}

:deep(.el-table td.el-table__cell) {
  border-bottom-color: var(--agrinex-border-color-split);
  color: var(--agrinex-text-primary);
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background: var(--agrinex-bg-hover) !important;
}

:deep(.el-tag) {
  border-color: var(--agrinex-border-color);
  background: var(--agrinex-bg-secondary);
  color: var(--agrinex-text-primary);
}

:deep(.el-tag--primary) {
  background: var(--agrinex-primary);
  border-color: var(--agrinex-primary);
  color: #ffffff;
}

:deep(.el-tag--success) {
  background: var(--agrinex-success);
  border-color: var(--agrinex-success);
  color: #ffffff;
}

:deep(.el-progress-bar__outer) {
  background: var(--agrinex-bg-tertiary);
}

:deep(.el-progress-bar__inner) {
  background: var(--agrinex-primary);
}

:deep(.el-pagination) {
  color: var(--agrinex-text-primary);
}

:deep(.el-pagination .el-pager li) {
  background: var(--agrinex-bg-card);
  color: var(--agrinex-text-primary);
  border: 1px solid var(--agrinex-border-color-split);
}

:deep(.el-pagination .el-pager li.is-active) {
  color: var(--agrinex-primary);
  border-color: var(--agrinex-primary);
}

:deep(.el-pagination button) {
  background: var(--agrinex-bg-card);
  color: var(--agrinex-text-primary);
  border-color: var(--agrinex-border-color-split);
}

:deep(.el-pagination button:disabled) {
  color: var(--agrinex-text-disabled);
  background: var(--agrinex-bg-secondary);
}

:deep(.el-select-dropdown) {
  background: var(--agrinex-bg-card);
  border-color: var(--agrinex-border-color-split);
}

:deep(.el-select-dropdown .el-select-dropdown__item) {
  color: var(--agrinex-text-primary);
}

:deep(.el-select-dropdown .el-select-dropdown__item:hover) {
  background: var(--agrinex-bg-hover);
}

:deep(.el-select-dropdown .el-select-dropdown__item.is-selected) {
  color: var(--agrinex-primary);
  background: var(--agrinex-bg-active);
}

:deep(.el-loading-mask) {
  background: rgba(0, 0, 0, 0.7);
}

:deep(.el-loading-spinner .el-loading-text) {
  color: var(--agrinex-text-primary);
}

/* ECharts 图表暗色主题适配 */
:deep(.echarts) {
  background: var(--agrinex-bg-card) !important;
}

/* 修复下拉框颜色问题 */
:deep(.el-select-dropdown) {
  background: var(--agrinex-bg-card) !important;
  border-color: var(--agrinex-border-color-split) !important;
  box-shadow: var(--agrinex-shadow-medium) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item) {
  color: var(--agrinex-text-primary) !important;
  background: transparent !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item:hover) {
  background: var(--agrinex-bg-hover) !important;
  color: var(--agrinex-text-primary) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item.is-selected) {
  color: var(--agrinex-primary) !important;
  background: var(--agrinex-bg-active) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item.is-disabled) {
  color: var(--agrinex-text-disabled) !important;
  background: transparent !important;
}

/* 修复分页下拉框 */
:deep(.el-pagination .el-select .el-select-dropdown) {
  background: var(--agrinex-bg-card) !important;
  border-color: var(--agrinex-border-color-split) !important;
}

:deep(.el-pagination .el-select .el-select-dropdown .el-select-dropdown__item) {
  color: var(--agrinex-text-primary) !important;
  background: transparent !important;
}

:deep(.el-pagination .el-select .el-select-dropdown .el-select-dropdown__item:hover) {
  background: var(--agrinex-bg-hover) !important;
}

:deep(.el-pagination .el-select .el-select-dropdown .el-select-dropdown__item.is-selected) {
  color: var(--agrinex-primary) !important;
  background: var(--agrinex-bg-active) !important;
}
</style>
