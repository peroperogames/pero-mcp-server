"""
应用相关数据模型
"""

from dataclasses import dataclass
from enum import Enum


class Platform(Enum):
    """平台类型"""
    IOS = "IOS"
    MAC_OS = "MAC_OS"
    TV_OS = "TV_OS"
    WATCH_OS = "WATCH_OS"
    UNKNOWN = "UNKNOWN"


@dataclass
class App:
    """应用信息"""
    id: str
    name: str
    bundle_id: str
    platform: Platform

    @classmethod
    def from_api_response(cls, data: dict) -> 'App':
        """从 API 响应创建 App 实例"""
        attributes = data.get("attributes", {})
        platform_str = attributes.get("platform", "UNKNOWN")

        try:
            platform = Platform(platform_str)
        except ValueError:
            platform = Platform.UNKNOWN

        return cls(
            id=data.get("id", ""),
            name=attributes.get("name", "未知应用"),
            bundle_id=attributes.get("bundleId", ""),
            platform=platform
        )
