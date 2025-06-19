/**
 * Vue Router路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import type { RouteRecordRaw } from 'vue-router'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: {
      requiresAuth: false,
      title: '用户登录'
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: {
      requiresAuth: false,
      title: '用户注册'
    }
  },
  {
    path: '/',
    component: () => import('@/layout/LayoutView.vue'),
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          requiresAuth: true,
          title: '主页'
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: {
          requiresAuth: true,
          title: '个人中心'
        }
      },
      {
        path: 'devices',
        name: 'DeviceManagement',
        component: () => import('@/views/DeviceManagement.vue'),
        meta: {
          requiresAuth: true,
          permission: 'device:read',
          title: '设备管理'
        }
      },
      {
        path: 'system/users',
        name: 'UserManagement',
        component: () => import('@/views/system/UserManagement.vue'),
        meta: {
          requiresAuth: true,
          permission: 'user:read',
          title: '用户管理'
        }
      },
      {
        path: 'system/roles',
        name: 'RoleManagement',
        component: () => import('@/views/system/RoleManagement.vue'),
        meta: {
          requiresAuth: true,
          permission: 'role:read',
          title: '角色管理'
        }
      },
      {
        path: 'system/permissions',
        name: 'PermissionManagement',
        component: () => import('@/views/system/PermissionManagement.vue'),
        meta: {
          requiresAuth: true,
          permission: 'permission:read',
          title: '权限管理'
        }
      },
      {
        path: 'system/menus',
        name: 'MenuManagement',
        component: () => import('@/views/system/MenuManagement.vue'),
        meta: {
          requiresAuth: true,
          permission: 'menu:read',
          title: '菜单管理'
        }
      },
      {
        path: 'system/logs',
        name: 'LoginLogs',
        component: () => import('@/views/system/LoginLogs.vue'),
        meta: {
          requiresAuth: true,
          permission: 'system:log',
          title: '登录日志'
        }
      }
    ]
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: {
      requiresAuth: false,
      title: '页面不存在'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - crTools后台管理系统`
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      ElMessage.warning('请先登录')
      next('/login')
      return
    }
    
    // 检查权限
    if (to.meta.permission) {
      if (!userStore.hasPermission(to.meta.permission as string)) {
        // ElMessage.error('权限不足')
        next('/dashboard')
        return
      }
    }
  } else {
    // 如果是登录页面且已经登录，重定向到首页
    if ((to.path === '/login' || to.path === '/register') && userStore.isLoggedIn) {
      next('/dashboard')
      return
    }
  }
  
  next()
})

// 全局后置守卫
router.afterEach(() => {
  // 可以在这里添加页面加载完成后的逻辑
})

export default router