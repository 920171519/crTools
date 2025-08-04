#!/usr/bin/env python3
"""
测试定期清理功能
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tortoise import Tortoise
from models.deviceModel import Device, DeviceUsage, DeviceStatusEnum
from models.admin import User
from scheduler.scheduler import DeviceScheduler


async def setup_test_data():
    """设置测试数据"""
    print("设置测试数据...")

    # 查找现有用户
    user = await User.first()
    if not user:
        print("没有找到用户，请先创建用户")
        return None, None

    # 查找现有设备
    device = await Device.first()
    if not device:
        print("没有找到设备，请先创建设备")
        return None, None

    # 获取设备使用信息
    usage_info = await DeviceUsage.filter(device=device).first()
    if not usage_info:
        usage_info = await DeviceUsage.create(device=device)

    # 设置为已到期的长时间占用
    usage_info.current_user = user.employee_id
    usage_info.start_time = datetime.now() - timedelta(hours=1)
    usage_info.status = DeviceStatusEnum.LONG_TERM_OCCUPIED
    usage_info.is_long_term = True
    usage_info.long_term_purpose = "测试长时间占用"
    usage_info.end_date = datetime.now() - timedelta(minutes=30)  # 30分钟前就到期了
    await usage_info.save()

    print(f"使用设备: {device.name}")
    print(f"设备状态: {usage_info.status}")
    print(f"是否长时间占用: {usage_info.is_long_term}")
    print(f"截至时间: {usage_info.end_date}")
    print(f"当前时间: {datetime.now()}")
    print(f"是否已到期: {usage_info.end_date < datetime.now()}")

    return device, usage_info


async def test_cleanup():
    """测试清理功能"""
    print("\n开始测试定期清理功能...")
    
    # 初始化数据库
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["models.deviceModel", "models.admin", "models.systemModel"]}
    )
    await Tortoise.generate_schemas()
    
    try:
        # 设置测试数据
        device, usage_info = await setup_test_data()
        if not device or not usage_info:
            print("无法设置测试数据")
            return
        
        print(f"\n清理前状态:")
        print(f"设备: {device.name}")
        print(f"当前使用人: {usage_info.current_user}")
        print(f"状态: {usage_info.status}")
        print(f"是否长时间占用: {usage_info.is_long_term}")
        print(f"截至时间: {usage_info.end_date}")
        
        # 执行清理
        scheduler = DeviceScheduler()
        await scheduler.daily_device_cleanup()
        
        # 检查清理后的状态
        await usage_info.refresh_from_db()
        print(f"\n清理后状态:")
        print(f"设备: {device.name}")
        print(f"当前使用人: {usage_info.current_user}")
        print(f"状态: {usage_info.status}")
        print(f"是否长时间占用: {usage_info.is_long_term}")
        print(f"截至时间: {usage_info.end_date}")
        
        # 验证结果
        if usage_info.current_user is None and usage_info.status == DeviceStatusEnum.AVAILABLE:
            print("\n✅ 测试通过：已到期的长时间占用设备已被正确清理")
        else:
            print("\n❌ 测试失败：已到期的长时间占用设备未被清理")
            
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(test_cleanup())
