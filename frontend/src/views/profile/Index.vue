<template>
  <div class="profile-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>个人中心</h1>
      <p class="page-description">管理您的个人信息和系统偏好设置</p>
    </div>

    <a-row :gutter="24">
      <!-- 个人信息卡片 -->
      <a-col :xs="24" :lg="8">
        <a-card class="profile-card">
          <div class="profile-header">
            <div class="avatar-section">
              <a-avatar :size="80" :src="userInfo.avatar">
                <template #icon>
                  <user-outlined />
                </template>
              </a-avatar>
              <a-button type="link" size="small" @click="showAvatarUpload">
                更换头像
              </a-button>
            </div>
            <div class="user-info">
              <h3>{{ userInfo.username }}</h3>
              <p>{{ userInfo.email }}</p>
              <a-tag :color="getRoleColor(userInfo.role)">
                {{ getRoleText(userInfo.role) }}
              </a-tag>
            </div>
          </div>

          <a-divider />

          <div class="stats-section">
            <a-row :gutter="16">
              <a-col :span="8">
                <div class="stat-item">
                  <div class="stat-value">{{ userStats.devices }}</div>
                  <div class="stat-label">管理设备</div>
                </div>
              </a-col>
              <a-col :span="8">
                <div class="stat-item">
                  <div class="stat-value">{{ userStats.alarms }}</div>
                  <div class="stat-label">处理告警</div>
                </div>
              </a-col>
              <a-col :span="8">
                <div class="stat-item">
                  <div class="stat-value">{{ userStats.days }}</div>
                  <div class="stat-label">使用天数</div>
                </div>
              </a-col>
            </a-row>
          </div>

          <a-divider />

          <div class="account-info">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="用户ID">
                {{ userInfo.id }}
              </a-descriptions-item>
              <a-descriptions-item label="注册时间">
                {{ formatTime(userInfo.created_at) }}
              </a-descriptions-item>
              <a-descriptions-item label="最后登录">
                {{ formatTime(userInfo.last_login) }}
              </a-descriptions-item>
              <a-descriptions-item label="登录次数">
                {{ userInfo.login_count || 0 }} 次
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </a-card>
      </a-col>

      <!-- 主要内容区域 -->
      <a-col :xs="24" :lg="16">
        <a-tabs v-model:activeKey="activeTab" type="card">
          <!-- 基本信息 -->
          <a-tab-pane key="basic" tab="基本信息">
            <a-card>
              <a-form
                ref="basicFormRef"
                :model="basicForm"
                :rules="basicRules"
                layout="vertical"
              >
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="用户名" name="username">
                      <a-input v-model:value="basicForm.username" placeholder="请输入用户名" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="邮箱" name="email">
                      <a-input v-model:value="basicForm.email" placeholder="请输入邮箱" />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="手机号" name="phone">
                      <a-input v-model:value="basicForm.phone" placeholder="请输入手机号" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="部门" name="department">
                      <a-input v-model:value="basicForm.department" placeholder="请输入部门" />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-form-item label="个人简介" name="bio">
                  <a-textarea
                    v-model:value="basicForm.bio"
                    placeholder="请输入个人简介"
                    :rows="3"
                  />
                </a-form-item>

                <a-form-item>
                  <a-space>
                    <a-button type="primary" @click="saveBasicInfo" :loading="basicLoading">
                      保存修改
                    </a-button>
                    <a-button @click="resetBasicForm">
                      重置
                    </a-button>
                  </a-space>
                </a-form-item>
              </a-form>
            </a-card>
          </a-tab-pane>

          <!-- 安全设置 -->
          <a-tab-pane key="security" tab="安全设置">
            <a-card title="修改密码">
              <a-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                layout="vertical"
              >
                <a-form-item label="当前密码" name="current_password">
                  <a-input-password
                    v-model:value="passwordForm.current_password"
                    placeholder="请输入当前密码"
                  />
                </a-form-item>

                <a-form-item label="新密码" name="new_password">
                  <a-input-password
                    v-model:value="passwordForm.new_password"
                    placeholder="请输入新密码"
                  />
                </a-form-item>

                <a-form-item label="确认新密码" name="confirm_password">
                  <a-input-password
                    v-model:value="passwordForm.confirm_password"
                    placeholder="请再次输入新密码"
                  />
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" @click="changePassword" :loading="passwordLoading">
                    修改密码
                  </a-button>
                </a-form-item>
              </a-form>
            </a-card>

            <a-card title="两步验证" style="margin-top: 16px;">
              <a-descriptions :column="1">
                <a-descriptions-item label="状态">
                  <a-badge
                    :status="userInfo.two_factor_enabled ? 'success' : 'default'"
                    :text="userInfo.two_factor_enabled ? '已启用' : '未启用'"
                  />
                </a-descriptions-item>
                <a-descriptions-item label="操作">
                  <a-button
                    v-if="!userInfo.two_factor_enabled"
                    type="primary"
                    size="small"
                    @click="enableTwoFactor"
                  >
                    启用两步验证
                  </a-button>
                  <a-button
                    v-else
                    danger
                    size="small"
                    @click="disableTwoFactor"
                  >
                    禁用两步验证
                  </a-button>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>

            <a-card title="登录历史" style="margin-top: 16px;">
              <a-table
                :columns="loginHistoryColumns"
                :data-source="loginHistory"
                :pagination="{ pageSize: 5 }"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'login_time'">
                    {{ formatTime(record.login_time) }}
                  </template>
                  <template v-if="column.key === 'status'">
                    <a-tag :color="record.success ? 'green' : 'red'">
                      {{ record.success ? '成功' : '失败' }}
                    </a-tag>
                  </template>
                </template>
              </a-table>
            </a-card>
          </a-tab-pane>

          <!-- 偏好设置 -->
          <a-tab-pane key="preferences" tab="偏好设置">
            <a-card>
              <a-form layout="vertical">
                <a-form-item label="语言设置">
                  <a-select v-model:value="preferences.language" style="width: 200px;">
                    <a-select-option value="zh-CN">中文简体</a-select-option>
                    <a-select-option value="en-US">English</a-select-option>
                  </a-select>
                </a-form-item>

                <a-form-item label="时区设置">
                  <a-select v-model:value="preferences.timezone" style="width: 200px;">
                    <a-select-option value="Asia/Shanghai">北京时间 (UTC+8)</a-select-option>
                    <a-select-option value="UTC">UTC 时间</a-select-option>
                    <a-select-option value="America/New_York">美东时间</a-select-option>
                  </a-select>
                </a-form-item>

                <a-form-item label="主题设置">
                  <a-radio-group v-model:value="preferences.theme">
                    <a-radio value="light">浅色主题</a-radio>
                    <a-radio value="dark">深色主题</a-radio>
                    <a-radio value="auto">跟随系统</a-radio>
                  </a-radio-group>
                </a-form-item>

                <a-form-item label="通知设置">
                  <a-space direction="vertical">
                    <a-checkbox v-model:checked="preferences.email_notifications">
                      邮件通知
                    </a-checkbox>
                    <a-checkbox v-model:checked="preferences.browser_notifications">
                      浏览器通知
                    </a-checkbox>
                    <a-checkbox v-model:checked="preferences.alarm_notifications">
                      告警通知
                    </a-checkbox>
                  </a-space>
                </a-form-item>

                <a-form-item label="数据刷新间隔">
                  <a-select v-model:value="preferences.refresh_interval" style="width: 200px;">
                    <a-select-option value="5">5秒</a-select-option>
                    <a-select-option value="10">10秒</a-select-option>
                    <a-select-option value="30">30秒</a-select-option>
                    <a-select-option value="60">1分钟</a-select-option>
                  </a-select>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" @click="savePreferences" :loading="preferencesLoading">
                    保存设置
                  </a-button>
                </a-form-item>
              </a-form>
            </a-card>
          </a-tab-pane>

          <!-- 活动日志 -->
          <a-tab-pane key="activity" tab="活动日志">
            <a-card>
              <a-timeline>
                <a-timeline-item
                  v-for="activity in activities"
                  :key="activity.id"
                  :color="getActivityColor(activity.type)"
                >
                  <div class="activity-item">
                    <div class="activity-content">
                      <strong>{{ activity.action }}</strong>
                      <p>{{ activity.description }}</p>
                    </div>
                    <div class="activity-time">
                      {{ formatTime(activity.created_at) }}
                    </div>
                  </div>
                </a-timeline-item>
              </a-timeline>
            </a-card>
          </a-tab-pane>
        </a-tabs>
      </a-col>
    </a-row>

    <!-- 头像上传弹窗 -->
    <a-modal
      v-model:open="avatarModalVisible"
      title="更换头像"
      @ok="handleAvatarUpload"
      @cancel="avatarModalVisible = false"
    >
      <a-upload
        v-model:file-list="avatarFileList"
        :before-upload="beforeAvatarUpload"
        list-type="picture-card"
        :max-count="1"
      >
        <div v-if="avatarFileList.length < 1">
          <plus-outlined />
          <div style="margin-top: 8px">上传头像</div>
        </div>
      </a-upload>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { message } from 'ant-design-vue';
