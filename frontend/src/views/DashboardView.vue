<template>
  <div class="dashboard">
    <!-- 欢迎区域 -->
    <el-card class="welcome-card" shadow="never">
      <div class="welcome-content">
        <div class="welcome-text">
          <h2>欢迎使用CR工具集网站，{{ userStore.userInfo?.username }}！</h2>
          <p>{{ currentTime }}</p>
        </div>

      </div>
    </el-card>

    <!-- crTools管理系统标题 -->
    <div class="system-title">
      <h1>crTools 管理系统</h1>
      <p>基于工号认证的环境管理平台</p>
    </div>

    <!-- 快捷操作模块 - 紧跟在标题下方 -->
    <el-card class="modules-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon><Lightning /></el-icon>
          <span>系统模块</span>
        </div>
      </template>
      <div class="modules-grid">
        <div class="module-item" @click="goToPage('/system/users')" v-if="userStore.hasPermission('user:read')">
          <div class="module-icon user-module">
            <el-icon size="32"><User /></el-icon>
          </div>
          <div class="module-info">
            <h3>用户管理</h3>
            <p>管理系统用户信息</p>
          </div>
        </div>
        

        
        <div class="module-item" @click="goToPage('/system/logs')" v-if="userStore.hasPermission('system:log')">
          <div class="module-icon log-module">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="module-info">
            <h3>操作日志</h3>
            <p>查看用户登录和设备操作记录</p>
          </div>
        </div>
        
        <div class="module-item" @click="goToPage('/profile')">
          <div class="module-icon profile-module">
            <el-icon size="32"><Setting /></el-icon>
          </div>
          <div class="module-info">
            <h3>个人中心</h3>
            <p>管理个人账户信息</p>
          </div>
        </div>
      </div>
    </el-card>



    <!-- 信息区域 -->
    <el-row :gutter="20" class="content-row">
      <!-- 设备相关信息 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="recent-login-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>设备相关信息</span>
            </div>
          </template>
          <div class="login-info">
            <div class="info-item">
              <span class="info-label">当前登录：</span>
              <span class="info-value">{{ userStore.userInfo?.employee_id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">用户角色：</span>
              <span class="info-value">
                <el-tag
                  size="small"
                  type="primary"
                >
                  {{ userStore.userInfo?.role || '未知' }}
                </el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">占用设备：</span>
              <span class="info-value">
                <el-tag size="small" type="warning">{{ deviceStats.occupiedCount }}台</el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">排队设备：</span>
              <span class="info-value">
                <el-tag size="small" type="info">{{ deviceStats.queueCount }}台</el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="info-label">总设备数：</span>
              <span class="info-value">
                <el-tag size="small" type="success">{{ deviceStats.totalCount }}台</el-tag>
              </span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 系统信息 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="system-info-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>系统信息</span>
            </div>
          </template>
          <div class="system-info">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统名称">crTools管理系统</el-descriptions-item>
              <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
              <el-descriptions-item label="前端技术">Vue3 + TypeScript + Element Plus</el-descriptions-item>
              <el-descriptions-item label="后端技术">FastAPI + SQLite + Tortoise-ORM</el-descriptions-item>
              <el-descriptions-item label="认证方式">工号 + JWT令牌</el-descriptions-item>
              <el-descriptions-item label="权限控制">基于角色的访问控制(RBAC)</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { deviceApi } from '@/api/device'
import {
  User, Document, Setting,
  Lightning, Clock, Monitor
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 设备统计数据
const deviceStats = ref({
  occupiedCount: 0,
  queueCount: 0,
  totalCount: 0
})

// 当前时间
const currentTime = computed(() => {
  const now = new Date()
  const hour = now.getHours()
  let greeting = ''
  
  if (hour < 6) {
    greeting = '凌晨好'
  } else if (hour < 9) {
    greeting = '早上好'
  } else if (hour < 12) {
    greeting = '上午好'
  } else if (hour < 14) {
    greeting = '中午好'
  } else if (hour < 17) {
    greeting = '下午好'
  } else if (hour < 19) {
    greeting = '傍晚好'
  } else {
    greeting = '晚上好'
  }
  
  return greeting
})

// 跳转页面
const goToPage = (path: string) => {
  router.push(path)
}

// 格式化时间
const formatTime = (timeStr?: string) => {
  if (!timeStr) return '暂无'
  
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载设备统计数据
const loadDeviceStats = async () => {
  try {
    const response = await deviceApi.getDevices()
    const devices = response.data.items || []

    let occupiedCount = 0
    let queueCount = 0
    let totalCount = devices.length

    // 确保devices是数组
    if (Array.isArray(devices)) {
      devices.forEach(device => {
      // 统计当前用户占用的设备
      if (device.current_user === userStore.userInfo?.employee_id) {
        occupiedCount++
      }
      // 统计当前用户排队的设备
      if (device.is_current_user_in_queue) {
        queueCount++
      }
    })
    }

    deviceStats.value = {
      occupiedCount,
      queueCount,
      totalCount
    }
  } catch (error) {
    console.error('加载设备统计失败:', error)
    deviceStats.value = {
      occupiedCount: 0,
      queueCount: 0,
      totalCount: 0
    }
  }
}

// 初始化
onMounted(() => {
  loadDeviceStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.welcome-card {
  margin-bottom: 20px;
  border: none;
}

.welcome-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.welcome-text h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.welcome-text p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

/* 系统标题样式 */
.system-title {
  text-align: center;
  margin: 40px 0 30px 0;
  padding: 30px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.system-title h1 {
  font-size: 48px;
  font-weight: 600;
  margin: 0 0 12px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.system-title p {
  font-size: 18px;
  margin: 0;
  opacity: 0.9;
}

/* 模块卡片样式 */
.modules-card {
  margin-bottom: 30px;
  border: none;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  padding: 10px 0;
}

.module-item {
  display: flex;
  align-items: center;
  padding: 20px;
  border: 2px solid #f0f2f5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafbfc;
}

.module-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(64, 158, 255, 0.15);
}

.module-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  color: white;
}

.user-module {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.role-module {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.permission-module {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.menu-module {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.log-module {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.profile-module {
  background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
}

.module-info h3 {
  margin: 0 0 6px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.module-info p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}



.content-row {
  margin-bottom: 20px;
}

.recent-login-card, .system-info-card {
  border: none;
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.card-header .el-icon {
  margin-right: 8px;
  color: #409eff;
}

.login-info {
  padding: 8px 0;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.info-label {
  width: 80px;
  color: #909399;
  font-size: 14px;
}

.info-value {
  flex: 1;
  color: #303133;
  font-size: 14px;
}

.system-info {
  padding: 8px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .welcome-content {
    flex-direction: column;
    text-align: center;
  }

  .welcome-text {
    margin-bottom: 16px;
  }

  .welcome-text h2 {
    font-size: 20px;
  }

  .system-title h1 {
    font-size: 32px;
  }

  .system-title p {
    font-size: 16px;
  }

  .modules-grid {
    grid-template-columns: 1fr;
  }

  .module-item {
    padding: 16px;
  }

  .module-icon {
    width: 50px;
    height: 50px;
  }

  .module-info h3 {
    font-size: 16px;
  }
}
</style> 