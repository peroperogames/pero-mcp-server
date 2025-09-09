"""
配置相关数据模型
"""

from dataclasses import dataclass


@dataclass
class AppStoreConnectConfig:
    """App Store Connect 配置"""
    key_id: str
    issuer_id: str
    private_key: str
    vendor_number: str  # 用于销售报告和分析数据
