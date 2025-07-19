<template>
  <div class="chatbot-container">
    <div class="chat-header">
      <h3>🌱 AgriNex AI 农业助手</h3>
      <div class="status-indicator" :class="{ 'online': isOnline, 'offline': !isOnline }">
        {{ isOnline ? '● 在线' : '● 离线' }}
      </div>
    </div>
    <div class="chat-messages" ref="chatMessages">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message"
        :class="message.isUser ? 'user-message' : 'bot-message'"
      >
        <div class="message-avatar">
          <span v-if="message.isUser">👤</span>
          <span v-else>🤖</span>
        </div>
        <div class="message-bubble">
          <div class="message-content" v-html="formatMessageText(message.text)"></div>
          <div class="message-time">
            {{ formatTime(message.timestamp) }}
            <span v-if="message.confidence" class="confidence">
              置信度: {{ (message.confidence * 100).toFixed(0) }}%
            </span>
          </div>
        </div>
      </div>
      
      <!-- 流式输出的临时消息 -->
      <div v-if="streamingMessage" class="message bot-message">
        <div class="message-avatar">
          <span>🤖</span>
        </div>
        <div class="message-bubble">
          <div class="message-content" v-html="formatMessageText(streamingMessage)"></div>
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="quick-actions" v-if="!loading">
      <button 
        v-for="action in quickActions" 
        :key="action.text"
        @click="sendQuickMessage(action.text)"
        class="quick-action-btn"
      >
        {{ action.emoji }} {{ action.text }}
      </button>
    </div>
    
    <div class="chat-input">
      <div class="input-wrapper">
        <input
          v-model="currentMessage"
          @keypress.enter="sendMessage"
          placeholder="输入您的农业问题，例如：温度30度对番茄有什么影响？"
          :disabled="loading"
          class="message-input"
        />
        <button 
          @click="sendMessage" 
          :disabled="loading || !currentMessage.trim()"
          class="send-btn"
        >
          <span v-if="loading">⏳</span>
          <span v-else>📤</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'

