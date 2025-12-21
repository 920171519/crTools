<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <h1>用户注册</h1>
        <p>创建您的crTools账户</p>
      </div>

      <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" class="register-form" size="large">
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入姓名" prefix-icon="Avatar" clearable />
        </el-form-item>

        <el-form-item prop="employee_id">
          <el-input v-model="registerForm.employee_id" placeholder="请输入工号(如: A12345678)" prefix-icon="User" clearable />
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password
            clearable />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码" prefix-icon="Lock"
            show-password clearable />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" class="register-btn" :loading="loading" @click="handleRegister">
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </el-form-item>

        <div class="register-links">
          <router-link to="/login" class="login-link">
            已有账号？立即登录
          </router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const registerFormRef = ref<FormInstance>()

// 表单数据
const registerForm = reactive({
  employee_id: '',
  username: '',
  password: '',
  confirmPassword: '',
})

// 自定义验证函数
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const registerRules: FormRules = {
  employee_id: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    {
      pattern: /^[A-Za-z]\d{8}$/,
      message: '工号格式错误，应为一个字母加8个数字',
      trigger: 'blur'
    }
  ],
  username: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度在2-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
}

// 注册状态
const loading = ref(false)

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    // 验证表单
    await registerFormRef.value.validate()

    loading.value = true

    // 准备注册数据
    const userData = {
      employee_id: registerForm.employee_id,
      username: registerForm.username,
      password: registerForm.password,
    }

    // 调用注册接口
    await userStore.registerAction(userData)

    ElMessage.success('注册成功，请登录')

    // 跳转到登录页面
    router.push('/login')
  } catch (error: any) {
    console.error('注册失败:', error)
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 0;
}

.register-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 450px;
  max-height: 90vh;
  overflow-y: auto;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h1 {
  color: #303133;
  font-size: 24px;
  margin-bottom: 8px;
  font-weight: 600;
}

.register-header p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.register-form {
  margin-bottom: 20px;
}

.register-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 500;
}

.register-links {
  text-align: center;
}

.login-link {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s;
}

.login-link:hover {
  color: #66b1ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-container {
    padding: 10px;
  }

  .register-box {
    padding: 20px;
  }
}
</style>