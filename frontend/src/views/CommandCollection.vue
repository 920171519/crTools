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
          <el-form-item label="命令行">
            <el-input
              v-model="searchForm.command_keyword"
              placeholder="请输入命令内容关键词"
              clearable
              style="width: 250px"
            />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="searchForm.description_keyword"
              placeholder="请输入描述关键词"
              clearable
              style="width: 250px"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input
              v-model="searchForm.remarks_keyword"
              placeholder="请输入备注关键词"
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
      <el-button type="primary" icon="Plus" @click="openImportDialog">
        导入
      </el-button>
      <el-button icon="Refresh" @click="loadCommands">
        刷新
      </el-button>
    </div>

    <!-- 命令行列表 -->
    <el-card shadow="never">
      <el-table :data="commands" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="view" label="视图" width="150">
          <template #default="{ row }">
            <span>{{ row.view || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="command_text" label="cli" min-width="300">
          <template #default="{ row }">
            <div class="command-text">{{ row.command_text }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <div class="remarks-text">{{ row.description || '-' }}</div>
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

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialog" title="导入命令行（xlsx）" width="500px">
      <div>
        <el-upload
          class="upload-block"
          drag
          :show-file-list="true"
          :limit="1"
          :auto-upload="false"
          accept=".xlsx"
          :on-change="onFileChange"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将文件拖拽到此处，或<em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">仅支持 .xlsx 文件</div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showImportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleImport" :loading="importLoading">导入</el-button>
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
          <!-- 顶部地址 -->
          <div class="detail-url">
            <label>地址：</label>
            <a v-if="commandDetail.link" :href="commandDetail.link" target="_blank" class="detail-link">{{ commandDetail.link }}</a>
            <span v-else>-</span>
          </div>

          <!-- 注意事项 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              注意事项
            </h3>
            <div class="remarks">{{ commandDetail.notice || '暂无' }}</div>
          </div>

          <!-- 参数范围（表格） -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              参数范围
            </h3>
            <el-table :data="(commandDetail.param_ranges || []) as any[]" size="small" style="width: 100%">
              <el-table-column prop="name" label="参数" width="140" />
              <el-table-column prop="range" label="取值范围" />
              <el-table-column prop="desc" label="说明" />
            </el-table>
          </div>

          <!-- 备注 -->
          <div class="detail-section">
            <h3 class="section-title">
              <el-icon><InfoFilled /></el-icon>
              备注
            </h3>
            <div class="remarks">{{ commandDetail.remarks || '暂无' }}</div>
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
  Plus, Refresh, Search, Link, InfoFilled, Edit, UploadFilled
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
const showImportDialog = ref(false)
const importFile = ref<File | null>(null)
const importLoading = ref(false)

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
const openImportDialog = () => {
  importFile.value = null
  showImportDialog.value = true
}

const onFileChange = (file: any) => {
  const f = file.raw as File
  if (!f) return
  if (!f.name.toLowerCase().endsWith('.xlsx')) {
    ElMessage.error('只支持 .xlsx 文件')
    return
  }
  importFile.value = f
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

const handleImport = async () => {
  if (!importFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  try {
    importLoading.value = true
    const res = await commandApi.importCommands(importFile.value)
    ElMessage.success(res.message || '导入成功')
    showImportDialog.value = false
    await loadCommands()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.message || e?.response?.data?.detail || '导入失败')
  } finally {
    importLoading.value = false
  }
}

// 详情仍保留编辑按钮逻辑，无需导入相关表单

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
