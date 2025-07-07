<template>
  <div class="user-management">
    <el-card shadow="never">
      <!-- 页面标题 -->
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleAdd" v-if="userStore.hasPermission('user:create')">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :model="searchForm" inline>
          <el-form-item label="工号">
            <el-input v-model="searchForm.employee_id" placeholder="请输入工号" clearable />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="searchForm.username" placeholder="请输入姓名" clearable />
          </el-form-item>
          <el-form-item label="角色">
            <el-select 
              v-model="searchForm.role_name" 
              placeholder="请选择角色" 
              clearable
              style="width: 130px"
            >
              <el-option 
                v-for="option in roleOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 数据表格 -->
      <el-table :data="tableData" stripe v-loading="loading">
        <el-table-column prop="employee_id" label="工号"/>
        <el-table-column prop="username" label="姓名"/>
        <el-table-column label="角色">
          <template #default="{ row }">
            <el-tag
              :type="getRoleTagType(row.role)"
              size="small"
            >
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- <el-table-column prop="is_superuser" label="超级用户" >
          <template #default="{ row }">
            <el-tag :type="row.is_superuser ? 'success' : 'info'" size="small">
              {{ row.is_superuser ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column> -->
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="handleEdit(row)"
              :disabled="row.is_superuser"
              v-if="userStore.hasPermission('user:update')"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="handleDelete(row)"
                             :disabled="row.is_superuser || row.id === userStore.userInfo?.id"
              v-if="userStore.hasPermission('user:delete')"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :small="false"
          :disabled="false"
          :background="false"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 编辑用户角色对话框 -->
    <el-dialog 
      v-model="editDialogVisible" 
      title="编辑用户角色" 
      width="400px"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="工号">
          <el-input v-model="editForm.employee_id" disabled />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="当前角色">
          <el-tag :type="getRoleTagType(editForm.current_role)">
            {{ editForm.current_role }}
          </el-tag>
        </el-form-item>
        <el-form-item label="新角色">
          <el-select v-model="editForm.new_role" placeholder="请选择新角色">
            <el-option 
              v-for="option in roleOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmEdit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getUserList, updateUserRole, deleteUser, getRoleList, ROLE_OPTIONS, getRoleTagType } from '@/api/user'

const userStore = useUserStore()

// 搜索表单
const searchForm = reactive({
  employee_id: '',
  username: '',
  role_name: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 表格数据
const tableData = ref([])
const loading = ref(false)

// 角色选项
const roleOptions = ref(ROLE_OPTIONS)

// 编辑对话框
const editDialogVisible = ref(false)
const editForm = reactive({
  id: 0,
  employee_id: '',
  username: '',
  current_role: '',
  new_role: ''
})

// 获取用户列表
const fetchUserList = async () => {
  loading.value = true
  try {
    const response = await getUserList({
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    })
    
    // API拦截器已经处理了code=200的情况，直接使用response.data
    tableData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('获取用户列表错误:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchUserList()
}

// 重置搜索
const handleReset = () => {
  Object.assign(searchForm, {
    employee_id: '',
    username: '',
    role_name: ''
  })
  pagination.page = 1
  fetchUserList()
}

// 分页大小改变
const handleSizeChange = (val: number) => {
  pagination.page_size = val
  pagination.page = 1
  fetchUserList()
}

// 当前页改变
const handleCurrentChange = (val: number) => {
  pagination.page = val
  fetchUserList()
}

// 编辑用户
const handleEdit = (row: any) => {
  editForm.id = row.id
  editForm.employee_id = row.employee_id
  editForm.username = row.username
  editForm.current_role = row.role
  editForm.new_role = row.role
  editDialogVisible.value = true
}

// 确认编辑
const handleConfirmEdit = async () => {
  if (!editForm.new_role) {
    ElMessage.error('请选择新角色')
    return
  }
  
  if (editForm.new_role === editForm.current_role) {
    ElMessage.error('新角色与当前角色相同')
    return
  }
  
  try {
    const response = await updateUserRole(editForm.id, editForm.new_role)
    // API拦截器已经处理了成功情况，能执行到这里说明请求成功
    ElMessage.success('用户角色更新成功')
    editDialogVisible.value = false
    fetchUserList() // 刷新列表
  } catch (error) {
    console.error('更新用户角色错误:', error)
    ElMessage.error('更新用户角色失败')
  }
}

// 删除用户
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${row.username}(${row.employee_id}) 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const response = await deleteUser(row.id)
    // API拦截器已经处理了成功情况，能执行到这里说明请求成功
    ElMessage.success('删除用户成功')
    fetchUserList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户错误:', error)
      ElMessage.error('删除用户失败')
    }
  }
}

// 新增用户（待实现）
const handleAdd = () => {
  ElMessage.info('新增用户功能待实现')
}

// 初始化
onMounted(() => {
  fetchUserList()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 