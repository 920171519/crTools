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

    <el-alert v-if="pendingShareRequests.length" type="warning" show-icon :closable="false" class="share-alert"
      :title="`有 ${pendingShareRequests.length} 个共用申请待处理`" />

    <el-card class="share-requests-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon>
            <User />
          </el-icon>
          <span>设备共用申请</span>
          <el-button text size="small" @click="loadPendingShareRequests">
            <el-icon>
              <Refresh />
            </el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <el-table :data="pendingShareRequests" size="small" style="width:100%">
        <el-table-column label="申请人" min-width="200">
          <template #default="{ row }">
            {{ row.requester_username }} ({{ row.requester_employee_id }})
          </template>
        </el-table-column>
        <el-table-column label="申请时间" width="200">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="申请备注" min-width="240">
          <template #default="{ row }">
            <span>{{ row.request_message || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button type="primary" plain size="small" @click="handleShareDecision(row, true)"
              :loading="shareDecisionLoading[row.id]">允许</el-button>
            <el-button type="danger" plain size="small" @click="handleShareDecision(row, false)"
              :loading="shareDecisionLoading[row.id]">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 快捷操作模块 - 紧跟在标题下方 -->
    <el-card class="modules-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon>
            <Lightning />
          </el-icon>
          <span>系统模块</span>
        </div>
      </template>
      <div class="modules-grid">
        <div class="module-item" @click="goToPage('/system/users')" v-if="userStore.hasPermission('user:read')">
          <div class="module-icon user-module">
            <el-icon size="32">
              <User />
            </el-icon>
          </div>
          <div class="module-info">
            <h3>用户管理</h3>
            <p>管理系统用户信息</p>
          </div>
        </div>



        <div class="module-item" @click="goToPage('/system/logs')" v-if="userStore.hasPermission('system:log')">
          <div class="module-icon log-module">
            <el-icon size="32">
              <Document />
            </el-icon>
          </div>
          <div class="module-info">
            <h3>操作日志</h3>
            <p>查看用户登录和设备操作记录</p>
          </div>
        </div>

        <div class="module-item" @click="goToPage('/profile')">
          <div class="module-icon profile-module">
            <el-icon size="32">
              <Setting />
            </el-icon>
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
              <el-icon>
                <Clock />
              </el-icon>
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
                <el-tag size="small" type="primary">
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
              <el-icon>
                <Monitor />
              </el-icon>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { deviceApi } from '@/api/device'
import { ElMessage } from 'element-plus'
import {
  User, Document, Setting,
  Lightning, Clock, Monitor, Refresh
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 设备统计数据
const deviceStats = ref({
  occupiedCount: 0,
  queueCount: 0,
  totalCount: 0
})

const pendingShareRequests = ref([])
const shareDecisionLoading = reactive<Record<number, boolean>>({})

// 与设备管理页保持一致的状态文案/标签
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    available: '可用',
    occupied: '占用中',
    long_term_occupied: '长时间占用',
    maintenance: '维护中',
    offline: '不可占用',
    queue: '排队中'
  }
  return statusMap[status] || status
}

const getStatusTag = (status: string) => {
  const tagMap: Record<string, string> = {
    available: 'success',
    occupied: 'warning',
    long_term_occupied: 'danger',
    maintenance: 'info',
    offline: 'danger'
  }
  return tagMap[status] || 'info'
}

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

// 时长格式化（分钟->可读）
const formatDuration = (minutes?: number) => {
  if (!minutes || minutes <= 0) return '-'
  if (minutes < 60) return `${minutes} 分钟`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m ? `${h} 小时 ${m} 分` : `${h} 小时`
}

const loadPendingShareRequests = async () => {
  try {
    const response = await deviceApi.getPendingShareRequests()
    pendingShareRequests.value = response.data || []
  } catch (error) {
    console.error('加载共用申请失败:', error)
    pendingShareRequests.value = []
  }
}


const handleShareDecision = async (request: any, approve: boolean) => {
  if (shareDecisionLoading[request.id]) return
  try {
    shareDecisionLoading[request.id] = true
    await deviceApi.decideShareRequest(request.id, { approve })
    ElMessage.success(approve ? '已允许共用' : '已拒绝共用')
    await loadPendingShareRequests()
  } catch (error: any) {
    console.error('处理共用申请失败:', error)
    const message = error?.response?.data?.detail || '处理共用申请失败'
    ElMessage.error(message)
  } finally {
    shareDecisionLoading[request.id] = false
  }
}

// 释放（首页）
const releaseFromDashboard = async (row: any) => {
  if (!row) return
  try {
    row.__releasing = true
    await deviceApi.releaseDevice({ device_id: row.id, user: (userStore.userInfo?.employee_id || '').toLowerCase() })
    ElMessage.success('设备已释放')
    await loadMyUsageSummary()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '释放失败')
  } finally {
    row.__releasing = false
  }
}

// 取消共用（首页）
const cancelShareFromDashboard = async (row: any) => {
  if (!row?.share_request_id) return
  try {
    row.__canceling = true
    await deviceApi.cancelShareRequest(row.share_request_id)
    ElMessage.success('已取消共用')
    await loadMyUsageSummary()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '取消失败')
  } finally {
    row.__canceling = false
  }
}

const goToDeviceDetails = (row: any) => {
  router.push('/devices')
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
  loadPendingShareRequests()
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

.my-usage-card {
  margin-bottom: 20px;
}

.usage-section {
  margin-bottom: 16px;
}

.usage-title {
  font-weight: 500;
  margin-bottom: 8px;
}

.usage-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-icon {
  color: #909399;
}

.name-text {
  font-weight: 500;
}

.ip-tag {
  margin-left: 4px;
}

.device-status {
  min-width: 100px;
  text-align: right;
}

.device-user {
  color: #606266;
  display: flex;
  align-items: center;
  gap: 4px;
}

.share-message {
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
}

.share-text {
  color: #606266;
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

.recent-login-card,
.system-info-card {
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

.share-alert {
  margin-top: 20px;
}

.share-requests-card {
  margin-top: 20px;
}

.share-request-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-request-item {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  padding: 12px 0;
  border-bottom: 1px solid #f2f2f2;
}

.share-request-item:last-child {
  border-bottom: none;
}

.share-request-info .device-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.request-meta {
  color: #909399;
  font-size: 13px;
}

.request-message {
  margin-top: 6px;
  color: #606266;
}

.share-request-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 160px;
  align-items: flex-end;
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
