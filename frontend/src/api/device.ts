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
  start_time: string
  occupied_duration?: number
  is_current_user_in_queue?: boolean
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

export interface DeviceCancelQueueRequest {
  device_id: number
}

export interface DevicePreemptRequest {
  device_id: number
  user: string
  expected_duration?: number
  purpose?: string
}

export interface DevicePriorityQueueRequest {
  device_id: number
  user: string
  expected_duration?: number
  purpose?: string
}

export interface DeviceUnifiedQueueRequest {
  device_id: number
  user: string
  expected_duration?: number
  purpose?: string
}

export interface BaseResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface DeviceSearchParams {
  page?: number
  page_size?: number
  name?: string
  ip?: string
  status?: string
}

export interface DeviceListResponse {
  items: DeviceListItem[]
  total: number
  page: number
  page_size: number
}

// 设备管理API
export const deviceApi = {
  // 获取设备列表
  getDevices: (params?: DeviceSearchParams) => {
    return api.get<DeviceListResponse>('/devices/', { params })
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

  // 取消排队
  cancelQueue: (data: DeviceCancelQueueRequest) => {
    return api.post('/devices/cancel-queue', data)
  },

  // 获取设备使用情况
  getDeviceUsage: (deviceId: number) => {
    return api.get(`/devices/${deviceId}/usage`)
  },

  // 抢占设备
  preemptDevice: (data: DevicePreemptRequest) => {
    return api.post('/devices/preempt', data)
  },

  // 优先排队
  priorityQueue: (data: DevicePriorityQueueRequest) => {
    return api.post('/devices/priority-queue', data)
  },

  // 统一排队
  unifiedQueue: (data: DeviceUnifiedQueueRequest) => {
    return api.post('/devices/unified-queue', data)
  },

  // 批量释放我的设备
  batchReleaseMyDevices: () => {
    return api.post('/devices/batch-release-my-devices')
  },

  // 批量取消我的排队
  batchCancelMyQueues: () => {
    return api.post('/devices/batch-cancel-my-queues')
  }
}