"""
App Store Connect MCP 客户端 - 重构为中转站模式
"""

import os
import time
from typing import Dict, Any, Optional

import jwt
import requests

from .models import AppStoreConnectConfig
from ..mcp_client_interface import IMCPClient


class AppStoreConnectMCPClient(IMCPClient):
    """App Store Connect MCP 客户端 - 作为中转站协调各个处理器"""

    def __init__(self):
        """初始化客户端和各个处理器"""
        self.config = None
        # 调用父类的初始化方法来自动发现处理器
        super().__init__()

    # =============================================================================
    # 配置和基础服务方法 - 供handler调用
    # =============================================================================

    def set_config(self, config: AppStoreConnectConfig) -> None:
        """设置配置"""
        self.config = config

    def load_config_from_env(self) -> Optional[AppStoreConnectConfig]:
        """从环境变量加载App Store Connect配置"""
        key_id = os.getenv('APPSTORE_KEY_ID')
        issuer_id = os.getenv('APPSTORE_ISSUER_ID')
        vendor_number = os.getenv('APPSTORE_VENDOR_NUMBER')

        # 支持多种私钥配置方式
        private_key = (
                os.getenv('APPSTORE_PRIVATE_KEY') or
                self._load_private_key_from_file()
        )

        # 处理私钥格式 - 将 \n 转换为真正的换行符
        if private_key and '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')

        # 检查所有必填字段
        if not all([key_id, issuer_id, private_key, vendor_number]):
            return None

        try:
            return AppStoreConnectConfig(
                key_id=key_id,
                issuer_id=issuer_id,
                private_key=private_key,
                vendor_number=vendor_number
            )
        except ValueError as e:
            print(f"配置验证失败: {str(e)}")
            return None

    @classmethod
    def _load_private_key_from_file(cls) -> Optional[str]:
        """从文件加载私钥"""
        key_path = os.getenv('APPSTORE_PRIVATE_KEY_PATH')
        if key_path and os.path.exists(key_path):
            try:
                with open(key_path, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"读取私钥文件失败: {str(e)}")
                pass
        return None

    def generate_jwt_token(self) -> str:
        """生成JWT认证令牌"""
        if not self.config:
            self.config = self.load_config_from_env()

        header = {
            "alg": "ES256",
            "kid": self.config.key_id,
            "typ": "JWT"
        }

        payload = {
            "iss": self.config.issuer_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 20 * 60,  # 20分钟过期
            "aud": "appstoreconnect-v1"
        }

        return jwt.encode(payload, self.config.private_key, algorithm="ES256", headers=header)

    def make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送API请求"""
        if not self.config:
            self.config = self.load_config_from_env()

        if not self.config:
            raise ValueError("未找到App Store Connect配置，请先配置环境变量")

        token = self.generate_jwt_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"

        try:
            if method == "GET":
                # 对于GET请求，将data作为查询参数
                response = requests.get(url, headers=headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, json=data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()

            # 打印响应信息用于调试
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容类型: {response.headers.get('content-type', 'unknown')}")
            print(f"响应内容长度: {len(response.content)} bytes")

            # 检查响应内容类型
            content_type = response.headers.get('content-type', '').lower()

            if 'application/json' in content_type:
                return response.json()
            elif 'application/a-gzip' in content_type or 'application/gzip' in content_type:
                return {"raw_content": response.content, "content_type": content_type}

        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")
        except ValueError as e:
            raise Exception(f"API请求失败: {str(e)}")