import { useAuthStore } from '@/stores/auth';
import { userApi } from '@/api/user';
import dayjs from 'dayjs';

const authStore = useAuthStore();

// 响应式数据
const activeTab = ref('basic');
const basicLoading = ref(false);
const passwordLoading = ref(false);
const preferencesLoading = ref(false);
const avatarModalVisible = ref(false);
const avatarFileList = ref([]);

const userStats = reactive({
  devices: 12,
  alarms: 45,
  days: 89
});

const basicForm = reactive({
  username: '',
  email: '',
  phone: '',
  department: '',
  bio: ''
});

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
});

const preferences = reactive({
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  theme: 'light',
  email_notifications: true,
  browser_notifications: true,
  alarm_notifications: true,
  refresh_interval: '30'
});

const loginHistory = ref([]);
const activities = ref([]);

// 计算属性
const userInfo = computed(() => authStore.user || {});

// 表单验证规则
const basicRules = {
  username: [
    { required: true, message: '请输入用户名' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符' }
  ],
  email: [
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '请输入有效的邮箱地址' }
  ]
};

const passwordRules = {
  current_password: [
    { required: true, message: '请输入当前密码' }
  ],
  new_password: [
    { required: true, message: '请输入新密码' },
    { min: 6, max: 32, message: '密码长度为6-32个字符' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码' },
    {
      validator: (rule: any, value: string) => {
        if (value !== passwordForm.new_password) {
          return Promise.reject('两次输入的密码不一致');
        }
        return Promise.resolve();
      }
    }
  ]
};

// 登录历史表格列
const loginHistoryColumns = [
  {
    title: '登录时间',
    dataIndex: 'login_time',
    key: 'login_time'
  },
  {
    title: 'IP地址',
    dataIndex: 'ip_address',
    key: 'ip_address'
  },
  {
    title: '设备/浏览器',
    dataIndex: 'user_agent',
    key: 'user_agent',
    ellipsis: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 80
  }
];

// 方法
const saveBasicInfo = async () => {
  try {
    basicLoading.value = true;
    await userApi.updateProfile(basicForm);
    message.success('基本信息保存成功');
    // 更新 store 中的用户信息
    await authStore.getCurrentUser();
  } catch (error) {
    message.error('保存失败');
  } finally {
    basicLoading.value = false;
  }
};

const resetBasicForm = () => {
  Object.assign(basicForm, {
    username: userInfo.value.username || '',
    email: userInfo.value.email || '',
    phone: userInfo.value.phone || '',
    department: userInfo.value.department || '',
    bio: userInfo.value.bio || ''
  });
};

const changePassword = async () => {
  try {
    passwordLoading.value = true;
    await userApi.changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password
    });
    message.success('密码修改成功');
    // 清空表单
    Object.assign(passwordForm, {
      current_password: '',
      new_password: '',
      confirm_password: ''
    });
  } catch (error) {
    message.error('密码修改失败');
  } finally {
    passwordLoading.value = false;
  }
};

