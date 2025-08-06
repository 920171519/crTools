#!/usr/bin/env python3
"""
修改测试数据，创建一个已到期的长时间占用设备
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tortoise import Tortoise
from models.deviceModel import Device, DeviceUsage, DeviceStatusEnum


async def modify_test_data():
    """修改测试数据"""
    print("修改测试数据...")
    
    # 初始化数据库
    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={"models": ["models.deviceModel", "models.admin", "models.systemModel"]}
    )
    
    try:
        # 查找seaf设备
        device = await Device.filter(name="seaf").first()
        if not device:
            print("未找到seaf设备")
            return
        
        # 获取设备使用信息
        usage_info = await DeviceUsage.filter(device=device).first()
        if not usage_info:
            print("未找到设备使用信息")
            return
        
        print(f"修改前:")
        print(f"设备: {device.name}")
        print(f"当前使用人: {usage_info.current_user}")
        print(f"状态: {usage_info.status}")
        print(f"是否长时间占用: {usage_info.is_long_term}")
        print(f"截至时间: {usage_info.end_date}")
        print(f"当前时间: {datetime.now()}")
        
        # 修改截至时间为30分钟前（已到期）
        expired_time = datetime.now() - timedelta(minutes=30)
        usage_info.end_date = expired_time
        await usage_info.save()
        
        print(f"\n修改后:")
        print(f"设备: {device.name}")
        print(f"当前使用人: {usage_info.current_user}")
        print(f"状态: {usage_info.status}")
        print(f"是否长时间占用: {usage_info.is_long_term}")
        print(f"截至时间: {usage_info.end_date}")
        print(f"当前时间: {datetime.now()}")
        print(f"是否已到期: {usage_info.end_date < datetime.now()}")
        
        print("\n✅ 测试数据修改完成！现在seaf设备已经到期，可以测试清理功能了。")
        
    except Exception as e:
        print(f"\n❌ 修改失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(modify_test_data())
