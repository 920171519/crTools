"""通知相关工具方法"""
from typing import Optional

from models.deviceModel import Device
from models.admin import User
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())


async def send_device_notification(device: Device, user: Optional[User], action: str) -> None:
    """发送设备状态变更通知（当前仅打印）"""
    try:
        auth = os.getenv("AUTH")
        emp = user.employee_id if user else "-"
        name = user.username if user else "-"
        print(
            f"[通知] auth{auth} 设备: {device.name}({device.ip}) | 用户: {emp}({name}) | 动作: {action}")
    except Exception as exc:  # pragma: no cover - 通知失败不影响主流程
        print(f"发送通知失败: {exc}")
