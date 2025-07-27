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
            
            <el-table 
              :data="loginLogs" 
              :loading="loginLoading"
              height="500"
              stripe
            >
              <el-table-column prop="employee_id" label="工号" width="120" />
              <el-table-column prop="username" label="用户名" width="120" />
              <el-table-column prop="operation_type" label="操作" width="80">
                <template #default="{ row }">
                  <el-tag 
                    :type="row.operation_type === 'login' ? 'success' : 'warning'"
                    size="small"
                  >
                    {{ row.operation_type === 'login' ? '登录' : '退出' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="ip_address" label="IP地址" width="130" />
              <el-table-column prop="user_agent" label="浏览器" min-width="150" show-overflow-tooltip />
              <el-table-column prop="created_at" label="时间" width="160">
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
            
            <el-table 
              :data="deviceLogs" 
              :loading="deviceLoading"
              height="500"
              stripe
            >
              <el-table-column prop="employee_id" label="操作人" width="100" />
              <el-table-column prop="device_name" label="设备名称" width="120" />
              <el-table-column prop="operation_type" label="操作" width="100">
                <template #default="{ row }">
                  <el-tag 
                    :type="getDeviceOperationTagType(row.operation_type)"
                    size="small"
                  >
                    {{ getDeviceOperationText(row.operation_type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="operation_result" label="结果" width="80">
                <template #default="{ row }">
                  <el-tag 
                    :type="row.operation_result === 'success' ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ row.operation_result === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
              <el-table-column prop="created_at" label="时间" width="160">
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
    'use': 'success',
    'release': 'info',
    'queue': 'warning',
    'cancel_queue': 'info',
    'preempt': 'danger',
    'priority_queue': 'warning',
    'force_release': 'danger'
  }
  return typeMap[type] || 'info'
}

// 获取设备操作文本
const getDeviceOperationText = (type) => {
  const textMap = {
    'use': '使用',
    'release': '释放',
    'queue': '排队',
    'cancel_queue': '取消排队',
    'preempt': '抢占',
    'priority_queue': '优先排队',
    'force_release': '强制释放'
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
      operation_type: 'login,logout',
      ...searchForm.value
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
      operation_type: 'device',
      ...searchForm.value
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
}

.left-panel,
.right-panel {
  flex: 1;
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
</style>
