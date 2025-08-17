"""
设备连通性检测管理器
负责管理设备的ping检测、缓存结果、跟踪访问时间
"""
import asyncio
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


class ConnectivityManager:
    """设备连通性检测管理器"""
    
    def __init__(self):
        # 连通性状态缓存 {device_id: {"status": bool, "last_check": datetime, "last_ping": datetime}}
        self.connectivity_cache: Dict[int, Dict] = {}
        
        # 需要检测的设备集合
        self.active_devices: Set[int] = set()
        
        # 设备最后访问时间 {device_id: datetime}
        self.last_access_time: Dict[int, datetime] = {}
        
        # 检测任务是否正在运行
        self.is_running = False
        
        # 检测任务
        self.check_task: Optional[asyncio.Task] = None
        
        # 配置参数
        self.ping_interval = 10  # ping检测间隔（秒）
        self.access_timeout = 20  # 访问超时时间（秒）
        self.ping_timeout = 3  # ping超时时间（秒）
        self.cache_expire = 15  # 缓存过期时间（秒）
    
    async def start(self):
        """启动连通性检测服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.check_task = asyncio.create_task(self._check_loop())
        logger.info("连通性检测管理器已启动")
    
    async def stop(self):
        """停止连通性检测服务"""
        self.is_running = False
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        logger.info("连通性检测管理器已停止")
    
    async def get_connectivity_status(self, device_id: int) -> Optional[Dict]:
        """
        获取设备连通性状态
        
        Args:
            device_id: 设备ID
            
        Returns:
            {"status": bool, "last_check": datetime} 或 None
        """
        # 更新访问时间
        self.last_access_time[device_id] = datetime.now()
        
        # 将设备添加到活跃检测列表
        self.active_devices.add(device_id)
        
        # 检查缓存
        if device_id in self.connectivity_cache:
            cache_data = self.connectivity_cache[device_id]
            last_check = cache_data.get("last_check")
            
            # 检查缓存是否过期
            if last_check and (datetime.now() - last_check).total_seconds() < self.cache_expire:
                return {
                    "status": cache_data["status"],
                    "last_check": last_check,
                    "last_ping": cache_data.get("last_ping")
                }
        
        # 缓存不存在或已过期，触发立即检测
        await self._ping_device_immediate(device_id)
        
        # 返回检测结果
        if device_id in self.connectivity_cache:
            cache_data = self.connectivity_cache[device_id]
            return {
                "status": cache_data["status"],
                "last_check": cache_data.get("last_check"),
                "last_ping": cache_data.get("last_ping")
            }
        
        return None
    
    async def get_multiple_connectivity_status(self, device_ids: list) -> Dict[int, Dict]:
        """
        批量获取设备连通性状态
        
        Args:
            device_ids: 设备ID列表
            
        Returns:
            {device_id: {"status": bool, "last_check": datetime}}
        """
        results = {}
        for device_id in device_ids:
            status = await self.get_connectivity_status(device_id)
            if status:
                results[device_id] = status
        return results
    
    async def _check_loop(self):
        """连通性检测循环"""
        while self.is_running:
            try:
                # 清理长时间未访问的设备
                await self._cleanup_inactive_devices()
                
                # 对活跃设备进行ping检测
                if self.active_devices:
                    await self._ping_active_devices()
                
                # 等待下次检测
                await asyncio.sleep(self.ping_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"连通性检测循环出错: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_inactive_devices(self):
        """清理长时间未访问的设备"""
        current_time = datetime.now()
        inactive_devices = []
        
        for device_id in list(self.active_devices):
            last_access = self.last_access_time.get(device_id)
            if last_access and (current_time - last_access).total_seconds() > self.access_timeout:
                inactive_devices.append(device_id)
        
        for device_id in inactive_devices:
            self.active_devices.discard(device_id)
            self.last_access_time.pop(device_id, None)
            # 保留缓存一段时间，但不再主动检测
            logger.info(f"设备 {device_id} 长时间未访问，已从活跃检测列表中移除")
    
    async def _ping_active_devices(self):
        """对活跃设备进行ping检测"""
        # 导入设备模型（避免循环导入）
        from models.deviceModel import Device
        
        # 获取需要检测的设备信息
        devices = await Device.filter(id__in=list(self.active_devices))
        
        # 并发执行ping检测
        tasks = []
        for device in devices:
            task = asyncio.create_task(self._ping_device(device.id, device.ip))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _ping_device_immediate(self, device_id: int):
        """立即对指定设备进行ping检测"""
        from models.deviceModel import Device
        
        device = await Device.filter(id=device_id).first()
        if device:
            await self._ping_device(device_id, device.ip)
    
    async def _ping_device(self, device_id: int, ip: str):
        """
        对单个设备进行ping检测
        
        Args:
            device_id: 设备ID
            ip: 设备IP地址
        """
        try:
            # 执行ping命令
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', str(self.ping_timeout), ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 等待ping完成
            await asyncio.wait_for(process.wait(), timeout=self.ping_timeout + 2)
            
            # 判断ping结果
            is_connected = process.returncode == 0
            current_time = datetime.now()
            
            # 更新缓存
            self.connectivity_cache[device_id] = {
                "status": is_connected,
                "last_check": current_time,
                "last_ping": current_time
            }
            
            # 更新数据库中的连通性状态
            from models.deviceModel import Device
            await Device.filter(id=device_id).update(
                connectivity_status=is_connected,
                last_ping_time=current_time,
                last_connectivity_check=current_time
            )
            
            logger.debug(f"设备 {device_id} ({ip}) ping检测完成: {'连通' if is_connected else '不连通'}")
            
        except asyncio.TimeoutError:
            # ping超时，认为不连通
            current_time = datetime.now()
            self.connectivity_cache[device_id] = {
                "status": False,
                "last_check": current_time,
                "last_ping": current_time
            }
            logger.warning(f"设备 {device_id} ({ip}) ping超时")
            
        except Exception as e:
            # ping出错，认为不连通
            current_time = datetime.now()
            self.connectivity_cache[device_id] = {
                "status": False,
                "last_check": current_time,
                "last_ping": current_time
            }
            logger.error(f"设备 {device_id} ({ip}) ping检测出错: {e}")
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息（用于调试）"""
        return {
            "active_devices": list(self.active_devices),
            "cache_count": len(self.connectivity_cache),
            "last_access_count": len(self.last_access_time)
        }


# 全局连通性管理器实例
connectivity_manager = ConnectivityManager()
