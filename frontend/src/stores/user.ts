/**
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

// 用户信息类型定义
export interface UserInfo {
  id: number
  employee_id: string
  username: string
  is_superuser: boolean
  roles: string[]
}

// 菜单项类型定义
export interface MenuItem {
  id: number
  name: string
  path: string
  component?: string
  icon?: string
  parent_id?: number
  sort_order: number
  children?: MenuItem[]
}

export const useUserStore = defineStore('user', () => {
  // 状态定义
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)
  const permissions = ref<string[]>([])
  const menus = ref<MenuItem[]>([])
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!userInfo.value)
  const isSuperUser = computed(() => userInfo.value?.is_superuser || false)
  
  // 用户登录
  const loginAction = async (loginData: { employee_id: string; password: string }) => {
    try {
      const response = await authApi.login(loginData)
      const { access_token, user } = response.data
      
      // 保存token和用户信息
      token.value = access_token
      userInfo.value = user
      
      // 保存到localStorage
      localStorage.setItem('crtools_token', access_token)
      localStorage.setItem('crtools_user', JSON.stringify(user))
      
      // 获取用户权限和菜单
      try {
        await fetchUserPermissions()
        await fetchUserMenus()
      } catch (error) {
        console.warn('获取权限或菜单失败:', error)
      }
      
      return response
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }
  
  // 用户注册
  const registerAction = async (userData: {
    employee_id: string
    username: string
    password: string
  }) => {
    try {
      const response = await authApi.register(userData)
      return response
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }
  
  // 用户登出
  const logout = async () => {
    try {
      // 调用登出API
      await authApi.logout()
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地状态
      token.value = ''
      userInfo.value = null
      permissions.value = []
      menus.value = []
      // 清除localStorage
      localStorage.removeItem('crtools_token')
      localStorage.removeItem('crtools_user')
    }
  }
  
  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await authApi.getCurrentUser()
      userInfo.value = response.data
      localStorage.setItem('crtools_user', JSON.stringify(response.data))
      return response
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }
  
  // 获取用户权限
  const fetchUserPermissions = async () => {
    try {
      const response = await authApi.getUserPermissions()
      permissions.value = response.data.permissions.map((p: any) => p.code)
      return response
    } catch (error) {
      console.error('获取用户权限失败:', error)
      throw error
    }
  }
  
  // 获取用户菜单
  const fetchUserMenus = async () => {
    try {
      const response = await authApi.getUserMenus()
      menus.value = response.data.menus
      return response
    } catch (error) {
      console.error('获取用户菜单失败:', error)
      throw error
    }
  }
  
  // 修改密码
  const changePassword = async (passwordData: { old_password: string; new_password: string }) => {
    try {
      const response = await authApi.changePassword(passwordData)
      return response
    } catch (error) {
      console.error('修改密码失败:', error)
      throw error
    }
  }
  
  // 检查权限
  const hasPermission = (permissionCode: string): boolean => {
    return isSuperUser.value || permissions.value.includes(permissionCode)
  }
  
  // 从localStorage恢复状态
  const restoreFromStorage = async () => {
    const savedToken = localStorage.getItem('crtools_token')
    const savedUser = localStorage.getItem('crtools_user')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        userInfo.value = JSON.parse(savedUser)
        // 恢复状态后重新获取权限和菜单
        try {
          await fetchUserPermissions()
          await fetchUserMenus()
        } catch (error) {
          console.warn('恢复状态时获取权限或菜单失败:', error)
        }
      } catch (error) {
        console.error('解析用户信息失败:', error)
        localStorage.removeItem('crtools_user')
      }
    }
  }
  
  // 初始化时恢复状态
  restoreFromStorage()
  
  return {
    // 状态
    token,
    userInfo,
    permissions,
    menus,
    
    // 计算属性
    isLoggedIn,
    isSuperUser,
    
    // 方法
    loginAction,
    registerAction,
    logout,
    fetchUserInfo,
    fetchUserPermissions,
    fetchUserMenus,
    changePassword,
    hasPermission,
    restoreFromStorage,
  }
}) 