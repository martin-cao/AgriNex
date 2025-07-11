<template>
  <div class="chatbot-container">
    <div class="chat-header">
      <h3>AI 农业助手</h3>
    </div>
    <div class="chat-messages" ref="chatMessages">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message"
        :class="message.isUser ? 'user-message' : 'bot-message'"
      >
        <div class="message-content">
          {{ message.text }}
        </div>
        <div class="message-time">
          {{ formatTime(message.timestamp) }}
        </div>
      </div>
    </div>
    <div class="chat-input">
      <input
        v-model="currentMessage"
        @keypress.enter="sendMessage"
        placeholder="输入您的问题..."
        :disabled="loading"
      />
      <button @click="sendMessage" :disabled="loading || !currentMessage.trim()">
        {{ loading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, nextTick, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'ChatBot',
  setup() {
    const messages = reactive([
      {
        text: '您好！我是AI农业助手，可以为您提供农业相关的建议和解答。请问有什么可以帮助您的吗？',
        isUser: false,
        timestamp: new Date()
      }
    ])
    const currentMessage = ref('')
    const loading = ref(false)
    const chatMessages = ref(null)

    const formatTime = (timestamp) => {
      return timestamp.toLocaleTimeString()
    }

    const scrollToBottom = () => {
      nextTick(() => {
        if (chatMessages.value) {
          chatMessages.value.scrollTop = chatMessages.value.scrollHeight
        }
      })
    }

    const sendMessage = async () => {
      if (!currentMessage.value.trim() || loading.value) return

      const userMessage = {
        text: currentMessage.value,
        isUser: true,
        timestamp: new Date()
      }

      messages.push(userMessage)
      const question = currentMessage.value
      currentMessage.value = ''
      loading.value = true

      scrollToBottom()

      try {
        const response = await axios.post('/api/chat', {
          message: question
        })

        const botMessage = {
          text: response.data.response || '抱歉，我无法处理您的请求。',
          isUser: false,
          timestamp: new Date()
        }

        messages.push(botMessage)
      } catch (error) {
        console.error('Chat error:', error)
        const errorMessage = {
          text: '抱歉，服务暂时不可用。请稍后再试。',
          isUser: false,
          timestamp: new Date()
        }
        messages.push(errorMessage)
      } finally {
        loading.value = false
        scrollToBottom()
      }
    }

    onMounted(() => {
      scrollToBottom()
    })

    return {
      messages,
      currentMessage,
      loading,
      chatMessages,
      formatTime,
      sendMessage
    }
  }
}
</script>

<style scoped>
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 800px;
  margin: 0 auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.chat-header {
  background: #4CAF50;
  color: white;
  padding: 1rem;
  text-align: center;
}

.chat-header h3 {
  margin: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: #f5f5f5;
}

.message {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
}

.user-message {
  align-items: flex-end;
}

.bot-message {
  align-items: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 0.75rem 1rem;
  border-radius: 18px;
  word-wrap: break-word;
}

.user-message .message-content {
  background: #4CAF50;
  color: white;
}

.bot-message .message-content {
  background: white;
  color: #333;
  border: 1px solid #ddd;
}

.message-time {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
}

.chat-input {
  display: flex;
  padding: 1rem;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.chat-input input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 20px;
  outline: none;
  margin-right: 0.5rem;
}

.chat-input button {
  padding: 0.75rem 1.5rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.chat-input button:hover:not(:disabled) {
  background: #45a049;
}

.chat-input button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
