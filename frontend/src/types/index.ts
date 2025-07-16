// 基础 API 响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  code?: number;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  pagination: {
    current: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  success: boolean;
  message?: string;
}

// 用户相关类型
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  phone?: string;
  avatar?: string;
  role: 'admin' | 'user' | 'operator';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

// 设备相关类型
export interface Device {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'error' | 'maintenance';
  location?: string;
  description?: string;
  ip_address?: string;
  mac_address?: string;
  firmware_version?: string;
  last_seen?: string;
  created_at: string;
  updated_at: string;
  specifications?: Record<string, any>;
  configuration?: Record<string, any>;
  metadata?: Record<string, any>;
}

// 传感器相关类型
export interface Sensor {
  id: number;
  device_id: number;
  name: string;
  sensor_type: string;
  unit: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SensorData {
  id: number;
  sensor_id: number;
  timestamp: string;
  data_type: string;
  value: number;
  unit: string;
  created_at: string;
}

// 报警相关类型
export interface Alarm {
  id: string;
  device_id?: string;
  sensor_id?: string;
  type: 'threshold' | 'malfunction' | 'connection' | 'security' | 'system';
  level: 'low' | 'medium' | 'high' | 'critical';
  status: 'active' | 'resolved' | 'ignored' | 'acknowledged';
  title: string;
  message: string;
  description?: string;
  triggered_at: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_note?: string;
  trigger_value?: number;
  threshold_value?: number;
  rule_id?: string;
  rule_name?: string;
  device_name?: string;
  sensor_name?: string;
  value?: number;
  unit?: string;
  threshold?: number;
  created_at: string;
}

// 聊天相关类型
export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  type?: 'text' | 'chart' | 'table' | 'action';
  metadata?: {
    chart_title?: string;
    chart_data?: any;
    table_columns?: any[];
    table_data?: any[];
    actions?: Array<{
      label: string;
      action: string;
      params?: any;
    }>;
  };
  created_at: string;
}

export interface SendMessageRequest {
  conversation_id?: string;
  message: string;
  context?: Record<string, any>;
}

// 统计相关类型
export interface DashboardStats {
  devices: {
    total: number;
    online: number;
    offline: number;
    error: number;
    maintenance?: number;
  };
  sensors: {
    total: number;
    active: number;
    inactive: number;
    error: number;
  };
  alarms: {
    total: number;
    active: number;
    resolved: number;
    critical: number;
  };
  data_points: number;
  system_uptime?: number;
  last_updated: string;
}

// 表格相关类型
export interface TableColumn {
  title: string;
  dataIndex: string;
  key: string;
  width?: number;
  fixed?: 'left' | 'right';
  sorter?: boolean;
  filters?: Array<{
    text: string;
    value: any;
  }>;
  render?: (value: any, record: any, index: number) => any;
}

// 图表相关类型
export interface ChartData {
  name: string;
  value: number;
  timestamp?: string;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
  series?: string;
}

// 表单相关类型
export interface FormRule {
  required?: boolean;
  message?: string;
  type?: 'string' | 'number' | 'email' | 'url' | 'date';
  min?: number;
  max?: number;
  pattern?: RegExp;
  validator?: (rule: any, value: any) => Promise<void>;
}

// 路由相关类型
export interface RouteItem {
  path: string;
  name: string;
  component?: any;
  meta?: {
    title?: string;
    icon?: string;
    requireAuth?: boolean;
    roles?: string[];
    hidden?: boolean;
  };
  children?: RouteItem[];
}

// 主题相关类型
export interface ThemeConfig {
  primaryColor: string;
  borderRadius: number;
  componentSize: 'small' | 'middle' | 'large';
}

// 导出类型别名
export type DeviceStatus = Device['status'];
export type SensorStatus = Sensor['status'];
export type AlarmLevel = Alarm['level'];
export type AlarmStatus = Alarm['status'];
export type UserRole = User['role'];

// 表单类型
export interface LoginForm {
  username: string;
  password: string;
  remember?: boolean;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name?: string;
  phone?: string;
  agreement?: boolean;
}

// 读数类型（传感器数据的别名）
export type Reading = SensorData;