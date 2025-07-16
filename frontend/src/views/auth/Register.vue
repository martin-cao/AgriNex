<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-card">
        <!-- 左侧品牌介绍区域 -->
        <div class="brand-section">
          <div class="brand-content">
            <div class="logo-section">
              <div class="logo-icon">🌱</div>
              <h1>AgriNex</h1>
              <p class="brand-subtitle">农业物联网管理平台</p>
            </div>
            
            <div class="features">
              <div class="feature-item">
                <div class="feature-icon">📊</div>
                <h3>实时数据监控</h3>
                <p>全面监控农业设备状态和环境数据，让您随时掌握农场动态</p>
              </div>
              <div class="feature-item">
                <div class="feature-icon">🔔</div>
                <h3>智能告警系统</h3>
                <p>及时发现异常情况，自动预警，确保农业生产安全稳定</p>
              </div>
              <div class="feature-item">
                <div class="feature-icon">🤖</div>
                <h3>AI智能分析</h3>
                <p>基于大数据的智能分析，为您的农业决策提供科学依据</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧注册表单区域 -->
        <div class="form-section">
          <div class="form-container">
            <div class="form-header">
              <h2>创建您的账户</h2>
              <p>加入AgriNex，开启智慧农业之旅</p>
            </div>

            <a-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              class="register-form"
              layout="vertical"
              @finish="handleRegister"
            >
              <a-form-item label="用户名" name="username">
                <a-input
                  v-model:value="registerForm.username"
                  size="large"
                  placeholder="请输入用户名"
                  :prefix="h(UserOutlined)"
                />
              </a-form-item>

              <a-form-item label="邮箱地址" name="email">
                <a-input
                  v-model:value="registerForm.email"
                  size="large"
                  placeholder="请输入邮箱地址"
                  :prefix="h(MailOutlined)"
                />
              </a-form-item>

              <a-form-item label="密码" name="password">
                <a-input-password
                  v-model:value="registerForm.password"
                  size="large"
                  placeholder="请输入密码"
                  :prefix="h(LockOutlined)"
                />
              </a-form-item>

              <a-form-item label="确认密码" name="confirmPassword">
                <a-input-password
                  v-model:value="registerForm.confirmPassword"
                  size="large"
                  placeholder="请再次输入密码"
                  :prefix="h(LockOutlined)"
                />
              </a-form-item>

              <a-form-item name="agreement">
                <a-checkbox v-model:checked="registerForm.agreement">
                  我已阅读并同意 
                  <a href="#" class="agreement-link" @click.prevent>《用户服务协议》</a> 
                  和 
                  <a href="#" class="agreement-link" @click.prevent>《隐私政策》</a>
                </a-checkbox>
              </a-form-item>

              <a-form-item>
                <a-button
                  type="primary"
                  html-type="submit"
                  size="large"
                  block
                  :loading="loading"
                >
                  立即注册
                </a-button>
              </a-form-item>
            </a-form>

            <div class="form-footer">
              <a-divider>
                <span style="color: var(--agrinex-text-secondary); font-size: 12px;">已有账号？</span>
              </a-divider>
              
              <div class="login-link">
                <router-link to="/login">
                  <a-button type="link" size="large" block>
                    返回登录
                  </a-button>
                </router-link>
              </div>
            </div>
          </div>
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
  LockOutlined,
  MailOutlined
} from '@ant-design/icons-vue';

const router = useRouter();
const authStore = useAuthStore();

// 响应式数据
const loading = ref(false);
const registerFormRef = ref();

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreement: false
});

// 表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应为3-20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度应为6-32个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => {
        if (value !== registerForm.password) {
          return Promise.reject('两次输入的密码不一致');
        }
        return Promise.resolve();
      },
      trigger: 'blur'
    }
  ],
  agreement: [
    {
      validator: (rule: any, value: boolean) => {
        if (!value) {
          return Promise.reject('请阅读并同意用户协议');
        }
        return Promise.resolve();
      },
      trigger: 'change'
    }
  ]
};

