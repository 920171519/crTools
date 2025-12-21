<template>
  <div class="ai-tool">
    <div class="page-header">
      <h1>AI 工具</h1>
      <p>借助 AI 工具快速定位 Linux 设备错误</p>
    </div>

    <!-- 主要区域：诊断和历史记录切换 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 诊断工具 Tab -->
      <el-tab-pane label="AI 诊断" name="diagnosis">
        <div class="diagnosis-container">
          <!-- 上半部分：输入区域 -->
          <el-card shadow="never" class="input-section">
            <template #header>
              <div class="card-header">
                <span class="card-title">诊断信息</span>
              </div>
            </template>

            <el-form :model="diagnosisForm" :rules="formRules" ref="formRef" label-width="100px">
              <!-- 设备选择 -->
              <el-form-item label="选择设备" prop="device_id">
                <el-select v-model="diagnosisForm.device_id" placeholder="请选择要诊断的设备" filterable style="width: 100%"
                  @change="handleDeviceChange">
                  <el-option v-for="device in devices" :key="device.id" :label="`${device.name} (${device.ip})`"
                    :value="device.id">
                    <div class="device-option">
                      <span class="device-name">{{ device.name }}</span>
                      <span class="device-ip">{{ device.ip }}</span>
                      <el-tag :type="device.connectivity_status ? 'success' : 'danger'" size="small">
                        {{ device.connectivity_status ? '在线' : '离线' }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <!-- 设备信息展示 -->
              <el-form-item label="设备信息" v-if="selectedDevice">
                <div class="device-info">
                  <div class="info-item">
                    <span class="label">IP地址:</span>
                    <span class="value">{{ selectedDevice.ip }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">账号:</span>
                    <span class="value">{{ selectedDevice.admin_username || selectedDevice.username || '-' }}</span>
                  </div>
                  <div class="info-item">
                    <span class="label">连通状态:</span>
                    <el-tag :type="selectedDevice.connectivity_status ? 'success' : 'danger'" size="small">
                      {{ selectedDevice.connectivity_status ? '连通' : '不连通' }}
                    </el-tag>
                  </div>
                </div>
              </el-form-item>

              <!-- 问题描述 -->
              <el-form-item label="问题描述" prop="problem_description">
                <el-input v-model="diagnosisForm.problem_description" type="textarea" :rows="6"
                  placeholder="请详细描述遇到的问题，例如：&#10;- 系统运行缓慢&#10;- 磁盘空间不足&#10;- 网络连接异常&#10;- 服务启动失败等" maxlength="5000"
                  show-word-limit />
              </el-form-item>

              <!-- 操作按钮 -->
              <el-form-item>
                <el-button type="primary" @click="handleStartDiagnosis" :loading="diagnosing"
                  :disabled="!diagnosisForm.device_id">
                  <el-icon>
                    <DocumentChecked />
                  </el-icon>
                  {{ diagnosing ? '诊断中...' : '开始诊断' }}
                </el-button>
                <el-button @click="handleReset">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <!-- 下半部分：输出区域 -->
          <el-card shadow="never" class="output-section" v-if="showResult">
            <template #header>
              <div class="card-header">
                <span class="card-title">诊断结果</span>
                <div class="header-actions">
                  <el-button size="small" @click="handleCopyResult" :disabled="!diagnosisResult">
                    <el-icon>
                      <DocumentCopy />
                    </el-icon>
                    复制
                  </el-button>
                  <el-button size="small" @click="handleExportResult" :disabled="!currentDiagnosisId">
                    <el-icon>
                      <Download />
                    </el-icon>
                    导出
                  </el-button>
                </div>
              </div>
            </template>

            <div class="result-container" v-loading="diagnosing">
              <div v-if="diagnosisResult" class="markdown-body" v-html="renderedMarkdown"></div>
              <el-empty v-else description="暂无诊断结果" />
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 历史记录 Tab -->
      <el-tab-pane label="诊断历史" name="history">
        <el-card shadow="never">
          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-form :model="searchForm" inline>
              <el-form-item label="设备IP">
                <el-input v-model="searchForm.device_ip" placeholder="请输入设备IP" clearable style="width: 200px" />
              </el-form-item>
              <el-form-item label="状态">
                <el-select v-model="searchForm.status" placeholder="请选择状态" clearable style="width: 150px">
                  <el-option label="进行中" value="pending" />
                  <el-option label="成功" value="success" />
                  <el-option label="失败" value="failed" />
                  <el-option label="超时" value="timeout" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSearchHistory">
                  <el-icon>
                    <Search />
                  </el-icon>
                  搜索
                </el-button>
                <el-button @click="handleResetSearch">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 历史记录列表 -->
          <el-table :data="historyList" stripe style="width: 100%" v-loading="loadingHistory">
            <el-table-column prop="device_ip" label="设备IP" width="150" />
            <el-table-column prop="username" label="诊断人员" width="120" />
            <el-table-column prop="problem_description" label="问题描述" min-width="250">
              <template #default="{ row }">
                <div class="problem-text">{{ row.problem_description }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="connectivity_status" label="连通性" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.connectivity_status !== null" :type="row.connectivity_status ? 'success' : 'danger'"
                  size="small">
                  {{ row.connectivity_status ? '连通' : '不连通' }}
                </el-tag>
                <span v-else class="no-data">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="诊断时间" width="180">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="viewHistoryDetail(row)">
                  查看
                </el-button>
                <el-button type="danger" size="small" @click="deleteHistory(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
              :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next, jumper" :total="pagination.total"
              @size-change="handleSizeChange" @current-change="handleCurrentChange" />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 历史详情抽屉 -->
    <el-drawer v-model="showHistoryDrawer" title="诊断详情" direction="rtl" size="800px">
      <div v-loading="loadingDetail" class="history-detail">
        <template v-if="historyDetail">
          <div class="detail-section">
            <h3 class="section-title">基本信息</h3>
            <div class="info-grid">
              <div class="info-item">
                <label>诊断ID:</label>
                <span>{{ historyDetail.id }}</span>
              </div>
              <div class="info-item">
                <label>设备IP:</label>
                <span>{{ historyDetail.device_ip }}</span>
              </div>
              <div class="info-item">
                <label>诊断人员:</label>
                <span>{{ historyDetail.username }} ({{ historyDetail.employee_id }})</span>
              </div>
              <div class="info-item">
                <label>诊断状态:</label>
                <el-tag :type="getStatusType(historyDetail.status)" size="small">
                  {{ getStatusText(historyDetail.status) }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>连通状态:</label>
                <el-tag v-if="historyDetail.connectivity_status !== null"
                  :type="historyDetail.connectivity_status ? 'success' : 'danger'" size="small">
                  {{ historyDetail.connectivity_status ? '连通' : '不连通' }}
                </el-tag>
                <span v-else>-</span>
              </div>
              <div class="info-item">
                <label>诊断时间:</label>
                <span>{{ formatDateTime(historyDetail.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>完成时间:</label>
                <span>{{ historyDetail.completed_at ? formatDateTime(historyDetail.completed_at) : '-' }}</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h3 class="section-title">问题描述</h3>
            <div class="problem-description">{{ historyDetail.problem_description }}</div>
          </div>

          <div class="detail-section">
            <div class="section-header">
              <h3 class="section-title">诊断结果</h3>
              <div class="section-actions">
                <el-button size="small" @click="handleCopyHistoryResult">
                  <el-icon>
                    <DocumentCopy />
                  </el-icon>
                  复制
                </el-button>
                <el-button size="small" @click="handleExportHistoryResult">
                  <el-icon>
                    <Download />
                  </el-icon>
                  导出
                </el-button>
              </div>
            </div>
            <div v-if="historyDetail.diagnosis_result" class="markdown-body"
              v-html="renderMarkdown(historyDetail.diagnosis_result)"></div>
            <el-empty v-else description="暂无诊断结果" />
          </div>

          <div class="detail-section" v-if="historyDetail.error_message">
            <h3 class="section-title">错误信息</h3>
            <div class="error-message">{{ historyDetail.error_message }}</div>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Refresh, DocumentChecked, DocumentCopy, Download
} from '@element-plus/icons-vue'
import { aiToolApi, type AIDiagnosisListItem, type AIDiagnosisResponse } from '../api/aiTool'
import { deviceApi, type Device } from '../api/device'
import { useUserStore } from '@/stores/user'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 数据定义
const userStore = useUserStore()

const activeTab = ref('diagnosis')
const devices = ref<Device[]>([])
const diagnosing = ref(false)
const showResult = ref(false)
const diagnosisResult = ref('')
const currentDiagnosisId = ref<number | null>(null)
const selectedDevice = ref<Device | null>(null)
const formRef = ref()
let eventSource: EventSource | null = null

// 诊断表单
const diagnosisForm = reactive({
  device_id: null as number | null,
  problem_description: ''
})

// 表单验证规则
const formRules = {
  device_id: [
    { required: true, message: '请选择设备', trigger: 'change' }
  ],
  problem_description: [
    { required: true, message: '请输入问题描述', trigger: 'blur' },
    { min: 10, message: '问题描述至少需要10个字符', trigger: 'blur' }
  ]
}

// 历史记录相关
const historyList = ref<AIDiagnosisListItem[]>([])
const loadingHistory = ref(false)
const searchForm = reactive({
  device_ip: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 历史详情
const showHistoryDrawer = ref(false)
const loadingDetail = ref(false)
const historyDetail = ref<AIDiagnosisResponse | null>(null)

// Markdown 渲染
const renderedMarkdown = computed(() => {
  if (!diagnosisResult.value) return ''
  return renderMarkdown(diagnosisResult.value)
})

// 方法定义
const loadDevices = async () => {
  try {
    const response = await deviceApi.getDevices({
      page: 1,
      page_size: 1000 // 获取所有设备
    })
    devices.value = response.data.items
  } catch (error) {
    console.error('加载设备列表失败:', error)
    ElMessage.error('加载设备列表失败')
  }
}

const handleDeviceChange = () => {
  if (diagnosisForm.device_id) {
    selectedDevice.value = devices.value.find(d => d.id === diagnosisForm.device_id) || null
  } else {
    selectedDevice.value = null
  }
}

const handleStartDiagnosis = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    // 关闭之前的连接
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }

    diagnosing.value = true
    showResult.value = true
    diagnosisResult.value = ''
    currentDiagnosisId.value = null

    // 获取 token
    const token = userStore.token || localStorage.getItem('crtools_token')
    if (!token) {
      ElMessage.error('请先登录')
      return
    }

    // 构建 SSE URL
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const params = new URLSearchParams({
      device_id: diagnosisForm.device_id!.toString(),
      problem_description: diagnosisForm.problem_description
    })

    // 创建 EventSource，使用 POST 需要通过 URL 参数传递
    // 注意：标准 EventSource 不支持 POST，这里使用 GET 方式
    const url = `${baseUrl}/api/ai-tool/diagnose-stream?${params.toString()}&token=${token}`

    eventSource = new EventSource(url)

    eventSource.onopen = () => {
      console.log('SSE 连接已建立')
    }

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        switch (data.type) {
          case 'start':
            diagnosisResult.value = ''
            ElMessage.info(data.message)
            break

          case 'content':
            diagnosisResult.value += data.content
            break

          case 'done':
            ElMessage.success(data.message)
            currentDiagnosisId.value = data.log_id
            diagnosing.value = false
            if (eventSource) {
              eventSource.close()
              eventSource = null
            }
            break

          case 'error':
            ElMessage.error(data.message)
            diagnosing.value = false
            if (eventSource) {
              eventSource.close()
              eventSource = null
            }
            break
        }
      } catch (error) {
        console.error('解析 SSE 数据失败:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('SSE 连接错误:', error)
      ElMessage.error('诊断连接中断')
      diagnosing.value = false
      if (eventSource) {
        eventSource.close()
        eventSource = null
      }
    }

  } catch (error: any) {
    console.error('诊断失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('诊断失败')
    }
    showResult.value = false
    diagnosing.value = false
  }
}

const handleReset = () => {
  formRef.value?.resetFields()
  diagnosisForm.device_id = null
  diagnosisForm.problem_description = ''
  selectedDevice.value = null
  showResult.value = false
  diagnosisResult.value = ''
  currentDiagnosisId.value = null
}

const handleCopyResult = async () => {
  if (!diagnosisResult.value) return

  try {
    await navigator.clipboard.writeText(diagnosisResult.value)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const handleExportResult = async () => {
  if (!currentDiagnosisId.value) return

  try {
    const response = await aiToolApi.exportDiagnosis(currentDiagnosisId.value)

    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `diagnosis_${currentDiagnosisId.value}_${Date.now()}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 历史记录相关方法
const loadHistory = async () => {
  loadingHistory.value = true
  try {
    const response = await aiToolApi.getDiagnosisHistory({
      page: pagination.page,
      page_size: pagination.page_size,
      device_ip: searchForm.device_ip || undefined,
      status: searchForm.status || undefined
    })
    historyList.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载诊断历史失败:', error)
    ElMessage.error('加载诊断历史失败')
  } finally {
    loadingHistory.value = false
  }
}

const handleSearchHistory = () => {
  pagination.page = 1
  loadHistory()
}

const handleResetSearch = () => {
  searchForm.device_ip = ''
  searchForm.status = ''
  pagination.page = 1
  loadHistory()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadHistory()
}

const handleCurrentChange = () => {
  loadHistory()
}

const viewHistoryDetail = async (row: AIDiagnosisListItem) => {
  showHistoryDrawer.value = true
  loadingDetail.value = true

  try {
    const response = await aiToolApi.getDiagnosisDetail(row.id)
    historyDetail.value = response.data
  } catch (error) {
    console.error('加载诊断详情失败:', error)
    ElMessage.error('加载诊断详情失败')
  } finally {
    loadingDetail.value = false
  }
}

const deleteHistory = async (row: AIDiagnosisListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除此诊断记录吗？此操作不可恢复！`,
      '删除诊断记录',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await aiToolApi.deleteDiagnosis(row.id)
    ElMessage.success('删除成功')
    await loadHistory()
  } catch (error: any) {
    if (error === 'cancel') return

    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('删除失败')
    }
  }
}

const handleCopyHistoryResult = async () => {
  if (!historyDetail.value?.diagnosis_result) return

  try {
    await navigator.clipboard.writeText(historyDetail.value.diagnosis_result)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const handleExportHistoryResult = async () => {
  if (!historyDetail.value) return

  try {
    const response = await aiToolApi.exportDiagnosis(historyDetail.value.id)

    const blob = new Blob([response.data], { type: 'text/markdown' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `diagnosis_${historyDetail.value.id}_${Date.now()}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 工具方法
const renderMarkdown = (text: string): string => {
  const html = marked(text)
  return DOMPurify.sanitize(html as string)
}

const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, any> = {
    pending: 'info',
    success: 'success',
    failed: 'danger',
    timeout: 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '进行中',
    success: '成功',
    failed: '失败',
    timeout: '超时'
  }
  return statusMap[status] || status
}

// 初始化
onMounted(async () => {
  await loadDevices()
  await loadHistory()
})
</script>

<style scoped>
.ai-tool {
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

.main-tabs {
  margin-top: 20px;
}

.diagnosis-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-section,
.output-section {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 设备选择器样式 */
.device-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-name {
  font-weight: 500;
  flex: 1;
}

.device-ip {
  color: #909399;
  font-size: 13px;
}

/* 设备信息展示 */
.device-info {
  display: flex;
  gap: 24px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.device-info .info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-info .label {
  color: #606266;
  font-weight: 500;
}

.device-info .value {
  color: #303133;
}

/* 输出区域 */
.result-container {
  min-height: 300px;
  max-height: 600px;
  overflow-y: auto;
}

.markdown-body {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
}

.markdown-body :deep(h1) {
  font-size: 24px;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.markdown-body :deep(h2) {
  font-size: 20px;
  margin-top: 24px;
  margin-bottom: 12px;
  color: #303133;
}

.markdown-body :deep(h3) {
  font-size: 16px;
  margin-top: 20px;
  margin-bottom: 10px;
  color: #606266;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 12px 0;
}

.markdown-body :deep(li) {
  margin: 6px 0;
}

.markdown-body :deep(code) {
  background: #282c34;
  color: #abb2bf;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.markdown-body :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding-left: 16px;
  margin: 16px 0;
  color: #606266;
  background: #ecf5ff;
  padding: 12px 16px;
  border-radius: 4px;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #dcdfe6;
  margin: 24px 0;
}

/* 历史记录 */
.search-bar {
  margin-bottom: 20px;
}

.problem-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
}

.no-data {
  color: #c0c4cc;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 历史详情抽屉 */
.history-detail {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-grid .info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-grid .info-item label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.problem-description,
.error-message {
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-message {
  color: #f56c6c;
  border-color: #fbc4c4;
  background: #fef0f0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-tool {
    padding: 10px;
  }

  .diagnosis-container {
    gap: 12px;
  }

  .device-info {
    flex-direction: column;
    gap: 12px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
