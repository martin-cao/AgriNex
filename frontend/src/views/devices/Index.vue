<template>
  <div class="devices-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <h1>设备管理</h1>
          <p class="page-description">管理农业物联网设备，监控设备状态与数据</p>
        </div>
        <div class="header-actions">
          <a-space>
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索设备名称或位置"
              style="width: 300px"
              @search="handleSearch"
            />
            <a-button type="primary" @click="showAddDevice">
              <plus-outlined />
              添加设备
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 过滤器 -->
    <a-card class="filter-card" size="small">
      <a-space wrap>
        <span>状态筛选:</span>
        <a-radio-group v-model:value="statusFilter" @change="handleFilterChange">
          <a-radio-button value="">全部</a-radio-button>
          <a-radio-button value="online">在线</a-radio-button>
          <a-radio-button value="offline">离线</a-radio-button>
          <a-radio-button value="maintenance">维护中</a-radio-button>
        </a-radio-group>
        
        <a-divider type="vertical" />
        
        <span>设备类型:</span>
        <a-select 
          v-model:value="typeFilter" 
          placeholder="选择设备类型" 
          style="width: 150px"
          allowClear
          @change="handleFilterChange"
        >
          <a-select-option value="greenhouse">温室大棚</a-select-option>
          <a-select-option value="open_field">露天农场</a-select-option>
          <a-select-option value="greenhouse_control">温室控制</a-select-option>
          <a-select-option value="aquaculture">水产养殖</a-select-option>
          <a-select-option value="soil_monitoring">土壤监测</a-select-option>
          <a-select-option value="weather_station">气象站</a-select-option>
          <a-select-option value="irrigation">灌溉系统</a-select-option>
          <a-select-option value="livestock">畜牧监测</a-select-option>
        </a-select>
        
        <a-divider type="vertical" />
        
        <span>视图模式:</span>
        <a-radio-group v-model:value="viewMode" @change="handleViewModeChange">
          <a-radio-button value="card">
            <appstore-outlined />
            卡片
          </a-radio-button>
          <a-radio-button value="table">
            <table-outlined />
            表格
          </a-radio-button>
        </a-radio-group>
      </a-space>
    </a-card>

    <!-- 设备列表 - 卡片模式 -->
    <div v-if="viewMode === 'card'" class="devices-grid">
      <a-row :gutter="[16, 16]">
        <a-col 
          v-for="device in filteredDevices" 
          :key="device.id"
          :xs="24" 
          :sm="12" 
          :lg="8" 
          :xl="6"
        >
          <DeviceCard
            :device="device"
            :loading="loading"
            @edit="handleEditDevice"
            @delete="handleDeleteDevice"
            @reset="handleResetDevice"
          />
        </a-col>
      </a-row>
      
      <!-- 空状态 -->
      <a-empty 
        v-if="filteredDevices.length === 0 && !loading"
        description="暂无符合条件的设备"
      >
        <a-button type="primary" @click="showAddDevice">
          <plus-outlined />
          添加设备
        </a-button>
      </a-empty>
    </div>

    <!-- 设备列表 - 表格模式 -->
    <a-card v-else class="table-card">
      <a-table
        :columns="tableColumns"
        :data-source="filteredDevices"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1200 }"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'client_id'">
            <span>{{ record.client_id || '-' }}</span>
          </template>
          
          <template v-if="column.key === 'device_type'">
            <a-tag :color="getDeviceTypeColor(record.device_type)">
              {{ getDeviceTypeText(record.device_type) }}
            </a-tag>
          </template>
          
          <template v-if="column.key === 'ip_address'">
            <span>{{ record.ip_address || '-' }}</span>
          </template>
          
          <template v-if="column.key === 'port'">
            <span>{{ record.port || '-' }}</span>
          </template>
          
          <template v-if="column.key === 'status'">
            <a-badge :status="getDeviceStatusBadge(record.status)" :text="getDeviceStatusText(record.status)" />
          </template>
          
          <template v-if="column.key === 'updated_at'">
            <span>{{ formatDateTime(record.updated_at) }}</span>
          </template>
          
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="primary" size="small" @click="viewDeviceDetails(record)">
                <eye-outlined />
                详情
              </a-button>
              <a-button size="small" @click="handleEditDevice(record)">
                <edit-outlined />
                编辑
              </a-button>
              <a-dropdown>
                <a-button size="small">
                  更多 <down-outlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="handleResetDevice(record.id)">
                      <reload-outlined />
                      重置
                    </a-menu-item>
                    <a-menu-item danger @click="handleDeleteDevice(record.id)">
                      <delete-outlined />
                      删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 分页 -->
    <div v-if="viewMode === 'card' && filteredDevices.length > 0" class="pagination-wrapper">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total, range) => `第 ${range[0]}-${range[1]} 项，共 ${total} 项`"
        @change="handlePageChange"
        @showSizeChange="handlePageSizeChange"
      />
    </div>

    <!-- 添加/编辑设备弹窗 -->
    <a-modal
      v-model:open="deviceModalVisible"
      :title="editingDevice ? '编辑设备' : '添加设备'"
      :confirm-loading="modalLoading"
      @ok="handleSaveDevice"
      @cancel="handleCloseModal"
    >
      <a-form
        ref="deviceFormRef"
        :model="deviceForm"
        :rules="deviceFormRules"
        layout="vertical"
      >
        <a-form-item label="设备名称" name="name">
          <a-input v-model:value="deviceForm.name" placeholder="请输入设备名称" />
        </a-form-item>
        
        <a-form-item label="客户端ID" name="client_id">
          <a-input v-model:value="deviceForm.client_id" placeholder="请输入客户端ID（设备唯一标识）" />
        </a-form-item>
        
        <a-form-item label="设备位置" name="location">
          <a-input v-model:value="deviceForm.location" placeholder="请输入设备位置" />
        </a-form-item>
        
        <a-form-item label="设备类型" name="device_type">
          <a-select v-model:value="deviceForm.device_type" placeholder="请选择设备类型">
            <a-select-option value="greenhouse">温室大棚</a-select-option>
            <a-select-option value="aquaculture">水产养殖</a-select-option>
            <a-select-option value="soil_monitoring">土壤监测</a-select-option>
            <a-select-option value="weather_station">气象站</a-select-option>
            <a-select-option value="irrigation">灌溉系统</a-select-option>
            <a-select-option value="livestock">畜牧监控</a-select-option>
            <a-select-option value="crop_monitoring">作物监测</a-select-option>
            <a-select-option value="fishpond">鱼塘监测</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="IP地址" name="ip_address">
              <a-input v-model:value="deviceForm.ip_address" placeholder="请输入设备IP地址" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="端口" name="port">
              <a-input-number 
                v-model:value="deviceForm.port" 
                placeholder="请输入端口号" 
                :min="1" 
                :max="65535"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="设备描述" name="description">
          <a-textarea 
            v-model:value="deviceForm.description" 
            placeholder="请输入设备描述"
            :rows="3"
          />
        </a-form-item>
        
        <a-form-item label="连接配置" name="config">
          <a-textarea 
            v-model:value="deviceForm.config" 
            placeholder="请输入设备连接配置（JSON格式）"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import DeviceCard from '@/components/ui/DeviceCard.vue';