const savePreferences = async () => {
  try {
    preferencesLoading.value = true;
    await userApi.updatePreferences(preferences);
    message.success('偏好设置保存成功');
  } catch (error) {
    message.error('保存失败');
  } finally {
    preferencesLoading.value = false;
  }
};

const showAvatarUpload = () => {
  avatarModalVisible.value = true;
};

const beforeAvatarUpload = (file: any) => {
  const isImage = file.type.startsWith('image/');
  if (!isImage) {
    message.error('只能上传图片文件');
    return false;
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过2MB');
    return false;
  }
  return false; // 阻止自动上传
};

const handleAvatarUpload = async () => {
  if (avatarFileList.value.length === 0) {
    message.warning('请选择要上传的头像');
    return;
  }

  try {
    const formData = new FormData();
    formData.append('avatar', avatarFileList.value[0].originFileObj);
    
    await userApi.uploadAvatar(formData);
    message.success('头像上传成功');
    avatarModalVisible.value = false;
    avatarFileList.value = [];
    
    // 刷新用户信息
    await authStore.getCurrentUser();
  } catch (error) {
    message.error('头像上传失败');
  }
};

const enableTwoFactor = () => {
  message.info('两步验证功能开发中...');
};

const disableTwoFactor = () => {
  message.info('两步验证功能开发中...');
};

