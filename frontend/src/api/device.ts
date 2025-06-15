/**
 * 设备管理API接口
 */
import api from './index'

// 设备相关接口类型定义
export interface Device {
  id: number
  name: string
  ip: string
  required_vpn: string
  creator: string
  need_vpn_login: boolean
  support_queue: boolean
  owner: string
  device_type: string
  remarks?: string
  created_at: string
  updated_at: string
}

export interface DeviceListItem {
  id: number
  name: string
  ip: string
  device_type: string
  current_user?: string
  queue_count: number
  status: string
  occupied_duration: number
}

export interface DeviceCreateRequest {
  name: string
  ip: string
  required_vpn: string
  creator: string
  need_vpn_login: boolean
  support_queue: boolean
  owner: string
  device_type: string
  remarks?: string
}

export interface DeviceUseRequest {
  device_id: number
  user: string
  expected_duration: number
  purpose?: string
}

export interface DeviceReleaseRequest {
  device_id: number
  user: string
}

// 设备管理API
export const deviceApi = {
  // 获取设备列表
  getDevices: () => {
    // let ret =  api.get<DeviceListItem[]>('/devices/')
    let ret =  api.get('/devices/')
    console.log(ret)
    return ret
  },

  // 创建设备
  createDevice: (data: DeviceCreateRequest) => {
    return api.post<Device>('/devices/', data)
  },

  // 获取设备详情
  getDevice: (id: number) => {
    return api.get<Device>(`/devices/${id}`)
  },

  // 更新设备信息
  updateDevice: (id: number, data: Partial<DeviceCreateRequest>) => {
    return api.put<Device>(`/devices/${id}`, data)
  },

  // 删除设备
  deleteDevice: (id: number) => {
    return api.delete(`/devices/${id}`)
  },

  // 使用设备
  useDevice: (data: DeviceUseRequest) => {
    return api.post('/devices/use', data)
  },

  // 释放设备
  releaseDevice: (data: DeviceReleaseRequest) => {
    return api.post('/devices/release', data)
  },

  // 获取设备使用情况
  getDeviceUsage: (deviceId: number) => {
    return api.get(`/devices/${deviceId}/usage`)
  }
} 