/**
 * 用户管理相关API接口
 */
import api from './index'

// 获取用户列表
export const getUserList = (params: {
  page?: number
  page_size?: number
  employee_id?: string
  username?: string
  user_type?: string
}) => {
  return api.get('/users/', { params })
}

// 更新用户类型
export const updateUserType = (userId: number, newType: string) => {
  return api.put(`/users/${userId}/type`, null, {
    params: { new_type: newType }
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

// 用户类型选项
export const USER_TYPE_OPTIONS = [
  { label: '普通用户', value: 'normal' },
  { label: '高级用户', value: 'advanced' },
  { label: '管理员', value: 'admin' }
]

// 获取用户类型标签
export const getUserTypeLabel = (type: string) => {
  const option = USER_TYPE_OPTIONS.find(item => item.value === type)
  return option ? option.label : type
} 