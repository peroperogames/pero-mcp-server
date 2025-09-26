"""
Google Play Developer Reporting API 配置模型
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GooglePlayConfig:
    """Google Play Developer Reporting API 配置"""
    service_account_file: str  # 服务账号 JSON 文件路径
    package_name: Optional[str] = None  # 应用包名（可选，用于特定应用报告）

    def __post_init__(self):
        """验证配置"""
        if not self.service_account_file:
            raise ValueError("service_account_file is required")
