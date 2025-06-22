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
        
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <!-- 设备可用时的按钮 -->
              <el-button 
                v-if="row.status === 'available'"
                type="primary" 
                size="small" 
                @click="useDevice(row)"
                :loading="useLoading[row.id]"
              >
                使用
              </el-button>
              
              <!-- 统一排队按钮 -->
              <el-button 
                type="warning" 
                size="small" 
                @click="unifiedQueueAction(row)"
                :loading="useLoading[row.id]"
              >
                排队
              </el-button>
              
              <!-- 设备被占用时的按钮 -->
              <template v-if="row.status === 'occupied'">
                <!-- 高级用户专用按钮 -->
                <template v-if="isAdvancedUser || isAdminUser || isAdmin">
                  <el-button 
                    type="danger" 
                    size="small" 
                    @click="preemptDevice(row)"
                    :loading="useLoading[row.id]"
                  >
                    抢占
                  </el-button>
                  
                  <el-button 
                    v-if="!row.is_current_user_in_queue"
                    type="success" 
                    size="small" 
                    @click="priorityQueue(row)"
                    :loading="useLoading[row.id]"
                  >
                    优先排队
                  </el-button>
                </template>
                
                <!-- 普通用户排队控制 - 单个按钮 -->
                <el-button 
                  v-if="!(isAdvancedUser || isAdminUser || isAdmin)"
                  :type="row.is_current_user_in_queue ? 'info' : 'warning'" 
                  size="small" 
                  @click="row.is_current_user_in_queue ? cancelQueue(row) : joinQueue(row)"
                  :loading="useLoading[row.id]"
                >
                  {{ row.is_current_user_in_queue ? '取消排队' : '排队' }}
                </el-button>
                
                <!-- 高级用户/管理员的取消排队按钮 -->
                <el-button 
                  v-if="row.is_current_user_in_queue && (isAdvancedUser || isAdminUser || isAdmin)"
                  type="info" 
                  size="small" 
                  @click="cancelQueue(row)"
                  :loading="useLoading[row.id]"
                >
                  取消排队
                </el-button>
                
                <!-- 释放设备按钮 -->
                <el-button 
                  v-if="row.current_user === currentUser || isAdmin"
                  type="danger" 
                  size="small" 
                  @click="releaseDevice(row)"
                  :loading="releaseLoading[row.id]"
                >
                  释放
                </el-button>
              </template>
              
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

    <!-- 设备详情抽屉 -->
    <el-drawer
      v-model="showDetailDrawer"
      title="设备详情"
      direction="rtl"
      size="600px"
      :before-close="handleDetailDrawerClose"
    >
      <div v-loading="detailLoading" class="device-detail">
        <template v-if="deviceDetail">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              基本信息
            </h3>
            <div class="info-grid">
              <div class="info-item">
                <label>设备名称：</label>
                <span>{{ deviceDetail.name }}</span>
              </div>
              <div class="info-item">
                <label>设备IP：</label>
                <el-tag type="info" size="small">{{ deviceDetail.ip }}</el-tag>
              </div>
              <div class="info-item">
                <label>设备类型：</label>
                <el-tag 
                  :type="getDeviceTypeTag(deviceDetail.device_type)"
                  size="small"
                >
                  {{ getDeviceTypeText(deviceDetail.device_type) }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>所需VPN：</label>
                <span>{{ deviceDetail.required_vpn }}</span>
              </div>
              <div class="info-item">
                <label>添加人：</label>
                <span>{{ deviceDetail.creator }}</span>
              </div>
              <div class="info-item">
                <label>归属人：</label>
                <span>{{ deviceDetail.owner }}</span>
              </div>
              <div class="info-item">
                <label>登录需VPN：</label>
                <el-tag :type="deviceDetail.need_vpn_login ? 'warning' : 'success'" size="small">
                  {{ deviceDetail.need_vpn_login ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>支持排队：</label>
                <el-tag :type="deviceDetail.support_queue ? 'success' : 'info'" size="small">
                  {{ deviceDetail.support_queue ? '是' : '否' }}
                </el-tag>
              </div>
              <div class="info-item full-width" v-if="deviceDetail.remarks">
                <label>备注信息：</label>
                <div class="remarks">{{ deviceDetail.remarks }}</div>
              </div>
            </div>
          </div>

          <!-- 使用状态 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><Clock /></el-icon>
              使用状态
            </h3>
            <div class="usage-info">
              <div class="usage-item">
                <label>当前状态：</label>
                <el-tag 
                  :type="getStatusTag(usageDetail?.status || 'available')"
                  size="small"
                >
                  {{ getStatusText(usageDetail?.status || 'available') }}
                </el-tag>
              </div>
              <div class="usage-item" v-if="usageDetail?.current_user">
                <label>当前使用人：</label>
                <span class="current-user">
                  <el-icon><User /></el-icon>
                  {{ usageDetail.current_user }}
                </span>
              </div>
              <div class="usage-item" v-if="usageDetail?.start_time">
                <label>开始时间：</label>
                <span>{{ formatDateTime(usageDetail.start_time) }}</span>
              </div>
              <div class="usage-item" v-if="usageDetail?.expected_duration">
                <label>预计时长：</label>
                <span>{{ usageDetail.expected_duration }}分钟</span>
              </div>
              <div class="usage-item" v-if="usageDetail?.occupied_duration">
                <label>已使用时长：</label>
                <span class="duration">{{ formatDuration(usageDetail.occupied_duration) }}</span>
              </div>
              <div class="usage-item" v-if="usageDetail?.is_long_term">
                <label>长时间占用：</label>
                <el-tag type="warning" size="small">是</el-tag>
              </div>
              <div class="usage-item full-width" v-if="usageDetail?.long_term_purpose">
                <label>占用目的：</label>
                <div class="purpose">{{ usageDetail.long_term_purpose }}</div>
              </div>
            </div>
          </div>

          <!-- 排队信息 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><UserFilled /></el-icon>
              排队信息
              <el-tag 
                v-if="usageDetail?.queue_count > 0" 
                type="warning" 
                size="small"
                style="margin-left: 8px;"
              >
                {{ usageDetail.queue_count }}人排队
              </el-tag>
            </h3>
            <div class="queue-info">
              <template v-if="usageDetail?.queue_users && usageDetail.queue_users.length > 0">
                <div 
                  v-for="(user, index) in usageDetail.queue_users" 
                  :key="index"
                  class="queue-item"
                >
                  <div class="queue-position">{{ index + 1 }}</div>
                  <div class="queue-user">
                    <el-icon><User /></el-icon>
                    {{ user }}
                  </div>
                  <div class="queue-time">等待中</div>
                </div>
              </template>
              <div v-else class="no-queue">
                <el-empty description="暂无排队用户" :image-size="80" />
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="detail-actions">
            <el-button 
              v-if="usageDetail?.status === 'available'"
              type="primary" 
              @click="useDeviceFromDetail"
              :loading="useLoading[deviceDetail.id]"
            >
              <el-icon><VideoPlay /></el-icon>
              使用设备
            </el-button>
            
            <!-- 统一排队按钮 -->
            <el-button 
              type="warning" 
              @click="unifiedQueueFromDetail"
              :loading="useLoading[deviceDetail.id]"
            >
              <el-icon><Clock /></el-icon>
              排队
            </el-button>
            
            <!-- 高级用户专用按钮 -->
            <template v-if="(isAdvancedUser || isAdminUser || isAdmin) && usageDetail?.status === 'occupied'">
              <el-button 
                type="danger" 
                @click="preemptDeviceFromDetail"
                :loading="useLoading[deviceDetail.id]"
              >
                <el-icon><VideoPlay /></el-icon>
                抢占设备
              </el-button>
              
              <el-button 
                v-if="!isCurrentUserInQueue"
                type="success" 
                @click="priorityQueueFromDetail"
                :loading="useLoading[deviceDetail.id]"
              >
                <el-icon><Clock /></el-icon>
                优先排队
              </el-button>
            </template>
            
            <!-- 释放设备按钮 -->
            <el-button 
              v-if="usageDetail?.status === 'occupied' && (usageDetail?.current_user === currentUser || isAdmin)"
              type="danger" 
              @click="releaseDeviceFromDetail"
              :loading="releaseLoading[deviceDetail.id]"
            >
              <el-icon><VideoPause /></el-icon>
              释放设备
            </el-button>
            
            <!-- 删除设备按钮 - 只有设备归属人或管理员才能看到 -->
            <el-button 
              v-if="deviceDetail.owner === currentUser || isAdmin"
              type="danger" 
              plain
              @click="deleteDeviceFromDetail"
              :loading="deleteLoading"
            >
              <el-icon><Delete /></el-icon>
              删除设备
            </el-button>
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
  Monitor, User, Plus, Refresh, InfoFilled, Clock, UserFilled, 
  VideoPlay, VideoPause, Delete 
} from '@element-plus/icons-vue'
import { deviceApi } from '../api/device'
import { useUserStore } from '@/stores/user'

// 获取用户store
const userStore = useUserStore()

// 数据定义
const loading = ref(false)
const devices = ref([])
const useLoading = reactive({})
const releaseLoading = reactive({})
const deleteLoading = ref(false)

// 计算属性
const currentUser = computed(() => userStore.userInfo?.username || '')
const isAdmin = computed(() => userStore.userInfo?.is_superuser || false)
const isAdvancedUser = computed(() => userStore.isAdvancedUser)
const isAdminUser = computed(() => userStore.isAdminUser)

// 检查用户是否在指定设备的排队中（用于列表）
const isUserInDeviceQueue = (device) => {
  // 这里需要通过API获取设备使用详情才能知道排队情况
  // 为了性能考虑，我们可以在设备列表中添加当前用户的排队状态字段
  return false // 暂时返回false，后续优化
}

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

// 抽屉相关
const showDetailDrawer = ref(false)
const detailLoading = ref(false)
const deviceDetail = ref(null)
const usageDetail = ref(null)

// 方法定义
const loadDevices = async () => {
  loading.value = true
  try {
    const response = await deviceApi.getDevices()
    devices.value = response.data
    console.log('成功加载设备列表，数量:', devices.value?.length)
  } catch (error) {
    console.error('加载设备失败:', error)
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

const cancelQueue = async (device) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消排队吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    useLoading[device.id] = true
    await deviceApi.cancelQueue({
      device_id: device.id
    })
    
    ElMessage.success('已取消排队')
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('取消排队失败')
      }
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 统一排队操作
const unifiedQueueAction = async (device) => {
  try {
    useLoading[device.id] = true
    const response = await deviceApi.unifiedQueue({
      device_id: device.id,
      user: currentUser.value,
      expected_duration: 60,
      purpose: '使用设备'
    })
    
    if (response.data.action === 'use') {
      ElMessage.success('设备使用成功')
    } else {
      ElMessage.success(`已加入排队，排队位置：${response.data.queue_position}`)
    }
    
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('操作失败')
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 抢占设备
const preemptDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      '确定要抢占此设备吗？原使用者将被加入排队列表首位。',
      '确认抢占',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    useLoading[device.id] = true
    const response = await deviceApi.preemptDevice({
      device_id: device.id,
      user: currentUser.value,
      expected_duration: 60,
      purpose: '抢占使用'
    })
    
    ElMessage.success(response.data.message)
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('抢占设备失败')
      }
    }
  } finally {
    useLoading[device.id] = false
  }
}

// 优先排队
const priorityQueue = async (device) => {
  try {
    useLoading[device.id] = true
    const response = await deviceApi.priorityQueue({
      device_id: device.id,
      user: currentUser.value,
      expected_duration: 60,
      purpose: '优先排队'
    })
    
    ElMessage.success(response.data.message)
    await loadDevices()
    
    // 如果详情抽屉打开，刷新详情数据
    if (showDetailDrawer.value && deviceDetail.value?.id === device.id) {
      await viewDetails(device)
    }
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('优先排队失败')
    }
  } finally {
    useLoading[device.id] = false
  }
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
    const response = await deviceApi.releaseDevice({
      device_id: device.id,
      user: currentUser.value
    })
    
    // 显示后端返回的消息
    ElMessage.success(response.data?.message || '设备释放成功')
    await loadDevices()
  } catch (error) {
    if (error !== 'cancel') {
      if (error.response?.data?.detail) {
        ElMessage.error(error.response.data.detail)
      } else {
        ElMessage.error('释放设备失败')
      }
    }
  } finally {
    releaseLoading[device.id] = false
  }
}

