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

    def __post_init__(self):
        """配置验证"""
        if not self.key_id or not self.key_id.strip():
            raise ValueError("key_id 不能为空")

        if not self.issuer_id or not self.issuer_id.strip():
            raise ValueError("issuer_id 不能为空")

        if not self.private_key or not self.private_key.strip():
            raise ValueError("private_key 不能为空")

        if not self.vendor_number or not self.vendor_number.strip():
            raise ValueError("vendor_number 不能为空")

        # 验证私钥格式
        if not (self.private_key.startswith('-----BEGIN PRIVATE KEY-----') or
                '-----BEGIN PRIVATE KEY-----' in self.private_key):
            raise ValueError("private_key 格式不正确，应该是 PEM 格式的私钥")
