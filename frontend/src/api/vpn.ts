import api from './index'

export interface VPNConfig {
  id: number
  region: string
  network: string
}

export interface VPNConfigCreate {
  region: string
  network: string
}

export interface VPNConfigUpdate {
  region?: string
  network?: string
}

export interface UserVPNConfig {
  id: number
  vpn_config_id: number
  vpn_region: string
  vpn_network: string
  ip_address?: string
}

export interface UserVPNConfigUpdate {
  ip_address?: string
}

export interface VPNSearchParams {
  page?: number
  page_size?: number
  region?: string
  network?: string
}

export interface VPNListResponse {
  items: VPNConfig[]
  total: number
  page: number
  page_size: number
}

// VPN配置管理API
export const vpnApi = {
  // 管理员VPN配置管理
  getVPNConfigs: (params?: VPNSearchParams) => {
    return api.get<VPNListResponse>('/vpn/configs', { params })
  },

  createVPNConfig: (data: VPNConfigCreate) => {
    return api.post('/vpn/configs', data)
  },

  updateVPNConfig: (id: number, data: VPNConfigUpdate) => {
    return api.put(`/vpn/configs/${id}`, data)
  },

  deleteVPNConfig: (id: number) => {
    return api.delete(`/vpn/configs/${id}`)
  },

  // 用户VPN IP配置管理
  getUserVPNConfigs: () => {
    return api.get<UserVPNConfig[]>('/vpn/user-configs')
  },

  updateUserVPNConfig: (vpnConfigId: number, data: UserVPNConfigUpdate) => {
    return api.put(`/vpn/user-configs/${vpnConfigId}`, data)
  }
}
