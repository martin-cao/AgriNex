<template>
  <div class="theme-switcher-wrapper">
    <!-- 简单的主题切换按钮 -->
    <a-dropdown placement="bottomRight" v-if="!detailed">
      <a-button class="theme-toggle-btn" size="small" :type="isDark ? 'default' : 'text'">
        <component :is="currentThemeIcon" />
        <span v-if="showText" class="theme-text">{{ currentThemeText }}</span>
      </a-button>
      <template #overlay>
        <a-menu class="theme-menu" @click="handleThemeMenuClick">
          <a-menu-item key="light" :class="{ active: mode === 'light' }">
            <sun-outlined />
            <span>浅色模式</span>
          </a-menu-item>
          <a-menu-item key="dark" :class="{ active: mode === 'dark' }">
            <moon-outlined />
            <span>暗色模式</span>
          </a-menu-item>
          <a-menu-item key="auto" :class="{ active: mode === 'auto' }">
            <desktop-outlined />
            <span>跟随系统</span>
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>

    <!-- 详细的主题切换器 -->
    <div v-else class="theme-switcher-detailed">
      <div class="theme-switcher">
        <div 
          v-for="option in themeOptions" 
          :key="option.value"
          class="theme-option"
          :class="{ active: mode === option.value }"
          @click="setThemeMode(option.value)"
        >
          <component :is="option.icon" />
          <span>{{ option.label }}</span>
        </div>
      </div>
      
      <!-- 系统主题状态指示 -->
      <div v-if="mode === 'auto'" class="system-theme-indicator">
        <span class="indicator-text">
          系统当前: {{ systemDark ? '暗色' : '亮色' }}
        </span>
        <a-tag :color="systemDark ? 'purple' : 'orange'" size="small">
          <component :is="systemDark ? 'moon-outlined' : 'sun-outlined'" />
          {{ systemDark ? '暗色' : '亮色' }}
        </a-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useThemeStore, type ThemeMode } from '@/stores/theme';

interface Props {
  detailed?: boolean;
  showText?: boolean;
  size?: 'small' | 'middle' | 'large';
}

const props = withDefaults(defineProps<Props>(), {
  detailed: false,
  showText: false,
  size: 'middle'
});

const themeStore = useThemeStore();

// 计算属性
const mode = computed(() => themeStore.mode);
const isDark = computed(() => themeStore.isDark);
const systemDark = computed(() => themeStore.systemDark);

const currentThemeIcon = computed(() => {
  if (mode.value === 'auto') {
    return 'desktop-outlined';
  }
  return isDark.value ? 'moon-outlined' : 'sun-outlined';
});

const currentThemeText = computed(() => {
  switch (mode.value) {
    case 'light':
      return '浅色';
    case 'dark':
      return '暗色';
    case 'auto':
      return '自动';
    default:
      return '主题';
  }
});

const themeOptions = computed(() => [
  {
    value: 'light' as ThemeMode,
    label: '浅色',
    icon: 'sun-outlined'
  },
  {
    value: 'dark' as ThemeMode,
    label: '暗色',
    icon: 'moon-outlined'
  },
  {
    value: 'auto' as ThemeMode,
    label: '自动',
    icon: 'desktop-outlined'
  }
]);

// 方法
const setThemeMode = (newMode: ThemeMode) => {
  themeStore.setMode(newMode);
};

const handleThemeMenuClick = ({ key }: { key: string }) => {
  setThemeMode(key as ThemeMode);
};
</script>

<style lang="less" scoped>
.theme-switcher-wrapper {
  .theme-toggle-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    border: none;
    background: transparent;
    color: var(--agrinex-text-secondary);
    transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
    
    &:hover {
      color: var(--agrinex-primary);
      background: var(--agrinex-bg-secondary);
    }
    
    .theme-text {
      font-size: 12px;
    }
  }
  
  .theme-switcher-detailed {
    .theme-switcher {
      display: inline-flex;
      align-items: center;
      padding: 4px;
      background: var(--agrinex-bg-secondary);
      border: 1px solid var(--agrinex-border-color);
      border-radius: 20px;
      transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
      
      .theme-option {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 16px;
        cursor: pointer;
        font-size: 12px;
        color: var(--agrinex-text-secondary);
        transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
        user-select: none;
        
        &.active {
          background: var(--agrinex-primary);
          color: #ffffff;
          box-shadow: 0 2px 4px rgba(24, 144, 255, 0.3);
        }
        
        &:hover:not(.active) {
          color: var(--agrinex-text-primary);
          background: var(--agrinex-bg-tertiary);
        }
        
        span {
          font-weight: 500;
        }
      }
    }
    
    .system-theme-indicator {
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      
      .indicator-text {
        color: var(--agrinex-text-tertiary);
      }
    }
  }
}

:deep(.theme-menu) {
  .ant-menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    
    &.active {
      background: var(--agrinex-bg-secondary);
      color: var(--agrinex-primary);
    }
    
    .anticon {
      font-size: 14px;
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .theme-switcher-wrapper {
    .theme-switcher-detailed {
      .theme-switcher {
        padding: 3px;
        
        .theme-option {
          padding: 6px 12px;
          font-size: 11px;
          
          span {
            display: none;
          }
        }
      }
    }
  }
}
</style>
