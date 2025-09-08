"""
App Store Connect 应用管理处理器 - 负责应用相关操作
"""

from typing import Any, List, Optional, Dict
from ...i_mcp_handler import IMCPHandler
from ..models import App, Platform


class AppHandler(IMCPHandler):
    """应用管理处理器 - 负责应用列表、应用信息等应用相关操作"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册应用管理相关工具"""

        @mcp.tool("get_apps")
        def get_apps_tool(limit: int = 100, bundle_id: Optional[str] = None) -> str:
            """获取所有应用"""
            try:
                apps = self.get_apps(limit=limit, bundle_id=bundle_id)
                if not apps:
                    return "未找到任何应用"

                result = f"找到 {len(apps)} 个应用:\n"
                for app in apps:
                    result += f"- {app.name} ({app.bundle_id}) - {app.platform.value}\n"
                    result += f"  应用ID: {app.id}\n"
                    if hasattr(app, 'sku') and app.sku:
                        result += f"  SKU: {app.sku}\n"
                    result += "\n"
                return result
            except Exception as e:
                return f"获取应用列表失败: {str(e)}"

        @mcp.tool("get_app_info")
        def get_app_info_tool(app_id: str, include_details: bool = False) -> str:
            """获取应用详细信息"""
            try:
                app_data = self.get_app_info(app_id, include_details)
                if not app_data:
                    return f"未找到应用 {app_id}"

                attributes = app_data.get("attributes", {})

                result = f"应用详细信息:\n"
                result += f"- 名称: {attributes.get('name', 'N/A')}\n"
                result += f"- Bundle ID: {attributes.get('bundleId', 'N/A')}\n"
                result += f"- 平台: {attributes.get('platform', 'N/A')}\n"
                result += f"- 应用ID: {app_data.get('id', 'N/A')}\n"

                if attributes.get('sku'):
                    result += f"- SKU: {attributes['sku']}\n"
                if attributes.get('primaryLocale'):
                    result += f"- 主要语言: {attributes['primaryLocale']}\n"
                if attributes.get('contentRightsDeclaration'):
                    result += f"- 内容权利声明: {attributes['contentRightsDeclaration']}\n"

                return result
            except Exception as e:
                return f"获取应用信息失败: {str(e)}"

        @mcp.tool("get_app_versions")
        def get_app_versions_tool(app_id: str, limit: int = 10) -> str:
            """获取应用版本列表"""
            try:
                versions = self.get_app_versions(app_id, limit)
                if not versions:
                    return f"应用 {app_id} 没有版本信息"

                result = f"应用版本列表 ({len(versions)} 个):\n"
                for version in versions:
                    attributes = version.get("attributes", {})
                    result += f"- 版本 {attributes.get('versionString', 'N/A')}\n"
                    result += f"  状态: {attributes.get('appStoreState', 'N/A')}\n"
                    result += f"  版本ID: {version.get('id', 'N/A')}\n"
                    if attributes.get('createdDate'):
                        result += f"  创建时间: {attributes['createdDate']}\n"
                    result += "\n"

                return result
            except Exception as e:
                return f"获取应用版本失败: {str(e)}"

        @mcp.tool("find_app_by_bundle_id")
        def find_app_by_bundle_id_tool(bundle_id: str) -> str:
            """根据Bundle ID查找应用"""
            try:
                app = self.find_app_by_bundle_id(bundle_id)
                if not app:
                    return f"未找到Bundle ID为 {bundle_id} 的应用"

                result = f"找到应用:\n"
                result += f"- 名称: {app.name}\n"
                result += f"- Bundle ID: {app.bundle_id}\n"
                result += f"- 平台: {app.platform.value}\n"
                result += f"- 应用ID: {app.id}\n"

                return result
            except Exception as e:
                return f"查找应用失败: {str(e)}"

        @mcp.tool("get_app_builds")
        def get_app_builds_tool(app_id: str, limit: int = 10) -> str:
            """获取应用构建列表"""
            try:
                builds = self.get_app_builds(app_id, limit)
                if not builds:
                    return f"应用 {app_id} 没有构建信息"

                result = f"应用构建列表 ({len(builds)} 个):\n"
                for build in builds:
                    attributes = build.get("attributes", {})
                    result += f"- 构建版本: {attributes.get('version', 'N/A')}\n"
                    result += f"  构建号: {attributes.get('buildNumber', 'N/A')}\n"
                    result += f"  状态: {attributes.get('processingState', 'N/A')}\n"
                    result += f"  构建ID: {build.get('id', 'N/A')}\n"
                    if attributes.get('uploadedDate'):
                        result += f"  上传时间: {attributes['uploadedDate']}\n"
                    result += "\n"

                return result
            except Exception as e:
                return f"获取应用构建失败: {str(e)}"

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

        @mcp.resource("appstore://apps/ios")
        def get_ios_apps_resource() -> str:
            """获取iOS应用列表资源"""
            try:
                apps = self.get_apps_by_platform(Platform.IOS)
                return f"iOS应用列表:\n" + "\n".join([f"- {app.name} ({app.bundle_id})" for app in apps])
            except Exception as e:
                return f"获取iOS应用列表失败: {str(e)}"

    def register_prompts(self, mcp: Any) -> None:
        """注册应用管理相关提示"""

        @mcp.prompt("appstore_app_management")
        def appstore_app_management_prompt(
            operation: str = "",
            app_id: str = "",
            bundle_id: str = "",
            platform: str = ""
        ) -> str:
            """App Store Connect应用管理提示"""
            return f"""App Store Connect 应用管理助手

操作信息:
- 操作类型: {operation}
- 应用ID: {app_id}
- Bundle ID: {bundle_id}
- 平台: {platform}

支持的操作类型:
- get_apps: 获取应用列表
- get_app_info: 获取应用详细信息
- get_app_versions: 获取应用版本列表
- get_app_builds: 获取应用构建列表
- find_app_by_bundle_id: 根据Bundle ID查找应用

应用信息包含:
- 基本信息: 名称、Bundle ID、平台、SKU
- 版本信息: 版本号、状态、发布时间
- 构建信息: 构建号、处理状态、上传时间
- 本地化信息: 支持的语言和地区

使用步骤:
1. 使用get_apps获取应用列表
2. 选择目标应用的ID或Bundle ID
3. 使用相应工具获取详细信息
4. 查看版本和构建状态

注意事项:
- 应用ID在整个App Store Connect中唯一
- Bundle ID在开发者账户中唯一
- 版本状态决定了应用的发布阶段
- 构建必须通过审核才能发布
"""

    # =============================================================================
    # 业务逻辑方法 - 增强功能
    # =============================================================================

    def get_apps(self, limit: int = 100, bundle_id: Optional[str] = None) -> List[App]:
        """获取应用列表（增强版）"""
        params = {"limit": min(limit, 200)}

        if bundle_id:
            params["filter[bundleId]"] = bundle_id

        response = self.client.make_api_request("apps", method="GET")
        apps = []
        for app_data in response.get("data", []):
            app = App.from_api_response(app_data)
            apps.append(app)
        return apps

    def get_app_info(self, app_id: str, include_details: bool = False) -> Optional[Dict[str, Any]]:
        """获取应用详细信息（增强版）"""
        params = {}
        if include_details:
            params["include"] = "appInfos,appStoreVersions,builds"

        try:
            response = self.client.make_api_request(f"apps/{app_id}", method="GET")
            return response.get("data")
        except Exception:
            return None

    def get_app_versions(self, app_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取应用版本列表"""
        params = {"limit": min(limit, 200)}

        try:
            response = self.client.make_api_request(f"apps/{app_id}/appStoreVersions", method="GET")
            return response.get("data", [])
        except Exception:
            return []

    def get_app_builds(self, app_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取应用构建列表"""
        params = {"limit": min(limit, 200)}

        try:
            response = self.client.make_api_request(f"apps/{app_id}/builds", method="GET")
            return response.get("data", [])
        except Exception:
            return []

    def find_app_by_bundle_id(self, bundle_id: str) -> Optional[App]:
        """根据Bundle ID查找应用（优化版）"""
        apps = self.get_apps(bundle_id=bundle_id, limit=1)
        return apps[0] if apps else None
