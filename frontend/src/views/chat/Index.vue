<template>
  <div class="chat-page">
    <div class="chat-container">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="header-info">
          <a-avatar :size="40" style="background-color: #52c41a;">
            <robot-outlined />
          </a-avatar>
          <div class="header-text">
            <h3>AgriNex AI 助手</h3>
            <p>我是您的农业物联网智能助手，有什么可以帮您的吗？</p>
          </div>
        </div>
        <div class="header-actions">
          <a-space>
            <a-button @click="clearChat" size="small">
              <delete-outlined />
              清空对话
            </a-button>
            <a-button @click="exportChat" size="small">
              <download-outlined />
              导出对话
            </a-button>
          </a-space>
        </div>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <div class="messages-content">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-content">
              <a-avatar :size="60" style="background-color: #52c41a; margin-bottom: 16px;">
                <robot-outlined />
              </a-avatar>
              <h3>欢迎使用 AgriNex AI 助手！</h3>
              <p>我可以帮您：</p>
              <div class="capabilities">
                <a-row :gutter="[16, 16]">
                  <a-col :span="12">
                    <div class="capability-item" @click="sendQuickMessage('查看设备状态')">
                      <laptop-outlined />
                      <span>查看设备状态</span>
                    </div>
                  </a-col>
                  <a-col :span="12">
                    <div class="capability-item" @click="sendQuickMessage('分析传感器数据')">
                      <line-chart-outlined />
                      <span>分析传感器数据</span>
                    </div>
                  </a-col>
                  <a-col :span="12">
                    <div class="capability-item" @click="sendQuickMessage('告警分析')">
                      <bell-outlined />
                      <span>告警分析</span>
                    </div>
                  </a-col>
                  <a-col :span="12">
                    <div class="capability-item" @click="sendQuickMessage('农业建议')">
                      <bulb-outlined />
                      <span>农业建议</span>
                    </div>
                  </a-col>
                </a-row>
              </div>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-for="message in messages" :key="message.id" class="message-item">
            <div :class="['message-wrapper', message.role]">
              <div class="message-avatar">
                <a-avatar v-if="message.role === 'assistant'" :size="32" style="background-color: #52c41a;">
                  <robot-outlined />
                </a-avatar>
                <a-avatar v-else :size="32" style="background-color: #1890ff;">
                  <user-outlined />
                </a-avatar>
              </div>
              
              <div class="message-content">
                <div class="message-header">
                  <span class="message-role">
                    {{ message.role === 'assistant' ? 'AI 助手' : '我' }}
                  </span>
                  <span class="message-time">
                    {{ formatTime(message.timestamp) }}
                  </span>
                </div>
                
                <div class="message-text">
                  <div v-if="message.loading" class="message-loading">
                    <a-spin size="small" />
                    <span>AI 正在思考...</span>
                  </div>
                  <div v-else-if="message.type === 'text'" v-html="formatMessageContent(message.content)"></div>
                  <div v-else-if="message.type === 'chart'" class="message-chart">
                    <ChartContainer
                      :title="message.chartTitle"
                      :option="message.chartData"
                      :height="300"
                    />
                  </div>
                  <div v-else-if="message.type === 'table'" class="message-table">
                    <a-table
                      :columns="message.tableColumns"
                      :data-source="message.tableData"
                      :pagination="false"
                      size="small"
                    />
                  </div>
                </div>
                
                <div v-if="message.actions" class="message-actions">
                  <a-space wrap>
                    <a-button
                      v-for="action in message.actions"
                      :key="action.label"
                      size="small"
                      @click="handleMessageAction(action)"
                    >
                      {{ action.label }}
                    </a-button>
                  </a-space>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="input-container">
          <a-textarea
            v-model:value="inputMessage"
            placeholder="输入您的问题或需求..."
            :auto-size="{ minRows: 1, maxRows: 4 }"
            @keydown.enter.ctrl="sendMessage"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <div class="input-actions">
            <a-tooltip title="Ctrl+Enter 发送">
              <a-button
                type="primary"
                :loading="sending"
                :disabled="!inputMessage.trim()"
                @click="sendMessage"
              >
                <send-outlined />
                发送
              </a-button>
            </a-tooltip>
          </div>
        </div>
        
        <!-- 快捷操作 -->
        <div class="quick-actions">
          <a-space wrap>
            <a-tag
              v-for="suggestion in suggestions"
              :key="suggestion"
              color="blue"
              style="cursor: pointer;"
              @click="sendQuickMessage(suggestion)"
            >
              {{ suggestion }}
            </a-tag>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import ChartContainer from '@/components/charts/ChartContainer.vue';
