<template>
  <div class="user-management">
    <el-tabs v-model="activeTab" class="user-tabs">
      <el-tab-pane label="用户列表" name="users">
        <el-card shadow="never">
          <!-- 页面标题 -->
          <template #header>
            <div class="card-header">
              <span>用户管理</span>
              <el-button type="primary" @click="handleAdd" v-if="userStore.hasPermission('user:create')">
                <el-icon>
                  <Plus />
                </el-icon>
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
                <el-select v-model="searchForm.role_name" placeholder="请选择角色" clearable style="width: 130px">
                  <el-option v-for="option in roleOptions" :key="option.value" :label="option.label"
                    :value="option.value" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSearch">
                  <el-icon>
                    <Search />
                  </el-icon>
                  搜索
                </el-button>
                <el-button @click="handleReset">
                  <el-icon>
                    <Refresh />
                  </el-icon>
                  重置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 数据表格 -->
          <el-table :data="tableData" stripe v-loading="loading">
            <el-table-column prop="employee_id" label="工号" />
            <el-table-column prop="username" label="姓名" />
            <el-table-column label="角色">
              <template #default="{ row }">
                <el-tag :type="getRoleTagType(row.role)" size="small">
                  {{ row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="所属分组" min-width="200">
              <template #default="{ row }">
                <div v-if="row.groups?.length" class="group-tags">
                  <el-tag v-for="group in row.groups" :key="group.id" type="info" size="small" class="group-tag">
                    {{ group.name }}
                  </el-tag>
                </div>
                <span v-else class="no-data">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="260">
              <template #default="{ row }">
                <el-button size="small" @click="handleEdit(row)" :disabled="row.is_superuser"
                  v-if="userStore.hasPermission('user:update')">
                  编辑
                </el-button>
                <el-button size="small" type="success" @click="openUserGroupDialog(row)"
                  v-if="userStore.hasPermission('user:update')">
                  分组
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)"
                  :disabled="row.is_superuser || row.id === userStore.userInfo?.id"
                  v-if="userStore.hasPermission('user:delete')">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
              :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper" :total="pagination.total"
              @size-change="handleSizeChange" @current-change="handleCurrentChange" />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="分组管理" name="groups">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>分组管理</span>
              <el-button type="primary" size="small" @click="openGroupDialog()"
                v-if="userStore.hasPermission('user:update')">
                <el-icon>
                  <Plus />
                </el-icon>
                新增分组
              </el-button>
            </div>
          </template>

          <el-empty v-if="groupList.length === 0" description="暂无分组" />
          <el-collapse v-else class="group-collapse">
            <el-collapse-item v-for="group in groupList" :key="group.id" :name="group.id">
              <template #title>
                <div class="group-title">
                  <span class="group-name">{{ group.name }}</span>
                  <span class="group-meta">成员 {{ group.member_count }}</span>
                  <div class="group-actions" v-if="userStore.hasPermission('user:update')">
                    <el-button text type="primary" size="small" @click.stop="openGroupMemberDialog(group)">
                      新增成员
                    </el-button>
                    <el-button text type="primary" size="small" @click.stop="openGroupDialog(group)">
                      编辑
                    </el-button>
                    <el-button text type="danger" size="small" @click.stop="confirmDeleteGroup(group)">
                      删除
                    </el-button>
                  </div>
                </div>
              </template>

              <div class="group-body">
                <p class="group-description" v-if="group.description">{{ group.description }}</p>
                <div v-if="group.members?.length" class="group-members">
                  <div class="group-members-toolbar" v-if="userStore.hasPermission('user:update')">
                    <el-button type="danger" size="small" :disabled="!(selectedGroupMemberIds[group.id]?.length)"
                      :loading="!!removingGroupMembers[group.id]" @click.stop="confirmRemoveMembers(group)">
                      删除成员
                    </el-button>
                  </div>
                  <el-table :data="group.members" stripe size="small" class="group-members-table"
                    @selection-change="(selection: any[]) => onGroupMemberSelectionChange(group.id, selection)">
                    <el-table-column type="selection" width="44" />
                    <el-table-column prop="username" label="姓名" min-width="120" />
                    <el-table-column prop="employee_id" label="工号" min-width="120" />
                    <el-table-column label="角色" min-width="120">
                      <template #default="{ row }">
                        <el-tag :type="getRoleTagType(row.role)" size="small">
                          {{ row.role }}
                        </el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无成员" />
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑用户角色对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑用户角色" width="400px">
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
            <el-option v-for="option in roleOptions" :key="option.value" :label="option.label" :value="option.value" />
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

    <!-- 用户分组管理对话框 -->
    <el-dialog v-model="userGroupDialogVisible"
      :title="currentUserForGroups?.username ? `管理 ${currentUserForGroups.username} 的分组` : '管理分组'" width="500px">
      <el-form label-width="90px">
        <el-form-item label="所属分组">
          <el-select v-model="userGroupSelection" multiple filterable placeholder="请选择分组" style="width: 100%">
            <el-option v-for="group in groupList" :key="group.id" :label="group.name" :value="group.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userGroupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveUserGroups" :loading="userGroupSaving">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分组新增成员对话框 -->
    <el-dialog v-model="groupMemberDialogVisible"
      :title="selectedGroupForMembers ? `向 ${selectedGroupForMembers.name} 添加成员` : '添加分组成员'" width="500px">
      <el-form label-width="90px">
        <el-form-item label="选择用户">
          <el-select v-model="groupMemberSelection" multiple filterable :loading="userOptionsLoading"
            placeholder="请选择要加入的用户" style="width: 100%">
            <el-option v-for="user in userOptions" :key="user.id" :label="`${user.username} (${user.employee_id})`"
              :value="user.id" :disabled="selectedGroupForMembers?.members?.some(member => member.id === user.id)" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="groupMemberDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAddMembersToGroup" :loading="addingGroupMembers">
            添加
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分组创建/编辑对话框 -->
    <el-dialog v-model="groupDialogVisible" :title="isEditingGroup ? '编辑分组' : '新增分组'" width="400px">
      <el-form :model="groupForm" label-width="90px">
        <el-form-item label="分组名称" required>
          <el-input v-model="groupForm.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="3" placeholder="请输入分组描述" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="groupForm.sort_order" :min="0" :max="9999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="groupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveGroup" :loading="groupSaving">
            {{ isEditingGroup ? '更新' : '创建' }}
          </el-button>
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
import { getUserList, updateUserRole, deleteUser, ROLE_OPTIONS, getRoleTagType, getGroupList, createGroup, updateGroup, deleteGroup, updateUserGroups, addGroupMembers, removeGroupMembers, type GroupItem } from '@/api/user'

const userStore = useUserStore()

const activeTab = ref('users')

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

// 分组管理
const groupList = ref<GroupItem[]>([])
const groupDialogVisible = ref(false)
const isEditingGroup = ref(false)
const groupForm = reactive({
  id: null as number | null,
  name: '',
  description: '',
  sort_order: 0
})
const groupSaving = ref(false)

const userGroupDialogVisible = ref(false)
const currentUserForGroups = ref<any>(null)
const userGroupSelection = ref<number[]>([])
const userGroupSaving = ref(false)
const groupMemberDialogVisible = ref(false)
const selectedGroupForMembers = ref<GroupItem | null>(null)
const groupMemberSelection = ref<number[]>([])
const userOptions = ref<any[]>([])
const userOptionsLoading = ref(false)
const addingGroupMembers = ref(false)
const selectedGroupMemberIds = reactive<Record<number, number[]>>({})
const removingGroupMembers = reactive<Record<number, boolean>>({})

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

const fetchGroupList = async () => {
  try {
    const response = await getGroupList()
    groupList.value = response.data || []
  } catch (error) {
    console.error('获取分组列表错误:', error)
    ElMessage.error('获取分组列表失败')
  }
}

const fetchUserOptions = async () => {
  userOptionsLoading.value = true
  try {
    const response = await getUserList({
      page: 1,
      page_size: 100
    })
    userOptions.value = response.data.items || []
  } catch (error) {
    console.error('获取用户列表错误:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    userOptionsLoading.value = false
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

    await deleteUser(row.id)
    ElMessage.success('删除用户成功')
    fetchUserList()
    fetchGroupList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户错误:', error)
      ElMessage.error('删除用户失败')
    }
  }
}

const openGroupDialog = (group?: GroupItem) => {
  if (group) {
    groupForm.id = group.id
    groupForm.name = group.name
    groupForm.description = group.description || ''
    groupForm.sort_order = group.sort_order || 0
    isEditingGroup.value = true
  } else {
    groupForm.id = null
    groupForm.name = ''
    groupForm.description = ''
    groupForm.sort_order = 0
    isEditingGroup.value = false
  }
  groupDialogVisible.value = true
}

const handleSaveGroup = async () => {
  if (!groupForm.name.trim()) {
    ElMessage.error('请输入分组名称')
    return
  }
  groupSaving.value = true
  try {
    if (isEditingGroup.value && groupForm.id) {
      await updateGroup(groupForm.id, {
        name: groupForm.name,
        description: groupForm.description,
        sort_order: groupForm.sort_order
      })
      ElMessage.success('分组更新成功')
    } else {
      await createGroup({
        name: groupForm.name,
        description: groupForm.description,
        sort_order: groupForm.sort_order
      })
      ElMessage.success('分组创建成功')
    }
    groupDialogVisible.value = false
    fetchGroupList()
  } catch (error: any) {
    console.error('保存分组失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('保存分组失败')
    }
  } finally {
    groupSaving.value = false
  }
}

const confirmDeleteGroup = async (group: GroupItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除分组「${group.name}」吗？该操作不可恢复`,
      '删除分组',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
    await deleteGroup(group.id)
    ElMessage.success('分组删除成功')
    fetchGroupList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分组失败:', error)
      ElMessage.error('删除分组失败')
    }
  }
}

const openGroupMemberDialog = async (group: GroupItem) => {
  selectedGroupForMembers.value = group
  groupMemberSelection.value = []
  await fetchUserOptions()
  groupMemberDialogVisible.value = true
}

const handleAddMembersToGroup = async () => {
  if (!selectedGroupForMembers.value) return
  if (!groupMemberSelection.value.length) {
    ElMessage.error('请选择要添加的用户')
    return
  }
  addingGroupMembers.value = true
  try {
    await addGroupMembers(selectedGroupForMembers.value.id, groupMemberSelection.value)
    ElMessage.success('已添加到分组')
    groupMemberDialogVisible.value = false
    await fetchGroupList()
    await fetchUserList()
  } catch (error: any) {
    console.error('添加分组成员失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('添加分组成员失败')
    }
  } finally {
    addingGroupMembers.value = false
  }
}

const openUserGroupDialog = (row: any) => {
  currentUserForGroups.value = row
  userGroupSelection.value = row.groups?.map((group: any) => group.id) || []
  userGroupDialogVisible.value = true
}

const handleSaveUserGroups = async () => {
  if (!currentUserForGroups.value) return
  userGroupSaving.value = true
  try {
    await updateUserGroups(currentUserForGroups.value.id, userGroupSelection.value)
    ElMessage.success('用户分组已更新')
    userGroupDialogVisible.value = false
    await fetchUserList()
    await fetchGroupList()
  } catch (error: any) {
    console.error('更新用户分组失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('更新用户分组失败')
    }
  } finally {
    userGroupSaving.value = false
  }
}

const onGroupMemberSelectionChange = (groupId: number, selection: any[]) => {
  selectedGroupMemberIds[groupId] = (selection || []).map(member => member.id)
}

const confirmRemoveMembers = async (group: GroupItem) => {
  const userIds = selectedGroupMemberIds[group.id] || []
  if (!userIds.length) return

  try {
    await ElMessageBox.confirm(
      `确定要从分组「${group.name}」移除选中的 ${userIds.length} 个成员吗？`,
      '删除成员',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )

    removingGroupMembers[group.id] = true
    await removeGroupMembers(group.id, userIds)
    ElMessage.success('成员已移除')
    selectedGroupMemberIds[group.id] = []
    await fetchGroupList()
    await fetchUserList()
  } catch (error: any) {
    if (error === 'cancel') return
    console.error('删除分组成员失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('删除分组成员失败')
    }
  } finally {
    removingGroupMembers[group.id] = false
  }
}

// 新增用户（待实现）
const handleAdd = () => {
  ElMessage.info('新增用户功能待实现')
}

// 初始化
onMounted(() => {
  fetchUserList()
  fetchGroupList()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.user-tabs {
  --el-tabs-header-margin: 0 0 16px 0;
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

.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.group-tag {
  margin-bottom: 4px;
}

.no-data {
  color: #909399;
  font-size: 13px;
}

.group-collapse {
  margin-top: 10px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.group-name {
  font-weight: 600;
}

.group-meta {
  font-size: 12px;
  color: #909399;
}

.group-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.group-body {
  padding: 8px 0;
}

.group-description {
  margin-bottom: 10px;
  color: #666;
}

.group-members {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-members-toolbar {
  display: flex;
  justify-content: flex-end;
}

.group-members-table {
  width: 100%;
}
</style>
