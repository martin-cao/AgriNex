// types/index.ts
export interface User {
  id: number;
  username: string;
  email?: string;
  role: string;
  created_at: string;
}

export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface Device {
  id: number;
  name: string;
  device_type: string;
  location: string;
  description?: string;
  is_active: boolean;
  last_seen?: string;
  created_at: string;
  updated_at: string;
}

export interface Sensor {
  id: number;
  name: string;
  sensor_type: string;
  unit: string;
  device_id: number;
  is_active: boolean;
  min_value?: number;
  max_value?: number;
  created_at: string;
  updated_at: string;
}

export interface Reading {
  id: number;
  sensor_id: number;
  value: number;
  timestamp: string;
  created_at: string;
}

export interface MediaReading {
  id: number;
  sensor_id: number;
  file_path: string;
  file_type: string;
  file_size: number;
  timestamp: string;
  created_at: string;
}

export interface Alarm {
  id: number;
  sensor_id: number;
  alarm_type: string;
  threshold_value: number;
  current_value: number;
  status: string;
  message: string;
  created_at: string;
  resolved_at?: string;
}

export interface Prediction {
  id: number;
  sensor_id: number;
  predict_ts: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
  generated_at: string;
}

export interface DashboardStats {
  total_devices: number;
  online_devices: number;
  active_alerts: number;
  today_data_points: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  pagination?: {
    page: number;
    per_page: number;
    pages: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface ChartData {
  name: string;
  type: string;
  data: [string, number][];
  smooth?: boolean;
}

export interface ChartOption {
  title: {
    text: string;
    left: string;
  };
  tooltip: {
    trigger: string;
    axisPointer: {
      type: string;
    };
  };
  legend: {
    data: string[];
  };
  grid: {
    left: string;
    right: string;
    bottom: string;
    containLabel: boolean;
  };
  xAxis: {
    type: string;
    boundaryGap: boolean;
    data?: string[];
  };
  yAxis: {
    type: string;
    name?: string;
  };
  series: ChartData[];
}

export interface LLMRequest {
  sensor_id: number;
  minutes?: number;
  context?: string;
}

export interface LLMResponse {
  advice: string;
  confidence: number;
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  data?: Record<string, any>;
  actions?: MessageAction[];
}

export interface MessageAction {
  id: string;
  label: string;
  type: 'primary' | 'success' | 'info' | 'warning' | 'danger';
  action: string;
}

export interface QuickAction {
  id: string;
  label: string;
  type: 'primary' | 'success' | 'info' | 'warning' | 'danger';
  description: string;
  action: string;
  icon?: string;
}

export interface SystemDiagnosis {
  diagnosis: string;
  health_score: number;
  recommendations: string[];
  priority_actions: string[];
}

export interface AgriculturalAdvice {
  advice: string;
  actions: string[];
  urgency: 'low' | 'medium' | 'high';
  timestamp: string;
}

export interface ReportData {
  report: string;
  summary: string;
  recommendations: string[];
  timestamp: string;
}

export interface MCPRequest {
  command: string;
  context?: any;
}

export interface MCPResponse {
  success: boolean;
  message: string;
  data?: any;
}
