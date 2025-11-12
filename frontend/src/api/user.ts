/**
 * 用户管理相关API接口
 */
import api from './index'

export interface UserGroupSummary {
  id: number
  name: string
  description?: string
}

export interface GroupMember {
  id: number
  employee_id: string
  username: string
  is_superuser: boolean
  role: string
}

export interface GroupItem {
  id: number
  name: string
  description?: string
  sort_order?: number
  member_count: number
  members: GroupMember[]
}

// 获取用户列表
export const getUserList = (params: {
  page?: number
  page_size?: number
  employee_id?: string
  username?: string
  role_name?: string
}) => {
  return api.get('/users/', { params })
}

// 更新用户角色
export const updateUserRole = (userId: number, newRole: string) => {
  return api.put(`/users/${userId}/role`, null, {
    params: { new_role_name: newRole }
  })
}

// 获取用户详情
export const getUserDetail = (userId: number) => {
  return api.get(`/users/${userId}`)
}

// 删除用户
export const deleteUser = (userId: number) => {
  return api.delete(`/users/${userId}`)
}

// 获取可用角色列表
export const getRoleList = () => {
  return api.get('/users/roles/list')
}

// 角色类型选项
export const ROLE_OPTIONS = [
  { label: '普通用户', value: '普通用户' },
  { label: '高级用户', value: '高级用户' },
  { label: '管理员', value: '管理员' }
]

// 获取角色标签
export const getRoleLabel = (role: string) => {
  const option = ROLE_OPTIONS.find(opt => opt.value === role)
  return option ? option.label : role
}

// 获取角色标签类型（用于el-tag的type属性）
export const getRoleTagType = (role: string) => {
  const typeMap: Record<string, string> = {
    '普通用户': '',
    '高级用户': 'warning',
    '管理员': 'danger',
    '超级管理员': 'success'
  }
  return typeMap[role] || ''
}

// 分组相关接口
export const getGroupList = () => {
  return api.get('/users/groups')
}

export const createGroup = (data: { name: string; description?: string; sort_order?: number }) => {
  return api.post('/users/groups', data)
}

export const updateGroup = (groupId: number, data: { name: string; description?: string; sort_order?: number }) => {
  return api.put(`/users/groups/${groupId}`, data)
}

export const deleteGroup = (groupId: number) => {
  return api.delete(`/users/groups/${groupId}`)
}

export const updateUserGroups = (userId: number, groupIds: number[]) => {
  return api.put(`/users/${userId}/groups`, {
    group_ids: groupIds
  })
}
