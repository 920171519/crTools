<template>
  <div class="profile-view">
    <!-- 基本信息卡片 -->
    <el-card style="margin-bottom: 20px;">
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

    <!-- VPN配置卡片 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>VPN配置</span>
          <el-button type="primary" size="small" @click="loadVPNConfigs">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      <div class="vpn-content" v-loading="vpnLoading">
        <el-table :data="vpnConfigs" stripe style="width: 100%">
          <el-table-column prop="vpn_region" label="地域" min-width="150" />
          <el-table-column prop="vpn_network" label="网段" min-width="150" />
          <el-table-column prop="ip_address" label="IP地址" min-width="200">
            <template #default="{ row }">
              <span v-if="!row.editing">{{ row.ip_address || '未配置' }}</span>
              <el-input
                v-else
                v-model="row.editValue"
                placeholder="请输入IP地址，如：192.168.1.100"
                size="small"
                @keyup.enter="saveVPNConfig(row)"
                @blur="handleInputBlur(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" align="center">
            <template #default="{ row }">
              <el-button
                v-if="!row.editing"
                type="primary"
                size="small"
                @click="startEdit(row)"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <div v-else>
                <el-button
                  type="success"
                  size="small"
                  @click="saveVPNConfig(row)"
                  :loading="row.saving"
                >
                  <el-icon><Check /></el-icon>
                  保存
                </el-button>
                <el-button
                  size="small"
                  @click="cancelEdit(row)"
                >
                  <el-icon><Close /></el-icon>
                  取消
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="vpnConfigs.length === 0 && !vpnLoading" class="empty-state">
          <el-empty description="暂无VPN配置" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { Refresh, Edit, Check, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { vpnApi, UserVPNConfig } from '@/api/vpn'

const userStore = useUserStore()

// 基本信息
const userInfo = computed(() => userStore.userInfo)

// VPN配置相关
const vpnLoading = ref(false)
const vpnConfigs = ref<(UserVPNConfig & { editing?: boolean; editValue?: string; saving?: boolean })[]>([])

// 加载VPN配置
const loadVPNConfigs = async () => {
  vpnLoading.value = true
  try {
    const response = await vpnApi.getUserVPNConfigs()
    vpnConfigs.value = response.data.map(config => ({
      ...config,
      editing: false,
      editValue: config.ip_address || '',
      saving: false
    }))
  } catch (error: any) {
    console.error('加载VPN配置失败:', error)
    ElMessage.error(error.response?.data?.message || '加载VPN配置失败')
  } finally {
    vpnLoading.value = false
  }
}

// IP地址验证函数
const isValidIP = (ip: string): boolean => {
  if (!ip) return true // 允许空值

  const ipRegex = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
  return ipRegex.test(ip)
}

// 开始编辑
const startEdit = (row: any) => {
  row.editing = true
  row.editValue = row.ip_address || ''
}

// 取消编辑
const cancelEdit = (row: any) => {
  row.editing = false
  row.editValue = row.ip_address || ''
}

// 处理输入框失焦（延迟取消编辑，避免与保存按钮冲突）
const handleInputBlur = (row: any) => {
  setTimeout(() => {
    if (row.editing && !row.saving) {
      cancelEdit(row)
    }
  }, 200)
}

// 保存VPN配置
const saveVPNConfig = async (row: any) => {
  if (row.saving) return

  // 验证IP地址格式
  if (row.editValue && !isValidIP(row.editValue)) {
    ElMessage.error('请输入有效的IP地址格式，如：192.168.1.100')
    return
  }

  try {
    row.saving = true
    await vpnApi.updateUserVPNConfig(row.vpn_config_id, {
      ip_address: row.editValue || null
    })

    // 更新本地数据
    row.ip_address = row.editValue
    row.editing = false

    ElMessage.success('VPN IP配置更新成功')
  } catch (error: any) {
    console.error('更新VPN配置失败:', error)
    ElMessage.error(error.response?.data?.message || '更新VPN配置失败')
  } finally {
    row.saving = false
  }
}



// 生命周期
onMounted(() => {
  loadVPNConfigs()
})
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

.vpn-content {
  padding: 0;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.upload-btn {
  margin-top: 16px;
  width: 120px;
}
</style>