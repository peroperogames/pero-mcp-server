"""
设备相关数据模型
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class DeviceClass(Enum):
    """设备类别枚举"""
    IPHONE = "IPHONE"
    IPAD = "IPAD"
    APPLE_WATCH = "APPLE_WATCH"
    APPLE_TV = "APPLE_TV"
    MAC = "MAC"


class DeviceStatus(Enum):
    """设备状态枚举"""
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class DevicePlatform(Enum):
    """设备平台枚举"""
    IOS = "IOS"
    MAC_OS = "MAC_OS"
    TV_OS = "TV_OS"
    WATCH_OS = "WATCH_OS"


@dataclass
class Device:
    """设备信息模型"""
    id: str
    name: str
    udid: str
    device_class: DeviceClass
    status: DeviceStatus
    platform: DevicePlatform
    model: Optional[str] = None
    added_date: Optional[datetime] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Device':
        """从API响应创建Device对象"""
        attributes = data.get("attributes", {})
        
        # 处理日期
        added_date = None
        if attributes.get("addedDate"):
            try:
                added_date = datetime.fromisoformat(attributes["addedDate"].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        return cls(
            id=data["id"],
            name=attributes.get("name", ""),
            udid=attributes.get("udid", ""),
            device_class=DeviceClass(attributes.get("deviceClass", "IPHONE")),
            status=DeviceStatus(attributes.get("status", "ENABLED")),
            platform=DevicePlatform(attributes.get("platform", "IOS")),
            model=attributes.get("model"),
            added_date=added_date
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "udid": self.udid,
            "device_class": self.device_class.value,
            "status": self.status.value,
            "platform": self.platform.value,
            "model": self.model,
            "added_date": self.added_date.isoformat() if self.added_date else None
        }
