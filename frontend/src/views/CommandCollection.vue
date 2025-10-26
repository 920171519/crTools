<template>
  <div class="command-collection">
    <div class="page-header">
      <h1>命令行集</h1>
      <p>保存和管理常用的 Linux 设备命令行</p>
    </div>

    <!-- 搜索栏 -->
    <el-card shadow="never" style="margin-bottom: 20px;">
      <div class="search-bar">
        <el-form :model="searchForm" inline>
          <el-form-item label="命令内容">
            <el-input
              v-model="searchForm.command_keyword"
              placeholder="请输入命令内容关键词"
              clearable
              style="width: 250px"
            />
          </el-form-item>
          <el-form-item label="备注内容">
            <el-input
              v-model="searchForm.remarks_keyword"
              placeholder="请输入备注内容关键词"
              clearable
              style="width: 250px"
            />
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
    </el-card>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" icon="Plus" @click="openAddDialog">
        添加命令行
      </el-button>
      <el-button icon="Refresh" @click="loadCommands">
        刷新
      </el-button>
    </div>

    <!-- 命令行列表 -->
    <el-card shadow="never">
      <el-table :data="commands" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="command_text" label="命令内容" min-width="300">
          <template #default="{ row }">
            <div class="command-text">{{ row.command_text }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="link" label="链接" width="150">
          <template #default="{ row }">
            <a
              v-if="row.link"
              :href="row.link"
              target="_blank"
              class="command-link"
            >
              <el-icon><Link /></el-icon>
              打开链接
            </a>
            <span v-else class="no-link">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="remarks" label="备注" min-width="200">
          <template #default="{ row }">
            <div class="remarks-text">{{ row.remarks || '-' }}</div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="info" size="small" @click="viewDetails(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[20, 50, 100]"
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

    <!-- 添加/编辑命令行对话框 -->
    <el-dialog
      v-model="showFormDialog"
      :title="isEditing ? '编辑命令行' : '添加命令行'"
      width="700px"
      :before-close="handleFormDialogClose"
    >
      <el-form
        ref="formRef"
        :model="commandForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="命令内容" prop="command_text">
          <el-input
            v-model="commandForm.command_text"
            type="textarea"
            :rows="3"
            placeholder="请输入命令内容（最多1000字符）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="链接" prop="link">
          <el-input
            v-model="commandForm.link"
            placeholder="请输入介绍网页链接（选填，最多1000字符）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="备注" prop="remarks">
          <el-input
            v-model="commandForm.remarks"
            type="textarea"
            :rows="5"
            placeholder="请输入备注内容（选填，最多5000字符）"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showFormDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmitForm"
            :loading="submitLoading"
          >
            {{ isEditing ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 命令行详情抽屉 -->
    <el-drawer
      v-model="showDetailDrawer"
      title="命令行详情"
      direction="rtl"
      size="600px"
      :before-close="handleDetailDrawerClose"
    >
      <div v-loading="detailLoading" class="command-detail">
        <template v-if="commandDetail">
          <div class="detail-section">
            <div class="section-header">
              <h3 class="section-title">
                <el-icon><InfoFilled /></el-icon>
                基本信息
              </h3>
              <el-button
                type="primary"
                size="small"
                plain
                @click="toggleEditMode"
                class="edit-button"
              >
                <el-icon><Edit /></el-icon>
                {{ isEditMode ? '取消编辑' : '编辑' }}
              </el-button>
            </div>

            <div class="info-grid">
              <div class="info-item full-width">
                <label>命令内容：</label>
                <el-input
                  v-if="isEditMode"
                  v-model="editCommandForm.command_text"
                  type="textarea"
                  :rows="3"
                  maxlength="1000"
                  show-word-limit
                />
                <div v-else class="command-content">{{ commandDetail.command_text }}</div>
              </div>

              <div class="info-item full-width">
                <label>链接：</label>
                <el-input
                  v-if="isEditMode"
                  v-model="editCommandForm.link"
                  maxlength="1000"
                  show-word-limit
                />
                <a
                  v-else-if="commandDetail.link"
                  :href="commandDetail.link"
                  target="_blank"
                  class="detail-link"
                >
                  {{ commandDetail.link }}
                </a>
                <span v-else class="no-link">未设置</span>
              </div>

              <div class="info-item full-width">
                <label>备注：</label>
                <el-input
                  v-if="isEditMode"
                  v-model="editCommandForm.remarks"
                  type="textarea"
                  :rows="5"
                  maxlength="5000"
                  show-word-limit
                />
                <div v-else class="remarks">
                  {{ commandDetail.remarks || '暂无备注' }}
                </div>
              </div>

              <div class="info-item">
                <label>创建人：</label>
                <span>{{ commandDetail.creator }}</span>
              </div>

              <div class="info-item">
                <label>最后编辑人：</label>
                <span>{{ commandDetail.last_editor || '-' }}</span>
              </div>

              <div class="info-item">
                <label>创建时间：</label>
                <span>{{ formatDateTime(commandDetail.created_at) }}</span>
              </div>

              <div class="info-item">
                <label>更新时间：</label>
                <span>{{ formatDateTime(commandDetail.updated_at) }}</span>
              </div>
            </div>

            <!-- 编辑模式下的操作按钮 -->
            <div v-if="isEditMode" class="edit-actions">
              <el-button type="primary" @click="handleSaveEdit" :loading="saveLoading">
                保存
              </el-button>
              <el-button @click="toggleEditMode">取消</el-button>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Search, Link, InfoFilled, Edit
} from '@element-plus/icons-vue'
import { commandApi, type CommandListItem, type Command } from '../api/command'
import { useUserStore } from '@/stores/user'

// 获取用户store
const userStore = useUserStore()

// 数据定义
const loading = ref(false)
const commands = ref<CommandListItem[]>([])
const detailLoading = ref(false)
const submitLoading = ref(false)
const saveLoading = ref(false)

// 搜索表单
const searchForm = reactive({
  command_keyword: '',
  remarks_keyword: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框相关
const showFormDialog = ref(false)
const isEditing = ref(false)
const formRef = ref()
const commandForm = reactive({
  command_text: '',
  link: '',
  remarks: ''
})

const formRules = {
  command_text: [
    { required: true, message: '请输入命令内容', trigger: 'blur' }
  ]
}

// 抽屉相关
const showDetailDrawer = ref(false)
const commandDetail = ref<Command | null>(null)
const isEditMode = ref(false)
const editCommandForm = reactive({
  command_text: '',
  link: '',
  remarks: ''
})
const currentEditId = ref<number | null>(null)

// 计算属性
const currentUser = computed(() => userStore.userInfo?.username || '')
const currentUserEmployeeId = computed(() => userStore.userInfo?.employee_id?.toLowerCase() || '')
const isAdmin = computed(() => userStore.userInfo?.is_superuser || false)
const isAdminRole = computed(() => userStore.userInfo?.role === '管理员')

// 判断是否可以删除
const canDelete = (command: CommandListItem) => {
  // 管理员或超级管理员可以删除任何命令
  if (isAdmin.value || isAdminRole.value) {
    return true
  }
  // 创建人可以删除自己的命令（需要获取详细信息才能判断，这里先返回true，实际删除时会验证）
  return true
}

// 方法定义
const loadCommands = async () => {
  loading.value = true
  try {
    const response = await commandApi.getCommands({
      page: pagination.page,
      page_size: pagination.page_size,
      command_keyword: searchForm.command_keyword,
      remarks_keyword: searchForm.remarks_keyword
    })
    commands.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载命令行列表失败:', error)
    ElMessage.error('加载命令行列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadCommands()
}

// 重置搜索
const handleReset = () => {
  searchForm.command_keyword = ''
  searchForm.remarks_keyword = ''
  pagination.page = 1
  loadCommands()
}

// 分页大小改变
const handleSizeChange = (val: number) => {
  pagination.page_size = val
  pagination.page = 1
  loadCommands()
}

// 当前页改变
const handleCurrentChange = (val: number) => {
  pagination.page = val
  loadCommands()
}

// 打开添加对话框
const openAddDialog = () => {
  isEditing.value = false
  commandForm.command_text = ''
  commandForm.link = ''
  commandForm.remarks = ''
  showFormDialog.value = true
}

// 打开编辑对话框
const openEditDialog = (command: CommandListItem) => {
  isEditing.value = true
  currentEditId.value = command.id
  // 需要获取完整的命令详情
  loadCommandDetail(command.id, true)
}

// 加载命令详情
const loadCommandDetail = async (id: number, forEdit = false) => {
  detailLoading.value = true
  try {
    const response = await commandApi.getCommand(id)
    commandDetail.value = response.data
    
    if (forEdit) {
      // 用于编辑对话框
      commandForm.command_text = response.data.command_text
      commandForm.link = response.data.link || ''
      commandForm.remarks = response.data.remarks || ''
      showFormDialog.value = true
    } else {
      // 用于详情抽屉
      editCommandForm.command_text = response.data.command_text
      editCommandForm.link = response.data.link || ''
      editCommandForm.remarks = response.data.remarks || ''
    }
  } catch (error) {
    console.error('获取命令行详情失败:', error)
    ElMessage.error('获取命令行详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 查看详情
const viewDetails = async (command: CommandListItem) => {
  showDetailDrawer.value = true
  isEditMode.value = false
  await loadCommandDetail(command.id)
}

// 提交表单
const handleSubmitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitLoading.value = true

    if (isEditing.value && currentEditId.value) {
      // 更新命令行
      await commandApi.updateCommand(currentEditId.value, commandForm)
      ElMessage.success('命令行更新成功')
    } else {
      // 创建命令行
      await commandApi.createCommand(commandForm)
      ElMessage.success('命令行创建成功')
    }

    showFormDialog.value = false
    await loadCommands()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error(isEditing.value ? '更新命令行失败' : '创建命令行失败')
    }
  } finally {
    submitLoading.value = false
  }
}

// 关闭表单对话框
const handleFormDialogClose = () => {
  formRef.value?.resetFields()
  showFormDialog.value = false
}

// 切换编辑模式
const toggleEditMode = () => {
  if (isEditMode.value) {
    // 取消编辑，恢复原值
    if (commandDetail.value) {
      editCommandForm.command_text = commandDetail.value.command_text
      editCommandForm.link = commandDetail.value.link || ''
      editCommandForm.remarks = commandDetail.value.remarks || ''
    }
  }
  isEditMode.value = !isEditMode.value
}

// 保存编辑
const handleSaveEdit = async () => {
  if (!commandDetail.value) return

  try {
    saveLoading.value = true
    await commandApi.updateCommand(commandDetail.value.id, editCommandForm)
    ElMessage.success('命令行更新成功')
    
    // 重新加载详情
    await loadCommandDetail(commandDetail.value.id)
    isEditMode.value = false
    
    // 刷新列表
    await loadCommands()
  } catch (error: any) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('更新命令行失败')
    }
  } finally {
    saveLoading.value = false
  }
}

// 关闭详情抽屉
const handleDetailDrawerClose = () => {
  showDetailDrawer.value = false
  commandDetail.value = null
  isEditMode.value = false
}

// 删除命令行
const deleteCommand = async (command: CommandListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除命令 "${command.command_text.substring(0, 30)}..." 吗？此操作不可恢复！`,
      '删除命令行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await commandApi.deleteCommand(command.id)
    ElMessage.success('命令行删除成功')
    await loadCommands()
  } catch (error: any) {
    if (error === 'cancel') {
      return
    }

    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('删除命令行失败')
    }
  }
}

// 格式化时间
const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(async () => {
  await loadCommands()
})
</script>

<style scoped>
.command-collection {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
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

.command-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.remarks-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.command-link {
  color: #409eff;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

.command-link:hover {
  text-decoration: underline;
}

.no-link,
.no-editor {
  color: #c0c4cc;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 抽屉样式 */
.command-detail {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.edit-button {
  margin-left: auto;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.info-item.full-width {
  grid-column: 1 / -1;
  flex-direction: column;
}

.info-item label {
  font-weight: 500;
  color: #606266;
  min-width: 100px;
}

.command-content,
.remarks {
  background: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  width: 100%;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.detail-link:hover {
  text-decoration: underline;
}

.edit-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .command-collection {
    padding: 10px;
  }

  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }

  .action-buttons .el-button {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .command-detail {
    padding: 15px;
  }

  .detail-section {
    padding: 15px;
  }
}
</style>

