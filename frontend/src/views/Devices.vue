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
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="deviceFormRef"
        :model="deviceForm"
        :rules="deviceRules"
        label-width="100px"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="deviceForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="deviceForm.device_type" placeholder="请选择设备类型">
            <el-option label="环境监控" value="environment" />
            <el-option label="土壤监测" value="soil" />
            <el-option label="气象站" value="weather" />
            <el-option label="摄像头" value="camera" />
            <el-option label="其他" value="other" />
          </el-select>
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
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
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
  is_active: true
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
      await devicesStore.updateDevice(currentEditingDevice.value.id, deviceForm);
      ElMessage.success('设备更新成功');
    } else {
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
