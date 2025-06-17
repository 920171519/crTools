<template>
  <div class="device-management">
    <div class="page-header">
      <h1>设备管理</h1>
      <p>管理和监控Linux设备的使用情况</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" icon="Plus" @click="showAddDialog = true">
        添加设备
      </el-button>
      <el-button icon="Refresh" @click="loadDevices">
        刷新
      </el-button>
    </div>

    <!-- 设备列表 -->
    <div class="device-list">
      <el-table :data="devices" stripe style="width: 100%" v-loading="loading">
        <!-- <el-table-column prop="name" label="环境名称" width="150"> -->
        <el-table-column prop="name" label="环境名称" >
          <template #default="{ row }">
            <div class="device-name">
              <el-icon class="device-icon">
                <Monitor />
              </el-icon>
              {{ row.name }}
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="ip" label="环境IP">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.ip }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="device_type" label="设备类型">
          <template #default="{ row }">
            <el-tag 
              :type="getDeviceTypeTag(row.device_type)" 
              size="small"
            >
              {{ getDeviceTypeText(row.device_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="current_user" label="当前使用人">
          <template #default="{ row }">
            <span v-if="row.current_user" class="current-user">
              <el-icon><User /></el-icon>
              {{ row.current_user }}
            </span>
            <span v-else class="no-user">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="occupied_duration" label="已使用时长" width="120">
          <template #default="{ row }">
            <span v-if="row.occupied_duration > 0" class="duration">
              {{ formatDuration(row.occupied_duration) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="queue_count" label="排队人数" width="100">
          <template #default="{ row }">
            <el-tag 
              v-if="row.queue_count > 0" 
              type="warning" 
              size="small"
            >
              {{ row.queue_count }}人
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="环境状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusTag(row.status)" 
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                v-if="row.status === 'available'"
                type="primary" 
                size="small" 
                @click="useDevice(row)"
                :loading="useLoading[row.id]"
              >
                使用
              </el-button>
              
              <el-button 
                v-else-if="row.status === 'occupied' && row.current_user === currentUser"
                type="danger" 
                size="small" 
                @click="releaseDevice(row)"
                :loading="releaseLoading[row.id]"
              >
                释放
              </el-button>
              
              <el-button 
                v-else-if="row.status === 'occupied'"
                type="warning" 
                size="small" 
                @click="joinQueue(row)"
                :loading="useLoading[row.id]"
              >
                排队
              </el-button>
              
              <el-button 
                type="info" 
                size="small" 
                @click="viewDetails(row)"
              >
                详情
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加设备对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      title="添加设备" 
      width="600px"
      :before-close="handleAddDialogClose"
    >
      <el-form 
        ref="addFormRef" 
        :model="addForm" 
        :rules="addFormRules" 
        label-width="120px"
      >
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="addForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        
        <el-form-item label="设备IP" prop="ip">
          <el-input v-model="addForm.ip" placeholder="请输入设备IP地址" />
        </el-form-item>
        
        <el-form-item label="所需VPN" prop="required_vpn">
          <el-input v-model="addForm.required_vpn" placeholder="请输入所需VPN" />
        </el-form-item>
        
        <el-form-item label="添加人" prop="creator">
          <el-input v-model="addForm.creator" placeholder="请输入添加人" />
        </el-form-item>
        
        <el-form-item label="归属人" prop="owner">
          <el-input v-model="addForm.owner" placeholder="请输入归属人" />
        </el-form-item>
        
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="addForm.device_type" placeholder="请选择设备类型">
            <el-option label="测试设备" value="test" />
            <el-option label="开发设备" value="develop" />
            <el-option label="CI设备" value="ci" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="登录需VPN">
          <el-switch v-model="addForm.need_vpn_login" />
        </el-form-item>
        
        <el-form-item label="支持排队">
          <el-switch v-model="addForm.support_queue" />
        </el-form-item>
        
        <el-form-item label="备注信息">
          <el-input 
            v-model="addForm.remarks" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="handleAddDevice" :loading="addLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 使用设备对话框 -->
    <el-dialog 
      v-model="showUseDialog" 
      title="使用设备" 
      width="500px"
    >
      <el-form 
        ref="useFormRef" 
        :model="useForm" 
        :rules="useFormRules" 
        label-width="120px"
      >
        <el-form-item label="设备名称">
          <el-input :value="selectedDevice?.name" disabled />
        </el-form-item>
        
        <el-form-item label="使用人" prop="user">
          <el-input v-model="useForm.user" placeholder="请输入使用人" />
        </el-form-item>
        
        <el-form-item label="预计时长" prop="expected_duration">
          <el-input-number 
            v-model="useForm.expected_duration" 
            :min="1" 
            :max="480" 
            controls-position="right"
          />
          <span style="margin-left: 8px;">分钟</span>
        </el-form-item>
        
        <el-form-item label="使用目的">
          <el-input 
            v-model="useForm.purpose" 
            type="textarea" 
            :rows="3"
            placeholder="请输入使用目的"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUseDialog = false">取消</el-button>
          <el-button type="primary" @click="handleUseDevice" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Monitor, User, Plus, Refresh } from '@element-plus/icons-vue'
import { deviceApi } from '@/api/device'

// 数据定义
const loading = ref(false)
const devices = ref([])
const currentUser = ref('当前用户') // 这里应该从用户store获取
const useLoading = reactive({})
const releaseLoading = reactive({})

// 添加设备相关
const showAddDialog = ref(false)
const addLoading = ref(false)
const addFormRef = ref()
const addForm = reactive({
  name: '',
  ip: '',
  required_vpn: '',
  creator: '',
  owner: '',
  device_type: 'test',
  need_vpn_login: false,
  support_queue: true,
  remarks: ''
})

const addFormRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  ip: [
    { required: true, message: '请输入设备IP', trigger: 'blur' },
    { pattern: /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/, message: '请输入正确的IP地址格式', trigger: 'blur' }
  ],
  required_vpn: [{ required: true, message: '请输入所需VPN', trigger: 'blur' }],
  creator: [{ required: true, message: '请输入添加人', trigger: 'blur' }],
  owner: [{ required: true, message: '请输入归属人', trigger: 'blur' }]
}

// 使用设备相关
const showUseDialog = ref(false)
const submitLoading = ref(false)
const selectedDevice = ref(null)
const useFormRef = ref()
const useForm = reactive({
  user: '',
  expected_duration: 60,
  purpose: ''
})

const useFormRules = {
  user: [{ required: true, message: '请输入使用人', trigger: 'blur' }],
  expected_duration: [{ required: true, message: '请输入预计使用时长', trigger: 'blur' }]
}

// 方法定义
const loadDevices = async () => {
  loading.value = true
  try {
    const response = await deviceApi.getDevices()
    devices.value = response.data.data
  } catch (error) {
    console.log(error)
    ElMessage.error('加载设备列表失败')
  } finally {
    loading.value = false
  }
}

const useDevice = (device) => {
  selectedDevice.value = device
  useForm.user = currentUser.value
  showUseDialog.value = true
}

const joinQueue = (device) => {
  selectedDevice.value = device
  useForm.user = currentUser.value
  showUseDialog.value = true
}

const releaseDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      '确定要释放此设备吗？',
      '确认释放',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    releaseLoading[device.id] = true
    await deviceApi.releaseDevice({
      device_id: device.id,
      user: currentUser.value
    })
    
    ElMessage.success('设备释放成功')
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('释放设备失败')
    }
  } finally {
    releaseLoading[device.id] = false
  }
}

