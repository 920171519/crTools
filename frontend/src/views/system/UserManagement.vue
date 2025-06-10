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
          <el-form-item>
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 用户表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="employee_id" label="工号"  /> <!-- width="120" -->
        <el-table-column prop="username" label="姓名"  /> <!-- 不设置宽度,就可以让它平铺整个页面, 并且对齐 -->
        <el-table-column label="超级用户" >
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="warning" size="small">是</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
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
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              v-if="userStore.hasPermission('user:delete') && !row.is_superuser"
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  employee_id: '',
  username: '',
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

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 800))
    
    // 模拟数据
    const users = [
      {
        id: 1,
        employee_id: 'A12345678',
        username: '超级管理员',
        is_superuser: true,
      },
      {
        id: 2,
        employee_id: 'B12345679',
        username: '张三',
        is_superuser: false,
      }
    ]
    
    tableData.value = users
    pagination.total = users.length
  } catch (error) {
    ElMessage.error('获取用户列表失败')
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

// 删除用户
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.username}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    ElMessage.success('删除成功')
    fetchUsers()
  } catch {
    // 用户取消删除
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
    dialogVisible.value = false
    fetchUsers()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitLoading.value = false
  }
}

// 关闭对话框
const handleCloseDialog = () => {
  dialogVisible.value = false
  resetForm()
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: 0,
    employee_id: '',
    username: '',
    password: '',
  })
  formRef.value?.resetFields()
}

// 分页处理
const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  fetchUsers()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  fetchUsers()
}

// 格式化时间
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management {
  padding: 0;
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
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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