// 处理注册
const handleRegister = async () => {
  try {
    loading.value = true;
    
    // 从表单数据中提取注册需要的字段，排除 confirmPassword 和 agreement
    const { confirmPassword, agreement, ...registerData } = registerForm;
    
    console.log('准备注册用户:', registerData);
    
    // 调用注册API
    const response = await authStore.register(registerData);
    
    console.log('注册响应:', response);
    
    // 注册成功提示
    message.success('注册成功！正在跳转到登录页面...');
    
    // 清空表单
    Object.assign(registerForm, {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
      agreement: false
    });
    
    // 延迟跳转到登录页面
    setTimeout(() => {
      router.push('/login');
    }, 1500);
    
  } catch (error: any) {
    console.error('注册失败:', error);
    
    let errorMessage = '注册失败，请重试';
    
    // 处理不同类型的错误信息
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error;
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    message.error(errorMessage);
  } finally {
    loading.value = false;
  }
};
</script>

<style lang="less" scoped>
.register-page {
  position: relative;
  min-height: 100vh;
  background: var(--agrinex-bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: hidden;

  .register-container {
    position: relative;
    z-index: 10;
    width: 100%;
    max-width: 900px;

    .register-card {
      background: var(--agrinex-bg-card);
      border-radius: 12px;
      box-shadow: var(--agrinex-shadow-medium);
      backdrop-filter: blur(10px);
      border: none;
      display: flex;
      overflow: hidden;
      min-height: 500px;

      // 左侧品牌介绍区域
      .brand-section {
        flex: 1;
        background: linear-gradient(135deg, #689f38 0%, #7cb342 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px 30px;
        position: relative;

        &::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="20" cy="20" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="60" r="1" fill="rgba(255,255,255,0.1)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
          opacity: 0.3;
        }

        .brand-content {
          position: relative;
          z-index: 2;
          text-align: center;
          color: white;
          max-width: 400px;

          .logo-section {
            margin-bottom: 30px;

            .logo-icon {
              font-size: 48px;
              margin-bottom: 12px;
              text-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }

            h1 {
              font-size: 28px;
              font-weight: 700;
              margin: 0 0 8px 0;
              text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
            }

            .brand-subtitle {
              font-size: 14px;
              margin: 0;
              opacity: 0.9;
              font-weight: 300;
            }
          }

          .features {
            .feature-item {
              margin-bottom: 24px;
              text-align: left;

              .feature-icon {
                font-size: 20px;
                margin-bottom: 8px;
              }

              h3 {
                font-size: 14px;
                font-weight: 600;
                margin: 0 0 6px 0;
                color: white;
              }

              p {
                font-size: 12px;
                line-height: 1.4;
                margin: 0;
                opacity: 0.9;
                font-weight: 300;
              }
            }
          }
        }
      }

      // 右侧表单区域
      .form-section {
        flex: 0 0 400px;
        background: var(--agrinex-bg-card);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px 32px;

        .form-container {
          width: 100%;
          max-width: 360px;

          .form-header {
            text-align: center;
            margin-bottom: 24px;

            h2 {
              font-size: 20px;
              font-weight: 600;
              color: var(--agrinex-text-primary);
              margin: 0 0 6px 0;
            }

            p {
              font-size: 13px;
              color: var(--agrinex-text-tertiary);
              margin: 0;
            }
          }

          .register-form {
            margin-bottom: 20px;

            // 表单项标签样式
            :deep(.ant-form-item-label) {
              > label {
                font-size: 13px;
                font-weight: 500;
                color: var(--agrinex-text-primary);
                height: auto;
              }
            }

            // 表单项间距
            :deep(.ant-form-item) {
              margin-bottom: 16px;
            }

            // 保持与登录页面一致的输入框样式
            :deep(.ant-input) {
              height: 40px;
              border-radius: 6px;
              border: 1px solid var(--agrinex-border-color);
              transition: all 0.3s;

              &:hover {
                border-color: #52c41a;
              }

              &:focus {
                border-color: #52c41a;
                box-shadow: 0 0 0 2px rgba(82, 196, 26, 0.2);
              }
            }

            :deep(.ant-input-password) {
              .ant-input {
                height: 40px;
                border-radius: 6px;
              }
            }

            :deep(.ant-input-affix-wrapper) {
              height: 40px;
              border-radius: 6px;
              border: 1px solid var(--agrinex-border-color);
              padding: 0;
              overflow: hidden;

              .ant-input-prefix {
                padding: 0 12px;
                display: flex;
                align-items: center;
                background: var(--agrinex-bg-hover);
                border-right: 1px solid var(--agrinex-border-color-split);
                margin: 0;
                
                .anticon {
                  color: var(--agrinex-text-secondary);
                  font-size: 16px;
                }
              }

              .ant-input {
                border: none !important;
                box-shadow: none !important;
                padding-left: 12px;
              }

              &:hover {
                border-color: #52c41a;
                
                .ant-input-prefix {
                  border-right-color: #52c41a;
                }
              }

              &.ant-input-affix-wrapper-focused {
                border-color: #52c41a;
                box-shadow: 0 0 0 2px rgba(82, 196, 26, 0.2);
                
                .ant-input-prefix {
                  border-right-color: #52c41a;
                  background: var(--agrinex-bg-active);
                  
                  .anticon {
                    color: #52c41a;
                  }
                }
              }
            }

            // 保持与登录页面一致的按钮样式
            :deep(.ant-btn-primary) {
              background: #52c41a;
              border-color: #52c41a;
              height: 40px;
              font-size: 14px;
              border-radius: 6px;
              font-weight: 500;

              &:hover {
                background: #73d13d;
                border-color: #73d13d;
              }
            }

            :deep(.ant-checkbox-wrapper) {
              font-size: 13px;
              line-height: 1.5;
            }

            .agreement-link {
              color: #52c41a;
              text-decoration: none;
              
              &:hover {
                color: #73d13d;
                text-decoration: underline;
              }
            }
          }

          .form-footer {
            .login-link {
              :deep(.ant-btn-link) {
                color: #52c41a;
                font-weight: 500;
                
                &:hover {
                  color: #73d13d;
                }
              }
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
      animation: float 8s ease-in-out infinite;

      &.circle-1 {
        width: 240px;
        height: 240px;
        top: 8%;
        left: 8%;
        animation-delay: 0s;
      }

      &.circle-2 {
        width: 180px;
        height: 180px;
        top: 65%;
        right: 10%;
        animation-delay: 3s;
      }

      &.circle-3 {
        width: 120px;
        height: 120px;
        bottom: 15%;
        left: 15%;
        animation-delay: 6s;
      }
    }
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.6;
  }
  50% {
    transform: translateY(-30px) rotate(180deg);
    opacity: 0.8;
  }
}

// 响应式设计
@media (max-width: 1024px) {
  .register-page {
    .register-container {
      max-width: 900px;

      .register-card {
        .brand-section {
          padding: 40px 30px;

          .brand-content {
            .logo-section {
              margin-bottom: 40px;

              .logo-icon {
                font-size: 48px;
              }

              h1 {
                font-size: 28px;
              }
            }

            .features {
              .feature-item {
                margin-bottom: 28px;

                .feature-icon {
                  font-size: 24px;
                }

                h3 {
                  font-size: 16px;
                }

                p {
                  font-size: 13px;
                }
              }
            }
          }
        }

        .form-section {
          flex: 0 0 400px;
          padding: 40px 30px;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .register-page {
    padding: 16px;

    .register-container {
      .register-card {
        flex-direction: column;
        min-height: auto;

        .brand-section {
          flex: 0 0 auto;
          min-height: 300px;
          padding: 40px 30px;

          .brand-content {
            .logo-section {
              margin-bottom: 20px;

              .logo-icon {
                font-size: 48px;
              }

              h1 {
                font-size: 28px;
              }

              .brand-subtitle {
                font-size: 14px;
              }
            }

            .features {
              display: none; // 在移动端隐藏特性列表
            }
          }
        }

        .form-section {
          flex: 1;
          padding: 30px 20px;

          .form-container {
            .form-header {
              margin-bottom: 24px;

              h2 {
                font-size: 22px;
              }

              p {
                font-size: 13px;
              }
            }
          }
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .register-page {
    padding: 12px;

    .register-container {
      .register-card {
        border-radius: 12px;

        .brand-section {
          padding: 30px 20px;
        }

        .form-section {
          padding: 24px 16px;

          .form-container {
            .form-header {
              h2 {
                font-size: 20px;
              }
            }
          }
        }
      }
    }
  }
}
</style>
