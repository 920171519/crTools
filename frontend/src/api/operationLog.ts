import api from './index'

export const operationLogApi = {
  // 获取操作日志列表
  getOperationLogs: (params: {
    page?: number
    page_size?: number
    employee_id?: string
    operation_type?: string
    start_date?: string
    end_date?: string
  }) => {
    return api.get('/operation-logs', { params })
  }
}
