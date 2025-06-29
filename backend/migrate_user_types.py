#!/usr/bin/env python3
"""
数据迁移脚本：将user_type字段数据迁移到角色系统
运行此脚本前请确保数据库备份
"""
import asyncio
from tortoise import Tortoise
from models.admin import User, Role, UserRole
from database import TORTOISE_ORM


async def migrate_user_types():
    """迁移用户类型到角色系统"""
    print("开始迁移用户类型到角色系统...")
    
    # 获取所有用户
    users = await User.all()
    print(f"找到 {len(users)} 个用户需要迁移")
    
    # 获取角色
    roles = {}
    for role_name in ["普通用户", "高级用户", "管理员", "超级管理员"]:
        role = await Role.filter(name=role_name).first()
        if role:
            roles[role_name] = role
        else:
            print(f"警告: 未找到角色 {role_name}")
    
    migrated_count = 0
    
    for user in users:
        # 检查用户是否已经有角色
        existing_roles = await UserRole.filter(user=user).count()
        if existing_roles > 0:
            print(f"用户 {user.employee_id} 已有角色，跳过")
            continue
        
        # 根据用户类型和超级用户标志分配角色
        target_role = None
        
        if user.is_superuser:
            target_role = roles.get("超级管理员")
        elif hasattr(user, 'user_type'):
            # 如果用户类型字段仍然存在
            user_type = getattr(user, 'user_type', None)
            if user_type == 'admin':
                target_role = roles.get("管理员")
            elif user_type == 'advanced':
                target_role = roles.get("高级用户")
            elif user_type == 'normal':
                target_role = roles.get("普通用户")
        
        # 如果没有找到对应角色，默认分配普通用户角色
        if not target_role:
            target_role = roles.get("普通用户")
        
        if target_role:
            try:
                await UserRole.create(user=user, role=target_role)
                print(f"✅ 用户 {user.employee_id}({user.username}) 分配角色: {target_role.name}")
                migrated_count += 1
            except Exception as e:
                print(f"❌ 为用户 {user.employee_id} 分配角色失败: {e}")
        else:
            print(f"❌ 未找到用户 {user.employee_id} 的对应角色")
    
    print(f"\n迁移完成! 成功迁移 {migrated_count} 个用户")


async def verify_migration():
    """验证迁移结果"""
    print("\n开始验证迁移结果...")
    
    users = await User.all()
    no_role_users = []
    
    for user in users:
        user_roles = await UserRole.filter(user=user).prefetch_related('role')
        if not user_roles:
            no_role_users.append(user)
        else:
            roles_str = ", ".join([ur.role.name for ur in user_roles])
            print(f"用户 {user.employee_id}({user.username}) 的角色: {roles_str}")
    
    if no_role_users:
        print(f"\n⚠️  以下 {len(no_role_users)} 个用户没有角色:")
        for user in no_role_users:
            print(f"  - {user.employee_id}({user.username})")
    else:
        print("\n✅ 所有用户都已分配角色")


async def main():
    """主函数"""
    # 初始化数据库连接
    await Tortoise.init(config=TORTOISE_ORM)
    
    try:
        # 执行迁移
        await migrate_user_types()
        
        # 验证迁移结果
        await verify_migration()
        
        print("\n数据迁移完成!")
        
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main()) 