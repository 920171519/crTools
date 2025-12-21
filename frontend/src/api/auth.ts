/**
 * 认证相关API接口
 */
import api from "./index";

// 用户注册接口
export const register = (userData: {
  employee_id: string;
  username: string;
  password: string;
}) => {
  return api.post("/auth/register", userData);
};

// 用户登录接口
export const login = (loginData: { employee_id: string; password: string }) => {
  return api.post("/auth/login", loginData);
};

// 用户登出接口
export const logout = () => {
  return api.post("/auth/logout");
};

// 获取当前用户信息
export const getCurrentUser = () => {
  return api.get("/auth/me");
};

// 修改密码
export const changePassword = (passwordData: {
  old_password: string;
  new_password: string;
}) => {
  return api.post("/auth/change-password", passwordData);
};

// 获取用户权限
export const getUserPermissions = () => {
  return api.get("/auth/permissions");
};

// 获取用户菜单
export const getUserMenus = () => {
  return api.get("/auth/menus");
};
