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
            <el-select v-model="searchForm.user_type" placeholder="请选择用户类型" clearable>
              <el-option 
                v-for="option in userTypeOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
      <div class="action-bar">
      <el-button icon="Refresh" @click="fetchUsers">
        刷新用户列表
      </el-button>
    </div>
      <!-- 用户表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="employee_id" label="工号"/>
        <el-table-column prop="username" label="姓名" />
        <el-table-column prop="roles" label="角色">
          <template #default="{ row }">
            <el-tag 
              v-for="role in row.roles"
              :key="role"
              type="info"
              size="small"
              style="margin-right: 5px;"
            >
              {{ role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="handleEdit(row)"
              v-if="userStore.hasPermission('user:update')"
            >
              编辑
            </el-button>
            <el-button 
              type="success" 
              size="small" 
              @click="handleEditUserType(row)"
              v-if="canEditUserType(row)"
            >
              修改类型
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              v-if="userStore.hasPermission('user:delete') && !row.is_superuser && row.id !== userStore.userInfo?.id"
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
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="600px"
      :before-close="handleCloseDialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="employee_id">
              <el-input v-model="form.employee_id" placeholder="如: A12345678" :disabled="isEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="username">
              <el-input v-model="form.username" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" v-if="!isEdit">
          <el-col :span="24">
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 修改用户类型对话框 -->
    <el-dialog
      v-model="userTypeDialogVisible"
      title="修改用户类型"
      width="400px"
    >
      <el-form label-width="100px">
        <el-form-item label="用户工号">
          <el-input v-model="selectedUser.employee_id" disabled />
        </el-form-item>
        <el-form-item label="用户姓名">
          <el-input v-model="selectedUser.username" disabled />
        </el-form-item>
        <el-form-item label="当前类型">
          <el-tag :type="getUserTypeTagType(selectedUser)" size="small">
            {{ getUserTypeLabel(selectedUser) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="新类型" required>
          <el-select 
            v-model="newUserType" 
            placeholder="请选择新的用户类型"
            style="width: 100%"
          >
            <el-option 
              v-for="option in editableUserTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userTypeDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleUpdateUserType" 
            :loading="updateTypeLoading"
            :disabled="!newUserType || newUserType === selectedUser.user_type"
          >
            确定修改
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import * as userApi from '@/api/user'

const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const userTypeDialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const updateTypeLoading = ref(false)
const formRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  employee_id: '',
  username: '',
  user_type: ''
})

// 表格数据
const tableData = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 表单数据
const form = reactive({
  id: 0,
  employee_id: '',
  username: '',
  password: '',
})

// 选中的用户和新用户类型
const selectedUser = ref<any>({})
const newUserType = ref('')

// 用户类型选项
const userTypeOptions = userApi.USER_TYPE_OPTIONS

// 可编辑的用户类型选项（排除管理员）
const editableUserTypeOptions = userTypeOptions.filter(option => option.value !== 'admin')

// 表单验证规则
const formRules: FormRules = {
  employee_id: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { pattern: /^[A-Za-z]\d{8}$/, message: '工号格式错误', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度在2-50个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6-20个字符', trigger: 'blur' }
  ],
}

// 获取用户类型标签
const getUserTypeLabel = (user: any) => {
  if (user.is_superuser) {
    return '超级管理员'
  }
  return userApi.getUserTypeLabel(user.user_type)
}

// 获取用户类型标签类型
const getUserTypeTagType = (user: any) => {
  if (user.is_superuser) return 'danger'
  switch (user.user_type) {
    case 'admin': return 'warning'
    case 'advanced': return 'success'
    case 'normal': return 'info'
    default: return 'info'
  }
}

// 判断是否可以编辑用户类型
const canEditUserType = (user: any) => {
  // 需要有user:update权限
  if (!userStore.hasPermission('user:update')) return false
  
  // 不能修改超级用户
  if (user.is_superuser) return false
  
  // 不能修改自己
  if (user.id === userStore.userInfo?.id) return false
  
  // 只有管理员可以修改
  const currentUser = userStore.userInfo
  return currentUser?.is_superuser || currentUser?.user_type === 'admin'
}

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    }
    
    // 清理空参数
    Object.keys(params).forEach(key => {
      if (params[key] === '') {
        delete params[key]
      }
    })
    
    const response = await userApi.getUserList(params)
    const data = response.data
    
    tableData.value = data.items
    pagination.total = data.total
  } catch (error: any) {
    console.error('获取用户列表失败:', error)
    ElMessage.error(error.response?.data?.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchUsers()
}

// 重置搜索
const handleReset = () => {
  Object.assign(searchForm, {
    employee_id: '',
    username: '',
    user_type: ''
  })
  handleSearch()
}

// 新增用户
const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 编辑用户
const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

// 编辑用户类型
const handleEditUserType = (row: any) => {
  selectedUser.value = { ...row }
  newUserType.value = ''
  userTypeDialogVisible.value = true
}

// 更新用户类型
const handleUpdateUserType = async () => {
  if (!newUserType.value) {
    ElMessage.warning('请选择新的用户类型')
    return
  }
  
  updateTypeLoading.value = true
  try {
    await userApi.updateUserType(selectedUser.value.id, newUserType.value)
    ElMessage.success('用户类型修改成功')
    userTypeDialogVisible.value = false
    await fetchUsers()
  } catch (error: any) {
    console.error('修改用户类型失败:', error)
    ElMessage.error(error.response?.data?.message || '修改用户类型失败')
  } finally {
    updateTypeLoading.value = false
  }
}

// 删除用户
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await userApi.deleteUser(row.id)
    ElMessage.success('用户删除成功')
    await fetchUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error(error.response?.data?.message || '删除用户失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    if (isEdit.value) {
      ElMessage.info('编辑用户功能待开发')
    } else {
      ElMessage.info('新增用户功能待开发')
    }
    
    dialogVisible.value = false
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: 0,
    employee_id: '',
    username: '',
    password: '',
  })
}

// 关闭对话框
const handleCloseDialog = () => {
  resetForm()
  dialogVisible.value = false
}

// 分页相关
const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  pagination.page = 1
  fetchUsers()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  fetchUsers()
}

// 页面加载时获取数据
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management {
  padding: 0;
}
.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}
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

.dialog-footer {
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-bar .el-form {
    display: block;
  }
  
  .search-bar .el-form-item {
    margin-bottom: 10px;
  }
}
</style> 