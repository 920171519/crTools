<template>
  <div class="operation-logs">
    <div class="page-header">
      <h1>操作日志</h1>
      <p>查看系统各类操作日志记录</p>
    </div>

    <!-- 用户登录退出日志 -->
    <el-card shadow="never" class="log-section">
      <template #header>
        <div class="section-header">
          <div class="header-title">
            <el-icon><User /></el-icon>
            <span>用户登录退出日志</span>
          </div>
          <el-button @click="loadLoginLogs" :loading="loginLoading" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 登录日志搜索栏 -->
      <div class="search-bar">
        <el-form :model="loginSearchForm" inline>
          <el-form-item label="工号">
            <el-input v-model="loginSearchForm.employee_id" placeholder="请输入工号" clearable size="small" style="width: 200px" />
          </el-form-item>
          <el-form-item label="操作">
            <el-select
              v-model="loginSearchForm.operation_type"
              placeholder="请选择操作"
              clearable
              size="small"
              style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="登录" value="login" />
              <el-option label="退出" value="logout" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="handleLoginSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button size="small" @click="handleLoginReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="loginLogs" :loading="loginLoading" stripe style="width: 100%">
        <el-table-column prop="employee_id" label="工号" width="120" align="center">
          <template #default="{ row }">
            {{ row.employee_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120" align="center">
          <template #default="{ row }">
            {{ row.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="operation_type" label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.operation_type === 'logout' ? 'warning' : 'success'"
              size="small"
            >
              {{ getLoginOperationText(row.operation_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP地址" width="150" align="center">
          <template #default="{ row }">
            {{ row.ip_address || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="loginPagination.page"
          v-model:page-size="loginPagination.page_size"
          :total="loginPagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleLoginSizeChange"
          @current-change="handleLoginPageChange"
        />
      </div>
    </el-card>

    <!-- 设备操作日志 -->
    <el-card shadow="never" class="log-section">
      <template #header>
        <div class="section-header">
          <div class="header-title">
            <el-icon><Monitor /></el-icon>
            <span>设备操作日志</span>
          </div>
          <el-button @click="loadDeviceLogs" :loading="deviceLoading" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 设备日志搜索栏 -->
      <div class="search-bar">
        <el-form :model="deviceSearchForm" inline>
          <el-form-item label="工号">
            <el-input v-model="deviceSearchForm.employee_id" placeholder="请输入工号" clearable size="small" style="width: 200px" />
          </el-form-item>
          <el-form-item label="操作">
            <el-select
              v-model="deviceSearchForm.operation_type"
              placeholder="请选择操作"
              clearable
              size="small"
              style="width: 160px"
            >
              <el-option label="全部" value="" />
              <el-option label="使用" value="device_use" />
              <el-option label="释放" value="device_release" />
              <el-option label="普通排队" value="device_queue" />
              <el-option label="取消排队" value="device_cancel_queue" />
              <el-option label="抢占" value="device_preempt" />
              <el-option label="优先排队" value="device_priority_queue" />
              <el-option label="统一排队" value="device_unified_queue" />
              <el-option label="批量释放" value="device_batch_release" />
              <el-option label="批量取消排队" value="device_batch_cancel_queue" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="handleDeviceSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button size="small" @click="handleDeviceReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="deviceLogs" :loading="deviceLoading" stripe style="width: 100%">
        <el-table-column label="操作人" width="100" align="center">
          <template #default="{ row }">
            {{ row.employee_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="用户名" width="120" align="center">
          <template #default="{ row }">
            {{ row.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="设备名称" width="150" align="center">
          <template #default="{ row }">
            {{ row.device_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="设备IP" width="150" align="center">
          <template #default="{ row }">
            {{ row.ip_address || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getDeviceOperationTagType(row.operation_type)"
              size="small"
            >
              {{ getDeviceOperationText(row.operation_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.operation_result === 'success' ? 'success' : 'danger'"
              size="small"
            >
              {{ row.operation_result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="devicePagination.page"
          v-model:page-size="devicePagination.page_size"
          :total="devicePagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleDeviceSizeChange"
          @current-change="handleDevicePageChange"
        />
      </div>
    </el-card>

    <!-- 命令行修改记录日志 -->
    <el-card shadow="never" class="log-section">
      <template #header>
        <div class="section-header">
          <div class="header-title">
            <el-icon><DocumentChecked /></el-icon>
            <span>命令行修改记录日志</span>
          </div>
          <el-button @click="loadCommandLogs" :loading="commandLoading" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 命令行日志搜索栏 -->
      <div class="search-bar">
        <el-form :model="commandSearchForm" inline>
          <el-form-item label="工号">
            <el-input v-model="commandSearchForm.employee_id" placeholder="请输入工号" clearable size="small" style="width: 200px" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="handleCommandSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button size="small" @click="handleCommandReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="commandLogs" :loading="commandLoading" stripe style="width: 100%">
        <el-table-column prop="employee_id" label="操作人" width="100" align="center" />
        <el-table-column prop="username" label="用户名" width="100" align="center" />
        <el-table-column prop="command_id" label="命令ID" width="100" align="center" />
        <el-table-column prop="description" label="操作描述" min-width="300" align="left" />
        <el-table-column prop="operation_result" label="结果" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.operation_result === 'success' ? 'success' : 'danger'"
              size="small"
            >
              {{ row.operation_result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="commandPagination.page"
          v-model:page-size="commandPagination.page_size"
          :total="commandPagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleCommandSizeChange"
          @current-change="handleCommandPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, User, Monitor, Search, DocumentChecked } from '@element-plus/icons-vue'
import { operationLogApi } from '@/api/operationLog'
import { commandApi } from '@/api/command'

// 响应式数据
const loginLoading = ref(false)
const deviceLoading = ref(false)
const commandLoading = ref(false)

// 登录日志搜索表单
const loginSearchForm = ref({
  employee_id: '',
  operation_type: ''
})

// 设备日志搜索表单
const deviceSearchForm = ref({
  employee_id: '',
  operation_type: ''
})

// 命令行日志搜索表单
const commandSearchForm = ref({
  employee_id: ''
})

// 登录日志数据
const loginLogs = ref([])
const loginPagination = ref({
  page: 1,
  page_size: 10,
  total: 0
})

// 设备日志数据
const deviceLogs = ref([])
const devicePagination = ref({
  page: 1,
  page_size: 10,
  total: 0
})

// 命令行日志数据
const commandLogs = ref([])
const commandPagination = ref({
  page: 1,
  page_size: 10,
  total: 0
})

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 获取设备操作标签类型
const getDeviceOperationTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'device_use': 'success',
    'device_release': 'info',
    'device_queue': 'warning',
    'device_cancel_queue': 'info',
    'device_preempt': 'danger',
    'device_priority_queue': 'warning',
    'device_unified_queue': 'primary',
    'device_batch_release': 'info',
    'device_batch_cancel_queue': 'info'
  }
  return typeMap[type] || 'info'
}

// 获取设备操作文本
const getDeviceOperationText = (type: string) => {
  const textMap: Record<string, string> = {
    'device_use': '使用',
    'device_release': '释放',
    'device_queue': '普通排队',
    'device_cancel_queue': '取消排队',
    'device_preempt': '抢占',
    'device_priority_queue': '优先排队',
    'device_unified_queue': '统一排队',
    'device_batch_release': '批量释放',
    'device_batch_cancel_queue': '批量取消排队'
  }
  return textMap[type] || type
}

const getLoginOperationText = (type: string) => {
  if (type === 'logout') {
    return '退出'
  }
  if (type === 'login') {
    return '登录'
  }
  return type || '-'
}

// 加载登录日志
const loadLoginLogs = async () => {
  try {
    loginLoading.value = true
    const params: any = {
      page: loginPagination.value.page,
      page_size: loginPagination.value.page_size,
      employee_id: loginSearchForm.value.employee_id || undefined,
      operation_type: loginSearchForm.value.operation_type ? loginSearchForm.value.operation_type : 'login,logout'
    }

    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })

    const response = await operationLogApi.getOperationLogs(params)
    loginLogs.value = response.data.items || []
    loginPagination.value.total = response.data.total || 0
  } catch (error) {
    console.error('加载登录日志失败:', error)
    ElMessage.error('加载登录日志失败')
    loginLogs.value = []
    loginPagination.value.total = 0
  } finally {
    loginLoading.value = false
  }
}

// 加载设备日志
const loadDeviceLogs = async () => {
  try {
    deviceLoading.value = true
    const params: any = {
      page: devicePagination.value.page,
      page_size: devicePagination.value.page_size,
      employee_id: deviceSearchForm.value.employee_id || undefined,
      operation_type: deviceSearchForm.value.operation_type || undefined
    }

    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })

    const response = await operationLogApi.getOperationLogs(params)
    deviceLogs.value = response.data.items || []
    devicePagination.value.total = response.data.total || 0
  } catch (error) {
    console.error('加载设备日志失败:', error)
    ElMessage.error('加载设备日志失败')
    deviceLogs.value = []
    devicePagination.value.total = 0
  } finally {
    deviceLoading.value = false
  }
}

// 加载命令行日志
const loadCommandLogs = async () => {
  try {
    commandLoading.value = true
    const params: any = {
      page: commandPagination.value.page,
      page_size: commandPagination.value.page_size,
      employee_id: commandSearchForm.value.employee_id || undefined
    }

    // 移除空值参数
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })

    const response = await commandApi.getCommandOperationLogs(params)
    const result = response?.data || {}
    commandLogs.value = result.items || []
    commandPagination.value.total = result.total || 0
  } catch (error) {
    console.error('加载命令行日志失败:', error)
    ElMessage.error('加载命令行日志失败')
    commandLogs.value = []
    commandPagination.value.total = 0
  } finally {
    commandLoading.value = false
  }
}

// 登录日志搜索处理
const handleLoginSearch = () => {
  loginPagination.value.page = 1
  loadLoginLogs()
}

// 登录日志重置搜索
const handleLoginReset = () => {
  loginSearchForm.value = {
    employee_id: '',
    operation_type: ''
  }
  handleLoginSearch()
}

// 设备日志搜索处理
const handleDeviceSearch = () => {
  devicePagination.value.page = 1
  loadDeviceLogs()
}

// 设备日志重置搜索
const handleDeviceReset = () => {
  deviceSearchForm.value = {
    employee_id: '',
    operation_type: ''
  }
  handleDeviceSearch()
}

// 命令行日志搜索处理
const handleCommandSearch = () => {
  commandPagination.value.page = 1
  loadCommandLogs()
}

// 命令行日志重置搜索
const handleCommandReset = () => {
  commandSearchForm.value = {
    employee_id: ''
  }
  handleCommandSearch()
}

// 登录日志分页处理
const handleLoginSizeChange = (size: number) => {
  loginPagination.value.page_size = size
  loginPagination.value.page = 1
  loadLoginLogs()
}

const handleLoginPageChange = (page: number) => {
  loginPagination.value.page = page
  loadLoginLogs()
}

// 设备日志分页处理
const handleDeviceSizeChange = (size: number) => {
  devicePagination.value.page_size = size
  devicePagination.value.page = 1
  loadDeviceLogs()
}

const handleDevicePageChange = (page: number) => {
  devicePagination.value.page = page
  loadDeviceLogs()
}

// 命令行日志分页处理
const handleCommandSizeChange = (size: number) => {
  commandPagination.value.page_size = size
  commandPagination.value.page = 1
  loadCommandLogs()
}

const handleCommandPageChange = (page: number) => {
  commandPagination.value.page = page
  loadCommandLogs()
}

// 初始化
onMounted(() => {
  loadLoginLogs()
  loadDeviceLogs()
  loadCommandLogs()
})
</script>

<style scoped>
.operation-logs {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.log-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 16px;
}

.search-bar {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .operation-logs {
    padding: 10px;
  }
}
</style>
