<template>
  <div class="devices-page">
    <div class="page-header">
      <h2>设备管理</h2>
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加设备
      </el-button>
    </div>

    <!-- 设备列表 -->
    <el-card class="devices-card">
      <template #header>
        <div class="card-header">
          <span>设备列表</span>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索设备"
              style="width: 200px; margin-right: 10px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button @click="refreshDevices">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="filteredDevices"
        :loading="devicesStore.isLoading"
        stripe
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="设备名称" min-width="150" />
        <el-table-column prop="device_type" label="设备类型" width="120" />
        <el-table-column prop="location" label="位置" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag
              :type="getStatusType(scope.row.is_active, scope.row.last_seen)"
              size="small"
            >
              {{ getStatusText(scope.row.is_active, scope.row.last_seen) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后在线" width="180">
          <template #default="scope">
            {{ scope.row.last_seen ? formatDateTime(scope.row.last_seen) : '从未连接' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click.stop="viewDevice(scope.row)"
            >
              查看
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click.stop="editDevice(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click.stop="deleteDevice(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑设备对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="isEditing ? '编辑设备' : '添加设备'"
      width="700px"
      @close="resetForm"
    >
      <el-form
        ref="deviceFormRef"
        :model="deviceForm"
        :rules="deviceRules"
        label-width="120px"
        style="margin-top: 20px"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="deviceForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="deviceForm.device_type" placeholder="请选择设备类型">
            <el-option label="土壤传感器" value="soil_sensor" />
            <el-option label="气象站" value="weather_station" />
            <el-option label="灌溉控制器" value="irrigation_controller" />
            <el-option label="环境监控" value="environment" />
            <el-option label="摄像头" value="camera" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <!-- 设备网络配置 -->
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="deviceForm.ip_address" placeholder="如: localhost 或 192.168.1.100" />
          <div class="form-help">
            设备的IP地址或主机名
          </div>
        </el-form-item>
        
        <el-form-item label="端口" prop="port">
          <el-input-number 
            v-model="deviceForm.port" 
            :min="1" 
            :max="65535" 
            placeholder="如: 30001"
            style="width: 100%"
          />
          <div class="form-help">
            设备HTTP服务端口
          </div>
        </el-form-item>
        
        <el-form-item label="Client ID" prop="client_id">
          <el-input v-model="deviceForm.client_id" placeholder="如: agrinex_sensor_docker" />
          <div class="form-help">
            MQTT客户端ID，必须与设备发送的主题中的client_id一致
          </div>
        </el-form-item>
        
        <el-form-item label="位置" prop="location">
          <el-input v-model="deviceForm.location" placeholder="请输入设备位置" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="deviceForm.description"
            type="textarea"
            rows="3"
            placeholder="请输入设备描述"
          />
        </el-form-item>
        
        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="deviceForm.is_active" />
          <div class="form-help">
            关闭后设备将无法接收MQTT数据
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="submitLoading"
            @click="submitDevice"
          >
            {{ isEditing ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { useDevicesStore } from '../stores/devices';
import { formatDateTime, getDeviceStatusText, getDeviceStatusColor } from '../utils';
import type { Device } from '../types';
import { devicesApi } from '../api';

const router = useRouter();
const devicesStore = useDevicesStore();

const searchQuery = ref('');
const showAddDialog = ref(false);
const isEditing = ref(false);
const submitLoading = ref(false);
const deviceFormRef = ref<FormInstance>();
const currentEditingDevice = ref<Device | null>(null);

// 设备表单
const deviceForm = reactive({
  name: '',
  device_type: '',
  location: '',
  description: '',
  is_active: true,
  // 网络配置字段
  ip_address: '',
  port: null as number | null,
  client_id: ''
});

// 表单验证规则
const deviceRules: FormRules = {
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 2, max: 50, message: '设备名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  device_type: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  location: [
    { required: true, message: '请输入设备位置', trigger: 'blur' }
  ],
  ip_address: [
    { required: true, message: '请输入IP地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号必须在1-65535之间', trigger: 'blur' }
  ],
  client_id: [
    { required: true, message: '请输入Client ID', trigger: 'blur' },
    { min: 1, max: 100, message: 'Client ID长度在 1 到 100 个字符', trigger: 'blur' }
  ]
};

// 过滤后的设备列表
const filteredDevices = computed(() => {
  if (!searchQuery.value) {
    return devicesStore.devices;
  }
  return devicesStore.devices.filter(device =>
    device.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    device.device_type.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    device.location.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

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

// 处理行点击
const handleRowClick = (row: Device) => {
  router.push(`/devices/${row.id}`);
};

// 查看设备
const viewDevice = (device: Device) => {
  router.push(`/devices/${device.id}`);
};

// 编辑设备
const editDevice = (device: Device) => {
  isEditing.value = true;
  currentEditingDevice.value = device;
  
  // 填充表单
  deviceForm.name = device.name;
  deviceForm.device_type = device.device_type;
  deviceForm.location = device.location;
  deviceForm.description = device.description || '';
  deviceForm.is_active = device.is_active;
  
  showAddDialog.value = true;
};

// 删除设备
const deleteDevice = async (device: Device) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 "${device.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await devicesStore.deleteDevice(device.id);
    ElMessage.success('设备删除成功');
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除设备失败');
    }
  }
};

// 提交设备
const submitDevice = async () => {
  if (!deviceFormRef.value) return;
  
  try {
    await deviceFormRef.value.validate();
    submitLoading.value = true;
    
    if (isEditing.value && currentEditingDevice.value) {
      // 编辑现有设备
      await devicesStore.updateDevice(currentEditingDevice.value.id, deviceForm);
      ElMessage.success('设备更新成功');
    } else {
      // 创建新设备
      await devicesStore.createDevice(deviceForm);
      ElMessage.success('设备创建成功');
    }
    
    showAddDialog.value = false;
    resetForm();
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败');
  } finally {
    submitLoading.value = false;
  }
};

// 重置表单
const resetForm = () => {
  if (deviceFormRef.value) {
    deviceFormRef.value.resetFields();
  }
  
  deviceForm.name = '';
  deviceForm.device_type = '';
  deviceForm.location = '';
  deviceForm.description = '';
  deviceForm.is_active = true;
  deviceForm.ip_address = '';
  deviceForm.port = null;
  deviceForm.client_id = '';
  
  isEditing.value = false;
  currentEditingDevice.value = null;
};

// 刷新设备列表
const refreshDevices = async () => {
  await devicesStore.fetchDevices();
};

// 页面加载时获取设备列表
onMounted(async () => {
  await devicesStore.fetchDevices();
});
</script>

<style scoped>
.devices-page {
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

.devices-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}

/* 新增样式 */
.device-type-selector {
  margin-bottom: 20px;
  text-align: center;
}

.device-type-selector .el-radio-group {
  margin: 0 auto;
}

.simulation-status {
  margin-bottom: 20px;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.validation-progress {
  margin: 20px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.validation-progress h4 {
  margin: 0 0 15px 0;
  color: #606266;
}

.validation-details {
  margin-top: 15px;
}

.validation-details p {
  margin: 10px 0;
  color: #666;
}

@media (max-width: 768px) {
  .devices-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
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