import { deviceApi } from '@/api/device';
import dayjs from 'dayjs';

const router = useRouter();

// 响应式数据
const loading = ref(true);
const modalLoading = ref(false);
const searchKeyword = ref('');
const statusFilter = ref('');
const typeFilter = ref('');
const viewMode = ref<'card' | 'table'>('card');
const devices = ref<any[]>([]);
const deviceModalVisible = ref(false);
const editingDevice = ref<any>(null);

const deviceForm = reactive({
  name: '',
  location: '',
  device_type: '',
  client_id: '',
  ip_address: '',
  port: null as number | null,
  description: '',
  config: ''
});

const deviceFormRules = {
  name: [{ required: true, message: '请输入设备名称' }],
  location: [{ required: true, message: '请输入设备位置' }],
  device_type: [{ required: true, message: '请选择设备类型' }],
  client_id: [{ required: true, message: '请输入客户端ID' }],
  ip_address: [
    { required: true, message: '请输入IP地址' },
    { pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^localhost$/, message: '请输入有效的IP地址' }
  ],
  port: [
    { required: true, message: '请输入端口号' },
    { pattern: /^[0-9]+$/, message: '端口号必须是数字' },
    { validator: (rule: any, value: any) => {
        const port = parseInt(value);
        if (port < 1 || port > 65535) {
          return Promise.reject('端口号必须在1-65535之间');
        }
        return Promise.resolve();
      }
    }
  ]
};

