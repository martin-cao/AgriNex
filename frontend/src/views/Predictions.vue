<template>
  <div class="predictions-container">
    <el-card class="header-card">
      <div class="header-content">
        <h2>📊 预测分析</h2>
        <p>基于历史数据和机器学习模型进行农业预测</p>
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
          <el-col :span="8">
            <el-form-item label="预测类型" prop="type">
              <el-select v-model="predictionForm.type" placeholder="选择预测类型">
                <el-option label="温度预测" value="temperature" />
                <el-option label="湿度预测" value="humidity" />
                <el-option label="产量预测" value="yield" />
                <el-option label="病虫害预测" value="pest" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="预测时长" prop="duration">
              <el-select v-model="predictionForm.duration" placeholder="选择预测时长">
                <el-option label="1天" value="1d" />
                <el-option label="3天" value="3d" />
                <el-option label="7天" value="7d" />
                <el-option label="30天" value="30d" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="设备选择" prop="deviceId">
              <el-select v-model="predictionForm.deviceId" placeholder="选择设备">
                <el-option
                  v-for="device in devices"
                  :key="device.id"
                  :label="device.name"
                  :value="device.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button type="primary" @click="generatePrediction" :loading="loading">
            生成预测
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 预测结果 -->
    <el-card v-if="predictions.length > 0" class="results-card">
      <template #header>
        <div class="card-header">
          <span>预测结果</span>
          <el-button type="text" @click="refreshPredictions">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <div class="chart-container">
        <v-chart
          :option="chartOption"
          :style="{ height: '400px', width: '100%' }"
          autoresize
        />
      </div>
      
      <el-table :data="predictions" style="width: 100%; margin-top: 20px">
        <el-table-column prop="predict_ts" label="时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.predict_ts) }}
          </template>
        </el-table-column>
        <el-table-column prop="sensor_id" label="传感器ID" width="120" />
        <el-table-column prop="yhat" label="预测值" width="120">
          <template #default="scope">
            {{ scope.row.yhat.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="置信区间" width="120">
          <template #default="scope">
            {{ scope.row.yhat_lower.toFixed(2) }} - {{ scope.row.yhat_upper.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="generated_at" label="生成时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.generated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewDetails(scope.row)">
              详情
            </el-button>
            <el-button type="text" size="small" @click="exportData(scope.row)">
              导出
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 历史预测 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>历史预测</span>
        </div>
      </template>
      
      <el-table :data="historicalPredictions" style="width: 100%">
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="duration" label="时长" width="100" />
        <el-table-column prop="accuracy" label="准确率" width="120">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.accuracy"
              :stroke-width="8"
              :show-text="false"
            />
            <span style="margin-left: 10px">{{ scope.row.accuracy }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewHistory(scope.row)">
              查看
            </el-button>
            <el-button type="text" size="small" @click="downloadReport(scope.row)">
              下载报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
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
import { predictionsApi, devicesApi } from '@/api'
import { formatDate } from '@/utils'
import type { Device, Prediction } from '@/types'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// 表单相关
const formRef = ref()
const predictionForm = ref({
  type: '',
  duration: '',
  deviceId: null as number | null
})

const rules = {
  type: [{ required: true, message: '请选择预测类型', trigger: 'change' }],
  duration: [{ required: true, message: '请选择预测时长', trigger: 'change' }],
  deviceId: [{ required: true, message: '请选择设备', trigger: 'change' }]
}

// 数据相关
const loading = ref(false)
const devices = ref<Device[]>([])
const predictions = ref<Prediction[]>([])
const historicalPredictions = ref<Prediction[]>([])

// 图表配置
const chartOption = computed(() => {
  if (predictions.value.length === 0) return {}
  
  const data = predictions.value.map(p => [p.predict_ts, p.yhat])
  const confidenceData = predictions.value.map(p => [p.predict_ts, (p.yhat_upper - p.yhat_lower) / 2])
  
  return {
    title: {
      text: '预测趋势图',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const time = formatDate(params[0].axisValue)
        let content = `${time}<br/>`
        params.forEach((param: any) => {
          content += `${param.seriesName}: ${param.value[1]}<br/>`
        })
        return content
      }
    },
    legend: {
      data: ['预测值', '置信度'],
      top: 30
    },
    grid: {
      top: 80,
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false
    },
    yAxis: [
      {
        type: 'value',
        name: '预测值',
        position: 'left'
      },
      {
        type: 'value',
        name: '置信度(%)',
        position: 'right',
        min: 0,
        max: 100
      }
    ],
    series: [
      {
        name: '预测值',
        type: 'line',
        data: data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2
        }
      },
      {
        name: '置信度',
        type: 'line',
        yAxisIndex: 1,
        data: confidenceData,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 4,
        lineStyle: {
          width: 2,
          type: 'dashed'
        }
      }
    ]
  }
})

// 获取设备列表
const fetchDevices = async () => {
  try {
    const response = await devicesApi.getDevices()
    devices.value = response.data || []
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  }
}

// 获取预测列表
const fetchPredictions = async () => {
  try {
    const response = await predictionsApi.getPredictions()
    predictions.value = response.data || []
  } catch (error) {
    ElMessage.error('获取预测数据失败')
  }
}

// 获取历史预测
const fetchHistoricalPredictions = async () => {
  try {
    // 使用同样的API获取历史数据
    const response = await predictionsApi.getPredictions()
    historicalPredictions.value = response.data || []
  } catch (error) {
    ElMessage.error('获取历史预测失败')
  }
}

// 生成预测
const generatePrediction = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const payload = {
      sensor_id: predictionForm.value.deviceId || 1,
      periods: predictionForm.value.duration === '1d' ? 24 : 
               predictionForm.value.duration === '3d' ? 72 : 
               predictionForm.value.duration === '7d' ? 168 : 720,
      freq: 'H'
    }
    await predictionsApi.triggerPrediction(payload)
    ElMessage.success('预测生成成功')
    
    await fetchPredictions()
    await fetchHistoricalPredictions()
  } catch (error) {
    ElMessage.error('生成预测失败')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 刷新预测
const refreshPredictions = async () => {
  await fetchPredictions()
  ElMessage.success('数据已刷新')
}

// 状态处理
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': 'success',
    'running': 'warning',
    'failed': 'danger',
    'pending': 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'completed': '已完成',
    'running': '运行中',
    'failed': '失败',
    'pending': '待处理'
  }
  return statusMap[status] || status
}

// 查看详情
const viewDetails = (prediction: Prediction) => {
  ElMessageBox.alert(
    `预测ID: ${prediction.id}\n传感器ID: ${prediction.sensor_id}\n预测值: ${prediction.yhat.toFixed(2)}\n置信区间: ${prediction.yhat_lower.toFixed(2)} - ${prediction.yhat_upper.toFixed(2)}`,
    '预测详情',
    {
      confirmButtonText: '确定'
    }
  )
}

// 导出数据
const exportData = (prediction: Prediction) => {
  const data = JSON.stringify(prediction, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `prediction_${prediction.id}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('数据导出成功')
}

// 查看历史
const viewHistory = (prediction: Prediction) => {
  ElMessage.info('查看历史功能待开发')
}

// 下载报告
const downloadReport = (prediction: Prediction) => {
  ElMessage.info('下载报告功能待开发')
}

onMounted(async () => {
  await fetchDevices()
  await fetchPredictions()
  await fetchHistoricalPredictions()
})
</script>

<style scoped>
.predictions-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  text-align: center;
}

.header-content h2 {
  margin: 0 0 10px 0;
  color: var(--agrinex-text-primary);
}

.header-content p {
  margin: 0;
  color: var(--agrinex-text-secondary);
}

.config-card,
.results-card,
.history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.el-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-table {
  border-radius: 8px;
}

.el-progress {
  display: inline-block;
  width: 80px;
}
</style>
