<template>
  <div class="profile-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人中心</span>
        </div>
      </template>
      <div class="profile-content">
        <el-row :gutter="20">

          <el-col :span="16">
            <el-descriptions title="基本信息" :column="2" border>
              <el-descriptions-item label="工号">{{ userInfo?.employee_id }}</el-descriptions-item>
              <el-descriptions-item label="姓名">{{ userInfo?.username }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const userInfo = computed(() => userStore.userInfo)

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

const handleAvatarUpload = () => {
  ElMessage.info('头像上传功能待开发')
}
</script>

<style scoped>
.profile-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.profile-content {
  padding: 20px 0;
}

.upload-btn {
  margin-top: 16px;
  width: 120px;
}
</style> 