const viewDetails = (device) => {
  // 查看设备详情的逻辑
  ElMessage.info('设备详情功能开发中...')
}

const handleAddDevice = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    addLoading.value = true
    
    await deviceApi.createDevice(addForm)
    ElMessage.success('设备添加成功')
    showAddDialog.value = false
    await loadDevices()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('添加设备失败')
    }
  } finally {
    addLoading.value = false
  }
}

const handleUseDevice = async () => {
  if (!useFormRef.value) return
  
  try {
    await useFormRef.value.validate()
    submitLoading.value = true
    const response = await deviceApi.useDevice({
      device_id: selectedDevice.value.id,
      user: useForm.user,
      expected_duration: useForm.expected_duration,
      purpose: useForm.purpose
    })
    ElMessage.success(response.message)
    showUseDialog.value = false
    await loadDevices()
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('操作失败')
    }
  } finally {
    submitLoading.value = false
  }
}

const handleAddDialogClose = () => {
  addFormRef.value?.resetFields()
  showAddDialog.value = false
}

// 辅助方法
const getDeviceTypeText = (type) => {
  const typeMap = {
    test: '测试',
    develop: '开发',
    ci: 'CI'
  }
  return typeMap[type] || type
}

const getDeviceTypeTag = (type) => {
  const tagMap = {
    test: 'success',
    develop: 'primary',
    ci: 'warning'
  }
  return tagMap[type] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    available: '可用',
    occupied: '占用中',
    maintenance: '维护中',
    offline: '不可占用',
    queue: '排队中'
  }
  return statusMap[status] || status
}

const getStatusTag = (status) => {
  const tagMap = {
    available: 'success',
    occupied: 'warning',
    maintenance: 'info',
    offline: 'danger'
  }
  return tagMap[status] || 'info'
}

const formatDuration = (minutes) => {
  if (minutes < 60) {
    return `${minutes}分钟`
  } else {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}小时${mins > 0 ? mins + '分钟' : ''}`
  }
}

// 生命周期
onMounted(() => {
  loadDevices()
})
</script>

<style scoped>
.device-management {
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

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.device-list {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-icon {
  color: #409eff;
}

.current-user {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
}

.no-user {
  color: #c0c4cc;
}

.duration {
  color: #e6a23c;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .device-management {
    padding: 10px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  
  .action-buttons .el-button {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
}
</style> 