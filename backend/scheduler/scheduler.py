"""
定时任务调度器
"""
import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from models.deviceModel import Device, DeviceUsage, DeviceStatusEnum
from models.admin import User, OperationLog
from models.systemModel import SystemSettings
from connectivity_manager import connectivity_manager
from utils.notification import send_device_notification
import logging


def get_current_time():
    """获取当前时间，统一使用naive datetime"""
    return datetime.now()


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def _notify_forced_release(self, device: Device, employee_id: str | None, context: str):
        """通知占用人被系统/管理员清理释放（仅打印）。
        使用本地打印以避免与routers.device的循环依赖。
        打印格式与设备路由中的保持一致：
        [通知] 设备: name(ip) | 用户: emp(name) | 动作: action
        """
        try:
            emp = (employee_id or "-")
            user = None
            username = "-"
            if employee_id:
                user = await User.filter(employee_id__iexact=employee_id).first()
                if user:
                    username = user.username or "-"
            action = f"{context}：被强制释放"
            print(
                f"[通知] 设备: {device.name}({device.ip}) | 用户: {emp}({username}) | 动作: {action}")
        except Exception as e:
            logger.error(f"发送定时/管理员清理通知失败: {e}")

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
        # 占用时长检查（每分钟）
        self.scheduler.add_job(
            self.enforce_occupancy_limits,
            IntervalTrigger(minutes=1),
            id="enforce_occupancy_limits",
            name="占用时长限制检查",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"定时任务调度器已启动，清理时间: {cleanup_time}")

        # 启动连通性检测管理器
        await connectivity_manager.start()
        logger.info("连通性检测管理器已启动")

    async def _get_cleanup_time(self):
        """获取清理时间设置"""
        try:
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
        # 停止连通性检测管理器
        await connectivity_manager.stop()
        logger.info("连通性检测管理器已停止")

        self.scheduler.shutdown()
        logger.info("定时任务调度器已停止")

    async def enforce_occupancy_limits(self):
        """检查并处理超时占用的设备（仅在有排队用户时释放并切换）"""
        try:
            now = get_current_time()
            usage_list = await DeviceUsage.filter(
                status=DeviceStatusEnum.OCCUPIED,
                current_user__isnull=False,
                device__max_occupy_minutes__isnull=False,
            ).prefetch_related("device")

            for usage in usage_list:
                device = usage.device
                if not device or device.max_occupy_minutes is None or device.max_occupy_minutes <= 0:
                    continue
                if not usage.start_time:
                    continue

                start_time = usage.start_time.replace(
                    tzinfo=None) if usage.start_time.tzinfo else usage.start_time
                elapsed_minutes = (now - start_time).total_seconds() / 60
                if elapsed_minutes < device.max_occupy_minutes:
                    continue

                queue = list(usage.queue_users or [])
                if not queue:
                    # 无排队用户则不释放
                    continue

                previous_emp = usage.current_user
                next_emp_raw = queue.pop(0)
                next_emp = next_emp_raw.lower() if isinstance(
                    next_emp_raw, str) else next_emp_raw

                usage.current_user = next_emp
                usage.start_time = now
                usage.status = DeviceStatusEnum.OCCUPIED
                usage.queue_users = queue
                await usage.save()

                prev_user_obj = await User.filter(employee_id__iexact=previous_emp).first() if previous_emp else None
                next_user_obj = await User.filter(employee_id__iexact=next_emp).first() if next_emp else None

                await send_device_notification(device, prev_user_obj, "占用超时，系统自动释放")
                await send_device_notification(device, next_user_obj, "排队自动转为占用")

                log_user = prev_user_obj or next_user_obj
                if log_user:
                    await OperationLog.create_log(
                        user=log_user,
                        operation_type="device_auto_release",
                        operation_result="success",
                        device_name=device.name,
                        description=f"占用超过 {device.max_occupy_minutes} 分钟，自动释放并分配给排队用户 {next_emp}",
                        device_ip=device.ip,
                    )
        except Exception as exc:
            logger.error(f"占用时长限制检查失败: {exc}")

    async def daily_device_cleanup(self, force_cleanup=False):
        """每日设备清理任务：释放所有设备占用和排队

        Args:
            force_cleanup (bool): 是否强制清理，True时会清理所有设备包括未到期的长时间占用
        """
        try:
            cleanup_type = "强制清理" if force_cleanup else "定期清理"
            logger.info(f"开始执行{cleanup_type}任务...")

            # 获取所有设备使用信息
            usage_infos = await DeviceUsage.all().prefetch_related("device")

            released_count = 0
            queue_cleared_count = 0

            for usage_info in usage_infos:
                try:
                    # 如果不是强制清理，检查是否为长时间占用且未到期
                    if not force_cleanup and usage_info.is_long_term and usage_info.end_date:
                        current_time = get_current_time()
                        # 如果数据库中的时间是aware的，转换为naive进行比较
                        end_date = usage_info.end_date.replace(
                            tzinfo=None) if usage_info.end_date.tzinfo else usage_info.end_date
                        if end_date > current_time:
                            logger.info(
                                f"跳过长时间占用设备: {usage_info.device.name}，截至时间：{usage_info.end_date}")
                            continue
                        else:
                            logger.info(
                                f"长时间占用设备已到期，开始清理: {usage_info.device.name}，截至时间：{usage_info.end_date}")
                    elif force_cleanup and usage_info.is_long_term:
                        logger.info(f"强制清理长时间占用设备: {usage_info.device.name}")

                    # 记录清理前的状态
                    had_user = bool(usage_info.current_user)
                    prev_emp = (usage_info.current_user.lower()
                                if usage_info.current_user else None)
                    had_queue = bool(usage_info.queue_users)

                    # 清理占用状态
                    usage_info.current_user = None
                    usage_info.start_time = None
                    usage_info.status = DeviceStatusEnum.AVAILABLE
                    usage_info.is_long_term = False
                    usage_info.long_term_purpose = None
                    usage_info.end_date = None

                    # 清理排队列表
                    usage_info.queue_users = []

                    await usage_info.save()

                    if had_user:
                        released_count += 1
                        logger.info(f"已释放设备: {usage_info.device.name}")
                        # 通知上一位占用人
                        context = "强制清理" if force_cleanup else "定时清理"
                        await self._notify_forced_release(usage_info.device, prev_emp, context)

                    if had_queue:
                        queue_cleared_count += 1
                        logger.info(f"已清理设备排队: {usage_info.device.name}")

                except Exception as e:
                    logger.error(f"清理设备 {usage_info.device.name} 失败: {e}")

            logger.info(
                f"{cleanup_type}任务完成 - 释放设备: {released_count}台, 清理排队: {queue_cleared_count}台")

        except Exception as e:
            logger.error(f"{cleanup_type}任务执行失败: {e}")

    async def force_cleanup_all_devices(self):
        """手动强制清理所有设备（管理员功能）"""
        return await self.daily_device_cleanup(force_cleanup=True)


# 全局调度器实例
device_scheduler = DeviceScheduler()


async def start_scheduler():
    """启动调度器"""
    await device_scheduler.start()


async def stop_scheduler():
    """停止调度器"""
    await device_scheduler.stop()