const pagination = reactive({
  current: 1,
  pageSize: 12,
  total: 0
});

// 表格列定义
const tableColumns = [
  {
    title: '设备名称',
    dataIndex: 'name',
    key: 'name',
    width: 150,
    ellipsis: true
  },
  {
    title: '客户端ID',
    dataIndex: 'client_id',
    key: 'client_id',
    width: 120,
    ellipsis: true
  },
  {
    title: '位置',
    dataIndex: 'location',
    key: 'location',
    width: 120,
    ellipsis: true
  },
  {
    title: '设备类型',
    dataIndex: 'device_type',
    key: 'device_type',
    width: 120
  },
  {
    title: 'IP地址',
    dataIndex: 'ip_address',
    key: 'ip_address',
    width: 120
  },
  {
    title: '端口',
    dataIndex: 'port',
    key: 'port',
    width: 80
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '最后更新',
    dataIndex: 'updated_at',
    key: 'updated_at',
    width: 150
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
];

// 计算属性
const filteredDevices = computed(() => {
  let result = devices.value;
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(device => 
      device.name.toLowerCase().includes(keyword) ||
      device.location.toLowerCase().includes(keyword)
    );
  }
  
  // 状态过滤
  if (statusFilter.value) {
    result = result.filter(device => device.status === statusFilter.value);
  }
  
  // 类型过滤
  if (typeFilter.value) {
    result = result.filter(device => device.device_type === typeFilter.value);
  }
  
  return result;
});

// 方法
const fetchDevices = async () => {
  try {
    loading.value = true;
    const response = await deviceApi.getDevices({
      page: pagination.current,
      size: pagination.pageSize
    }) as any; // 临时使用any类型
    
    // 适配后端API响应格式: { data: [...], success: true, total: 6 }
    if (response.success && response.data) {
      devices.value = response.data;
      pagination.total = (response as any).total || response.data.length;
    } else {
      devices.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    message.error('获取设备列表失败');
    console.error('获取设备失败:', error);
    devices.value = [];
    pagination.total = 0;
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.current = 1;
  // 在实际应用中，这里应该调用API进行搜索
  // 现在只是客户端过滤
};

const handleFilterChange = () => {
  pagination.current = 1;
  // 重新筛选数据
};

const handleViewModeChange = () => {
  // 切换视图模式
};

const showAddDevice = () => {
  editingDevice.value = null;
  resetDeviceForm();
  deviceModalVisible.value = true;
};

const handleEditDevice = (device: any) => {
  editingDevice.value = device;
  Object.assign(deviceForm, {
    name: device.name,
    location: device.location,
    device_type: device.device_type,
    client_id: device.client_id || '',
    ip_address: device.ip_address || '',
    port: device.port || null,
    description: device.description || '',
    config: device.config ? JSON.stringify(device.config, null, 2) : ''
  });
  deviceModalVisible.value = true;
};

const handleDeleteDevice = async (deviceId: number) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个设备吗？此操作不可恢复。',
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await deviceApi.deleteDevice(deviceId.toString());
        message.success('设备删除成功');
        fetchDevices();
      } catch (error) {
        message.error('设备删除失败');
      }
    }
  });
};

const handleResetDevice = async (deviceId: number) => {
  try {
    // 由于resetDevice方法不存在，我们使用controlDevice方法
    await (deviceApi as any).controlDevice?.(deviceId.toString(), 'restart') || 
          deviceApi.updateDevice(deviceId.toString(), { status: 'maintenance' });
    message.success('设备重置成功');
    fetchDevices();
  } catch (error) {
    message.error('设备重置失败');
  }
};

