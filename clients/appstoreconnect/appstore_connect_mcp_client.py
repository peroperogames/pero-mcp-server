"""
App Store Connect MCP 客户端 - 整合了客户端和服务器功能
"""

import os
import jwt
import time
import requests
from typing import List, Dict, Any, Optional

from ..i_mcp_client import IMCPClient
from .models import AppStoreConnectConfig


class AppStoreConnectMCPClient(IMCPClient):
    """App Store Connect MCP 客户端 - 实现 IMCPClient 接口"""

    def __init__(self):
        """初始化客户端"""
        self.config = None

    def _load_config_from_env(self) -> Optional[AppStoreConnectConfig]:
        """从环境变量加载App Store Connect配置"""
        key_id = os.getenv('APPSTORE_KEY_ID')
        issuer_id = os.getenv('APPSTORE_ISSUER_ID')
        private_key = os.getenv('APPSTORE_PRIVATE_KEY')
        app_id = os.getenv('APPSTORE_APP_ID')

        if not all([key_id, issuer_id, private_key]):
            return None

        return AppStoreConnectConfig(
            key_id=key_id,
            issuer_id=issuer_id,
            private_key=private_key,
            app_id=app_id
        )

    def _generate_jwt_token(self) -> str:
        """生成JWT认证令牌"""
        if not self.config:
            self.config = self._load_config_from_env()

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

    def _make_api_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送API请求"""

        token = self._generate_jwt_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.appstoreconnect.apple.com/v1/{endpoint}"

        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

        response.raise_for_status()
        return response.json()

    def get_apps(self) -> List[Dict[str, str]]:
        """获取应用列表"""
        response = self._make_api_request("apps")
        apps = []
        for app in response.get("data", []):
            apps.append({
                "id": app["id"],
                "name": app["attributes"]["name"],
                "bundle_id": app["attributes"]["bundleId"],
                "platform": app["attributes"]["platform"]
            })
        return apps

    def get_team_members(self) -> List[Dict[str, Any]]:
        """获取团队成员"""
        response = self._make_api_request("users")
        members = []
        for user in response.get("data", []):
            members.append({
                "id": user["id"],
                "email": user["attributes"]["username"],
                "first_name": user["attributes"]["firstName"],
                "last_name": user["attributes"]["lastName"],
                "roles": [role["type"] for role in user.get("relationships", {}).get("visibleApps", {}).get("data", [])]
            })
        return members

    def register_tools(self, mcp) -> None:
        """注册App Store Connect工具到FastMCP实例"""

        @mcp.tool("configure_appstore")
        def configure_appstore(key_id: str, issuer_id: str, private_key: str, app_id: Optional[str] = None) -> str:
            """配置App Store Connect凭据"""
            self.config = AppStoreConnectConfig(
                key_id=key_id,
                issuer_id=issuer_id,
                private_key=private_key,
                app_id=app_id
            )
            return "App Store Connect 配置已成功设置"

        @mcp.tool("get_apps")
        def get_apps_tool() -> str:
            """获取所有应用"""

            try:
                apps = self.get_apps()
                return f"找到 {len(apps)} 个应用:\n" + "\n".join([f"- {app['name']} ({app['bundle_id']})" for app in apps])
            except Exception as e:
                return f"获取应用列表失败: {str(e)}"

        @mcp.tool("get_team_members")
        def get_team_members_tool() -> str:
            """获取团队成员"""

            try:
                members = self.get_team_members()
                return f"团队共有 {len(members)} 名成员:\n" + "\n".join([f"- {m['email']} ({m['first_name']} {m['last_name']})" for m in members])
            except Exception as e:
                return f"获取团队成员失败: {str(e)}"

    def register_resources(self, mcp) -> None:
        """注册App Store Connect资源到FastMCP实例"""

        @mcp.resource("appstore://apps")
        def get_apps_resource() -> str:
            """获取应用列表资源"""

            try:
                apps = self.get_apps()
                return f"找到 {len(apps)} 个应用:\n" + "\n".join([f"- {app['name']} ({app['bundle_id']})" for app in apps])
            except Exception as e:
                return f"获取应用列表失败: {str(e)}"

        @mcp.resource("appstore://members")
        def get_team_members_resource() -> str:
            """获取团队成员资源"""

            try:
                members = self.get_team_members()
                return f"团队共有 {len(members)} 名成员:\n" + "\n".join([f"- {m['email']} ({', '.join(m['roles'])})" for m in members])
            except Exception as e:
                return f"获取团队成员失败: {str(e)}"

    def register_prompts(self, mcp) -> None:
        """注册App Store Connect提示到FastMCP实例"""

        @mcp.prompt("manage_testflight")
        def manage_testflight_prompt(action: str, app_name: str = "", group_name: str = "", tester_email: str = "") -> str:
            """生成 TestFlight 管理提示"""
            prompts = {
                "create_group": f"请为应用 '{app_name}' 创建一个名为 '{group_name}' 的 TestFlight 测试组",
                "add_tester": f"请将测试者 '{tester_email}' 添加到 '{group_name}' 测试组",
                "remove_tester": f"请从 '{group_name}' 测试组中移除测试者 '{tester_email}'"
            }
            return prompts.get(action, "请选择有效的 TestFlight 管理操作")
