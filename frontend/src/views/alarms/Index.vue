<template>
  <div class="alarms-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title">
          <h1>告警管理</h1>
          <p class="page-description">实时监控系统告警，快速响应异常情况</p>
        </div>
        <div class="header-actions">
          <a-space>
            <a-button @click="refreshAlarms" :loading="loading">
              <reload-outlined />
              刷新
            </a-button>
            <a-button type="primary" @click="showCreateRule">
              <plus-outlined />
              新建规则
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 空状态显示 -->
    <div v-if="!loading && alarms.length === 0" style="text-align: center; padding: 60px 0;">
      <a-empty description="暂无告警数据">
        <template #description>
          <p>当前系统没有告警信息</p>
          <p>系统会自动监控设备状态和传感器数据，异常时会生成告警</p>
        </template>
        <a-button type="primary" @click="refreshAlarms">
          <reload-outlined />
          刷新告警
        </a-button>
      </a-empty>
    </div>
    <a-row :gutter="[16, 16]" class="stats-row">
      <a-col :xs="24" :sm="6">
        <StatisticCard
          title="活跃告警"
          :value="alarmStats.active"
          icon="bell-outlined"
          icon-color="#ff4d4f"
          :loading="loading"
        />
      </a-col>
      <a-col :xs="24" :sm="6">
        <StatisticCard
          title="今日告警"
          :value="alarmStats.today"
          icon="calendar-outlined"
          icon-color="#faad14"
          :loading="loading"
        />
      </a-col>
      <a-col :xs="24" :sm="6">
        <StatisticCard
          title="已处理"
          :value="alarmStats.resolved"
          icon="check-circle-outlined"
          icon-color="#52c41a"
          :loading="loading"
        />
      </a-col>
      <a-col :xs="24" :sm="6">
        <StatisticCard
          title="告警规则"
          :value="alarmStats.rules"
          icon="setting-outlined"
          icon-color="#1890ff"
          :loading="loading"
        />
      </a-col>
    </a-row>

    <!-- 过滤器 -->
    <a-card class="filter-card" size="small" v-if="alarms.length > 0">
      <a-row :gutter="16" align="middle">
        <a-col :span="4">
          <span>告警级别:</span>
          <a-select
            v-model:value="filters.level"
            placeholder="全部"
            style="width: 100%; margin-left: 8px;"
            allowClear
            @change="handleFilterChange"
          >
            <a-select-option value="critical">严重</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="medium">中等</a-select-option>
            <a-select-option value="low">低</a-select-option>
          </a-select>
        </a-col>
        
        <a-col :span="4">
          <span>状态:</span>
          <a-select
            v-model:value="filters.status"
            placeholder="全部"
            style="width: 100%; margin-left: 8px;"
            allowClear
            @change="handleFilterChange"
          >
            <a-select-option value="active">活跃</a-select-option>
            <a-select-option value="resolved">已处理</a-select-option>
            <a-select-option value="acknowledged">已确认</a-select-option>
          </a-select>
        </a-col>
        
        <a-col :span="4">
          <span>设备:</span>
          <a-select
            v-model:value="filters.device"
            placeholder="全部设备"
            style="width: 100%; margin-left: 8px;"
            allowClear
            @change="handleFilterChange"
          >
            <a-select-option
              v-for="device in devices"
              :key="device.id"
              :value="device.id"
            >
              {{ device.name }}
            </a-select-option>
          </a-select>
        </a-col>
        
        <a-col :span="6">
          <span>时间范围:</span>
          <a-range-picker
            v-model:value="filters.dateRange"
            style="width: 100%; margin-left: 8px;"
            @change="handleFilterChange"
          />
        </a-col>
        
        <a-col :span="6">
          <a-input-search
            v-model:value="filters.keyword"
            placeholder="搜索告警内容"
            @search="handleFilterChange"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- 调试信息 -->
    <a-card v-if="isDev" style="margin-bottom: 16px; background: #f0f0f0;">
      <h4>🐛 分页调试信息</h4>
      <p><strong>当前页:</strong> {{ pagination.current }}</p>
      <p><strong>每页大小:</strong> {{ pagination.pageSize }}</p>
      <p><strong>总记录数:</strong> {{ pagination.total }}</p>
      <p><strong>当前显示条数:</strong> {{ alarms.length }}</p>
      <p><strong>过滤后条数:</strong> {{ filteredAlarms.length }}</p>
      <p><strong>全局测试数据总数:</strong> {{ globalTestAlarms.length }}</p>
      <p><strong>分页配置:</strong> {{ JSON.stringify({
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: pagination.total,
        showSizeChanger: pagination.showSizeChanger,
        showQuickJumper: pagination.showQuickJumper
      }) }}</p>
    </a-card>

    <!-- 告警列表 -->
    <a-card class="alarms-list" v-if="alarms.length > 0">
      <a-table
        :columns="alarmColumns"
        :data-source="filteredAlarms"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 1200 }"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'level'">
            <a-tag :color="getAlarmLevelColor(record.level)">
              {{ getAlarmLevelText(record.level) }}
            </a-tag>
          </template>
          
          <template v-if="column.key === 'status'">
            <a-badge
              :status="getAlarmStatusBadge(record.status)"
              :text="getAlarmStatusText(record.status)"
            />
          </template>
          
          <template v-if="column.key === 'created_at'">
            <span>{{ formatTime(record.created_at) }}</span>
          </template>
          
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button
                v-if="record.status === 'active'"
                type="primary"
                size="small"
                @click="acknowledgeAlarm(record)"
              >
                确认
              </a-button>
              <a-button
                v-if="record.status !== 'resolved'"
                size="small"
                @click="resolveAlarm(record)"
              >
                处理
              </a-button>
              <a-button
                size="small"
                @click="viewAlarmDetail(record)"
              >
                详情
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 告警规则管理 -->
    <a-card class="rules-management" title="告警规则管理">
      <template #extra>
        <a-space>
          <a-button @click="fetchAlarmRules" :loading="loading">
            <reload-outlined />
            刷新规则
          </a-button>
          <a-button type="primary" @click="showCreateRule">
            <plus-outlined />
            新建规则
          </a-button>
        </a-space>
      </template>

      <a-table
        :columns="ruleColumns"
        :data-source="alarmRules"
        :loading="loading"
        :pagination="rulesPagination"
        row-key="id"
        @change="handleRulesTableChange"
      >
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'sensor_name'">
            <span>{{ getSensorName(record.sensor_id) }}</span>
          </template>
          
          <template v-if="column.key === 'sensor_type'">
            <a-tag color="blue">{{ getSensorType(record.sensor_id) }}</a-tag>
          </template>
          
          <template v-if="column.key === 'rule_type'">
            <a-tag>{{ getRuleTypeText(record.rule_type) }}</a-tag>
          </template>
          
          <template v-if="column.key === 'condition'">
            <span>{{ getConditionText(record.condition) }}</span>
          </template>
          
          <template v-if="column.key === 'threshold'">
            <strong>{{ record.threshold_value }}{{ getSensorUnit(record.sensor_id) }}</strong>
          </template>
          
          <template v-if="column.key === 'severity'">
            <a-tag :color="getSeverityColor(record.severity)">
              {{ getSeverityText(record.severity) }}
            </a-tag>
          </template>
          
          <template v-if="column.key === 'is_active'">
            <a-switch 
              :checked="record.is_active" 
              disabled
              :checked-children="'启用'" 
              :un-checked-children="'禁用'"
            />
          </template>
          
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button 
                size="small" 
                @click="editRule(record)"
                type="primary"
                ghost
              >
                <edit-outlined />
                编辑
              </a-button>
              <a-button 
                size="small" 
                danger
                @click="deleteRule(record)"
              >
                <delete-outlined />
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 告警详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="告警详情"
      :footer="null"
      width="600px"
    >
      <div v-if="selectedAlarm" class="alarm-detail">
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="告警级别">
            <a-tag :color="getAlarmLevelColor(selectedAlarm.level)">
              {{ getAlarmLevelText(selectedAlarm.level) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="告警状态">
            <a-badge
              :status="getAlarmStatusBadge(selectedAlarm.status)"
              :text="getAlarmStatusText(selectedAlarm.status)"
            />
          </a-descriptions-item>
          <a-descriptions-item label="设备名称">
            {{ selectedAlarm.device_name }}
          </a-descriptions-item>
          <a-descriptions-item label="传感器">
            {{ selectedAlarm.sensor_name || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="告警消息">
            {{ selectedAlarm.message }}
          </a-descriptions-item>
          <a-descriptions-item label="触发值">
            {{ selectedAlarm.value }} {{ selectedAlarm.unit || '' }}
          </a-descriptions-item>
          <a-descriptions-item label="阈值">
            {{ selectedAlarm.threshold }} {{ selectedAlarm.unit || '' }}
          </a-descriptions-item>
          <a-descriptions-item label="发生时间">
            {{ formatTime(selectedAlarm.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="处理时间" v-if="selectedAlarm.resolved_at">
            {{ formatTime(selectedAlarm.resolved_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="处理说明" v-if="selectedAlarm.resolution_note">
            {{ selectedAlarm.resolution_note }}
          </a-descriptions-item>
        </a-descriptions>
        
        <div class="alarm-actions" style="margin-top: 16px;">
          <a-space>
            <a-button
              v-if="selectedAlarm.status === 'active'"
              type="primary"
              @click="acknowledgeAlarm(selectedAlarm)"
            >
              确认告警
            </a-button>
            <a-button
              v-if="selectedAlarm.status !== 'resolved'"
              @click="showResolveModal"
            >
              处理告警
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>

    <!-- 处理告警弹窗 -->
    <a-modal
      v-model:open="resolveModalVisible"
      title="处理告警"
      @ok="handleResolveAlarm"
      @cancel="resolveModalVisible = false"
    >
      <a-form layout="vertical">
        <a-form-item label="处理说明">
          <a-textarea
            v-model:value="resolutionNote"
            placeholder="请输入处理说明"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 创建告警规则弹窗 -->
    <a-modal
      v-model:open="createRuleModalVisible"
      title="创建告警规则"
      @ok="handleCreateRule"
      @cancel="resetRuleForm"
      width="700px"
    >
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="规则名称" required>
              <a-input
                v-model:value="newRule.name"
                placeholder="请输入规则名称"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 地点-设备-传感器三级选择 -->
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="选择地点" required>
              <a-select
                v-model:value="newRule.location"
                placeholder="请选择地点"
                style="width: 100%"
                allow-clear
                @change="handleLocationChangeForRule"
              >
                <a-select-option value="">全部地点</a-select-option>
                <a-select-option
                  v-for="location in availableLocations"
                  :key="location"
                  :value="location"
                >
                  {{ location }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="选择设备" required>
              <a-select
                v-model:value="newRule.device_id"
                placeholder="请选择设备"
                style="width: 100%"
                :disabled="!newRule.location"
                @change="handleDeviceChangeForRule"
              >
                <a-select-option
                  v-for="device in filteredDevicesForRule"
                  :key="device.id"
                  :value="device.id"
                >
                  {{ device.name }} ({{ device.location }})
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="选择传感器" required>
              <a-select 
                v-model:value="newRule.sensor_id" 
                placeholder="请选择传感器"
                style="width: 100%"
                :disabled="!newRule.device_id"
                @change="handleSensorChange"
              >
                <a-select-option
                  v-for="sensor in filteredSensorsForRule"
                  :key="sensor.id"
                  :value="sensor.id"
                >
                  {{ sensor.name }} ({{ sensor.sensor_type }}) - {{ sensor.unit }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="规则类型" required>
              <a-select v-model:value="newRule.rule_type" style="width: 100%">
                <a-select-option value="threshold">阈值检测</a-select-option>
                <a-select-option value="change_rate">变化率检测</a-select-option>
                <a-select-option value="pattern">模式检测</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="条件" required>
              <a-select v-model:value="newRule.condition" style="width: 100%">
                <a-select-option value=">">大于 ></a-select-option>
                <a-select-option value="<">小于 <</a-select-option>
                <a-select-option value=">=">大于等于 >=</a-select-option>
                <a-select-option value="<=">小于等于 <=</a-select-option>
                <a-select-option value="==">等于 ==</a-select-option>
                <a-select-option value="!=">不等于 !=</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="阈值" required>
              <a-input-number
                v-model:value="newRule.threshold_value"
                :placeholder="getSelectedSensorUnit()"
                style="width: 100%"
                :precision="2"
                :addon-after="getSelectedSensorUnit()"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="告警级别">
              <a-select v-model:value="newRule.severity" style="width: 100%">
                <a-select-option value="low">低</a-select-option>
                <a-select-option value="medium">中等</a-select-option>
                <a-select-option value="high">高</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="连续触发次数">
              <a-input-number
                v-model:value="newRule.consecutive_count"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="规则状态">
              <a-switch
                v-model:checked="newRule.is_active"
                checked-children="启用"
                un-checked-children="禁用"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="规则描述">
          <a-textarea
            v-model:value="newRule.description"
            placeholder="请输入规则描述"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 编辑告警规则弹窗 -->
    <a-modal
      v-model:open="editRuleModalVisible"
      title="编辑告警规则"
      @ok="handleEditRule"
      @cancel="resetRuleForm"
      width="700px"
    >
      <a-form layout="vertical">
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="规则名称" required>
              <a-input
                v-model:value="newRule.name"
                placeholder="请输入规则名称"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 地点-设备-传感器三级选择 -->
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="选择地点" required>
              <a-select
                v-model:value="newRule.location"
                placeholder="请选择地点"
                style="width: 100%"
                allow-clear
                @change="handleLocationChangeForRule"
              >
                <a-select-option value="">全部地点</a-select-option>
                <a-select-option
                  v-for="location in availableLocations"
                  :key="location"
                  :value="location"
                >
                  {{ location }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="选择设备" required>
              <a-select
                v-model:value="newRule.device_id"
                placeholder="请选择设备"
                style="width: 100%"
                :disabled="!newRule.location"
                @change="handleDeviceChangeForRule"
              >
                <a-select-option
                  v-for="device in filteredDevicesForRule"
                  :key="device.id"
                  :value="device.id"
                >
                  {{ device.name }} ({{ device.location }})
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="选择传感器" required>
              <a-select 
                v-model:value="newRule.sensor_id" 
                placeholder="请选择传感器"
                style="width: 100%"
                :disabled="!newRule.device_id"
                @change="handleSensorChange"
              >
                <a-select-option
                  v-for="sensor in filteredSensorsForRule"
                  :key="sensor.id"
                  :value="sensor.id"
                >
                  {{ sensor.name }} ({{ sensor.sensor_type }}) - {{ sensor.unit }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="规则类型" required>
              <a-select v-model:value="newRule.rule_type" style="width: 100%">
                <a-select-option value="threshold">阈值检测</a-select-option>
                <a-select-option value="change_rate">变化率检测</a-select-option>
                <a-select-option value="pattern">模式检测</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="条件" required>
              <a-select v-model:value="newRule.condition" style="width: 100%">
                <a-select-option value=">">大于 ></a-select-option>
                <a-select-option value="<">小于 <</a-select-option>
                <a-select-option value=">=">大于等于 >=</a-select-option>
                <a-select-option value="<=">小于等于 <=</a-select-option>
                <a-select-option value="==">等于 ==</a-select-option>
                <a-select-option value="!=">不等于 !=</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="阈值" required>
              <a-input-number
                v-model:value="newRule.threshold_value"
                :placeholder="getSelectedSensorUnit()"
                style="width: 100%"
                :precision="2"
                :addon-after="getSelectedSensorUnit()"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="告警级别">
              <a-select v-model:value="newRule.severity" style="width: 100%">
                <a-select-option value="low">低</a-select-option>
                <a-select-option value="medium">中等</a-select-option>
                <a-select-option value="high">高</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="连续触发次数">
              <a-input-number
                v-model:value="newRule.consecutive_count"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="规则状态">
              <a-switch
                v-model:checked="newRule.is_active"
                checked-children="启用"
                un-checked-children="禁用"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="规则描述">
          <a-textarea
            v-model:value="newRule.description"
            placeholder="请输入规则描述"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import StatisticCard from '@/components/ui/StatisticCard.vue';
import { alarmApi } from '@/api/alarm';
import { deviceApi } from '@/api/device';
import { sensorsApi } from '@/api/sensors';
import type { Alarm, Device } from '@/types';
import dayjs, { type Dayjs } from 'dayjs';

const router = useRouter();

// 使用一个简单的通知函数
const showMessage = {
  success: (text: string) => {
    const notification = document.createElement('div');
    notification.innerHTML = `
      <div style="position: fixed; top: 20px; right: 20px; background: #52c41a; color: white; padding: 12px 16px; border-radius: 6px; z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        ✓ ${text}
      </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => document.body.removeChild(notification), 3000);
  },
  error: (text: string) => {
    const notification = document.createElement('div');
    notification.innerHTML = `
      <div style="position: fixed; top: 20px; right: 20px; background: #ff4d4f; color: white; padding: 12px 16px; border-radius: 6px; z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        ✗ ${text}
      </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => document.body.removeChild(notification), 4000);
  },
  warning: (text: string) => {
    const notification = document.createElement('div');
    notification.innerHTML = `
      <div style="position: fixed; top: 20px; right: 20px; background: #faad14; color: white; padding: 12px 16px; border-radius: 6px; z-index: 9999; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        ⚠ ${text}
      </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => document.body.removeChild(notification), 3000);
  },
  info: (text: string) => {
    console.log('INFO:', text);
  }
};

// 使用showMessage作为message
const message = showMessage;

// 响应式数据
const loading = ref(true);
const alarms = ref<Alarm[]>([]);
const devices = ref<Device[]>([]);
const sensors = ref<any[]>([]);
const detailModalVisible = ref(false);
const resolveModalVisible = ref(false);
const createRuleModalVisible = ref(false);
const editRuleModalVisible = ref(false);
const selectedAlarm = ref<Alarm | null>(null);
const selectedRule = ref<any | null>(null);
const resolutionNote = ref('');
const alarmRules = ref<any[]>([]);

// 全局测试数据，用于分页测试 - 改为 ref 以便在模板中访问
const globalTestAlarms = ref<Alarm[]>([]);

// 开发模式标识，用于模板中的条件判断
const isDev = ref(import.meta.env.DEV);

const newRule = reactive({
  name: '',
  description: '',
  location: '',
  device_id: undefined as string | undefined,
  sensor_id: undefined as number | undefined,
  rule_type: 'threshold' as const,
  condition: '>' as const,
  threshold_value: undefined as number | undefined,
  consecutive_count: 1,
  severity: 'medium' as const,
  is_active: true
});

const alarmStats = reactive({
  active: 0,
  today: 0,
  resolved: 0,
  rules: 0
});

const filters = reactive({
  level: undefined as string | undefined,
  status: undefined as string | undefined,
  device: undefined as string | undefined,
  dateRange: null as [Dayjs, Dayjs] | null,
  keyword: ''
});

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true
});

// 告警规则的分页配置
const rulesPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showTotal: (total: number, range: [number, number]) => 
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条规则`
});

// 表格列定义
const alarmColumns = [
  {
    title: '级别',
    dataIndex: 'level',
    key: 'level',
    width: 80
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '设备',
    dataIndex: 'device_name',
    key: 'device_name',
    width: 120,
    ellipsis: true
  },
  {
    title: '传感器',
    dataIndex: 'sensor_name',
    key: 'sensor_name',
    width: 120,
    ellipsis: true
  },
  {
    title: '告警消息',
    dataIndex: 'message',
    key: 'message',
    ellipsis: true
  },
  {
    title: '触发值',
    dataIndex: 'value',
    key: 'value',
    width: 100,
    render: (value: number, record: any) => {
      return `${value} ${record.unit || ''}`;
    }
  },
  {
    title: '发生时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 150
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right'
  }
];

// 规则表格列定义
const ruleColumns = [
  {
    title: '规则名称',
    dataIndex: 'name',
    key: 'name',
    width: 120,
    ellipsis: true
  },
  {
    title: '传感器名称',
    key: 'sensor_name',
    width: 130
  },
  {
    title: '传感器类型',
    key: 'sensor_type',
    width: 100
  },
  {
    title: '规则类型',
    key: 'rule_type',
    width: 100
  },
  {
    title: '条件',
    key: 'condition',
    width: 80
  },
  {
    title: '阈值',
    key: 'threshold',
    width: 100
  },
  {
    title: '级别',
    key: 'severity',
    width: 80
  },
  {
    title: '连续次数',
    dataIndex: 'consecutive_count',
    key: 'consecutive_count',
    width: 90
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    fixed: 'right'
  }
];

// 计算属性
const availableLocations = computed(() => {
  const locations = new Set<string>();
  devices.value.forEach(device => {
    if (device.location) {
      locations.add(device.location);
    }
  });
  return Array.from(locations).sort();
});

const filteredDevicesForRule = computed(() => {
  if (!newRule.location) {
    return devices.value;
  }
  return devices.value.filter(device => device.location === newRule.location);
});

const filteredSensorsForRule = computed(() => {
  if (!newRule.device_id) {
    return [];
  }
  return sensors.value.filter(sensor => sensor.device_id === newRule.device_id);
});

const filteredAlarms = computed(() => {
  let result = alarms.value;
  
  // 应用过滤器
  if (filters.level) {
    result = result.filter(alarm => alarm.level === filters.level);
  }
  
  if (filters.status) {
    result = result.filter(alarm => alarm.status === filters.status);
  }
  
  if (filters.device) {
    result = result.filter(alarm => alarm.device_id === filters.device);
  }
  
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase();
    result = result.filter(alarm =>
      alarm.message.toLowerCase().includes(keyword) ||
      (alarm.device_name && alarm.device_name.toLowerCase().includes(keyword))
    );
  }
  
  if (filters.dateRange && filters.dateRange.length === 2) {
    const [start, end] = filters.dateRange;
    result = result.filter(alarm => {
      const alarmDate = dayjs(alarm.created_at);
      return alarmDate.isAfter(start) && alarmDate.isBefore(end);
    });
  }
  
  return result;
});

// 方法
const checkAuth = () => {
  const token = localStorage.getItem('token');
  if (!token) {
    message.warning('请先登录后访问告警管理');
    router.push('/login');
    return false;
  }
  return true;
};

const createTestAlarms = () => {
  // 只在首次创建测试数据时生成
  if (globalTestAlarms.value.length === 0) {
    const baseAlarms = [
      {
        id: '1',
        device_id: '111',
        sensor_id: '1',
        type: 'threshold',
        level: 'critical',
        status: 'active',
        title: '温度告警',
        message: '土壤温度超过安全阈值',
        description: '传感器检测到土壤温度过高，可能影响作物生长',
        triggered_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        trigger_value: 35.5,
        threshold_value: 30.0,
        device_name: 'TEST_DEVICE',
        sensor_name: 'TEST_DEVICE (111)',
        value: 35.5,
        unit: '°C',
        threshold: 30.0,
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      },
      {
        id: '2',
        device_id: '111',
        sensor_id: '2',
        type: 'threshold',
        level: 'medium',
        status: 'acknowledged',
        title: '湿度告警',
        message: '土壤湿度偏低',
        description: '传感器检测到土壤湿度不足，建议增加灌溉',
        triggered_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        trigger_value: 25.0,
        threshold_value: 30.0,
        device_name: 'TEST_DEVICE',
        sensor_name: 'TEST_DEVICE (111)',
        value: 25.0,
        unit: '%',
        threshold: 30.0,
        created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()
      },
      {
        id: '3',
        device_id: '111',
        type: 'connection',
        level: 'high',
        status: 'resolved',
        title: '设备连接告警',
        message: '设备失去连接',
        description: '设备无法正常通信，已恢复连接',
        triggered_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        resolved_at: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(),
        resolution_note: '重启设备后恢复正常',
        device_name: 'TEST_DEVICE',
        created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
      }
    ];
    
    // 生成更多测试数据，总共25条记录来测试分页
    for (let i = 0; i < 25; i++) {
      const baseAlarm = baseAlarms[i % baseAlarms.length];
      globalTestAlarms.value.push({
        ...baseAlarm,
        id: `${i + 1}`,
        title: `${baseAlarm.title} ${i + 1}`,
        message: `${baseAlarm.message} (第${i + 1}条)`,
        created_at: new Date(Date.now() - i * 60 * 60 * 1000).toISOString(),
        triggered_at: new Date(Date.now() - i * 60 * 60 * 1000).toISOString()
      } as Alarm);
    }
  }
  
  // 根据当前页码和每页大小来切片数据
  const startIndex = (pagination.current - 1) * pagination.pageSize;
  const endIndex = startIndex + pagination.pageSize;
  alarms.value = globalTestAlarms.value.slice(startIndex, endIndex);
  pagination.total = globalTestAlarms.value.length; // 总记录数为25
  
  console.log(`📊 分页测试数据生成:`, {
    '当前页': pagination.current,
    '每页大小': pagination.pageSize,
    '起始索引': startIndex,
    '结束索引': endIndex,
    '总记录数': pagination.total,
    '当前页显示条数': alarms.value.length,
    '全局数据总数': globalTestAlarms.value.length,
    '当前页数据': alarms.value.map(a => ({ id: a.id, title: a.title }))
  });
  
  // 更新统计数据（基于全部数据）
  alarmStats.active = globalTestAlarms.value.filter(a => a.status === 'active').length;
  alarmStats.today = globalTestAlarms.value.filter(a => 
    dayjs(a.created_at).isAfter(dayjs().startOf('day'))
  ).length;
  alarmStats.resolved = globalTestAlarms.value.filter(a => a.status === 'resolved').length;
  alarmStats.rules = 5; // 模拟告警规则数量
};
const fetchAlarms = async () => {
  if (!checkAuth()) return;
  
  try {
    loading.value = true;
    console.log('🚀 开始获取告警列表，当前分页参数:', {
      current: pagination.current,
      pageSize: pagination.pageSize,
      total: pagination.total
    });
    
    const response = await alarmApi.getAlarms({
      page: pagination.current,
      per_page: pagination.pageSize
    });
    
    console.log('📡 API 响应:', response);
    
    // 处理API响应数据
    if (Array.isArray(response)) {
      alarms.value = response;
      pagination.total = response.length;
    } else if (response?.data) {
      if (Array.isArray(response.data)) {
        alarms.value = response.data;
        pagination.total = response.data.length;
      } else {
        // 尝试从分页响应中获取数据
        const responseData = response.data as any;
        if (responseData.items && Array.isArray(responseData.items)) {
          alarms.value = responseData.items;
          pagination.total = responseData.total || responseData.items.length;
        } else {
          alarms.value = [];
          pagination.total = 0;
        }
      }
    } else {
      alarms.value = [];
      pagination.total = 0;
    }
    
    console.log('获取告警成功:', alarms.value);
    
    // 如果没有告警数据，在开发模式下创建测试数据
    if (alarms.value.length === 0 && import.meta.env.DEV) {
      console.log('没有告警数据，创建测试数据');
      createTestAlarms();
      message.info('使用测试告警数据');
    }
  } catch (error) {
    console.error('获取告警列表失败:', error);
    if ((error as any).response?.status === 401) {
      message.error('登录已过期，请重新登录');
      router.push('/login');
    } else {
      message.error('获取告警列表失败，请检查网络连接');
      
      // 在开发模式下提供测试数据
      if (import.meta.env.DEV) {
        console.log('API失败，使用测试告警数据');
        createTestAlarms();
        message.info('网络连接失败，使用测试告警数据');
      }
    }
  } finally {
    loading.value = false;
  }
};

const fetchAlarmStats = async () => {
  if (!checkAuth()) return;
  
  try {
    const response = await alarmApi.getAlarmStats();
    if (response?.data) {
      Object.assign(alarmStats, response.data);
    }
  } catch (error) {
    console.error('获取告警统计失败:', error);
    // 在开发模式下提供默认统计数据
    if (import.meta.env.DEV) {
      alarmStats.active = alarms.value.filter(a => a.status === 'active').length;
      alarmStats.today = alarms.value.filter(a => 
        dayjs(a.created_at).isAfter(dayjs().startOf('day'))
      ).length;
      alarmStats.resolved = alarms.value.filter(a => a.status === 'resolved').length;
      alarmStats.rules = 5;
    }
  }
};

const fetchSensors = async () => {
  try {
    const response = await sensorsApi.getSensors();
    if (Array.isArray(response)) {
      sensors.value = response;
    } else if (response?.data) {
      sensors.value = Array.isArray(response.data) ? response.data : [];
    } else {
      sensors.value = [];
    }
    
    // 如果没有传感器数据，在开发模式下创建测试数据
    if (sensors.value.length === 0 && import.meta.env.DEV) {
      sensors.value = [
        {
          id: 1,
          name: '土壤温度传感器',
          sensor_type: 'soil_temperature',
          unit: '°C',
          device_id: '111',
          status: 'active'
        },
        {
          id: 2,
          name: '土壤湿度传感器',
          sensor_type: 'soil_moisture',
          unit: '%',
          device_id: '111',
          status: 'active'
        },
        {
          id: 3,
          name: '环境温度传感器',
          sensor_type: 'air_temperature',
          unit: '°C',
          device_id: '112',
          status: 'active'
        },
        {
          id: 4,
          name: '环境湿度传感器',
          sensor_type: 'air_humidity',
          unit: '%',
          device_id: '112',
          status: 'active'
        },
        {
          id: 5,
          name: '光照强度传感器',
          sensor_type: 'light_intensity',
          unit: 'lux',
          device_id: '113',
          status: 'active'
        }
      ];
      message.info('使用测试传感器数据');
    }
    
    console.log('获取传感器成功:', sensors.value);
  } catch (error) {
    console.error('获取传感器列表失败:', error);
    
    // 在开发模式下提供测试数据
    if (import.meta.env.DEV) {
      sensors.value = [
        {
          id: 1,
          name: '土壤温度传感器',
          sensor_type: 'soil_temperature',
          unit: '°C',
          device_id: '111',
          status: 'active'
        },
        {
          id: 2,
          name: '土壤湿度传感器',
          sensor_type: 'soil_moisture',
          unit: '%',
          device_id: '111',
          status: 'active'
        },
        {
          id: 3,
          name: '环境温度传感器',
          sensor_type: 'air_temperature',
          unit: '°C',
          device_id: '112',
          status: 'active'
        },
        {
          id: 4,
          name: '环境湿度传感器',
          sensor_type: 'air_humidity',
          unit: '%',
          device_id: '112',
          status: 'active'
        },
        {
          id: 5,
          name: '光照强度传感器',
          sensor_type: 'light_intensity',
          unit: 'lux',
          device_id: '113',
          status: 'active'
        }
      ];
      message.info('使用测试传感器数据');
    } else {
      sensors.value = [];
    }
  }
};

const fetchAlarmRules = async () => {
  try {
    console.log('开始获取告警规则列表...');
    const response = await alarmApi.getAlarmRules();
    console.log('告警规则API响应:', response);
    
    if (Array.isArray(response)) {
      alarmRules.value = response;
    } else if (response?.data) {
      alarmRules.value = Array.isArray(response.data) ? response.data : [];
    } else {
      alarmRules.value = [];
    }
    
    console.log('获取告警规则成功:', alarmRules.value);
    // 更新统计中的规则数量
    alarmStats.rules = alarmRules.value.length;
    // 更新告警规则分页总数
    rulesPagination.total = alarmRules.value.length;
    console.log('🔧 告警规则分页总数更新:', rulesPagination.total);
  } catch (error) {
    console.error('获取告警规则列表失败:', error);
    alarmRules.value = [];
    rulesPagination.total = 0;
  }
};

const handleSensorChange = (sensorId: number) => {
  // 传感器改变时的处理逻辑
  console.log('选择的传感器ID:', sensorId);
  
  // 找到选中的传感器，获取其单位信息
  const selectedSensor = sensors.value.find(s => s.id === sensorId);
  if (selectedSensor) {
    console.log('选中传感器信息:', selectedSensor);
    message.info(`已选择传感器: ${selectedSensor.name} (单位: ${selectedSensor.unit})`);
  }
};

const handleLocationChangeForRule = (location: string) => {
  console.log('地点选择改变:', location);
  newRule.device_id = undefined;
  newRule.sensor_id = undefined;
};

const handleDeviceChangeForRule = (deviceId: string) => {
  console.log('设备选择改变:', deviceId);
  newRule.sensor_id = undefined;
};

const fetchDevices = async () => {
  try {
    const response = await deviceApi.getDevices();
    if (Array.isArray(response)) {
      devices.value = response;
    } else if (response?.data) {
      devices.value = Array.isArray(response.data) ? response.data : [];
    } else {
      devices.value = [];
    }
    
    // 如果没有设备数据，在开发模式下创建测试数据
    if (devices.value.length === 0 && import.meta.env.DEV) {
      const now = new Date().toISOString();
      devices.value = [
        {
          id: '111',
          name: 'TEST_DEVICE',
          type: 'sensor_node',
          location: '温室A区',
          status: 'online' as const,
          last_seen: now,
          created_at: now,
          updated_at: now
        },
        {
          id: '112',
          name: 'DEVICE_B',
          type: 'sensor_node', 
          location: '温室B区',
          status: 'online' as const,
          last_seen: now,
          created_at: now,
          updated_at: now
        },
        {
          id: '113',
          name: 'DEVICE_C',
          type: 'sensor_node',
          location: '户外监测点',
          status: 'online' as const,
          last_seen: now,
          created_at: now,
          updated_at: now
        }
      ];
      console.log('使用测试设备数据:', devices.value);
      message.info('使用测试设备数据');
    }
  } catch (error) {
    console.error('获取设备列表失败:', error);
    
    // 在开发模式下提供测试数据
    if (import.meta.env.DEV) {
      const now = new Date().toISOString();
      devices.value = [
        {
          id: '111',
          name: 'TEST_DEVICE',
          type: 'sensor_node',
          location: '温室A区',
          status: 'online' as const,
          last_seen: now,
          created_at: now,
          updated_at: now
        },
        {
          id: '112',
          name: 'DEVICE_B',
          type: 'sensor_node',
          location: '温室B区', 
          status: 'online' as const,
          last_seen: now,
          created_at: now,
          updated_at: now
        },
        {
          id: '113',
          name: 'DEVICE_C',
          type: 'sensor_node',
          location: '户外监测点',
          status: 'online' as const,
          last_seen: now,
          created_at: now,
          updated_at: now
        }
      ];
      console.log('API失败，使用测试设备数据:', devices.value);
      message.info('网络连接失败，使用测试设备数据');
    } else {
      devices.value = [];
    }
  }
};

const refreshAlarms = () => {
  fetchAlarms();
  fetchAlarmStats();
};

const handleFilterChange = () => {
  pagination.current = 1;
  // 在实际应用中，这里应该调用API进行过滤
  // 现在只是客户端过滤
};

const handleTableChange = (pag: any) => {
  console.log('🔄 handleTableChange 被调用:', {
    '传入的pag参数': pag,
    '当前pagination': { ...pagination },
    '即将设置的current': pag.current,
    '即将设置的pageSize': pag.pageSize
  });
  
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  
  console.log('🔄 pagination 更新后:', { ...pagination });
  
  fetchAlarms();
};

// 告警规则表格分页处理
const handleRulesTableChange = (pag: any) => {
  console.log('🔧 告警规则分页改变:', pag);
  rulesPagination.current = pag.current;
  rulesPagination.pageSize = pag.pageSize;
  rulesPagination.total = pag.total;
  // 这里可以添加实际的规则数据获取逻辑
};

const acknowledgeAlarm = async (alarm: Alarm) => {
  try {
    await alarmApi.resolveAlarm(alarm.id);
    message.success('告警已确认');
    refreshAlarms();
    if (detailModalVisible.value && selectedAlarm.value) {
      selectedAlarm.value = { 
        ...selectedAlarm.value, 
        status: 'acknowledged' as const
      };
    }
  } catch (error) {
    message.error('确认告警失败');
  }
};

const resolveAlarm = (alarm: Alarm) => {
  selectedAlarm.value = alarm;
  resolutionNote.value = '';
  resolveModalVisible.value = true;
};

const handleResolveAlarm = async () => {
  if (!selectedAlarm.value) return;
  
  try {
    await alarmApi.resolveAlarm(selectedAlarm.value.id, resolutionNote.value);
    message.success('告警已处理');
    resolveModalVisible.value = false;
    refreshAlarms();
    if (detailModalVisible.value && selectedAlarm.value) {
      selectedAlarm.value = {
        ...selectedAlarm.value,
        status: 'resolved' as const,
        resolved_at: new Date().toISOString(),
        resolution_note: resolutionNote.value
      };
    }
  } catch (error) {
    message.error('处理告警失败');
  }
};

const viewAlarmDetail = (alarm: Alarm) => {
  selectedAlarm.value = alarm;
  detailModalVisible.value = true;
};

const showResolveModal = () => {
  detailModalVisible.value = false;
  resolveModalVisible.value = true;
};

const showCreateRule = () => {
  // 创建告警规则的简单表单
  createRuleModalVisible.value = true;
};

const handleCreateRule = async () => {
  console.log('开始创建告警规则，当前newRule:', newRule);
  
  if (!newRule.name || !newRule.sensor_id || newRule.threshold_value === undefined) {
    console.log('验证失败，缺少必填字段');
    message.error('请填写必填字段：规则名称、传感器和阈值');
    return;
  }

  try {
    // 确保必填字段不为undefined，添加后端需要的通知字段默认值
    const ruleData = {
      name: newRule.name,
      description: newRule.description || '',
      sensor_id: Number(newRule.sensor_id), // 确保转换为number类型
      rule_type: newRule.rule_type,
      condition: newRule.condition,
      threshold_value: newRule.threshold_value as number,
      consecutive_count: newRule.consecutive_count || 1,
      severity: newRule.severity,
      is_active: newRule.is_active,
      // 添加后端API需要的默认通知配置
      email_enabled: true,  // 默认启用邮件通知
      webhook_enabled: false,
      webhook_url: null
    };
    
    console.log('正在创建告警规则，发送数据:', ruleData);
    console.log('调用 alarmApi.createAlarmRule...');
    
    const response = await alarmApi.createAlarmRule(ruleData);
    console.log('创建告警规则响应:', response);
    
    message.success('告警规则创建成功');
    createRuleModalVisible.value = false;
    resetRuleForm();
    // 重新获取规则列表
    fetchAlarmRules();
  } catch (error) {
    console.error('创建告警规则失败，错误详情:', error);
    console.error('错误类型:', typeof error);
    console.error('错误构造函数:', error?.constructor?.name);
    
    // 显示具体的错误信息
    if (error && typeof error === 'object' && 'response' in error) {
      const apiError = error as any;
      console.error('API错误响应:', apiError.response);
      if (apiError.response?.data?.message) {
        message.error(`创建失败: ${apiError.response.data.message}`);
      } else if (apiError.response?.status === 401) {
        message.error('登录已过期，请重新登录');
        router.push('/login');
      } else {
        message.error('创建告警规则失败，请检查网络连接');
      }
    } else {
      message.error('创建告警规则失败');
    }
  }
};

const editRule = async (rule: any) => {
  selectedRule.value = rule;
  
  // 根据传感器ID找到对应的设备和位置
  const sensor = sensors.value.find(s => s.id === rule.sensor_id);
  let location = '';
  let device_id = '';
  
  if (sensor) {
    device_id = sensor.device_id;
    const device = devices.value.find(d => d.id === sensor.device_id);
    if (device && device.location) {
      location = device.location;
    }
  }
  
  // 填充编辑表单
  Object.assign(newRule, {
    name: rule.name,
    description: rule.description || '',
    location: location,
    device_id: device_id, 
    sensor_id: rule.sensor_id,
    rule_type: rule.rule_type,
    condition: rule.condition,
    threshold_value: rule.threshold_value,
    consecutive_count: rule.consecutive_count || 1,
    severity: rule.severity,
    is_active: rule.is_active
  });
  
  // 更新过滤后的设备和传感器列表
  if (location) {
    handleLocationChangeForRule(location);
    await nextTick();
    if (device_id) {
      handleDeviceChangeForRule(device_id);
    }
  }
  
  editRuleModalVisible.value = true;
};

const deleteRule = async (rule: any) => {
  // 显示确认对话框
  if (window.confirm(`确定要删除告警规则 "${rule.name}" 吗？此操作不可恢复。`)) {
    try {
      console.log('删除告警规则:', rule.id);
      await alarmApi.deleteAlarmRule(rule.id);
      message.success('告警规则删除成功');
      // 重新获取规则列表
      fetchAlarmRules();
    } catch (error) {
      console.error('删除告警规则失败:', error);
      message.error('删除告警规则失败');
    }
  }
};

const handleEditRule = async () => {
  if (!newRule.name || !newRule.sensor_id || newRule.threshold_value === undefined) {
    message.error('请填写必填字段：规则名称、传感器和阈值');
    return;
  }

  try {
    const ruleData = {
      name: newRule.name,
      description: newRule.description || '',
      sensor_id: Number(newRule.sensor_id),
      rule_type: newRule.rule_type,
      condition: newRule.condition,
      threshold_value: newRule.threshold_value as number,
      consecutive_count: newRule.consecutive_count || 1,
      severity: newRule.severity,
      is_active: newRule.is_active,
      email_enabled: true,
      webhook_enabled: false,
      webhook_url: null
    };
    
    console.log('更新告警规则:', selectedRule.value?.id, ruleData);
    await alarmApi.updateAlarmRule(selectedRule.value?.id, ruleData);
    message.success('告警规则更新成功');
    editRuleModalVisible.value = false;
    resetRuleForm();
    fetchAlarmRules();
  } catch (error) {
    console.error('更新告警规则失败:', error);
    message.error('更新告警规则失败');
  }
};

const resetRuleForm = () => {
  newRule.name = '';
  newRule.description = '';
  newRule.location = '';
  newRule.device_id = undefined;
  newRule.sensor_id = undefined;
  newRule.rule_type = 'threshold';
  newRule.condition = '>';
  newRule.threshold_value = undefined;
  newRule.consecutive_count = 1;
  newRule.severity = 'medium';
  newRule.is_active = true;
  selectedRule.value = null;
  createRuleModalVisible.value = false;
  editRuleModalVisible.value = false;
};

const getAlarmLevelColor = (level: string) => {
  switch (level) {
    case 'critical':
      return 'red';
    case 'high':
      return 'orange';
    case 'medium':
      return 'yellow';
    case 'low':
      return 'blue';
    default:
      return 'default';
  }
};

const getAlarmLevelText = (level: string) => {
  switch (level) {
    case 'critical':
      return '严重';
    case 'high':
      return '高';
    case 'medium':
      return '中等';
    case 'low':
      return '低';
    default:
      return '未知';
  }
};

const getAlarmStatusBadge = (status: string) => {
  switch (status) {
    case 'active':
      return 'error';
    case 'acknowledged':
      return 'warning';
    case 'resolved':
      return 'success';
    default:
      return 'default';
  }
};

const getAlarmStatusText = (status: string) => {
  switch (status) {
    case 'active':
      return '活跃';
    case 'acknowledged':
      return '已确认';
    case 'resolved':
      return '已处理';
    default:
      return '未知';
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'high':
      return 'red';
    case 'medium':
      return 'orange';
    case 'low':
      return 'blue';
    default:
      return 'default';
  }
};

const getSeverityText = (severity: string) => {
  switch (severity) {
    case 'high':
      return '高';
    case 'medium':
      return '中等';
    case 'low':
      return '低';
    default:
      return '未知';
  }
};

// 根据传感器ID获取传感器名称
const getSensorName = (sensorId: number) => {
  const sensor = sensors.value.find(s => s.id === sensorId);
  return sensor?.name || `传感器 ${sensorId}`;
};

// 根据传感器ID获取传感器类型
const getSensorType = (sensorId: number) => {
  const sensor = sensors.value.find(s => s.id === sensorId);
  return sensor?.sensor_type || '未知类型';
};

// 根据传感器ID获取传感器单位
const getSensorUnit = (sensorId: number) => {
  const sensor = sensors.value.find(s => s.id === sensorId);
  return sensor?.unit || '';
};

// 获取规则类型的中文显示
const getRuleTypeText = (ruleType: string) => {
  switch (ruleType) {
    case 'threshold':
      return '阈值检测';
    case 'change_rate':
      return '变化率检测';
    case 'pattern':
      return '模式检测';
    default:
      return ruleType;
  }
};

// 获取条件的中文显示
const getConditionText = (condition: string) => {
  switch (condition) {
    case '>':
      return '大于';
    case '<':
      return '小于';
    case '>=':
      return '大于等于';
    case '<=':
      return '小于等于';
    case '==':
      return '等于';
    case '!=':
      return '不等于';
    default:
      return condition;
  }
};

const getSelectedSensorUnit = () => {
  if (newRule.sensor_id) {
    const sensor = sensors.value.find(s => s.id === newRule.sensor_id);
    return sensor?.unit || '';
  }
  return '';
};

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

// 生命周期
onMounted(() => {
  // 先检查认证状态
  if (checkAuth()) {
    fetchDevices();
    fetchSensors();
    fetchAlarms();
    fetchAlarmStats();
    fetchAlarmRules(); // 获取告警规则列表
  }
});
</script>

<style lang="less" scoped>
.alarms-page {
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

  .stats-row {
    margin-bottom: 16px;
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .alarms-list {
    .alarm-detail {
      .alarm-actions {
        text-align: right;
      }
    }
  }

  .rules-management {
    margin-top: 24px;
    
    .ant-card-body {
      padding: 0;
    }
    
    .ant-table {
      margin: 0;
      
      .ant-table-thead > tr > th {
        background: #f5f5f5;
        color: #333;
        font-weight: 500;
      }
      
      .ant-table-tbody > tr > td {
        vertical-align: middle;
      }
    }
  }
}

@media (max-width: 768px) {
  .alarms-page {
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-actions {
          width: 100%;
        }
      }
    }

    .filter-card {
      :deep(.ant-row) {
        flex-direction: column;
        gap: 12px;
        
        .ant-col {
          width: 100% !important;
          flex: none !important;
        }
      }
    }
  }
}
</style>
