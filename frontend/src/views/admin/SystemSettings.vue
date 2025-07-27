<template>
  <div class="system-settings">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>

      <el-form :model="settingsForm" label-width="150px" :loading="loading">
        <el-form-item label="定时清理时间">
          <el-time-picker
            v-model="settingsForm.cleanup_time"
            format="HH:mm"
            placeholder="选择清理时间"
            style="width: 200px"
          />
          <div class="form-help">
            每天在指定时间自动释放所有设备占用和排队
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="saveSettings" :loading="saveLoading">
            保存设置
          </el-button>
          <el-button @click="resetSettings">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 当前设置显示 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>当前设置</span>
        </div>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="定时清理时间">
          {{ currentSettings.cleanup_time || '未设置' }}
        </el-descriptions-item>
        <el-descriptions-item label="下次执行时间">
          {{ nextExecutionTime || '计算中...' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后更新时间">
          {{ currentSettings.updated_at || '未知' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 手动操作 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>手动操作</span>
        </div>
      </template>

      <el-space>
        <el-button type="danger" @click="manualCleanup" :loading="cleanupLoading">
          立即清理所有设备
        </el-button>
        <el-button @click="refreshSettings" :loading="loading">
          刷新设置
        </el-button>
      </el-space>
      
      <div class="form-help" style="margin-top: 10px;">
        立即清理将释放所有设备的占用状态和排队列表
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { systemApi } from '@/api/system'

// 响应式数据
const loading = ref(false)
const saveLoading = ref(false)
const cleanupLoading = ref(false)

const settingsForm = ref({
  cleanup_time: null
})

const currentSettings = ref({
  cleanup_time: null,
  updated_at: null
})

// 计算下次执行时间
const nextExecutionTime = computed(() => {
  if (!currentSettings.value.cleanup_time) return null
  
  const now = new Date()
  const [hours, minutes] = currentSettings.value.cleanup_time.split(':')
  const nextExecution = new Date()
  nextExecution.setHours(parseInt(hours), parseInt(minutes), 0, 0)
  
  // 如果今天的时间已过，设置为明天
  if (nextExecution <= now) {
    nextExecution.setDate(nextExecution.getDate() + 1)
  }
  
  return nextExecution.toLocaleString('zh-CN')
})

// 加载设置
const loadSettings = async () => {
  try {
    loading.value = true
    const response = await systemApi.getSettings()
    currentSettings.value = response.data
    
    // 设置表单值
    if (response.data.cleanup_time) {
      const timeValue = new Date()
      const [hours, minutes] = response.data.cleanup_time.split(':')
      timeValue.setHours(parseInt(hours), parseInt(minutes), 0, 0)
      settingsForm.value.cleanup_time = timeValue
    }
  } catch (error) {
    console.error('加载设置失败:', error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

// 保存设置
const saveSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要保存系统设置吗？新的定时清理时间将在下次执行时生效。',
      '确认保存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    saveLoading.value = true
    
    // 格式化时间
    let cleanup_time = null
    if (settingsForm.value.cleanup_time) {
      const hours = settingsForm.value.cleanup_time.getHours().toString().padStart(2, '0')
      const minutes = settingsForm.value.cleanup_time.getMinutes().toString().padStart(2, '0')
      cleanup_time = `${hours}:${minutes}`
    }

    const response = await systemApi.updateSettings({
      cleanup_time
    })

    ElMessage.success(response.message)
    await loadSettings()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('保存设置失败:', error)
      ElMessage.error('保存设置失败')
    }
  } finally {
    saveLoading.value = false
  }
}

// 重置设置
const resetSettings = () => {
  settingsForm.value.cleanup_time = null
  if (currentSettings.value.cleanup_time) {
    const timeValue = new Date()
    const [hours, minutes] = currentSettings.value.cleanup_time.split(':')
    timeValue.setHours(parseInt(hours), parseInt(minutes), 0, 0)
    settingsForm.value.cleanup_time = timeValue
  }
}

// 刷新设置
const refreshSettings = () => {
  loadSettings()
}

// 手动清理
const manualCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要立即清理所有设备吗？这将释放所有设备的占用状态和排队列表。',
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    cleanupLoading.value = true
    const response = await systemApi.manualCleanup()
    ElMessage.success(response.message)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('手动清理失败:', error)
      ElMessage.error('手动清理失败')
    }
  } finally {
    cleanupLoading.value = false
  }
}

// 初始化
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.system-settings {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
