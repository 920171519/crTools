<template>
  <div class="operation-logs">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>操作日志</span>
          <el-button @click="refreshLogs" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :model="searchForm" inline>
          <el-form-item label="工号">
            <el-input v-model="searchForm.employee_id" placeholder="请输入工号" clearable />
          </el-form-item>
          <el-form-item label="操作类型">
            <el-select v-model="searchForm.operation_type" placeholder="请选择类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="登录" value="login" />
              <el-option label="退出" value="logout" />
              <el-option label="设备操作" value="device" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 双栏布局 -->
      <div class="logs-container">
        <!-- 左侧：用户登录退出日志 -->
        <div class="left-panel">
          <el-card shadow="never" class="log-panel">
            <template #header>
              <div class="panel-header">
                <el-icon><User /></el-icon>
                <span>用户登录退出日志</span>
              </div>
            </template>

            <div class="table-container">
              <el-table
                :data="loginLogs"
                :loading="loginLoading"
                height="500"
                stripe
                :table-layout="'fixed'"
                style="width: 100%"
              >
                <el-table-column prop="employee_id" label="工号" width="120" align="center" />
                <el-table-column prop="username" label="用户名" width="120" align="center" />
                <el-table-column prop="operation_type" label="操作" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag
                      :type="row.operation_type === 'login' ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ row.operation_type === 'login' ? '登录' : '退出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="ip_address" label="IP地址" width="130" align="center" />
                <el-table-column prop="user_agent" label="浏览器" min-width="150" show-overflow-tooltip />
                <el-table-column prop="created_at" label="时间" width="160" align="center">
                  <template #default="{ row }">
                    {{ formatTime(row.created_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>

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
        </div>

        <!-- 右侧：设备操作日志 -->
        <div class="right-panel">
          <el-card shadow="never" class="log-panel">
            <template #header>
              <div class="panel-header">
                <el-icon><Monitor /></el-icon>
                <span>设备操作日志</span>
              </div>
            </template>

            <div class="table-container">
              <el-table
                :data="deviceLogs"
                :loading="deviceLoading"
                height="500"
                stripe
                :table-layout="'fixed'"
                style="width: 100%"
              >
                <el-table-column prop="employee_id" label="操作人" width="120" align="center" />
                <el-table-column prop="device_name" label="设备名称" width="140" align="center" />
                <el-table-column prop="operation_type" label="操作" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag
                      :type="getDeviceOperationTagType(row.operation_type)"
                      size="small"
                    >
                      {{ getDeviceOperationText(row.operation_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
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
            </div>

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
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, User, Monitor } from '@element-plus/icons-vue'
import { operationLogApi } from '@/api/operationLog'

// 响应式数据
const loading = ref(false)
const loginLoading = ref(false)
const deviceLoading = ref(false)

const searchForm = ref({
  employee_id: '',
  operation_type: ''
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

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}

// 获取设备操作标签类型
const getDeviceOperationTagType = (type) => {
  const typeMap = {
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
const getDeviceOperationText = (type) => {
  const textMap = {
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

// 加载登录日志
const loadLoginLogs = async () => {
  try {
    loginLoading.value = true
    const params = {
      page: loginPagination.value.page,
      page_size: loginPagination.value.page_size,
      employee_id: searchForm.value.employee_id,
      operation_type: 'login,logout'
    }

    const response = await operationLogApi.getOperationLogs(params)
    loginLogs.value = response.data.items
    loginPagination.value.total = response.data.total
  } catch (error) {
    console.error('加载登录日志失败:', error)
    ElMessage.error('加载登录日志失败')
  } finally {
    loginLoading.value = false
  }
}

// 加载设备日志
const loadDeviceLogs = async () => {
  try {
    deviceLoading.value = true
    const params = {
      page: devicePagination.value.page,
      page_size: devicePagination.value.page_size,
      employee_id: searchForm.value.employee_id,
      // 不传operation_type，让后端默认返回设备操作日志
    }

    const response = await operationLogApi.getOperationLogs(params)
    deviceLogs.value = response.data.items
    devicePagination.value.total = response.data.total
  } catch (error) {
    console.error('加载设备日志失败:', error)
    ElMessage.error('加载设备日志失败')
  } finally {
    deviceLoading.value = false
  }
}

// 刷新所有日志
const refreshLogs = async () => {
  loading.value = true
  await Promise.all([loadLoginLogs(), loadDeviceLogs()])
  loading.value = false
}

// 搜索处理
const handleSearch = () => {
  loginPagination.value.page = 1
  devicePagination.value.page = 1
  refreshLogs()
}

// 重置搜索
const handleReset = () => {
  searchForm.value = {
    employee_id: '',
    operation_type: ''
  }
  handleSearch()
}

// 登录日志分页处理
const handleLoginSizeChange = (size) => {
  loginPagination.value.page_size = size
  loginPagination.value.page = 1
  loadLoginLogs()
}

const handleLoginPageChange = (page) => {
  loginPagination.value.page = page
  loadLoginLogs()
}

// 设备日志分页处理
const handleDeviceSizeChange = (size) => {
  devicePagination.value.page_size = size
  devicePagination.value.page = 1
  loadDeviceLogs()
}

const handleDevicePageChange = (page) => {
  devicePagination.value.page = page
  loadDeviceLogs()
}

// 初始化
onMounted(() => {
  refreshLogs()
})
</script>

<style scoped>
.operation-logs {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.logs-container {
  display: flex;
  gap: 20px;
  height: 600px;
  overflow: hidden;
}

.left-panel,
.right-panel {
  flex: 1;
  min-width: 0;
  max-width: 50%;
  overflow: hidden;
}

.log-panel {
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 表格容器样式 - 重新设计 */
.table-container {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: white;
}

/* 表格基础样式 */
.table-container :deep(.el-table) {
  width: 100% !important;
  min-width: 700px;
  border: none;
}

/* 表格头部和主体样式 */
.table-container :deep(.el-table__header-wrapper) {
  overflow: visible;
}

.table-container :deep(.el-table__body-wrapper) {
  overflow: visible;
}

/* 单元格样式 */
.table-container :deep(.el-table__cell) {
  padding: 12px 8px;
  text-align: center;
  vertical-align: middle;
  border-right: 1px solid #ebeef5;
}

.table-container :deep(.el-table__cell:last-child) {
  border-right: none;
}

/* 表格行样式 */
.table-container :deep(.el-table__row) {
  height: 50px;
}

/* 自定义滚动条样式 */
.table-container::-webkit-scrollbar {
  height: 12px;
}

.table-container::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 6px;
}

.table-container::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 6px;
  border: 2px solid #f5f5f5;
}

.table-container::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 强制显示滚动条 */
.table-container {
  scrollbar-width: thin;
  scrollbar-color: #c0c4cc #f5f5f5;
}
</style>
