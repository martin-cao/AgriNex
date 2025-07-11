<template>
  <div class="login-container">
    <div class="login-form">
      <div class="login-header">
        <h1>🌱 AgriNex 农业物联网平台</h1>
        <p>数据采集与可视化系统</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- 登录标签页 -->
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form-content"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="authStore.isLoading"
                class="login-button"
                @click="handleLogin"
              >
                {{ authStore.isLoading ? "登录中..." : "登录" }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 注册标签页 -->
        <el-tab-pane label="注册" name="register">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            class="login-form-content"
            @submit.prevent="handleRegister"
          >
            <el-form-item prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入邮箱"
                size="large"
                prefix-icon="Message"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请确认密码"
                size="large"
                prefix-icon="Lock"
                show-password
                @keyup.enter="handleRegister"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="authStore.isLoading"
                class="login-button"
                @click="handleRegister"
              >
                {{ authStore.isLoading ? "注册中..." : "注册" }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { useAuthStore } from '../stores/auth';
import type { LoginForm, RegisterForm } from '../types';

const router = useRouter();
const authStore = useAuthStore();

const activeTab = ref('login');
const loginFormRef = ref<FormInstance>();
const registerFormRef = ref<FormInstance>();

// 登录表单
const loginForm = reactive<LoginForm>({
  username: '',
  password: ''
});

// 注册表单
const registerForm = reactive<RegisterForm>({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
});

// 登录验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
};

// 注册验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return;
  
  try {
    await loginFormRef.value.validate();
    await authStore.login(loginForm);
    
    // 等待 Vue 的响应式更新完成
    await nextTick();
    
    ElMessage.success('登录成功');
    router.push('/dashboard');
  } catch (error: any) {
    console.error('登录错误:', error);
    
    let errorMessage = '登录失败';
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error;
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    ElMessage.error(errorMessage);
  }
};

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return;
  
  try {
    await registerFormRef.value.validate();
    const { confirmPassword, ...registerData } = registerForm;
    await authStore.register(registerData);
    ElMessage.success('注册成功');
    router.push('/dashboard');
  } catch (error: any) {
    ElMessage.error(error.message || '注册失败');
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-form {
  background: white;
  padding: 40px;
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #333;
  font-size: 28px;
  margin-bottom: 10px;
}

.login-header p {
  color: #666;
  font-size: 16px;
}

.login-tabs {
  margin-bottom: 20px;
}

.login-form-content {
  margin-top: 20px;
}

.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  border-radius: 10px;
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  padding: 0 30px;
  font-size: 16px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-input__inner) {
  height: 45px;
  border-radius: 10px;
  font-size: 16px;
}

@media (max-width: 480px) {
  .login-form {
    padding: 30px 20px;
  }
  
  .login-header h1 {
    font-size: 24px;
  }
}
</style>
