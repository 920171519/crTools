/**
 * 设备管理API接口
 */
import api from './index'

// 设备相关接口类型定义
export interface Device {
  id: number
  name: string
  ip: string
  vpn_config_id?: number
  vpn_region?: string
  vpn_network?: string
  vpn_display_name?: string
  creator: string
  ftp_prefix: boolean
  support_queue: boolean
  max_occupy_minutes?: number | null
  owner: string
  device_type: string
  form_type: string
  remarks?: string
  created_at: string
  updated_at: string
  username?: string
  password?: string
  admin_username?: string
  admin_password?: string
  connectivity_status?: boolean
  project_name?: string
  groups?: DeviceGroupSummary[]
}

export interface DeviceListItem {
  id: number
  name: string
  ip: string
  device_type: string
  form_type: string
  vpn_region?: string
  vpn_network?: string
  vpn_display_name?: string
  current_user?: string
  queue_count: number
  status: string
  start_time: string
  occupied_duration?: number
  is_current_user_in_queue?: boolean
  connectivity_status?: boolean
  last_connectivity_check?: string
  support_queue: boolean
  groups?: DeviceGroupSummary[]
  is_shared_user?: boolean
  has_pending_share_request?: boolean
  share_request_id?: number
  share_status?: string
}

export interface DeviceCreateRequest {
  name: string
  ip: string
  vpn_config_id?: number
  creator: string
  ftp_prefix: boolean
  support_queue: boolean
  max_occupy_minutes?: number | null
  owner: string
  device_type: string
  form_type: string
  remarks?: string
  group_ids?: number[]
}

export interface DeviceUseRequest {
  device_id: number
  user: string
}

export interface DeviceLongTermUseRequest {
  device_id: number
  user: string
  end_date: string
  purpose: string
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
  purpose?: string
}

export interface DevicePriorityQueueRequest {
  device_id: number
  user: string
  purpose?: string
}

export interface DeviceUnifiedQueueRequest {
  device_id: number
  user: string
  purpose?: string
}

export interface ConnectivityStatus {
  status: boolean
  last_check: string | null
  last_ping: string | null
  error?: string
}

export interface ConnectivityResponse {
  [deviceId: string]: ConnectivityStatus
}

export interface DeviceSharedUser {
  employee_id: string
  username: string
  approved_at?: string | null
}

export interface DeviceUsageDetail {
  id: number
  device_id: number
  current_user?: string
  start_time?: string | null
  is_long_term: boolean
  long_term_purpose?: string | null
  end_date?: string | null
  queue_users: string[]
  status: string
  occupied_duration: number
  queue_count: number
  updated_at?: string | null
  shared_users: DeviceSharedUser[]
  has_pending_share_request: boolean
  is_shared_user: boolean
  share_request_id?: number
  share_status?: string
}

// 设备配置相关接口类型定义
export interface DeviceConfig {
  id: number
  device_id: number
  config_param1: number
  config_param2: number
  config_value: string
  created_at: string
  updated_at: string
}

export interface DeviceConfigCreateRequest {
  config_param1: number
  config_param2: number
  config_value: string
}

export interface DeviceConfigUpdateRequest {
  config_param1: number
  config_param2: number
  config_value: string
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
  config_value?: string
}

export interface DeviceListResponse {
  items: DeviceListItem[]
  total: number
  page: number
  page_size: number
}

export interface DeviceGroupSummary {
  id: number
  name: string
  description?: string
}

export interface DeviceShareRequestPayload {
  device_id: number
  message?: string
}

export interface DeviceShareDecisionPayload {
  approve: boolean
  reason?: string
}

export interface DeviceShareRequestItem {
  id: number
  device_id: number
  device_name: string
  requester_employee_id: string
  requester_username: string
  status: string
  request_message?: string | null
  decision_reason?: string | null
  processed_by?: string | null
  processed_at?: string | null
  created_at?: string | null
}

export interface UsageSummaryItem {
  id: number
  name: string
  ip: string
  status: string
  owner: string
  current_user?: string | null
  share_message?: string
  occupied_duration?: number
  groups?: DeviceGroupSummary[]
  share_request_id?: number
}

export interface UsageSummaryResponse {
  occupied_devices: UsageSummaryItem[]
  shared_devices: UsageSummaryItem[]
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
    return api.get<DeviceUsageDetail>(`/devices/${deviceId}/usage`)
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
  },

  // 长时间占用设备
  longTermUseDevice: (data: DeviceLongTermUseRequest) => {
    return api.post('/devices/long-term-use', data)
  },

  // 获取设备连通性状态
  getDevicesConnectivityStatus: (deviceIds: number[]) => {
    const deviceIdsStr = deviceIds.join(',')
    return api.get<ConnectivityResponse>('/devices/connectivity-status', {
      params: { device_ids: deviceIdsStr }
    })
  },

  // 获取单个设备连通性状态
  getDeviceConnectivityStatus: (deviceId: number) => {
    return api.get(`/devices/${deviceId}/connectivity`)
  },

  // 获取连通性缓存信息（调试用）
  getConnectivityCacheInfo: () => {
    return api.get('/devices/connectivity-cache-info')
  },

  // 设备配置管理接口
  // 获取设备配置列表
  getDeviceConfigs: (deviceId: number) => {
    return api.get<DeviceConfig[]>(`/devices/${deviceId}/configs`)
  },

  // 创建设备配置
  createDeviceConfig: (deviceId: number, data: DeviceConfigCreateRequest) => {
    return api.post(`/devices/${deviceId}/configs`, data)
  },

  // 更新设备配置
  updateDeviceConfig: (deviceId: number, configId: number, data: DeviceConfigUpdateRequest) => {
    return api.put(`/devices/${deviceId}/configs/${configId}`, data)
  },

  // 一键导入设备全部配置
  importAllDeviceConfigs: (deviceId: number) => {
    return api.post(`/devices/${deviceId}/configs/import-all`)
  },

  // 删除设备配置
  deleteDeviceConfig: (deviceId: number, configId: number) => {
    return api.delete(`/devices/${deviceId}/configs/${configId}`)
  },

  // 申请共用
  requestShare: (data: DeviceShareRequestPayload) => {
    return api.post<DeviceShareRequestItem>('/devices/share-requests', data)
  },

  // 获取待处理共用申请
  getPendingShareRequests: () => {
    return api.get<DeviceShareRequestItem[]>('/devices/share-requests/pending')
  },

  // 处理共用申请
  decideShareRequest: (requestId: number, data: DeviceShareDecisionPayload) => {
    return api.post<DeviceShareRequestItem>(`/devices/share-requests/${requestId}/decision`, data)
  },

  // 取消共用申请/共用
  cancelShareRequest: (requestId: number) => {
    return api.post<DeviceShareRequestItem>(`/devices/share-requests/${requestId}/cancel`)
  },

  // 占用人/管理员剔除共用用户
  revokeSharedUser: (requestId: number) => {
    return api.post<DeviceShareRequestItem>(`/devices/share-requests/${requestId}/revoke`)
  },

  // 获取我的环境使用情况
  getMyUsageSummary: () => {
    return api.get<UsageSummaryResponse>('/devices/my-usage-summary')
  }
}
