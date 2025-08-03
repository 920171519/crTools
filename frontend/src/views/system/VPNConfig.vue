<template>
  <div class="vpn-config-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>VPN配置管理</span>
        </div>
      </template>

      <!-- 搜索栏 -->
      <!-- <el-card shadow="never" style="margin-bottom: 20px;">
        <div class="search-bar">
          <el-form :model="searchForm" inline>
            <el-form-item label="地域">
              <el-input v-model="searchForm.region" placeholder="请输入地域" clearable />
            </el-form-item>
            <el-form-item label="网段">
              <el-input v-model="searchForm.network" placeholder="请输入网段" clearable />
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
      </el-card> -->

      <!-- 操作栏 -->
      <div class="action-bar">
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          添加VPN
        </el-button>
        <el-button @click="loadVPNConfigs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <!-- VPN配置列表 -->
      <el-table :data="vpnConfigs" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="region" label="地域" min-width="200" align="center"/>
        <el-table-column prop="network" label="网段" min-width="200" align="center"/>
        <el-table-column label="操作" min-width="200" align="center">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
              :loading="deleteLoading[row.id]"
            >
              <el-icon><Delete /></el-icon>
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
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="地域" prop="region">
          <el-input v-model="form.region" placeholder="请输入地域" />
        </el-form-item>
        <el-form-item label="网段" prop="network">
          <el-input v-model="form.network" placeholder="请输入网段" />
        </el-form-item>
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
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Refresh, Search, Edit, Delete } from '@element-plus/icons-vue'
import { vpnApi, VPNConfig, VPNConfigCreate, VPNConfigUpdate } from '@/api/vpn'

// 数据定义
const loading = ref(false)
const vpnConfigs = ref<VPNConfig[]>([])
const deleteLoading = reactive<Record<number, boolean>>({})
const submitLoading = ref(false)

// 搜索表单
const searchForm = reactive({
  region: '',
  network: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 对话框相关
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const editId = ref(0)

// 表单相关
const formRef = ref<FormInstance>()
const form = reactive({
  region: '',
  network: ''
})

const rules = {
  region: [
    { required: true, message: '请输入地域', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  network: [
    { required: true, message: '请输入网段', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ]
}

// 方法定义
const loadVPNConfigs = async () => {
  loading.value = true
  try {
    const response = await vpnApi.getVPNConfigs({
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    })
    vpnConfigs.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载VPN配置失败:', error)
    ElMessage.error('加载VPN配置失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadVPNConfigs()
}

// 重置搜索
const handleReset = () => {
  Object.assign(searchForm, {
    region: '',
    network: ''
  })
  pagination.page = 1
  loadVPNConfigs()
}

// 分页处理
const handleSizeChange = (val: number) => {
  pagination.page_size = val
  pagination.page = 1
  loadVPNConfigs()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  loadVPNConfigs()
}

// 打开添加对话框
const openAddDialog = () => {
  dialogTitle.value = '添加VPN配置'
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (row: VPNConfig) => {
  dialogTitle.value = '编辑VPN配置'
  isEdit.value = true
  editId.value = row.id
  Object.assign(form, {
    region: row.region,
    network: row.network
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    region: '',
    network: ''
  })
  formRef.value?.clearValidate()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    if (isEdit.value) {
      // 编辑
      const updateData: VPNConfigUpdate = {
        region: form.region,
        network: form.network
      }
      await vpnApi.updateVPNConfig(editId.value, updateData)
      ElMessage.success('更新VPN配置成功')
    } else {
      // 添加
      const createData: VPNConfigCreate = {
        region: form.region,
        network: form.network
      }
      await vpnApi.createVPNConfig(createData)
      ElMessage.success('创建VPN配置成功')
    }
    
    dialogVisible.value = false
    loadVPNConfigs()
  } catch (error: any) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除VPN配置
const handleDelete = async (row: VPNConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除VPN配置 "${row.region}-${row.network}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    deleteLoading[row.id] = true
    await vpnApi.deleteVPNConfig(row.id)
    ElMessage.success('删除成功')
    loadVPNConfigs()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  } finally {
    deleteLoading[row.id] = false
  }
}



// 生命周期
onMounted(() => {
  loadVPNConfigs()
})
</script>

<style scoped>
.vpn-config-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 0;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
