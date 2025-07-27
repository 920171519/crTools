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
        # 从数据库获取清理时间设置
        cleanup_time = await self._get_cleanup_time()
        hour, minute = self._parse_time(cleanup_time)

        # 添加定时清理任务
        self.scheduler.add_job(
            self.daily_device_cleanup,
            CronTrigger(hour=hour, minute=minute),
            id='daily_device_cleanup',
            name='每日设备清理任务',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"定时任务调度器已启动，清理时间: {cleanup_time}")

    async def _get_cleanup_time(self):
        """获取清理时间设置"""
        try:
            from models.systemModel import SystemSettings
            settings = await SystemSettings.first()
            return settings.cleanup_time if settings else "00:30"
        except Exception as e:
            logger.error(f"获取清理时间设置失败: {e}")
            return "00:30"  # 默认时间

    def _parse_time(self, time_str):
        """解析时间字符串"""
        try:
            hour, minute = time_str.split(':')
            return int(hour), int(minute)
        except (ValueError, AttributeError):
            return 0, 30  # 默认00:30

    async def update_cleanup_schedule(self, cleanup_time):
        """更新清理任务的调度时间"""
        if not cleanup_time:
            cleanup_time = "00:30"

        hour, minute = self._parse_time(cleanup_time)

        # 移除旧任务并添加新任务
        if self.scheduler.get_job('daily_device_cleanup'):
            self.scheduler.remove_job('daily_device_cleanup')

        self.scheduler.add_job(
            self.daily_device_cleanup,
            CronTrigger(hour=hour, minute=minute),
            id='daily_device_cleanup',
            name='每日设备清理任务',
            replace_existing=True
        )

        logger.info(f"定时清理任务已更新，新的清理时间: {cleanup_time}")
        
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
