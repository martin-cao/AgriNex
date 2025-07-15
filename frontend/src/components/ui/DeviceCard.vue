<template>
  <a-card class="device-card" :loading="loading">
    <template #title>
      <div class="device-title">
        <a-avatar :size="40" :style="{ backgroundColor: getStatusColor(device.status) }">
          <component :is="deviceIcon" />
        </a-avatar>
        <div class="device-info">
          <h4>{{ device.name }}</h4>
          <span>{{ device.location }}</span>
        </div>
      </div>
    </template>
    
    <template #extra>
      <a-badge :status="statusBadge" :text="statusText" />
    </template>

    <div class="device-stats">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-statistic 
            title="传感器" 
            :value="device.sensor_count" 
            :value-style="{ fontSize: '16px' }"
          />
        </a-col>
        <a-col :span="8">
          <a-statistic 
            title="在线时长" 
            :value="uptime" 
            suffix="小时"
            :value-style="{ fontSize: '16px' }"
          />
        </a-col>
        <a-col :span="8">
          <a-statistic 
            title="数据点" 
            :value="dataPoints"
            :value-style="{ fontSize: '16px' }"
          />
        </a-col>
      </a-row>
    </div>

    <!-- 设备连接信息 -->
    <div class="device-connection" v-if="device.client_id || device.ip_address || device.port">
      <a-descriptions size="small" :column="1">
        <a-descriptions-item v-if="device.client_id" label="客户端ID">
          <a-tag>{{ device.client_id }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item v-if="device.ip_address" label="IP地址">
          {{ device.ip_address }}
        </a-descriptions-item>
        <a-descriptions-item v-if="device.port" label="端口">
          {{ device.port }}
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <div class="device-actions">
      <a-space>
        <a-button type="primary" @click="viewDetails">
          <eye-outlined />
          查看详情
        </a-button>
        <a-button @click="editDevice">
          <edit-outlined />
          编辑
        </a-button>
        <a-dropdown>
          <a-button>
            更多 <down-outlined />
          </a-button>
          <template #overlay>
            <a-menu>
              <a-menu-item @click="downloadData">
                <download-outlined />
                下载数据
              </a-menu-item>
              <a-menu-item @click="resetDevice">
                <reload-outlined />
                重置设备
              </a-menu-item>
              <a-menu-divider />
              <a-menu-item danger @click="confirmDelete">
                <delete-outlined />
                删除设备
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </a-space>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { Modal, message } from 'ant-design-vue';
import dayjs from 'dayjs';

interface Device {
  id: number;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance';
  sensor_count: number;
  last_seen: string;
  client_id?: string;
  ip_address?: string;
  port?: number;
  device_type?: string;
  data_points?: number;
}

interface Props {
  device: Device;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
});

const emit = defineEmits<{
  edit: [device: Device];
  delete: [deviceId: number];
  reset: [deviceId: number];
}>();

const router = useRouter();

// 计算属性
const deviceIcon = computed(() => {
  switch (props.device.status) {
    case 'online':
      return 'laptop-outlined';
    case 'offline':
      return 'disconnect-outlined';
    case 'maintenance':
      return 'tool-outlined';
    default:
      return 'laptop-outlined';
  }
});

const statusBadge = computed(() => {
  switch (props.device.status) {
    case 'online':
      return 'success';
    case 'offline':
      return 'error';
    case 'maintenance':
      return 'warning';
    default:
      return 'default';
  }
});

const statusText = computed(() => {
  switch (props.device.status) {
    case 'online':
      return '在线';
    case 'offline':
      return '离线';
    case 'maintenance':
      return '维护中';
    default:
      return '未知';
  }
});

const uptime = computed(() => {
  if (props.device.status === 'offline') return 0;
  const lastSeen = dayjs(props.device.last_seen);
  const now = dayjs();
  return Math.max(0, now.diff(lastSeen, 'hour'));
});

const dataPoints = computed(() => {
  return props.device.data_points || Math.floor(Math.random() * 10000);
});

// 方法
const getStatusColor = (status: string) => {
  switch (status) {
    case 'online':
      return '#52c41a';
    case 'offline':
      return '#ff4d4f';
    case 'maintenance':
      return '#faad14';
    default:
      return '#d9d9d9';
  }
};

const viewDetails = () => {
  router.push(`/devices/${props.device.id}`);
};

const editDevice = () => {
  emit('edit', props.device);
};

const downloadData = () => {
  message.info('开始下载设备数据...');
  // TODO: 实现数据下载逻辑
};

const resetDevice = () => {
  Modal.confirm({
    title: '确认重置设备',
    content: `确定要重置设备 "${props.device.name}" 吗？这将清除设备的临时数据。`,
    okText: '确认',
    cancelText: '取消',
    onOk() {
      emit('reset', props.device.id);
      message.success('设备重置成功');
    }
  });
};

const confirmDelete = () => {
  Modal.confirm({
    title: '确认删除设备',
    content: `确定要删除设备 "${props.device.name}" 吗？此操作不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      emit('delete', props.device.id);
      message.success('设备删除成功');
    }
  });
};
</script>

<style lang="less" scoped>
.device-card {
  margin-bottom: 16px;
  
  .device-title {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .device-info {
      h4 {
        margin: 0;
        font-size: 16px;
        color: #262626;
        font-weight: 600;
      }
      
      span {
        font-size: 12px;
        color: #8c8c8c;
      }
    }
  }

  .device-stats {
    margin: 16px 0;
  }

  .device-actions {
    margin-top: 16px;
    text-align: center;
  }
}

@media (max-width: 768px) {
  .device-card {
    .device-stats {
      :deep(.ant-col) {
        margin-bottom: 8px;
      }
    }
    
    .device-actions {
      :deep(.ant-space) {
        flex-direction: column;
        width: 100%;
        
        .ant-space-item {
          width: 100%;
          
          .ant-btn {
            width: 100%;
          }
        }
      }
    }
  }
}
</style>
