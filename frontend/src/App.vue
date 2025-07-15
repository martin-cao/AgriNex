<template>
  <div id="app">
    <!-- 如果用户未登录，显示登录页面 -->
    <div v-if="!authStore.isAuthenticated" class="login-container">
      <router-view />
    </div>
    
    <!-- 如果用户已登录，显示主布局 -->
    <MainLayout v-else />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import MainLayout from '@/components/layout/MainLayout.vue';

const route = useRoute();
const authStore = useAuthStore();

// 当前激活的菜单项
const activeMenu = computed(() => {
  return route.path;
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