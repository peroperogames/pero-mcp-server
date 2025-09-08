"""
App Store Connect 应用管理处理器 - 负责应用相关操作
"""

from typing import Any, List, Optional
from ...i_mcp_handler import IMCPHandler
from ..models import App, Platform


class AppHandler(IMCPHandler):
    """应用管理处理器 - 负责应用列表、应用信息等应用相关操作"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册应用管理相关工具"""

        @mcp.tool("get_apps")
        def get_apps_tool() -> str:
            """获取所有应用"""
            try:
                apps = self.get_apps()
                return f"找到 {len(apps)} 个应用:\n" + "\n".join([f"- {app.name} ({app.bundle_id}) - {app.platform.value}" for app in apps])
            except Exception as e:
                return f"获取应用列表失败: {str(e)}"

    def register_resources(self, mcp: Any) -> None:
        """注册应用管理相关资源"""

        @mcp.resource("appstore://apps")
        def get_apps_resource() -> str:
            """获取应用列表资源"""
            try:
                apps = self.get_apps()
                return f"应用列表:\n" + "\n".join([f"- {app.name} ({app.bundle_id}) - {app.platform.value}" for app in apps])
            except Exception as e:
                return f"获取应用列表失败: {str(e)}"

    def register_prompts(self, mcp: Any) -> None:
        """注册应用管理相关提示"""
        # 应用处理器暂时不需要特定的提示
        pass

    # =============================================================================
    # 业务逻辑方法
    # =============================================================================

    def get_apps(self) -> List[App]:
        """获取应用列表"""
        response = self.client.make_api_request("apps")
        apps = []
        for app_data in response.get("data", []):
            app = App.from_api_response(app_data)
            apps.append(app)
        return apps

    def get_app_by_name(self, app_name: str) -> Optional[App]:
        """根据应用名称获取应用信息"""
        apps = self.get_apps()
        for app in apps:
            if app.name.lower() == app_name.lower():
                return app
        return None

    def get_app_by_id(self, app_id: str) -> Optional[App]:
        """根据应用ID获取应用信息"""
        apps = self.get_apps()
        for app in apps:
            if app.id == app_id:
                return app
        return None

    def get_apps_by_platform(self, platform: Platform) -> List[App]:
        """根据平台获取应用列表"""
        apps = self.get_apps()
        return [app for app in apps if app.platform == platform]

    def search_apps(self, keyword: str) -> List[App]:
        """搜索应用（按名称或bundle_id）"""
        apps = self.get_apps()
        keyword_lower = keyword.lower()
        return [
            app for app in apps
            if keyword_lower in app.name.lower() or keyword_lower in app.bundle_id.lower()
        ]
