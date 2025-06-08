<template>
  <div class="login-logs">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>登录日志</span>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :model="searchForm" inline>
          <el-form-item label="工号">
            <el-input v-model="searchForm.employee_id" placeholder="请输入工号" clearable />
          </el-form-item>
          <el-form-item label="登录结果">
            <el-select v-model="searchForm.login_result" placeholder="请选择结果" clearable>
              <el-option label="全部" value="" />
              <el-option label="成功" :value="true" />
              <el-option label="失败" :value="false" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 日志表格 -->
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="employee_id" label="工号" width="120" />
        <el-table-column prop="username" label="姓名" width="120" />
        <el-table-column prop="ip_address" label="IP地址" width="140" />
        <el-table-column label="登录结果" width="100">
          <template #default="{ row }">
            <el-tag :type="row.login_result ? 'success' : 'danger'" size="small">
              {{ row.login_result ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="failure_reason" label="失败原因" />
        <el-table-column prop="login_time" label="登录时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.login_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="user_agent" label="用户代理" show-overflow-tooltip />
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const loading = ref(false)
const tableData = ref([])

const searchForm = reactive({
  employee_id: '',
  login_result: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const fetchLogs = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    const logs = [
      {
        id: 1,
        employee_id: 'A12345678',
        username: '超级管理员',
        ip_address: '192.168.1.100',
        login_result: true,
        failure_reason: null,
        login_time: '2024-01-01T10:00:00',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
      },
      {
        id: 2,
        employee_id: 'B12345679',
        username: '张三',
        ip_address: '192.168.1.101',
        login_result: false,
        failure_reason: '密码错误',
        login_time: '2024-01-01T09:30:00',
        user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
      }
    ]
    tableData.value = logs
    pagination.total = logs.length
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchLogs()
}

const handleReset = () => {
  Object.assign(searchForm, { employee_id: '', login_result: '' })
  handleSearch()
}

const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  fetchLogs()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  fetchLogs()
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 4px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 