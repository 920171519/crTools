<template>
  <div class="role-management">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="handleAdd" v-if="userStore.hasPermission('role:create')">
            <el-icon><Plus /></el-icon>
            新增角色
          </el-button>
        </div>
      </template>

      <!-- 角色表格 -->
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="name" label="角色名称" />
        <el-table-column prop="description" label="角色描述" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="handleEdit(row)"
              v-if="userStore.hasPermission('role:update')"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              v-if="userStore.hasPermission('role:delete')"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 角色表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑角色' : '新增角色'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px">
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            placeholder="请输入角色描述" 
            :rows="3"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
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

const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const tableData = ref([])

const form = reactive({
  id: 0,
  name: '',
  description: '',
})

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在2-50个字符', trigger: 'blur' }
  ]
}

const fetchRoles = async () => {
  loading.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 500)) // 模拟请求, 实际请求时, 需要调用后端接口
    tableData.value = [
      { id: 1, name: '超级管理员', description: '系统超级管理员', },
      { id: 2, name: '管理员', description: 'CMO', },
      { id: 3, name: '普通用户', description: '普通用户', }
    ]
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(form, { ...row })
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 "${row.name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    ElMessage.success('删除成功')
    fetchRoles()
  } catch {}
}

const handleSubmit = async () => {
  if (!formRef.value) {
    return
  }
  try {
    await formRef.value.validate()
    submitLoading.value = true
    await new Promise(resolve => setTimeout(resolve, 800)) // 模拟请求, 实际请求时, 需要调用后端接口
    ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
    dialogVisible.value = false
    fetchRoles()
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, { id: 0, name: '', description: ''})
  formRef.value?.resetFields()
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchRoles()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 