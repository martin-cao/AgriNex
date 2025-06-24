<template>
  <div id="app">
    <header>
      <h1>🌱 AgriNex 农业物联网平台</h1>
    </header>
    
    <main>
      <div class="welcome">
        <h2>欢迎使用农业数据管理平台</h2>
        <p>系统状态: <span :class="apiStatus.class">{{ apiStatus.text }}</span></p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface ApiStatus {
  text: string
  class: string
}

const apiStatus = ref<ApiStatus>({ text: '检查中...', class: 'checking' })

const checkApiHealth = async (): Promise<void> => {
  try {
    const response = await fetch('http://localhost:8000/api/health')
    if (response.ok) {
      apiStatus.value = { text: '正常', class: 'healthy' }
    } else {
      apiStatus.value = { text: '异常', class: 'error' }
    }
  } catch (error) {
    apiStatus.value = { text: '离线', class: 'error' }
  }
}

onMounted(() => {
  checkApiHealth()
})
</script>

<style>
#app {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  text-align: center;
  margin: 0;
  padding: 20px;
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
