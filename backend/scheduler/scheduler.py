"""
定时任务调度器
"""
import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from models.deviceModel import Device, DeviceUsage, DeviceStatusEnum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def start(self):
        """启动定时任务调度器"""
        # 添加每天零点30分的定时任务
        self.scheduler.add_job(
            self.daily_device_cleanup,
            CronTrigger(hour=23, minute=54),  # 每天00:30执行
            id='daily_device_cleanup',
            name='每日设备清理任务',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("定时任务调度器已启动")
        
    async def stop(self):
        """停止定时任务调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已停止")
        
    async def daily_device_cleanup(self):
        """每日设备清理任务：释放所有设备占用和排队"""
        try:
            logger.info("开始执行每日设备清理任务...")
            
            # 获取所有设备使用信息
            usage_infos = await DeviceUsage.all().prefetch_related("device")
            
            released_count = 0
            queue_cleared_count = 0
            
            for usage_info in usage_infos:
                try:
                    # 记录清理前的状态
                    had_user = bool(usage_info.current_user)
                    had_queue = bool(usage_info.queue_users)
                    
                    # 清理占用状态
                    usage_info.current_user = None
                    usage_info.start_time = None
                    usage_info.expected_duration = 0  # 设置为0而不是None
                    usage_info.purpose = None
                    usage_info.status = DeviceStatusEnum.AVAILABLE
                    usage_info.is_long_term = False
                    usage_info.long_term_purpose = None
                    
                    # 清理排队列表
                    usage_info.queue_users = []
                    
                    await usage_info.save()
                    
                    if had_user:
                        released_count += 1
                        logger.info(f"已释放设备: {usage_info.device.name}")
                    
                    if had_queue:
                        queue_cleared_count += 1
                        logger.info(f"已清理设备排队: {usage_info.device.name}")
                        
                except Exception as e:
                    logger.error(f"清理设备 {usage_info.device.name} 失败: {e}")
            
            logger.info(f"每日设备清理任务完成 - 释放设备: {released_count}台, 清理排队: {queue_cleared_count}台")
            
        except Exception as e:
            logger.error(f"每日设备清理任务执行失败: {e}")
    
    async def force_cleanup_all_devices(self):
        """手动强制清理所有设备（管理员功能）"""
        return await self.daily_device_cleanup()

# 全局调度器实例
device_scheduler = DeviceScheduler()

async def start_scheduler():
    """启动调度器"""
    await device_scheduler.start()

async def stop_scheduler():
    """停止调度器"""
    await device_scheduler.stop()
