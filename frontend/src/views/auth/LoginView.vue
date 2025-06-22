<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>crTools后台管理系统</h1>
        <p>基于工号的后台管理系统</p>
      </div>
      
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules"
        class="login-form"
        size="large"
      >
        <el-form-item prop="employee_id">
          <el-input 
            v-model="loginForm.employee_id"
            placeholder="请输入工号(如: A12345678)"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
        
        <div class="login-links">
          <router-link to="/register" class="register-link">
            还没有账号？立即注册
          </router-link>
        </div>
      </el-form>
      
      <div class="login-footer">
        <p>默认管理员账号: a12345678 / admin123</p>
      </div>
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
const loginFormRef = ref<FormInstance>()

// 表单数据
const loginForm = reactive({
  employee_id: '',
  password: ''
})

// 表单验证规则
const loginRules: FormRules = {
  employee_id: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { 
      pattern: /^[A-Za-z]\d{8}$/, 
      message: '工号格式错误，应为一个字母加8个数字', 
      trigger: 'blur' 
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 3, message: '密码长度至少3位', trigger: 'blur' }
  ]
}

// 登录状态
const loading = ref(false)

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    // 验证表单
    await loginFormRef.value.validate()
    
    loading.value = true
    
    // 调用登录接口
    await userStore.loginAction({
      employee_id: loginForm.employee_id,
      password: loginForm.password
    })
    
    ElMessage.success('登录成功')
    
    // 跳转到首页
    router.push('/dashboard')
  } catch (error: any) {
    console.error('登录失败:', error)
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #303133;
  font-size: 24px;
  margin-bottom: 8px;
  font-weight: 600;
}

.login-header p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 20px;
}

.login-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 500;
}

.login-links {
  text-align: center;
}

.register-link {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s;
}

.register-link:hover {
  color: #66b1ff;
}

.login-footer {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.login-footer p {
  color: #909399;
  font-size: 12px;
  margin: 0;
}
</style> 