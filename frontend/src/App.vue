<template>
  <div id="app">
    <!-- 如果用户未登录，显示登录页面 -->
    <div v-if="!authStore.isAuthenticated" class="login-container">
      <router-view />
    </div>
    
    <!-- 如果用户已登录，显示主布局 -->
    <el-container v-else class="main-container">
      <!-- 侧边栏 -->
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h3>🌱 AgriNex</h3>
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          @select="handleMenuSelect"
        >
          <el-menu-item index="/dashboard">
            <el-icon><Platform /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/devices">
            <el-icon><Monitor /></el-icon>
            <span>设备管理</span>
          </el-menu-item>
          
          <el-menu-item index="/sensors">
            <el-icon><Cpu /></el-icon>
            <span>传感器数据</span>
          </el-menu-item>
          
          <el-menu-item index="/alarms">
            <el-icon><Bell /></el-icon>
            <span>告警管理</span>
          </el-menu-item>
          
          <el-menu-item index="/predictions">
            <el-icon><TrendCharts /></el-icon>
            <span>预测分析</span>
          </el-menu-item>
          
          <el-menu-item index="/media">
            <el-icon><Picture /></el-icon>
            <span>媒体库</span>
          </el-menu-item>
          
          <el-menu-item index="/chatbot">
            <el-icon><ChatDotRound /></el-icon>
            <span>AI 助手</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <!-- 系统状态 -->
            <div class="status-indicator">
              <el-tooltip :content="systemStatus.text">
                <el-badge :type="systemStatus.type" is-dot>
                  <el-icon><Connection /></el-icon>
                </el-badge>
              </el-tooltip>
            </div>
            
            <!-- 用户菜单 -->
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <span class="username">{{ authStore.user?.username || '用户' }}</span>
                <el-icon class="el-icon--right"><arrow-down /></el-icon>
              </span>
              
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人资料
                  </el-dropdown-item>
                  <el-dropdown-item command="settings">
                    <el-icon><Setting /></el-icon>
                    系统设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 主体内容 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import {
  Platform,
  Monitor,
  Cpu,
  Bell,
  TrendCharts,
  Picture,
  ChatDotRound,
  Connection,
  User,
  Setting,
  SwitchButton,
  ArrowDown
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    path: item.path,
    name: item.meta?.title || item.name
  }))
})

// 系统状态
const systemStatus = ref({
  text: '检查中...',
  type: 'info' as 'success' | 'warning' | 'danger' | 'info'
})

// 检查系统健康状态
const checkSystemHealth = async () => {
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || (import.meta.env.VITE_APP_ENV === 'production' ? '' : 'http://localhost:8000')
    const response = await fetch(`${baseUrl}/api/health`)
    if (response.ok) {
      systemStatus.value = { text: '系统正常', type: 'success' }
    } else {
      systemStatus.value = { text: '系统异常', type: 'warning' }
    }
  } catch (error) {
    systemStatus.value = { text: '连接失败', type: 'danger' }
  }
}

// 处理菜单选择
const handleMenuSelect = (key: string) => {
  if (key !== route.path) {
    router.push(key)
  }
}

// 处理用户菜单命令
const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout()
      ElMessage.success('已安全退出')
      router.push('/login')
      break
  }
}

// 监听路由变化，更新页面标题
watch(() => route.meta.title, (title) => {
  if (title) {
    document.title = `${title} - AgriNex`
  }
}, { immediate: true })

onMounted(() => {
  checkSystemHealth()
  // 每30秒检查一次系统状态
  setInterval(checkSystemHealth, 30000)
})
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.main-container {
  height: 100vh;
}

.sidebar {
  background: #001529;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #1f2937;
}

.logo h3 {
  color: #fff;
  margin: 0;
  font-size: 18px;
}

.sidebar-menu {
  border-right: none;
  background: #001529;
}

.sidebar-menu .el-menu-item {
  color: rgba(255, 255, 255, 0.65);
  border-bottom: 1px solid #1f2937;
}

.sidebar-menu .el-menu-item:hover {
  background: #1890ff;
  color: #fff;
}

.sidebar-menu .el-menu-item.is-active {
  background: #1890ff;
  color: #fff;
}

.header {
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.status-indicator {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background: #f5f5f5;
}

.username {
  color: #333;
  font-size: 14px;
}

.main-content {
  background: #f5f5f5;
  padding: 20px;
  overflow-y: auto;
}
</style>

<style>
#app {
  font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  margin: 0;
  padding: 0;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
}

header {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.welcome {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  border-radius: 8px;
  background: #f8f9fa;
}

.healthy { color: #4CAF50; font-weight: bold; }
.error { color: #f44336; font-weight: bold; }
.checking { color: #ff9800; font-weight: bold; }
</style>
