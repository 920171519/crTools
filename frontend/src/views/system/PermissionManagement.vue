<template>
  <div class="permission-management">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>权限管理</span>
        </div>
      </template>

      <!-- 权限表格 -->
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="name" label="权限名称" width="150" />
        <el-table-column prop="code" label="权限代码" width="150" />
        <el-table-column prop="resource" label="资源" width="120" />
        <el-table-column prop="action" label="动作" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const loading = ref(false)
const tableData = ref([])

const fetchPermissions = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    tableData.value = [
      { id: 1, name: '用户查看', code: 'user:read', resource: 'user', action: 'read', description: '查看用户信息' },
      { id: 2, name: '用户创建', code: 'user:create', resource: 'user', action: 'create', description: '创建用户' },
      { id: 3, name: '用户更新', code: 'user:update', resource: 'user', action: 'update', description: '更新用户信息' },
      { id: 4, name: '用户删除', code: 'user:delete', resource: 'user', action: 'delete', description: '删除用户' },
      { id: 5, name: '角色查看', code: 'role:read', resource: 'role', action: 'read', description: '查看角色信息' },
      { id: 6, name: '角色创建', code: 'role:create', resource: 'role', action: 'create', description: '创建角色' }
    ]
  } finally {
    loading.value = false
  }
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchPermissions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 