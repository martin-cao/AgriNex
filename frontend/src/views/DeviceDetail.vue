<template>
  <div class="device-detail-page">
    <div class="page-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>设备详情</h2>
    </div>

    <div v-if="devicesStore.currentDevice" class="device-content">
      <!-- 设备基本信息 -->
      <el-card class="device-info-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-button size="small" @click="editDevice">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <span class="label">设备名称：</span>
              <span class="value">{{ devicesStore.currentDevice.name }}</span>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <span class="label">设备类型：</span>
              <span class="value">{{ devicesStore.currentDevice.device_type }}</span>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <span class="label">位置：</span>
              <span class="value">{{ devicesStore.currentDevice.location }}</span>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <span class="label">状态：</span>
              <el-tag
                :type="getStatusType(devicesStore.currentDevice.is_active, devicesStore.currentDevice.last_seen)"
                size="small"
              >
                {{ getStatusText(devicesStore.currentDevice.is_active, devicesStore.currentDevice.last_seen) }}
              </el-tag>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <span class="label">最后在线：</span>
              <span class="value">
                {{ devicesStore.currentDevice.last_seen ? formatDateTime(devicesStore.currentDevice.last_seen) : '从未连接' }}
              </span>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatDateTime(devicesStore.currentDevice.created_at) }}</span>
            </div>
          </el-col>
          <el-col :xs="24" :sm="24" :md="16" v-if="devicesStore.currentDevice.description">
            <div class="info-item">
              <span class="label">描述：</span>
              <span class="value">{{ devicesStore.currentDevice.description }}</span>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 传感器列表 -->
      <el-card class="sensors-card">
        <template #header>
          <div class="card-header">
            <span>传感器列表</span>
            <el-button size="small" @click="showAddSensorDialog = true">
              <el-icon><Plus /></el-icon>
              添加传感器
            </el-button>
          </div>
        </template>

        <el-table
          :data="devicesStore.deviceSensors"
          :loading="devicesStore.isLoading"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="传感器名称" min-width="150" />
          <el-table-column prop="sensor_type" label="类型" width="120" />
          <el-table-column prop="unit" label="单位" width="100" />
          <el-table-column label="范围" width="120">
            <template #default="scope">
              <span v-if="scope.row.min_value !== null && scope.row.max_value !== null">
                {{ scope.row.min_value }} - {{ scope.row.max_value }}
              </span>
              <span v-else>未设置</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
                {{ scope.row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="viewSensor(scope.row)"
              >
                查看
              </el-button>
              <el-button
                type="warning"
                size="small"
                @click="editSensor(scope.row)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="deleteSensor(scope.row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 最近数据 -->
      <el-card class="recent-data-card">
        <template #header>
          <div class="card-header">
            <span>最近数据</span>
            <el-button size="small" @click="refreshRecentData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <div class="recent-data-content">
          <div
            v-for="sensor in devicesStore.deviceSensors"
            :key="sensor.id"
            class="sensor-data-item"
          >
            <div class="sensor-info">
              <div class="sensor-name">{{ sensor.name }}</div>
              <div class="sensor-type">{{ sensor.sensor_type }}</div>
            </div>
            <div class="sensor-value">
              <div class="value">-- {{ sensor.unit }}</div>
              <div class="time">暂无数据</div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="devicesStore.isLoading" class="loading-container">
      <el-skeleton animated>
        <template #template>
          <el-skeleton-item variant="h1" style="width: 40%" />
          <el-skeleton-item variant="rect" style="width: 100%; height: 200px; margin-top: 20px;" />
          <el-skeleton-item variant="rect" style="width: 100%; height: 300px; margin-top: 20px;" />
        </template>
      </el-skeleton>
    </div>

    <!-- 设备不存在 -->
    <div v-else class="no-device">
      <el-empty description="设备不存在" />
    </div>

    <!-- 添加传感器对话框 -->
    <el-dialog
      v-model="showAddSensorDialog"
      title="添加传感器"
      width="600px"
      @close="resetSensorForm"
    >
      <el-form
        ref="sensorFormRef"
        :model="sensorForm"
        :rules="sensorRules"
        label-width="120px"
      >
        <el-form-item label="传感器名称" prop="name">
          <el-input v-model="sensorForm.name" placeholder="请输入传感器名称" />
        </el-form-item>
        <el-form-item label="传感器类型" prop="sensor_type">
          <el-select v-model="sensorForm.sensor_type" placeholder="请选择传感器类型">
            <el-option label="温度" value="temperature" />
            <el-option label="湿度" value="humidity" />
            <el-option label="光照强度" value="light" />
            <el-option label="土壤湿度" value="soil_moisture" />
            <el-option label="pH值" value="ph" />
            <el-option label="图像" value="image" />
            <el-option label="视频" value="video" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="sensorForm.unit" placeholder="请输入单位，如：℃、%、lux" />
        </el-form-item>
        <el-form-item label="最小值" prop="min_value">
          <el-input-number
            v-model="sensorForm.min_value"
            :precision="2"
            placeholder="可选"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="最大值" prop="max_value">
          <el-input-number
            v-model="sensorForm.max_value"
            :precision="2"
            placeholder="可选"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="sensorForm.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddSensorDialog = false">取消</el-button>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="submitSensor"
          >
            创建
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { useDevicesStore } from '../stores/devices';
import { useSensorsStore } from '../stores/sensors';
import { formatDateTime, getDeviceStatusText } from '../utils';
import type { Sensor } from '../types';

const route = useRoute();
const router = useRouter();
const devicesStore = useDevicesStore();
const sensorsStore = useSensorsStore();

const showAddSensorDialog = ref(false);
const submitLoading = ref(false);
const sensorFormRef = ref<FormInstance>();

// 传感器表单
const sensorForm = reactive({
  name: '',
  sensor_type: '',
  unit: '',
  device_id: 0,
  min_value: null as number | null,
  max_value: null as number | null,
  is_active: true
});

// 传感器表单验证规则
const sensorRules: FormRules = {
  name: [
    { required: true, message: '请输入传感器名称', trigger: 'blur' },
    { min: 2, max: 50, message: '传感器名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  sensor_type: [
    { required: true, message: '请选择传感器类型', trigger: 'change' }
  ],
  unit: [
    { required: true, message: '请输入单位', trigger: 'blur' }
  ]
};

// 获取状态类型
const getStatusType = (isActive: boolean, lastSeen?: string) => {
  if (!isActive) return 'info';
  if (!lastSeen) return 'danger';
  
  const now = Date.now();
  const lastSeenTime = new Date(lastSeen).getTime();
  const diffMinutes = (now - lastSeenTime) / (1000 * 60);
  
  if (diffMinutes <= 5) return 'success';
  if (diffMinutes <= 30) return 'warning';
  return 'danger';
};

// 获取状态文本
const getStatusText = (isActive: boolean, lastSeen?: string) => {
  return getDeviceStatusText(isActive, lastSeen);
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 编辑设备
const editDevice = () => {
  // 跳转到设备编辑页面或打开编辑对话框
  router.push('/devices');
};

// 查看传感器
const viewSensor = (sensor: Sensor) => {
  router.push(`/sensors/${sensor.id}`);
};

// 编辑传感器
const editSensor = (sensor: Sensor) => {
  // 实现编辑传感器逻辑
  console.log('编辑传感器:', sensor);
};

// 删除传感器
const deleteSensor = async (sensor: Sensor) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除传感器 "${sensor.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await sensorsStore.deleteSensor(sensor.id);
    ElMessage.success('传感器删除成功');
    
    // 重新获取设备传感器列表
    const deviceId = parseInt(route.params.id as string);
    await devicesStore.fetchDeviceSensors(deviceId);
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除传感器失败');
    }
  }
};

// 提交传感器
const submitSensor = async () => {
  if (!sensorFormRef.value) return;
  
  try {
    await sensorFormRef.value.validate();
    submitLoading.value = true;
    
    const deviceId = parseInt(route.params.id as string);
    
    // 准备传感器数据，处理null值
    const sensorData = {
      ...sensorForm,
      device_id: deviceId,
      min_value: sensorForm.min_value ?? undefined,
      max_value: sensorForm.max_value ?? undefined
    };
    
    await sensorsStore.createSensor(sensorData);
    ElMessage.success('传感器创建成功');
    
    showAddSensorDialog.value = false;
    resetSensorForm();
    
    // 重新获取设备传感器列表
    await devicesStore.fetchDeviceSensors(deviceId);
  } catch (error: any) {
    ElMessage.error(error.message || '创建传感器失败');
  } finally {
    submitLoading.value = false;
  }
};

// 重置传感器表单
const resetSensorForm = () => {
  if (sensorFormRef.value) {
    sensorFormRef.value.resetFields();
  }
  
  sensorForm.name = '';
  sensorForm.sensor_type = '';
  sensorForm.unit = '';
  sensorForm.device_id = 0;
  sensorForm.min_value = null;
  sensorForm.max_value = null;
  sensorForm.is_active = true;
};

// 刷新最近数据
const refreshRecentData = async () => {
  // 实现刷新最近数据逻辑
  console.log('刷新最近数据');
};

// 页面加载时获取设备详情
onMounted(async () => {
  const deviceId = parseInt(route.params.id as string);
  if (deviceId) {
    await devicesStore.fetchDevice(deviceId);
    await devicesStore.fetchDeviceSensors(deviceId);
  }
});
</script>

<style scoped>
.device-detail-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.device-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.device-info-card,
.sensors-card,
.recent-data-card {
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
  margin-bottom: 15px;
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

.recent-data-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  padding: 10px;
}

.sensor-data-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.sensor-info {
  flex: 1;
}

.sensor-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
}

.sensor-type {
  font-size: 12px;
  color: #666;
}

.sensor-value {
  text-align: right;
}

.sensor-value .value {
  font-size: 16px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.sensor-value .time {
  font-size: 12px;
  color: #999;
}

.loading-container {
  padding: 20px;
}

.no-device {
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
  .device-detail-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .recent-data-content {
    grid-template-columns: 1fr;
  }
}
</style>
