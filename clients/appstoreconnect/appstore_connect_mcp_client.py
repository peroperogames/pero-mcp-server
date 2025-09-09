"""
App Store Connect MCP 客户端 - 重构为中转站模式
"""

import os
import jwt
import time
import requests
from typing import Dict, Any, Optional

from ..i_mcp_client import IMCPClient
from .models import AppStoreConnectConfig
from .handlers import (
    ConfigureHandler, UserHandler, TestFlightHandler, AppHandler,
    DeviceHandler, AnalyticsHandler, LocalizationHandler
)


class AppStoreConnectMCPClient(IMCPClient):
    """App Store Connect MCP 客户端 - 作为中转站协调各个处理器"""

    def __init__(self):
        """初始化客户端和各个处理器"""
        self.config = None

        # 初始化各个处理器，传入self引用
        self.configure_handler = ConfigureHandler(self)
        self.app_handler = AppHandler(self)
        self.testflight_handler = TestFlightHandler(self, self.app_handler)
        self.user_handler = UserHandler(self, self.app_handler, self.testflight_handler)

        # 新增的处理器
        self.device_handler = DeviceHandler(self)
        self.analytics_handler = AnalyticsHandler(self)
        self.localization_handler = LocalizationHandler(self)

    # =============================================================================
    # MCP 接口方法 - 通过处理器注册工具、资源和提示
    # =============================================================================

    def register_tools(self, mcp: Any) -> None:
        """注册所有工具到FastMCP实例"""
        self.configure_handler.register_tools(mcp)
        self.user_handler.register_tools(mcp)
        self.testflight_handler.register_tools(mcp)
        self.app_handler.register_tools(mcp)

        # 注册新增的工具
        self.device_handler.register_tools(mcp)
        self.analytics_handler.register_tools(mcp)
        self.localization_handler.register_tools(mcp)

    def register_resources(self, mcp: Any) -> None:
        """注册所有资源到FastMCP实例"""
        self.configure_handler.register_resources(mcp)
        self.user_handler.register_resources(mcp)
        self.testflight_handler.register_resources(mcp)
        self.app_handler.register_resources(mcp)

        # 注册新增的资源
        self.device_handler.register_resources(mcp)
        self.analytics_handler.register_resources(mcp)
        self.localization_handler.register_resources(mcp)

    def register_prompts(self, mcp: Any) -> None:
        """注册所有提示到FastMCP实例"""
        self.configure_handler.register_prompts(mcp)
        self.user_handler.register_prompts(mcp)
        self.testflight_handler.register_prompts(mcp)
        self.app_handler.register_prompts(mcp)

        # 注册新增的提示
        self.device_handler.register_prompts(mcp)
        self.analytics_handler.register_prompts(mcp)
        self.localization_handler.register_prompts(mcp)

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

        # 支持多种私钥配置方式
        private_key = (
            os.getenv('APPSTORE_PRIVATE_KEY') or
            self._load_private_key_from_file()
        )

        # 处理私钥格式 - 将 \n 转换为真正的换行符
        if private_key and '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')

        vendor_number = os.getenv('APPSTORE_VENDOR_NUMBER')  # 添加vendor_number支持

        if not all([key_id, issuer_id, private_key]):
            return None

        return AppStoreConnectConfig(
            key_id=key_id,
            issuer_id=issuer_id,
            private_key=private_key,
            vendor_number=vendor_number
        )

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

    def make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None,
                        expect_json: bool = True) -> Dict[str, Any]:
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

            if expect_json and 'application/json' in content_type:
                return response.json()
            elif not expect_json or 'application/a-gzip' in content_type or 'application/gzip' in content_type:
                # 对于销售报告，返回原始内容
                print(f"收到非JSON响应，内容前100字节: {response.content[:100]}")
                return {"raw_content": response.content, "content_type": content_type}
            else:
                # 尝试解析JSON，如果失败则返回文本内容
                try:
                    return response.json()
                except ValueError:
                    print(f"JSON解析失败，返回文本内容，前200字符: {response.text[:200]}")
                    return {"text_content": response.text, "content_type": content_type}

        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")
        except ValueError as e:
            raise Exception(f"API请求失败: {str(e)}")
