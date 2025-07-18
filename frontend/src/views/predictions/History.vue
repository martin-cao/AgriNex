<template>
  <div class="prediction-history-container">
    <el-card class="header-card">
      <div class="header-content">
        <h2>📊 历史预测记录</h2>
        <p>查看所有历史预测结果和趋势分析</p>
      </div>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="action-card">
      <div class="action-bar">
        <div>
          <el-button type="primary" @click="goBackToPredictions">
            <el-icon><ArrowLeft /></el-icon>
            返回预测分析
          </el-button>
          <el-button type="success" @click="loadPredictionHistory" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
        <div class="stats">
          <el-statistic title="总预测记录" :value="pagination.total" />
        </div>
      </div>
    </el-card>

    <!-- 历史预测记录表格 -->
    <el-card class="history-table-card">
      <template #header>
        <div class="card-header">
          <span>预测历史记录</span>
          <el-button type="primary" size="small" @click="exportHistoryData" :disabled="!historyPredictions.length">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
      </template>
      
      <el-table 
        :data="historyPredictions" 
        style="width: 100%" 
        v-loading="loading"
        stripe
        height="600"
      >
        <el-table-column prop="generated_at" label="生成时间" width="180" sortable>
          <template #default="scope">
            <el-text type="info">{{ formatDateTime(scope.row.generated_at) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="sensor_name" label="传感器" width="200">
          <template #default="scope">
            <div class="sensor-info">
              <el-tag type="primary" size="small">{{ scope.row.sensor_type_desc }}</el-tag>
              <div class="sensor-name">{{ scope.row.sensor_name }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="metric_type" label="预测类型" width="120">
          <template #default="scope">
            <el-tag type="success">{{ scope.row.metric_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="predict_ts" label="预测时间" width="180" sortable>
          <template #default="scope">
            {{ formatDateTime(scope.row.predict_ts) }}
          </template>
        </el-table-column>
        <el-table-column prop="yhat" label="预测值" width="120" align="right">
          <template #default="scope">
            <el-text type="primary" style="font-weight: bold;">
              {{ scope.row.yhat.toFixed(3) }}
            </el-text>
            <div class="unit">{{ scope.row.unit }}</div>
          </template>
        </el-table-column>
        <el-table-column label="置信区间" width="200" align="center">
          <template #default="scope">
            <div class="confidence-interval">
              <span class="lower">{{ scope.row.yhat_lower.toFixed(3) }}</span>
              <span class="separator">~</span>
              <span class="upper">{{ scope.row.yhat_upper.toFixed(3) }}</span>
            </div>
            <div class="confidence-bar">
              <el-progress
                :percentage="calculateConfidenceWidth(scope.row)"
                :stroke-width="4"
                :show-text="false"
                color="#409EFF"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewPredictionDetail(scope.row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button type="text" size="small" @click="comparePrediction(scope.row)">
              <el-icon><TrendCharts /></el-icon>
              分析
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 预测详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="预测详情" width="500px">
      <div v-if="selectedPrediction" class="prediction-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="传感器">
            {{ selectedPrediction.sensor_name }}
          </el-descriptions-item>
          <el-descriptions-item label="传感器类型">
            <el-tag type="primary">{{ selectedPrediction.sensor_type_desc }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="预测类型">
            <el-tag type="success">{{ selectedPrediction.metric_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="预测时间">
            {{ formatDateTime(selectedPrediction.predict_ts) }}
          </el-descriptions-item>
          <el-descriptions-item label="预测值">
            <el-text type="primary" style="font-size: 18px; font-weight: bold;">
              {{ selectedPrediction.yhat.toFixed(3) }} {{ selectedPrediction.unit }}
            </el-text>
          </el-descriptions-item>
          <el-descriptions-item label="置信区间">
            {{ selectedPrediction.yhat_lower.toFixed(3) }} ~ {{ selectedPrediction.yhat_upper.toFixed(3) }} {{ selectedPrediction.unit }}
          </el-descriptions-item>
          <el-descriptions-item label="生成时间">
            {{ formatDateTime(selectedPrediction.generated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Refresh, Download, View, TrendCharts } from '@element-plus/icons-vue'
import { predictionsApi } from '@/api/predictions'
import dayjs from 'dayjs'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const historyPredictions = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const pagination = ref({
  total: 0,
  page: 1,
  pages: 1,
  per_page: 20
})

// 对话框
const detailDialogVisible = ref(false)
const selectedPrediction = ref<any>(null)

// 方法
const goBackToPredictions = () => {
  router.push('/predictions')
}

const loadPredictionHistory = async () => {
  loading.value = true
  try {
    const response = await predictionsApi.getPredictionHistory({
      page: currentPage.value,
      per_page: pageSize.value
    })
    
    if (response.success) {
      historyPredictions.value = response.data || []
      if (response.pagination) {
        pagination.value = {
          total: response.pagination.total || 0,
          page: response.pagination.page || 1,
          pages: response.pagination.pages || 1,
          per_page: response.pagination.per_page || 20
        }
      }
    } else {
      ElMessage.error('加载历史预测失败')
    }
  } catch (error) {
    console.error('加载历史预测失败:', error)
    ElMessage.error('加载历史预测失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (newSize: number) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadPredictionHistory()
}

const handleCurrentChange = (newPage: number) => {
  currentPage.value = newPage
  loadPredictionHistory()
}

const viewPredictionDetail = (prediction: any) => {
  selectedPrediction.value = prediction
  detailDialogVisible.value = true
}

const comparePrediction = (prediction: any) => {
  // TODO: 实现预测对比分析功能
  ElMessage.info('预测分析功能开发中...')
}

const calculateConfidenceWidth = (row: any) => {
  // 计算置信区间的相对宽度作为进度条的百分比
  const range = row.yhat_upper - row.yhat_lower
  const center = row.yhat
  const width = range / center * 100
  return Math.min(width, 100)
}

const exportHistoryData = () => {
  try {
    const data = historyPredictions.value.map(p => ({
      生成时间: formatDateTime(p.generated_at),
      传感器名称: p.sensor_name,
      传感器类型: p.sensor_type_desc,
      预测类型: p.metric_type,
      预测时间: formatDateTime(p.predict_ts),
      预测值: p.yhat.toFixed(3),
      置信区间下界: p.yhat_lower.toFixed(3),
      置信区间上界: p.yhat_upper.toFixed(3),
      单位: p.unit
    }))
    
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `prediction_history_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('历史数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('数据导出失败')
  }
}

const formatDateTime = (dateString: string) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss')
}

// 初始化
onMounted(() => {
  loadPredictionHistory()
})
</script>

<style scoped>
.prediction-history-container {
  padding: 16px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.header-card {
  margin-bottom: 16px;
}

.header-content {
  text-align: center;
}

.header-content h2 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.header-content p {
  margin: 0;
  color: #7f8c8d;
}

.action-card {
  margin-bottom: 16px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-table-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sensor-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sensor-name {
  font-size: 12px;
  color: #666;
}

.unit {
  font-size: 12px;
  color: #999;
}

.confidence-interval {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
}

.confidence-interval .lower {
  color: #67C23A;
  font-weight: bold;
}

.confidence-interval .upper {
  color: #E6A23C;
  font-weight: bold;
}

.confidence-interval .separator {
  color: #909399;
}

.confidence-bar {
  width: 100%;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.prediction-detail {
  padding: 10px 0;
}

.stats {
  display: flex;
  gap: 16px;
}
</style>
