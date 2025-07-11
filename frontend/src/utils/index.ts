// utils/index.ts
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

// 扩展dayjs插件
dayjs.extend(relativeTime);

/**
 * 格式化日期时间
 */
export const formatDateTime = (date: string | Date, format = 'YYYY-MM-DD HH:mm:ss') => {
  return dayjs(date).format(format);
};

/**
 * 格式化日期时间 (别名)
 */
export const formatDate = (date: string | Date, format = 'YYYY-MM-DD HH:mm:ss') => {
  return dayjs(date).format(format);
};

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (date: string | Date) => {
  return dayjs(date).fromNow();
};

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 格式化数值
 */
export const formatNumber = (value: number, decimals = 2) => {
  return Number(value).toFixed(decimals);
};

/**
 * 生成随机颜色
 */
export const generateRandomColor = () => {
  const colors = [
    '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
    '#00ACC1', '#FF7043', '#AB47BC', '#26A69A', '#FFA726'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

/**
 * 防抖函数
 */
export const debounce = (fn: Function, delay: number) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(null, args), delay);
  };
};

/**
 * 节流函数
 */
export const throttle = (fn: Function, delay: number) => {
  let lastCall = 0;
  return (...args: any[]) => {
    const now = Date.now();
    if (now - lastCall < delay) {
      return;
    }
    lastCall = now;
    return fn(...args);
  };
};

/**
 * 深拷贝
 */
export const deepClone = (obj: any): any => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof Array) return obj.map((item: any) => deepClone(item));
  if (typeof obj === 'object') {
    const clonedObj: any = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
};

/**
 * 获取设备状态颜色
 */
export const getDeviceStatusColor = (isActive: boolean, lastSeen?: string) => {
  if (!isActive) return '#909399'; // 禁用状态
  
  if (!lastSeen) return '#F56C6C'; // 从未连接
  
  const now = Date.now();
  const lastSeenTime = new Date(lastSeen).getTime();
  const diffMinutes = (now - lastSeenTime) / (1000 * 60);
  
  if (diffMinutes <= 5) return '#67C23A'; // 在线
  if (diffMinutes <= 30) return '#E6A23C'; // 警告
  return '#F56C6C'; // 离线
};

/**
 * 获取设备状态文本
 */
export const getDeviceStatusText = (isActive: boolean, lastSeen?: string) => {
  if (!isActive) return '已禁用';
  
  if (!lastSeen) return '从未连接';
  
  const now = Date.now();
  const lastSeenTime = new Date(lastSeen).getTime();
  const diffMinutes = (now - lastSeenTime) / (1000 * 60);
  
  if (diffMinutes <= 5) return '在线';
  if (diffMinutes <= 30) return '警告';
  return '离线';
};

/**
 * 获取告警级别颜色
 */
export const getAlarmLevelColor = (level: string) => {
  switch (level.toLowerCase()) {
    case 'critical':
      return '#F56C6C';
    case 'warning':
      return '#E6A23C';
    case 'info':
      return '#409EFF';
    default:
      return '#909399';
  }
};

/**
 * 获取告警级别文本
 */
export const getAlarmLevelText = (level: string) => {
  switch (level.toLowerCase()) {
    case 'critical':
      return '严重';
    case 'warning':
      return '警告';
    case 'info':
      return '信息';
    default:
      return '未知';
  }
};
