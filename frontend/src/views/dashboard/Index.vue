<template>
  <div class="dashboard">
    <h1>仪表盘</h1>
    <p>前端重构已完成，使用 Ant Design Vue 框架</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const loading = ref(false);
</script>

<style lang="less" scoped>
.dashboard {
  padding: 24px;
}
</style>