<template>
  <div class="menu-management">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>菜单管理</span>
        </div>
      </template>

      <!-- 菜单表格 -->
      <el-table v-loading="loading" :data="tableData" stripe row-key="id" default-expand-all>
        <el-table-column prop="name" label="菜单名称" width="200" />
        <el-table-column prop="path" label="路由路径" width="200" />
        <el-table-column prop="component" label="组件" width="200" />
        <el-table-column prop="icon" label="图标" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="显示状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_visible ? 'success' : 'danger'" size="small">
              {{ row.is_visible ? '显示' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="permission_code" label="权限代码" width="150" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const loading = ref(false)
const tableData = ref([])

const fetchMenus = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500))
    tableData.value = [
      {
        id: 1,
        name: '首页',
        path: '/dashboard',
        component: 'Dashboard',
        icon: 'el-icon-monitor',
        sort_order: 1,
        is_visible: true,
        permission_code: null
      },
      {
        id: 2,
        name: '环境管理',
        path: '/system',
        component: null,
        icon: 'el-icon-user',
        sort_order: 100,
        is_visible: true,
        permission_code: null,
        children: [
          {
            id: 3,
            name: '用户管理',
            path: '/system/users',
            component: 'UserManagement',
            icon: 'el-icon-user',
            sort_order: 101,
            is_visible: true,
            permission_code: 'user:read'
          },
          {
            id: 4,
            name: '角色管理',
            path: '/system/roles',
            component: 'RoleManagement',
            icon: 'el-icon-UserFilled',
            sort_order: 102,
            is_visible: true,
            permission_code: 'role:read'
          }
        ]
      }
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMenus()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 