const getRoleColor = (role: string) => {
  switch (role) {
    case 'admin':
      return 'red';
    case 'manager':
      return 'orange';
    case 'user':
      return 'blue';
    default:
      return 'default';
  }
};

const getRoleText = (role: string) => {
  switch (role) {
    case 'admin':
      return '管理员';
    case 'manager':
      return '管理者';
    case 'user':
      return '用户';
    default:
      return '未知';
  }
};

const getActivityColor = (type: string) => {
  switch (type) {
    case 'login':
      return 'green';
    case 'device':
      return 'blue';
    case 'alarm':
      return 'red';
    case 'settings':
      return 'orange';
    default:
      return 'gray';
  }
};

const formatTime = (time: string) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

const fetchUserStats = async () => {
  try {
    const response = await userApi.getUserStats();
    Object.assign(userStats, response.data);
  } catch (error) {
    console.error('获取用户统计失败:', error);
  }
};

const fetchLoginHistory = async () => {
  try {
    const response = await userApi.getLoginHistory();
    loginHistory.value = response.data;
  } catch (error) {
    console.error('获取登录历史失败:', error);
  }
};

const fetchActivities = async () => {
  try {
    const response = await userApi.getUserActivities();
    activities.value = response.data;
  } catch (error) {
    console.error('获取活动日志失败:', error);
  }
};

// 生命周期
onMounted(() => {
  resetBasicForm();
  fetchUserStats();
  fetchLoginHistory();
  fetchActivities();
});
</script>

<style lang="less" scoped>
.profile-page {
  .page-header {
    margin-bottom: 24px;
    
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

  .profile-card {
    .profile-header {
      text-align: center;

      .avatar-section {
        margin-bottom: 16px;

        .ant-btn {
          margin-top: 8px;
        }
      }

      .user-info {
        h3 {
          margin: 0 0 4px 0;
          font-size: 18px;
          color: #262626;
        }

        p {
          margin: 0 0 8px 0;
          color: #8c8c8c;
        }
      }
    }

    .stats-section {
      .stat-item {
        text-align: center;

        .stat-value {
          font-size: 20px;
          font-weight: 600;
          color: #262626;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 12px;
          color: #8c8c8c;
        }
      }
    }

    .account-info {
      :deep(.ant-descriptions-item-label) {
        font-size: 12px;
      }

      :deep(.ant-descriptions-item-content) {
        font-size: 12px;
      }
    }
  }

  .activity-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;

    .activity-content {
      flex: 1;

      strong {
        color: #262626;
      }

      p {
        margin: 4px 0 0 0;
        color: #8c8c8c;
        font-size: 12px;
      }
    }

    .activity-time {
      font-size: 12px;
      color: #8c8c8c;
      white-space: nowrap;
      margin-left: 16px;
    }
  }
}

@media (max-width: 768px) {
  .profile-page {
    :deep(.ant-col) {
      margin-bottom: 16px;
    }
  }
}
</style>