import { chatApi } from '@/api/chat';
import dayjs from 'dayjs';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'chart' | 'table';
  timestamp: string;
  loading?: boolean;
  chartTitle?: string;
  chartData?: any;
  tableColumns?: any[];
  tableData?: any[];
  actions?: Array<{ label: string; action: string; params?: any }>;
}

// 响应式数据
const messages = ref<ChatMessage[]>([]);
const inputMessage = ref('');
const sending = ref(false);
const messagesContainer = ref<HTMLElement>();

const suggestions = [
  '今天的设备状态如何？',
  '有哪些告警需要处理？',
  '分析最近的温度数据',
  '推荐灌溉计划',
  '查看产量预测',
  '设备维护建议'
];

// 方法
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value) return;

  const userMessage: ChatMessage = {
    id: generateMessageId(),
    role: 'user',
    content: inputMessage.value.trim(),
    type: 'text',
    timestamp: new Date().toISOString()
  };

  messages.value.push(userMessage);
  const userInput = inputMessage.value.trim();
  inputMessage.value = '';

  // 添加 AI 消息占位符
  const assistantMessage: ChatMessage = {
    id: generateMessageId(),
    role: 'assistant',
    content: '',
    type: 'text',
    timestamp: new Date().toISOString(),
    loading: true
  };

  messages.value.push(assistantMessage);
  scrollToBottom();

  try {
    sending.value = true;
    const response = await chatApi.sendMessage({
      message: userInput,
      conversation_id: getCurrentConversationId()
    });

    // 更新 AI 回复
    const messageIndex = messages.value.findIndex(m => m.id === assistantMessage.id);
    if (messageIndex !== -1) {
      messages.value[messageIndex] = {
        ...assistantMessage,
        content: response.data.message,
        type: response.data.type || 'text',
        loading: false,
        chartTitle: response.data.chart_title,
        chartData: response.data.chart_data,
        tableColumns: response.data.table_columns,
        tableData: response.data.table_data,
        actions: response.data.actions
      };
    }
  } catch (error) {
    message.error('发送消息失败');
    // 移除失败的消息
    const messageIndex = messages.value.findIndex(m => m.id === assistantMessage.id);
    if (messageIndex !== -1) {
      messages.value.splice(messageIndex, 1);
    }
  } finally {
    sending.value = false;
    scrollToBottom();
  }
};

const sendQuickMessage = (text: string) => {
  inputMessage.value = text;
  sendMessage();
};

const clearChat = () => {
  messages.value = [];
  message.success('对话已清空');
};

