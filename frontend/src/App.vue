<template>
  <a-config-provider :theme="themeStore.antdThemeConfig">
    <div id="app" :class="{ 'theme-transition': true }">
      <!-- 如果用户未登录，显示登录页面 -->
      <div v-if="!authStore.isAuthenticated" class="login-container">
        <router-view />
      </div>
      
      <!-- 如果用户已登录，显示主布局 -->
      <MainLayout v-else />
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/theme';
import MainLayout from '@/components/layout/MainLayout.vue';

const route = useRoute();
const authStore = useAuthStore();
const themeStore = useThemeStore();

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path;
});

// 初始化主题
onMounted(() => {
  themeStore.initializeTheme();
});
</script>

<style lang="less">
#app {
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
}

.login-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f9f0 0%, #e6f7e6 100%);
}
</style>