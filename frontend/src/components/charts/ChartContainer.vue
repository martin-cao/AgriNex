<template>
  <div class="chart-container">
    <div class="chart-header" v-if="title || $slots.header">
      <div class="chart-title">
        <h3 v-if="title">{{ title }}</h3>
        <slot name="header" />
      </div>
      <div class="chart-actions">
        <slot name="actions">
          <a-space>
            <a-button v-if="showRefresh" type="text" @click="handleRefresh">
              <reload-outlined />
            </a-button>
            <a-button v-if="showFullscreen" type="text" @click="handleFullscreen">
              <fullscreen-outlined />
            </a-button>
            <a-dropdown v-if="showExport">
              <a-button type="text">
                <download-outlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item @click="exportChart('png')">导出为 PNG</a-menu-item>
                  <a-menu-item @click="exportChart('jpg')">导出为 JPG</a-menu-item>
                  <a-menu-item @click="exportChart('svg')">导出为 SVG</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </slot>
      </div>
    </div>
    
    <div class="chart-content" v-loading="loading">
      <v-chart
        ref="chartRef"
        :option="chartOption"
        :style="{ height: height + 'px' }"
        :autoresize="true"
        @click="handleChartClick"
      />
    </div>
    
    <div class="chart-footer" v-if="$slots.footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart, PieChart, ScatterChart, RadarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
  DataZoomComponent
} from 'echarts/components';
import VChart from 'vue-echarts';
import { message } from 'ant-design-vue';

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  RadarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
  DataZoomComponent
]);

interface Props {
  title?: string;
  option: any;
  height?: number;
  loading?: boolean;
  showRefresh?: boolean;
  showFullscreen?: boolean;
  showExport?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  height: 400,
  loading: false,
  showRefresh: true,
  showFullscreen: true,
  showExport: true
});

const emit = defineEmits<{
  refresh: [];
  chartClick: [params: any];
}>();

const chartRef = ref();

// 计算属性
const chartOption = computed(() => {
  const defaultOption = {
    color: ['#52c41a', '#1890ff', '#faad14', '#ff4d4f', '#722ed1', '#13c2c2'],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#d9d9d9',
      borderWidth: 1,
      textStyle: {
        color: '#262626'
      }
    },
    legend: {
      textStyle: {
        color: '#262626'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  };

  return {
    ...defaultOption,
    ...props.option
  };
});

// 方法
const handleRefresh = () => {
  emit('refresh');
};

const handleFullscreen = () => {
  if (chartRef.value && typeof chartRef.value.getDom === 'function') {
    try {
      const chartDom = chartRef.value.getDom();
      if (chartDom && chartDom.requestFullscreen) {
        chartDom.requestFullscreen();
      }
    } catch (error) {
      console.error('全屏显示失败:', error);
      message.error('全屏显示失败');
    }
  }
};

const handleChartClick = (params: any) => {
  emit('chartClick', params);
};

const exportChart = (type: 'png' | 'jpg' | 'svg') => {
  if (chartRef.value && typeof chartRef.value.getChart === 'function') {
    try {
      const chart = chartRef.value.getChart();
      if (chart) {
        const url = chart.getDataURL({
          type: type,
          pixelRatio: 2,
          backgroundColor: '#fff'
        });
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = url;
        link.download = `chart.${type}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        message.success(`图表已导出为 ${type.toUpperCase()} 格式`);
      }
    } catch (error) {
      console.error('导出图表失败:', error);
      message.error('导出图表失败');
    }
  } else {
    message.error('图表未加载完成，无法导出');
  }
};

// 监听配置变化，重新渲染图表
watch(
  () => props.option,
  () => {
    if (chartRef.value && typeof chartRef.value.getChart === 'function') {
      try {
        const chart = chartRef.value.getChart();
        if (chart) {
          chart.setOption(chartOption.value, true);
        }
      } catch (error) {
        console.error('更新图表配置失败:', error);
      }
    }
  },
  { deep: true }
);

// 暴露方法给父组件
defineExpose({
  getChart: () => {
    try {
      return chartRef.value && typeof chartRef.value.getChart === 'function' 
        ? chartRef.value.getChart() 
        : null;
    } catch (error) {
      console.error('获取图表实例失败:', error);
      return null;
    }
  },
  refresh: () => {
    try {
      const chart = chartRef.value && typeof chartRef.value.getChart === 'function' 
        ? chartRef.value.getChart() 
        : null;
      if (chart && typeof chart.resize === 'function') {
        chart.resize();
      }
    } catch (error) {
      console.error('刷新图表失败:', error);
    }
  }
});
</script>

<style lang="less" scoped>
.chart-container {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #f0f0f0;

    .chart-title {
      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #262626;
      }
    }

    .chart-actions {
      flex-shrink: 0;
    }
  }

  .chart-content {
    padding: 20px;
    position: relative;
  }

  .chart-footer {
    padding: 12px 20px;
    border-top: 1px solid #f0f0f0;
    background: #fafafa;
  }
}

// 全屏样式
:global(.chart-container:-webkit-full-screen) {
  .chart-content {
    height: 100vh;
    padding: 0;
  }
}

:global(.chart-container:-moz-full-screen) {
  .chart-content {
    height: 100vh;
    padding: 0;
  }
}

:global(.chart-container:fullscreen) {
  .chart-content {
    height: 100vh;
    padding: 0;
  }
}
</style>