const handleSaveDevice = async () => {
  try {
    modalLoading.value = true;
    
    // 验证表单
    // TODO: 实现表单验证
    
    const deviceData = {
      ...deviceForm,
      config: deviceForm.config ? JSON.parse(deviceForm.config) : null
    };
    
    if (editingDevice.value) {
      await deviceApi.updateDevice(editingDevice.value.id, deviceData);
      message.success('设备更新成功');
    } else {
      await deviceApi.createDevice(deviceData);
      message.success('设备添加成功');
    }
    
    deviceModalVisible.value = false;
    fetchDevices();
  } catch (error) {
    message.error(editingDevice.value ? '设备更新失败' : '设备添加失败');
  } finally {
    modalLoading.value = false;
  }
};

const handleCloseModal = () => {
  deviceModalVisible.value = false;
  resetDeviceForm();
};

const resetDeviceForm = () => {
  Object.assign(deviceForm, {
    name: '',
    client_id: '',
    location: '',
    device_type: '',
    ip_address: '',
    port: null,
    description: '',
    config: ''
  });
};

const viewDeviceDetails = (device: any) => {
  router.push(`/devices/${device.id}`);
};

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchDevices();
};

const handlePageChange = (page: number, pageSize: number) => {
  pagination.current = page;
  pagination.pageSize = pageSize;
  fetchDevices();
};

const handlePageSizeChange = (current: number, size: number) => {
  pagination.current = 1;
  pagination.pageSize = size;
  fetchDevices();
};

const getDeviceStatusBadge = (status: string) => {
  switch (status) {
    case 'online':
      return 'success';
    case 'offline':
      return 'error';
    case 'maintenance':
      return 'warning';
    default:
      return 'default';
  }
};

const getDeviceStatusText = (status: string) => {
  switch (status) {
    case 'online':
      return '在线';
    case 'offline':
      return '离线';
    case 'maintenance':
      return '维护中';
    default:
      return '未知';
  }
};

const formatLastSeen = (lastSeen: string) => {
  return dayjs(lastSeen).format('YYYY-MM-DD HH:mm:ss');
};

// 新增设备类型相关函数
const getDeviceTypeText = (deviceType: string) => {
  const typeMap: Record<string, string> = {
    'greenhouse': '温室大棚',
    'open_field': '露天农场',
    'greenhouse_control': '温室控制',
    'aquaculture': '水产养殖',
    'soil_monitoring': '土壤监测',
    'weather_station': '气象站',
    'irrigation': '灌溉系统',
    'livestock': '畜牧监测'
  };
  return typeMap[deviceType] || deviceType;
};

const getDeviceTypeColor = (deviceType: string) => {
  const colorMap: Record<string, string> = {
    'greenhouse': 'green',
    'open_field': 'blue',
    'greenhouse_control': 'orange',
    'aquaculture': 'cyan',
    'soil_monitoring': 'brown',
    'weather_station': 'purple',
    'irrigation': 'geekblue',
    'livestock': 'magenta'
  };
  return colorMap[deviceType] || 'default';
};

// 格式化日期时间
const formatDateTime = (datetime: string) => {
  if (!datetime) return '-';
  return dayjs(datetime).format('YYYY-MM-DD HH:mm');
};

// 生命周期
onMounted(() => {
  fetchDevices();
});
</script>

<style lang="less" scoped>
.devices-page {
  .page-header {
    margin-bottom: 16px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
      .header-title {
        h1 {
          margin: 0;
          font-size: 24px;
          color: #262626;
        }
        
        .page-description {
          margin: 4px 0 0 0;
          color: #8c8c8c;
        }
      }
      
      .header-actions {
        flex-shrink: 0;
      }
    }
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .devices-grid {
    min-height: 400px;
  }

  .table-card {
    margin-bottom: 16px;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: center;
    margin-top: 24px;
  }
}

@media (max-width: 768px) {
  .devices-page {
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-actions {
          width: 100%;
          
          :deep(.ant-space) {
            width: 100%;
            justify-content: space-between;
            
            .ant-input-search {
              width: 100% !important;
              max-width: none !important;
            }
          }
        }
      }
    }

    .filter-card {
      :deep(.ant-space) {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
    }
  }
}
</style>
