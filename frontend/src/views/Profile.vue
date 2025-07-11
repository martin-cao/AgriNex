<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <span>👤 个人资料</span>
        </div>
      </template>
      
      <el-form :model="userForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" />
        </el-form-item>
        
        <el-form-item label="角色">
          <el-tag :type="getRoleType(userForm.role)">
            {{ getRoleText(userForm.role) }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="注册时间">
          <span>{{ formatDate(userForm.created_at) }}</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="updateProfile">
            更新资料
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="password-card">
      <template #header>
        <div class="card-header">
          <span>🔐 修改密码</span>
        </div>
      </template>
      
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="changePassword">
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils'

const authStore = useAuthStore()
const formRef = ref()
const passwordFormRef = ref()

const userForm = ref({
  username: '',
  email: '',
  role: '',
  created_at: ''
})

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule: any, value: any, callback: any) => {
        if (value !== passwordForm.value.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const getRoleType = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: 'danger',
    user: 'primary',
    guest: 'info'
  }
  return roleMap[role] || 'info'
}

const getRoleText = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: '管理员',
    user: '用户',
    guest: '访客'
  }
  return roleMap[role] || role
}

const updateProfile = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    // 模拟API调用
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    ElMessage.error('个人资料更新失败')
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    // 模拟API调用
    ElMessage.success('密码修改成功')
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error) {
    ElMessage.error('密码修改失败')
  }
}

onMounted(() => {
  if (authStore.user) {
    userForm.value = {
      username: authStore.user.username,
      email: authStore.user.email || '',
      role: authStore.user.role,
      created_at: authStore.user.created_at
    }
  }
})
</script>

<style scoped>
.profile-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.profile-card,
.password-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: bold;
}

.el-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
