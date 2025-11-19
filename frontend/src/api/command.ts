/**
 * 命令行集API接口
 */
import api from './index'

// 命令行相关接口类型定义
export interface Command {
  id: number
  command_text: string
  link?: string
  view?: string
  description?: string
  notice?: string
  param_ranges?: any[]
  remarks?: string
  creator: string
  last_editor?: string
  created_at: string
  updated_at: string
}

export interface CommandListItem {
  id: number
  command_text: string
  view?: string
  description?: string
  last_editor?: string
  updated_at: string
}

export interface CommandCreateRequest {
  command_text: string
  link?: string
  remarks?: string
}

export interface CommandUpdateRequest {
  command_text?: string
  link?: string
  view?: string
  description?: string
  notice?: string
  param_ranges?: any[]
  remarks?: string
}

export interface CommandSearchParams {
  page?: number
  page_size?: number
  command_keyword?: string
  description_keyword?: string
  remarks_keyword?: string
}

export interface CommandListResponse {
  items: CommandListItem[]
  total: number
  page: number
  page_size: number
}

// 命令行集API
export const commandApi = {
  // 获取命令行列表
  getCommands: (params?: CommandSearchParams) => {
    return api.get<CommandListResponse>('/commands/', { params })
  },

  // 创建命令行
  createCommand: (data: CommandCreateRequest) => {
    return api.post<Command>('/commands/', data)
  },

  // 获取命令行详情
  getCommand: (id: number) => {
    return api.get<Command>(`/commands/${id}`)
  },

  // 更新命令行信息
  updateCommand: (id: number, data: CommandUpdateRequest) => {
    return api.put<Command>(`/commands/${id}`, data)
  },

  // 删除命令行
  deleteCommand: (id: number) => {
    return api.delete(`/commands/${id}`)
  },

  // 导入命令行（xlsx）
  importCommands: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/commands/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取命令行操作日志
  getCommandOperationLogs: (params?: {
    page?: number
    page_size?: number
    employee_id?: string
  }) => {
    return api.get('/commands/operation-logs', { params })
  }
}
