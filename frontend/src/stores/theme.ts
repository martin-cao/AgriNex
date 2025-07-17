import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';
import { theme } from 'ant-design-vue';

export type ThemeMode = 'light' | 'dark' | 'auto';

export interface ThemeConfig {
  mode: ThemeMode;
  isDark: boolean;
  primaryColor: string;
  borderRadius: number;
  componentSize: 'small' | 'middle' | 'large';
}

export const useThemeStore = defineStore('theme', () => {
  // 状态
  const mode = ref<ThemeMode>('auto');
  const systemDark = ref(false);
  const primaryColor = ref('#1890ff');
  const borderRadius = ref(6);
  const componentSize = ref<'small' | 'middle' | 'large'>('middle');

  // 计算属性
  const isDark = computed(() => {
    if (mode.value === 'auto') {
      return systemDark.value;
    }
    return mode.value === 'dark';
  });

  const themeConfig = computed(() => ({
    mode: mode.value,
    isDark: isDark.value,
    primaryColor: primaryColor.value,
    borderRadius: borderRadius.value,
    componentSize: componentSize.value,
  }));

  // Ant Design Vue 主题token
  const antdThemeConfig = computed(() => ({
    algorithm: isDark.value ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: primaryColor.value,
      borderRadius: borderRadius.value,
      // 暗色模式下的颜色调整
      ...(isDark.value && {
        colorBgContainer: '#1f1f1f',
        colorBgElevated: '#262626',
        colorBgLayout: '#000000',
        colorBgSpotlight: '#434343',
        colorBorder: '#434343',
        colorBorderSecondary: '#303030',
        colorFill: '#1f1f1f',
        colorFillSecondary: '#262626',
        colorFillTertiary: '#434343',
        colorFillQuaternary: '#262626',
        colorText: 'rgba(255, 255, 255, 0.85)',
        colorTextSecondary: 'rgba(255, 255, 255, 0.65)',
        colorTextTertiary: 'rgba(255, 255, 255, 0.45)',
        colorTextQuaternary: 'rgba(255, 255, 255, 0.25)',
      }),
    },
    components: {
      Layout: {
        ...(isDark.value && {
          colorBgHeader: '#1f1f1f',
          colorBgBody: '#000000',
          colorBgTrigger: '#262626',
        }),
      },
      Menu: {
        ...(isDark.value && {
          colorBgContainer: '#1f1f1f',
          colorItemBg: 'transparent',
          colorItemBgSelected: '#262626',
          colorItemBgHover: '#262626',
          colorItemText: 'rgba(255, 255, 255, 0.65)',
          colorItemTextSelected: '#ffffff',
          colorItemTextHover: '#ffffff',
        }),
      },
      Card: {
        ...(isDark.value && {
          colorBgContainer: '#1f1f1f',
          colorBorderSecondary: '#434343',
        }),
      },
      Table: {
        ...(isDark.value && {
          colorBgContainer: '#1f1f1f',
          colorFillAlter: '#262626',
        }),
      },
      Modal: {
        ...(isDark.value && {
          colorBgElevated: '#1f1f1f',
          colorBgMask: 'rgba(0, 0, 0, 0.45)',
        }),
      },
      Drawer: {
        ...(isDark.value && {
          colorBgElevated: '#1f1f1f',
        }),
      },
      Dropdown: {
        ...(isDark.value && {
          colorBgElevated: '#1f1f1f',
        }),
      },
      Tooltip: {
        ...(isDark.value && {
          colorBgSpotlight: '#434343',
        }),
      },
    },
  }));

  // 方法
  const setMode = (newMode: ThemeMode) => {
    mode.value = newMode;
    localStorage.setItem('theme-mode', newMode);
    updateBodyClass();
  };

  const setPrimaryColor = (color: string) => {
    primaryColor.value = color;
    localStorage.setItem('theme-primary-color', color);
  };

  const setBorderRadius = (radius: number) => {
    borderRadius.value = radius;
    localStorage.setItem('theme-border-radius', radius.toString());
  };

  const setComponentSize = (size: 'small' | 'middle' | 'large') => {
    componentSize.value = size;
    localStorage.setItem('theme-component-size', size);
  };

  const updateBodyClass = () => {
    const body = document.body;
    if (isDark.value) {
      body.classList.add('dark-theme');
      body.classList.remove('light-theme');
    } else {
      body.classList.add('light-theme');
      body.classList.remove('dark-theme');
    }
  };

  const detectSystemTheme = () => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      systemDark.value = mediaQuery.matches;
      
      // 监听系统主题变化
      mediaQuery.addEventListener('change', (e) => {
        systemDark.value = e.matches;
      });
    }
  };

  const initializeTheme = () => {
    // 从localStorage恢复设置
    const savedMode = localStorage.getItem('theme-mode') as ThemeMode;
    const savedPrimaryColor = localStorage.getItem('theme-primary-color');
    const savedBorderRadius = localStorage.getItem('theme-border-radius');
    const savedComponentSize = localStorage.getItem('theme-component-size');

    if (savedMode && ['light', 'dark', 'auto'].includes(savedMode)) {
      mode.value = savedMode;
    }
    
    if (savedPrimaryColor) {
      primaryColor.value = savedPrimaryColor;
    }
    
    if (savedBorderRadius) {
      borderRadius.value = parseInt(savedBorderRadius, 10);
    }
    
    if (savedComponentSize && ['small', 'middle', 'large'].includes(savedComponentSize)) {
      componentSize.value = savedComponentSize as 'small' | 'middle' | 'large';
    }

    // 检测系统主题偏好
    detectSystemTheme();
    
    // 初始化body类名
    updateBodyClass();
  };

  const resetTheme = () => {
    mode.value = 'auto';
    primaryColor.value = '#1890ff';
    borderRadius.value = 6;
    componentSize.value = 'middle';
    
    localStorage.removeItem('theme-mode');
    localStorage.removeItem('theme-primary-color');
    localStorage.removeItem('theme-border-radius');
    localStorage.removeItem('theme-component-size');
    
    updateBodyClass();
  };

  // 监听主题变化，更新body类名
  watch(isDark, () => {
    updateBodyClass();
  }, { immediate: true });

  return {
    // 状态
    mode,
    systemDark,
    primaryColor,
    borderRadius,
    componentSize,
    
    // 计算属性
    isDark,
    themeConfig,
    antdThemeConfig,
    
    // 方法
    setMode,
    setPrimaryColor,
    setBorderRadius,
    setComponentSize,
    initializeTheme,
    resetTheme,
    updateBodyClass,
  };
});
