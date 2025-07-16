<template>
  <a-card class="statistic-card" :loading="loading">
    <a-statistic
      :title="title"
      :value="value"
      :precision="precision"
      :suffix="suffix"
      :prefix="prefix"
    >
      <template #prefix v-if="icon">
        <component :is="icon" :style="{ color: iconColor, fontSize: '24px' }" />
      </template>
    </a-statistic>
    
    <div class="trend" v-if="trend">
      <span :class="['trend-text', trendType]">
        <arrow-up-outlined v-if="trendType === 'up'" />
        <arrow-down-outlined v-if="trendType === 'down'" />
        {{ trend }}
      </span>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  title: string;
  value: number | string;
  precision?: number;
  suffix?: string;
  prefix?: string;
  icon?: string;
  iconColor?: string;
  trend?: string;
  trendType?: 'up' | 'down' | 'neutral';
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  precision: 0,
  iconColor: '#52c41a',
  trendType: 'neutral',
  loading: false
});

const trendIcon = computed(() => {
  return props.trendType === 'up' ? 'arrow-up-outlined' : 
         props.trendType === 'down' ? 'arrow-down-outlined' : '';
});
</script>

<style lang="less" scoped>
.statistic-card {
  :deep(.ant-statistic-title) {
    color: #8c8c8c;
    font-size: 14px;
    margin-bottom: 4px;
  }

  :deep(.ant-statistic-content) {
    color: #262626;
    font-size: 24px;
    font-weight: 600;
  }

  .trend {
    margin-top: 8px;
    
    .trend-text {
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 4px;
      
      &.up {
        color: #52c41a;
      }
      
      &.down {
        color: #ff4d4f;
      }
      
      &.neutral {
        color: #8c8c8c;
      }
    }
  }
}
</style>