const viewDetails = async (device) => {
  try {
    detailLoading.value = true
    showDetailDrawer.value = true
    
    // 获取设备详情
    const [deviceResponse, usageResponse] = await Promise.all([
      deviceApi.getDevice(device.id),
      deviceApi.getDeviceUsage(device.id)
    ])
    
    deviceDetail.value = deviceResponse.data
    usageDetail.value = usageResponse.data
  } catch (error) {
    ElMessage.error('获取设备详情失败')
    console.error(error)
  } finally {
    detailLoading.value = false
  }
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
    ElMessage.success(response.data.message)
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

const formatDateTime = (dateTimeStr) => {
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

// 抽屉相关方法
const handleDetailDrawerClose = () => {
  showDetailDrawer.value = false
  deviceDetail.value = null
  usageDetail.value = null
}

const useDeviceFromDetail = () => {
  if (deviceDetail.value) {
    useDevice(deviceDetail.value)
    showDetailDrawer.value = false
  }
}

const releaseDeviceFromDetail = async () => {
  if (deviceDetail.value) {
    await releaseDevice(deviceDetail.value)
    showDetailDrawer.value = false
  }
}

const joinQueueFromDetail = () => {
  if (deviceDetail.value) {
    joinQueue(deviceDetail.value)
    showDetailDrawer.value = false
  }
}

const unifiedQueueFromDetail = () => {
  if (deviceDetail.value) {
    unifiedQueueAction(deviceDetail.value)
    // 不关闭抽屉，让用户能看到结果
  }
}

const preemptDeviceFromDetail = () => {
  if (deviceDetail.value) {
    preemptDevice(deviceDetail.value)
    // 不关闭抽屉，让用户能看到结果
  }
}

const priorityQueueFromDetail = () => {
  if (deviceDetail.value) {
    priorityQueue(deviceDetail.value)
    // 不关闭抽屉，让用户能看到结果
  }
}

const cancelQueueFromDetail = async () => {
  if (deviceDetail.value) {
    await cancelQueue(deviceDetail.value)
    // 不关闭抽屉，因为cancelQueue已经会刷新详情数据
  }
}

// 删除设备
const deleteDeviceFromDetail = async () => {
  if (!deviceDetail.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除设备 "${deviceDetail.value.name}" 吗？此操作不可恢复！`,
      '删除设备',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    )
    
    deleteLoading.value = true
    await deviceApi.deleteDevice(deviceDetail.value.id)
    ElMessage.success('设备删除成功')
    showDetailDrawer.value = false
    await loadDevices()
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('删除设备失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

// 检查当前用户是否在抽屉设备的排队中
const isCurrentUserInQueue = computed(() => {
  if (!usageDetail.value?.queue_users || !currentUser.value) return false
  return usageDetail.value.queue_users.includes(currentUser.value)
})

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

/* 抽屉样式 */
.device-detail {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item.full-width {
  grid-column: 1 / -1;
  flex-direction: column;
  align-items: flex-start;
}

.info-item label {
  font-weight: 500;
  color: #606266;
  min-width: 80px;
}

.remarks, .purpose {
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  width: 100%;
  margin-top: 8px;
  line-height: 1.5;
}

.usage-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.usage-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.usage-item.full-width {
  flex-direction: column;
  align-items: flex-start;
}

.usage-item label {
  font-weight: 500;
  color: #606266;
  min-width: 100px;
}

.queue-info {
  max-height: 300px;
  overflow-y: auto;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 8px;
}

.queue-position {
  background: #409eff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.queue-user {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
  color: #303133;
}

.queue-time {
  color: #909399;
  font-size: 12px;
}

.no-queue {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.detail-actions {
  position: sticky;
  bottom: 0;
  background: white;
  padding: 20px 0;
  border-top: 1px solid #ebeef5;
  margin-top: 20px;
  display: flex;
  gap: 12px;
  justify-content: center;
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
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .device-detail {
    padding: 15px;
  }
  
  .detail-section {
    padding: 15px;
  }
}
</style> 