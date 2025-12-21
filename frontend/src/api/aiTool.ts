/**
 * AI 工具 API
 * 提供 AI 诊断相关的接口
 */
import api from "./index";

// 类型定义
export interface AIDiagnosisCreate {
  device_id: number;
  problem_description: string;
}

export interface AIDiagnosisResponse {
  id: number;
  device_id: number;
  device_ip: string;
  user_id: number;
  employee_id: string;
  username: string;
  problem_description: string;
  diagnosis_result: string | null;
  status: string;
  connectivity_status: boolean | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AIDiagnosisListItem {
  id: number;
  device_ip: string;
  username: string;
  problem_description: string;
  status: string;
  connectivity_status: boolean | null;
  created_at: string;
  completed_at: string | null;
}

export interface DiagnosisHistoryParams {
  page?: number;
  page_size?: number;
  device_ip?: string;
  status?: string;
}

// API 接口
export const aiToolApi = {
  /**
   * 创建 AI 诊断（非流式）
   */
  createDiagnosis(data: AIDiagnosisCreate) {
    return api.post("/ai-tool/diagnose", data);
  },

  /**
   * 创建 AI 诊断（流式输出）
   * 返回用于连接 SSE 的 URL
   */
  getDiagnosisStreamUrl(data: AIDiagnosisCreate): string {
    const params = new URLSearchParams({
      device_id: data.device_id.toString(),
      problem_description: data.problem_description,
    });
    const token = localStorage.getItem("crtools_token");
    if (token) {
      params.append("token", token);
    }
    return `/api/ai-tool/diagnose-stream?${params.toString()}`;
  },

  /**
   * 获取诊断历史列表
   */
  getDiagnosisHistory(params: DiagnosisHistoryParams) {
    return api.get("/ai-tool/history", { params });
  },

  /**
   * 获取诊断详情
   */
  getDiagnosisDetail(id: number) {
    return api.get(`/ai-tool/history/${id}`);
  },

  /**
   * 导出诊断结果
   */
  exportDiagnosis(id: number) {
    return api.get(`/ai-tool/export/${id}`, {
      responseType: "blob",
    });
  },

  /**
   * 删除诊断记录
   */
  deleteDiagnosis(id: number) {
    return api.delete(`/ai-tool/history/${id}`);
  },
};
