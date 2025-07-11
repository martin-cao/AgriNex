<template>
  <div class="settings-container">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>⚙️ 系统设置</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="通用设置" name="general">
          <el-form :model="generalSettings" label-width="120px">
            <el-form-item label="系统语言">
              <el-select v-model="generalSettings.language">
                <el-option label="中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="时间格式">
              <el-radio-group v-model="generalSettings.timeFormat">
                <el-radio label="24h">24小时制</el-radio>
                <el-radio label="12h">12小时制</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="主题模式">
              <el-radio-group v-model="generalSettings.theme">
                <el-radio label="light">浅色</el-radio>
                <el-radio label="dark">深色</el-radio>
                <el-radio label="auto">自动</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveGeneralSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="通知设置" name="notifications">
          <el-form :model="notificationSettings" label-width="120px">
            <el-form-item label="邮件通知">
              <el-switch v-model="notificationSettings.email" />
            </el-form-item>
            
            <el-form-item label="桌面通知">
              <el-switch v-model="notificationSettings.desktop" />
            </el-form-item>
            
            <el-form-item label="告警通知">
              <el-switch v-model="notificationSettings.alerts" />
            </el-form-item>
            
            <el-form-item label="系统维护通知">
              <el-switch v-model="notificationSettings.maintenance" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveNotificationSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="数据设置" name="data">
          <el-form :model="dataSettings" label-width="120px">
            <el-form-item label="数据刷新间隔">
              <el-select v-model="dataSettings.refreshInterval">
                <el-option label="5秒" value="5" />
                <el-option label="10秒" value="10" />
                <el-option label="30秒" value="30" />
                <el-option label="1分钟" value="60" />
                <el-option label="5分钟" value="300" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="数据保留期限">
              <el-select v-model="dataSettings.retentionPeriod">
                <el-option label="7天" value="7" />
                <el-option label="30天" value="30" />
                <el-option label="90天" value="90" />
                <el-option label="1年" value="365" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="自动备份">
              <el-switch v-model="dataSettings.autoBackup" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveDataSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="安全设置" name="security">
          <el-form :model="securitySettings" label-width="120px">
            <el-form-item label="会话超时">
              <el-select v-model="securitySettings.sessionTimeout">
                <el-option label="30分钟" value="30" />
                <el-option label="1小时" value="60" />
                <el-option label="4小时" value="240" />
                <el-option label="8小时" value="480" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="双因素认证">
              <el-switch v-model="securitySettings.twoFactorAuth" />
            </el-form-item>
            
            <el-form-item label="登录日志">
              <el-switch v-model="securitySettings.loginLog" />
            </el-form-item>
            
            <el-form-item label="IP白名单">
              <el-switch v-model="securitySettings.ipWhitelist" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveSecuritySettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('general')

const generalSettings = ref({
  language: 'zh-CN',
  timeFormat: '24h',
  theme: 'light'
})

const notificationSettings = ref({
  email: true,
  desktop: true,
  alerts: true,
  maintenance: false
})

const dataSettings = ref({
  refreshInterval: '30',
  retentionPeriod: '90',
  autoBackup: true
})

const securitySettings = ref({
  sessionTimeout: '60',
  twoFactorAuth: false,
  loginLog: true,
  ipWhitelist: false
})

const saveGeneralSettings = () => {
  ElMessage.success('通用设置保存成功')
}

const saveNotificationSettings = () => {
  ElMessage.success('通知设置保存成功')
}

const saveDataSettings = () => {
  ElMessage.success('数据设置保存成功')
}

const saveSecuritySettings = () => {
  ElMessage.success('安全设置保存成功')
}
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: bold;
}

.el-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-tabs {
  min-height: 400px;
}
</style>