export default {
  name: 'ChatBot',
  setup() {
    const messages = ref([])
    const currentMessage = ref('')
    const loading = ref(false)
    const chatMessages = ref(null)
    const streamingMessage = ref('')
    const isOnline = ref(false)
    
    // 快速操作按钮
    const quickActions = ref([
      { emoji: '🌡️', text: '查看当前环境数据' },
      { emoji: '💧', text: '灌溉建议' },
      { emoji: '🌾', text: '作物生长分析' },
      { emoji: '⚠️', text: '异常警报' }
    ])

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    const formatMessageText = (text) => {
      if (!text) return ''
      // 简单的markdown-like格式化
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    }

    const scrollToBottom = () => {
      nextTick(() => {
        if (chatMessages.value) {
          chatMessages.value.scrollTop = chatMessages.value.scrollHeight
        }
      })
    }

    const addMessage = (text, isUser = false, confidence = null) => {
      messages.value.push({
        text,
        isUser,
        timestamp: Date.now(),
        confidence
      })
      scrollToBottom()
    }

    // 检查连接状态
    const checkConnection = async () => {
      try {
        await axios.get('/api/health')
        isOnline.value = true
      } catch (error) {
        isOnline.value = false
        console.warn('API连接检查失败:', error)
      }
    }

    // 流式输出实现 - 使用Server-Sent Events
    const sendMessageWithStream = async (message) => {
      try {
        loading.value = true
        streamingMessage.value = ''
        
        const token = localStorage.getItem('token')
        
        // 构建EventSource URL，支持可选认证
        let streamUrl = `/api/llm/chat/stream?message=${encodeURIComponent(message)}`
        if (token) {
          streamUrl += `&token=${token}`
        }
        
        // 创建EventSource连接进行流式通信
        const eventSource = new EventSource(streamUrl)
        
        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data)
          
          if (data.type === 'chunk') {
            streamingMessage.value += data.content
            scrollToBottom()
          } else if (data.type === 'complete') {
            // 流式输出完成，添加到消息列表
            addMessage(streamingMessage.value, false, data.confidence)
            streamingMessage.value = ''
            eventSource.close()
            loading.value = false
          } else if (data.type === 'error') {
            console.error('流式输出错误:', data.error)
            addMessage('抱歉，发生了错误，请稍后重试。', false)
            streamingMessage.value = ''
            eventSource.close()
            loading.value = false
          }
        }
        
        eventSource.onerror = (error) => {
          console.error('EventSource错误:', error)
          eventSource.close()
          loading.value = false
          // 降级到普通API调用
          sendMessageFallback(message)
        }
        
      } catch (error) {
        console.error('流式请求失败:', error)
        loading.value = false
        // 降级到普通API调用
        sendMessageFallback(message)
      }
    }

    // 普通API调用（降级方案）
    const sendMessageFallback = async (message) => {
      try {
        loading.value = true
        
        const token = localStorage.getItem('token')
        const headers = {
          'Content-Type': 'application/json'
        }
        
        // 如果有token，添加到header中
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
        
        const response = await axios.post('/api/llm/chat', 
          { message },
          {
            headers,
            timeout: 30000 // 30秒超时
          }
        )
        
        if (response.data.success) {
          addMessage(response.data.response, false, response.data.confidence)
        } else {
          addMessage('抱歉，我暂时无法理解您的问题，请重新描述。', false)
        }
      } catch (error) {
        console.error('发送消息失败:', error)
        if (error.response?.status === 401) {
          addMessage('身份验证失败，请重新登录。', false)
        } else if (error.code === 'ECONNABORTED') {
          addMessage('请求超时，请检查网络连接或稍后重试。', false)
        } else {
          addMessage('网络连接失败，请检查网络设置。', false)
        }
      } finally {
        loading.value = false
      }
    }

    const sendMessage = async () => {
      if (!currentMessage.value.trim() || loading.value) return
      
      const message = currentMessage.value.trim()
      addMessage(message, true)
      currentMessage.value = ''
      
      // 优先使用流式输出，失败时降级到普通API
      await sendMessageWithStream(message)
    }

    const sendQuickMessage = (message) => {
      currentMessage.value = message
      sendMessage()
    }

    onMounted(() => {
      checkConnection()
      // 添加欢迎消息
      addMessage('您好！我是AgriNex智能农业助手🌱\n\n我可以帮助您：\n• 分析传感器数据\n• 提供灌溉建议\n• 监控作物健康\n• 预警异常情况\n\n请告诉我您需要什么帮助？', false)
      
      // 定期检查连接状态
      setInterval(checkConnection, 30000)
    })

    return {
      messages,
      currentMessage,
      loading,
      chatMessages,
      streamingMessage,
      isOnline,
      quickActions,
      formatTime,
      formatMessageText,
      sendMessage,
      sendQuickMessage
    }
  }
}
</script>

<style scoped>
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 900px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.chat-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.status-indicator {
  font-size: 0.9rem;
  padding: 5px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.status-indicator.online {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
}

.status-indicator.offline {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  margin-right: 12px;
  flex-shrink: 0;
}

.user-message {
  justify-content: flex-end;
}

.user-message .message-avatar {
  order: 1;
  margin-right: 0;
  margin-left: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.bot-message .message-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.message-bubble {
  max-width: 70%;
  padding: 15px 20px;
  border-radius: 20px;
  position: relative;
}

.user-message .message-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 5px;
}

.bot-message .message-bubble {
  background: white;
  color: #333;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 5px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.message-content {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-content pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 8px;
  margin: 10px 0;
  overflow-x: auto;
  font-size: 0.9rem;
}

.message-content code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.message-time {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confidence {
  background: rgba(76, 175, 80, 0.1);
  color: #4caf50;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
}

.typing-indicator {
  display: flex;
  align-items: center;
  margin-top: 8px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  border-radius: 50%;
  background: #999;
  margin-right: 4px;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.quick-actions {
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.9);
  border-top: 1px solid #e0e0e0;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.quick-action-btn {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  font-weight: 500;
}

.quick-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.chat-input {
  padding: 20px;
  background: rgba(255, 255, 255, 0.95);
  border-top: 1px solid #e0e0e0;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: center;
}

.message-input {
  flex: 1;
  padding: 15px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
  background: white;
}

.message-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.message-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chatbot-container {
    height: calc(100vh - 80px);
    border-radius: 0;
    margin: 0;
  }
  
  .message-bubble {
    max-width: 85%;
  }
  
  .quick-actions {
    padding: 10px 15px;
  }
  
  .quick-action-btn {
    font-size: 0.8rem;
    padding: 6px 12px;
  }
  
  .chat-input {
    padding: 15px;
  }
  
  .message-input {
    font-size: 16px; /* 防止iOS缩放 */
  }
}
</style>

