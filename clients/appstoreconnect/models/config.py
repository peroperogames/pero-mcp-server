"""
配置相关数据模型
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class AppStoreConnectConfig:
    """App Store Connect 配置"""
    key_id: str
    issuer_id: str
    private_key: str
    app_id: Optional[str] = None
