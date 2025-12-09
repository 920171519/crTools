<template>
  <div class="vpn-config-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>VPN项配置与管理</span>
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
        <el-table-column prop="lns" label="LNS" min-width="160" align="center"/>
        <el-table-column prop="gw" label="网关" min-width="160" align="center"/>
        <el-table-column prop="ip" label="VPN IP" min-width="160" align="center"/>
        <el-table-column prop="mask" label="掩码" min-width="140" align="center"/>
        <el-table-column label="状态" min-width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getVpnStatus(row) ? 'success' : 'danger'">
              {{ getVpnStatus(row) ? '可用' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
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

    <!-- IP搜索功能区域 -->
    <el-card shadow="never" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>IP地址搜索</span>
        </div>
      </template>

      <!-- IP搜索输入区 -->
      <div class="ip-search-section">
        <div class="search-input-group">
          <el-input
            v-model="ipSearchValue"
            placeholder="输入IP地址搜索用户配置（支持部分匹配）"
            style="width: 350px; margin-right: 15px;"
            clearable
            @keyup.enter="handleIPSearch"
          />
          <el-button type="success" @click="handleIPSearch" :loading="ipSearchLoading">
            <el-icon><Search /></el-icon>
            搜索IP
          </el-button>
          <el-button v-if="ipSearchResults.length > 0" @click="clearIPSearch">
            <el-icon><Close /></el-icon>
            清除搜索
          </el-button>
        </div>
      </div>

      <!-- IP搜索结果 -->
      <div v-if="ipSearchResults.length > 0" class="search-results">
        <div class="results-header">
          <span class="results-count">搜索结果：共找到 {{ ipSearchResults.length }} 条记录</span>
        </div>
        <el-table :data="ipSearchResults" stripe style="width: 100%; margin-top: 15px;">
          <el-table-column prop="employee_id" label="用户工号" min-width="120" align="center" />
          <el-table-column prop="username" label="用户姓名" min-width="120" align="center" />
          <el-table-column prop="region" label="地域" min-width="120" align="center" />
          <el-table-column prop="network" label="网段" min-width="150" align="center" />
          <el-table-column prop="ip_address" label="IP地址" min-width="150" align="center" />
        </el-table>
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
        <el-form-item label="LNS" prop="lns">
          <el-input v-model="form.lns" placeholder="请输入LNS地址" />
        </el-form-item>
        <el-form-item label="网关" prop="gw">
          <el-input v-model="form.gw" placeholder="请输入网关地址" />
        </el-form-item>
        <el-form-item label="VPN IP" prop="ip">
          <el-input v-model="form.ip" placeholder="请输入VPN IP" />
        </el-form-item>
        <el-form-item label="掩码" prop="mask">
          <el-input v-model="form.mask" placeholder="例如 255.0.0.0" />
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
import { Plus, Refresh, Search, Edit, Delete, Close } from '@element-plus/icons-vue'
import { vpnApi, VPNConfig, VPNConfigCreate, VPNConfigUpdate, IPSearchResult } from '@/api/vpn'

// 数据定义
const loading = ref(false)
const vpnConfigs = ref<VPNConfig[]>([])
const deleteLoading = reactive<Record<number, boolean>>({})
const submitLoading = ref(false)

// IP搜索相关
const ipSearchValue = ref('')
const ipSearchLoading = ref(false)
const ipSearchResults = ref<IPSearchResult[]>([])

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
  network: '',
  lns: '',
  gw: '',
  ip: '',
  mask: ''
})

const getVpnStatus = (config: VPNConfig) => {
  return !!config.status
}

const rules = {
  region: [
    { required: true, message: '请输入地域', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  network: [
    { required: true, message: '请输入网段', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  lns: [
    { required: true, message: '请输入LNS地址', trigger: 'blur' },
    { pattern: /^\d{1,3}(\.\d{1,3}){3}$/, message: '请输入正确的IP地址', trigger: 'blur' }
  ],
  gw: [
    { required: true, message: '请输入网关地址', trigger: 'blur' },
    { pattern: /^\d{1,3}(\.\d{1,3}){3}$/, message: '请输入正确的IP地址', trigger: 'blur' }
  ],
  ip: [
    { required: true, message: '请输入VPN IP', trigger: 'blur' },
    { pattern: /^\d{1,3}(\.\d{1,3}){3}$/, message: '请输入正确的IP地址', trigger: 'blur' }
  ],
  mask: [
    { required: true, message: '请输入掩码', trigger: 'blur' }
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
    network: row.network,
    lns: row.lns,
    gw: row.gw,
    ip: row.ip,
    mask: row.mask
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    region: '',
    network: '',
    lns: '',
    gw: '',
    ip: '',
    mask: ''
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
        network: form.network,
        lns: form.lns,
        gw: form.gw,
        ip: form.ip,
        mask: form.mask
      }
      await vpnApi.updateVPNConfig(editId.value, updateData)
      ElMessage.success('更新VPN配置成功')
    } else {
      // 添加
      const createData: VPNConfigCreate = {
        region: form.region,
        network: form.network,
        lns: form.lns,
        gw: form.gw,
        ip: form.ip,
        mask: form.mask
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



// IP搜索处理
const handleIPSearch = async () => {
  if (!ipSearchValue.value.trim()) {
    ElMessage.warning('请输入要搜索的IP地址')
    return
  }

  ipSearchLoading.value = true
  try {
    const response = await vpnApi.searchUserByIP(ipSearchValue.value.trim())
    ipSearchResults.value = response.data

    if (response.data.length === 0) {
      ElMessage.info('未找到匹配的用户配置')
    } else {
      ElMessage.success(`找到 ${response.data.length} 条匹配记录`)
    }
  } catch (error: any) {
    console.error('IP搜索失败:', error)
    ElMessage.error(error.response?.data?.message || 'IP搜索失败')
  } finally {
    ipSearchLoading.value = false
  }
}

// 清除IP搜索结果
const clearIPSearch = () => {
  ipSearchValue.value = ''
  ipSearchResults.value = []
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

.ip-search-section {
  margin-bottom: 20px;
}

.search-input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-results {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.results-header {
  margin-bottom: 10px;
}

.results-count {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
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
