<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <div class="logo">
            <div class="logo-icon">🌱</div>
            <h1>AgriNex</h1>
          </div>
          <p class="subtitle">农业物联网管理平台</p>
        </div>

        <a-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @finish="handleLogin"
        >
          <a-form-item name="username">
            <a-input
              v-model:value="loginForm.username"
              size="large"
              placeholder="用户名"
              :prefix="h(UserOutlined)"
            />
          </a-form-item>

          <a-form-item name="password">
            <a-input-password
              v-model:value="loginForm.password"
              size="large"
              placeholder="密码"
              :prefix="h(LockOutlined)"
            />
          </a-form-item>

          <a-form-item>
            <div class="login-options">
              <a-checkbox v-model:checked="loginForm.remember">
                记住我
              </a-checkbox>
              <a href="#" class="forgot-password">忘记密码？</a>
            </div>
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              size="large"
              block
              :loading="loading"
            >
              登录
            </a-button>
          </a-form-item>
        </a-form>

        <div class="login-footer">
          <p class="register-link">
            还没有账号？ <router-link to="/register" class="link">立即注册</router-link>
          </p>
        </div>
      </div>
    </div>

    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, h } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { useAuthStore } from '@/stores/auth';
import {
  UserOutlined,
  LockOutlined
} from '@ant-design/icons-vue';

const router = useRouter();
const authStore = useAuthStore();

// 响应式数据
const loading = ref(false);
const loginFormRef = ref();

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
});

const loginRules = {
  username: [
    { required: true, message: '请输入用户名' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 6, max: 32, message: '密码长度为6-32个字符' }
  ]
};

// 方法
const handleLogin = async () => {
  try {
    loading.value = true;
    
    await authStore.login({
      username: loginForm.username,
      password: loginForm.password,
      remember: loginForm.remember
    });
    
    message.success('登录成功');
    router.push('/dashboard');
  } catch (error: any) {
    message.error(error.message || '登录失败');
  } finally {
    loading.value = false;
  }
};
</script>

<style lang="less" scoped>
.login-page {
  position: relative;
  height: 100vh;
  background: var(--agrinex-bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  .login-container {
    position: relative;
    z-index: 10;
    
    .login-card {
      width: 400px;
      background: var(--agrinex-bg-card);
      border: none;
      border-radius: 12px;
      padding: 40px;
      box-shadow: var(--agrinex-shadow-heavy);
      backdrop-filter: blur(10px);

      .login-header {
        text-align: center;
        margin-bottom: 32px;

        .logo {
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 16px;

          .logo-icon {
            font-size: 48px;
            margin-right: 12px;
          }

          h1 {
            margin: 0;
            font-size: 28px;
            font-weight: 600;
            color: var(--agrinex-primary);
          }
        }

        .subtitle {
          margin: 0;
          color: var(--agrinex-text-tertiary);
          font-size: 14px;
        }
      }

      .login-form {
        .login-options {
          display: flex;
          justify-content: space-between;
          align-items: center;

          .forgot-password {
            color: var(--agrinex-primary);
            text-decoration: none;
            font-size: 12px;

            &:hover {
              text-decoration: underline;
            }
          }
        }

        :deep(.ant-btn-primary) {
          background: #52c41a;
          border-color: #52c41a;
          height: 44px;
          font-size: 16px;
          border-radius: 6px;

          &:hover {
            background: #73d13d;
            border-color: #73d13d;
          }
        }
      }

      .login-footer {
        margin-top: 24px;

        .register-link {
          text-align: center;
          margin: 0;
          font-size: 12px;
          color: var(--agrinex-text-secondary);

          .link {
            color: #52c41a;
            text-decoration: none;

            &:hover {
              text-decoration: underline;
            }
          }
        }
      }
    }
  }

  .background-decoration {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;

    .circle {
      position: absolute;
      border-radius: 50%;
      background: rgba(82, 196, 26, 0.05);
      animation: float 6s ease-in-out infinite;

      &.circle-1 {
        width: 200px;
        height: 200px;
        top: 10%;
        left: 10%;
        animation-delay: 0s;
      }

      &.circle-2 {
        width: 150px;
        height: 150px;
        top: 60%;
        right: 15%;
        animation-delay: 2s;
      }

      &.circle-3 {
        width: 100px;
        height: 100px;
        bottom: 20%;
        left: 20%;
        animation-delay: 4s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

// 响应式适配
@media (max-width: 768px) {
  .login-page {
    padding: 20px;

    .login-container {
      .login-card {
        width: 100%;
        max-width: 360px;
        padding: 32px 24px;
      }
    }
  }
}

@media (max-width: 480px) {
  .login-page {
    .login-container {
      .login-card {
        padding: 24px 20px;

        .login-header {
          .logo {
            h1 {
              font-size: 24px;
            }
          }
        }
      }
    }
  }
}
</style>
