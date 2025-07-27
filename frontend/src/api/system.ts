import api from './index'

export const systemApi = {
  // 获取系统设置
  getSettings: () => {
    return api.get('/system/settings')
  },

  // 更新系统设置
  updateSettings: (data: { cleanup_time: string | null }) => {
    return api.put('/system/settings', data)
  },

  // 手动清理所有设备
  manualCleanup: () => {
    return api.post('/devices/admin/force-cleanup-all')
  }
}