const exportChat = () => {
  const chatContent = messages.value
    .map(msg => `${msg.role === 'assistant' ? 'AI助手' : '用户'} [${formatTime(msg.timestamp)}]: ${msg.content}`)
    .join('\n\n');

  const blob = new Blob([chatContent], { type: 'text/plain;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `chat_export_${dayjs().format('YYYYMMDD_HHmmss')}.txt`;
  link.click();

  message.success('对话导出成功');
};

const handleMessageAction = (action: any) => {
  switch (action.action) {
    case 'view_device':
      // 跳转到设备详情
      break;
    case 'view_alarms':
      // 跳转到告警页面
      break;
    case 'send_message':
      sendQuickMessage(action.params.message);
      break;
    default:
      message.info(`执行操作: ${action.label}`);
  }
};

const formatMessageContent = (content: string) => {
  // 简单的文本格式化，支持换行和基本标记
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>');
};

const formatTime = (timestamp: string) => {
  return dayjs(timestamp).format('HH:mm');
};

const generateMessageId = () => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const getCurrentConversationId = () => {
  // 这里可以实现会话管理逻辑
  return 'default';
};

const scrollToBottom = async () => {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 生命周期
onMounted(() => {
  // 可以在这里加载历史对话
});
</script>

<style lang="less" scoped>
.chat-page {
  height: calc(100vh - 120px);
  display: flex;
  justify-content: center;
  
  .chat-container {
    width: 100%;
    max-width: 1000px;
    height: 100%;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .chat-header {
      padding: 16px 20px;
      border-bottom: 1px solid #f0f0f0;
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-info {
        display: flex;
        align-items: center;
        gap: 12px;

        .header-text {
          h3 {
            margin: 0;
            font-size: 16px;
            color: #262626;
          }

          p {
            margin: 0;
            font-size: 12px;
            color: #8c8c8c;
          }
        }
      }

      .header-actions {
        flex-shrink: 0;
      }
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 0;
      
      .messages-content {
        min-height: 100%;
        padding: 20px;
      }

      .welcome-message {
        text-align: center;
        padding: 40px 20px;

        .welcome-content {
          h3 {
            margin: 0 0 8px 0;
            color: #262626;
          }

          p {
            margin: 0 0 24px 0;
            color: #8c8c8c;
          }

          .capabilities {
            .capability-item {
              padding: 12px;
              border: 1px solid #f0f0f0;
              border-radius: 6px;
              cursor: pointer;
              transition: all 0.3s;
              display: flex;
              align-items: center;
              gap: 8px;

              &:hover {
                border-color: #52c41a;
                color: #52c41a;
              }

              span {
                font-size: 14px;
              }
            }
          }
        }
      }

      .message-item {
        margin-bottom: 16px;

        .message-wrapper {
          display: flex;
          gap: 12px;

          &.assistant {
            flex-direction: row;
          }

          &.user {
            flex-direction: row-reverse;

            .message-content {
              background: #52c41a;
              color: white;
            }
          }

          .message-avatar {
            flex-shrink: 0;
          }

          .message-content {
            max-width: 70%;
            background: #f5f5f5;
            border-radius: 12px;
            padding: 12px 16px;

            .message-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;

              .message-role {
                font-size: 12px;
                font-weight: 600;
                color: inherit;
              }

              .message-time {
                font-size: 11px;
                opacity: 0.7;
              }
            }

            .message-text {
              line-height: 1.6;

              .message-loading {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #8c8c8c;
              }
            }

            .message-chart,
            .message-table {
              margin-top: 12px;
              background: #fff;
              border-radius: 6px;
              padding: 12px;
              border: 1px solid #f0f0f0;
            }

            .message-actions {
              margin-top: 12px;
              padding-top: 8px;
              border-top: 1px solid rgba(255, 255, 255, 0.2);
            }
          }
        }
      }
    }

    .chat-input {
      border-top: 1px solid #f0f0f0;
      padding: 16px 20px;

      .input-container {
        display: flex;
        gap: 12px;
        margin-bottom: 12px;

        :deep(.ant-input) {
          flex: 1;
          border-radius: 20px;
          padding: 8px 16px;
        }

        .input-actions {
          flex-shrink: 0;

          .ant-btn {
            border-radius: 20px;
            height: auto;
            padding: 8px 16px;
          }
        }
      }

      .quick-actions {
        .ant-tag {
          margin-bottom: 4px;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .chat-page {
    height: calc(100vh - 80px);
    
    .chat-container {
      .chat-header {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;

        .header-actions {
          width: 100%;
        }
      }

      .chat-messages {
        .message-item {
          .message-wrapper {
            .message-content {
              max-width: 85%;
            }
          }
        }
      }

      .chat-input {
        .input-container {
          flex-direction: column;

          .input-actions {
            align-self: flex-end;
          }
        }
      }
    }
  }
}
</style>
