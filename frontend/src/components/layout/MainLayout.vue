<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :width="240"
      class="layout-sider"
      :theme="themeStore.isDark ? 'dark' : 'light'"
      collapsible
    >
      <div class="logo">
        <div class="logo-icon">🌱</div>
        <span v-show="!collapsed">AgriNex</span>
      </div>
      
      <a-menu 
        v-model:selectedKeys="selectedKeys" 
        v-model:openKeys="openKeys"
        mode="inline"
        :inline-collapsed="collapsed"
      >
        <a-menu-item key="dashboard" @click="$router.push('/dashboard')">
          <dashboard-outlined />
          <span>仪表盘</span>
        </a-menu-item>
        
        <a-menu-item key="devices" @click="$router.push('/devices')">
          <laptop-outlined />
          <span>设备管理</span>
        </a-menu-item>
        
        <a-menu-item key="sensors" @click="$router.push('/sensors')">
          <radar-chart-outlined />
          <span>传感器数据</span>
        </a-menu-item>
        
        <a-menu-item key="alarms" @click="$router.push('/alarms')">
          <bell-outlined />
          <span>告警管理</span>
        </a-menu-item>
        
        <a-menu-item key="predictions" @click="$router.push('/predictions')">
          <line-chart-outlined />
          <span>预测分析</span>
        </a-menu-item>
        
        <a-menu-item key="chat" @click="$router.push('/chat')">
          <robot-outlined />
          <span>AI助手</span>
        </a-menu-item>
        
        <a-sub-menu key="system">
          <template #icon>
            <setting-outlined />
          </template>
          <template #title>系统管理</template>
          <a-menu-item key="profile" @click="$router.push('/profile')">
            <user-outlined />
            <span>个人中心</span>
          </a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <!-- 顶部导航 -->
      <a-layout-header class="layout-header">
        <div class="header-left">
          <a-button type="text" @click="collapsed = !collapsed">
            <menu-unfold-outlined v-if="collapsed" />
            <menu-fold-outlined v-else />
          </a-button>
          
          <a-breadcrumb>
            <a-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              <router-link v-if="item.path" :to="item.path">
                {{ item.title }}
              </router-link>
              <span v-else>{{ item.title }}</span>
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>

        <div class="header-right">
          <a-space>
            <!-- 主题切换 -->
            <ThemeSwitcher :show-text="false" />
            
            <!-- 通知 -->
            <a-badge :count="notificationCount" :offset="[10, 0]">
              <a-button type="text" @click="showNotifications">
                <bell-outlined />
              </a-button>
            </a-badge>
            
            <!-- 用户菜单 -->
            <a-dropdown>
              <a-button type="text">
                <a-avatar :size="32" :src="userInfo?.avatar">
                  <template #icon>
                    <user-outlined />
                  </template>
                </a-avatar>
                <span style="margin-left: 8px;">{{ userInfo?.username || '用户' }}</span>
                <down-outlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="$router.push('/profile')">
                    <user-outlined />
                    个人中心
                  </a-menu-item>
                  <a-menu-item @click="$router.push('/settings')">
                    <setting-outlined />
                    系统设置
                  </a-menu-item>
                  <a-menu-divider />
                  <a-menu-item @click="handleLogout">
                    <logout-outlined />
                    退出登录
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </div>
      </a-layout-header>

      <!-- 主内容区 -->
      <a-layout-content class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/theme';
import { message } from 'ant-design-vue';
import ThemeSwitcher from '@/components/ui/ThemeSwitcher.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const themeStore = useThemeStore();

// 响应式数据
const collapsed = ref(false);
const selectedKeys = ref<string[]>([]);
const openKeys = ref<string[]>([]);
const notificationCount = ref(3);

// 计算属性
const userInfo = computed(() => authStore.user);

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title);
  return [
    { title: '首页', path: '/dashboard' },
    ...matched.map(item => ({
      title: item.meta?.title as string,
      path: item.path === route.path ? '' : item.path
    }))
  ];
});

// 监听路由变化，更新选中的菜单
watch(
  () => route.path,
  (newPath) => {
    const pathSegments = newPath.split('/').filter(Boolean);
    if (pathSegments.length > 0) {
      selectedKeys.value = [pathSegments[0]];
      if (pathSegments[0] === 'system') {
        openKeys.value = ['system'];
      }
    }
  },
  { immediate: true }
);

// 方法
const showNotifications = () => {
  message.info('通知功能开发中...');
};

const handleLogout = async () => {
  try {
    await authStore.logout();
    message.success('退出登录成功');
    router.push('/login');
  } catch (error) {
    message.error('退出登录失败');
  }
};
</script>

<style lang="less" scoped>
.main-layout {
  .layout-sider {
    .logo {
      height: 64px;
      display: flex;
      align-items: center;
      padding: 0 16px;
      border-bottom: 1px solid #f0f0f0;
      
      img {
        height: 32px;
        width: 32px;
        margin-right: 8px;
      }
      
      span {
        font-size: 18px;
        font-weight: 600;
        color: #52c41a;
      }
    }
  }

  .layout-header {
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }
}
</style>
