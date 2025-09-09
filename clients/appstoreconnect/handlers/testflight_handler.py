"""
App Store Connect TestFlight处理器 - 负责测试组和测试者管理
"""

from typing import Any, List, Dict, Optional
from ...i_mcp_handler import IMCPHandler
from ..models import BetaGroup, BetaTester


class TestFlightHandler(IMCPHandler):
    """TestFlight处理器 - 负责测试组、测试者等TestFlight相关操作"""

    def __init__(self, client, app_handler):
        self.client = client
        self.app_handler = app_handler

    def register_tools(self, mcp: Any) -> None:
        """注册TestFlight相关工具"""

        @mcp.tool("get_beta_groups")
        def get_beta_groups_tool(app_name: str) -> str:
            """
            获取指定应用的TestFlight测试组列表

            Args:
                app_name (str): 应用名称，用于查找对应的应用

            Returns:
                str: TestFlight测试组列表，包括组名和组类型（内部/外部测试组）
            """
            try:
                app = self.app_handler.get_app_by_name(app_name)
                if not app:
                    return f"未找到应用: {app_name}"

                groups = self.get_beta_groups_for_app(app.id)
                if not groups:
                    return f"应用 {app_name} 没有TestFlight测试组"

                result = f"应用 {app_name} 的测试组:\n"
                for group in groups:
                    result += f"- {group.name} ({group.group_type}测试组)\n"

                return result
            except Exception as e:
                return f"获取测试组失败: {str(e)}"

        @mcp.tool("get_beta_testers")
        def get_beta_testers_tool(app_name: str) -> str:
            """
            获取指定应用的TestFlight测试者列表

            Args:
                app_name (str): 应用名称，用于查找对应的应用

            Returns:
                str: TestFlight测试者列表，包括测试者邮箱、状态、加入时间等信息
            """
            try:
                app = self.app_handler.get_app_by_name(app_name)
                if not app:
                    return f"未找到应用: {app_name}"

                testers = self.get_beta_testers_for_app(app.id)
                if not testers:
                    return f"应用 {app_name} 没有TestFlight测试者"

                result = f"应用 {app_name} 的TestFlight测试者 ({len(testers)} 个):\n"
                for tester in testers:
                    result += f"- {tester.email} ({tester.full_name}) - 状态: {tester.state_description}\n"

                return result
            except Exception as e:
                return f"获取TestFlight测试者失败: {str(e)}"

        @mcp.tool("remove_testflight_tester")
        def remove_testflight_tester_tool(email: str, app_name: str) -> str:
            """从TestFlight测试组中移除测试者"""
            try:
                self.remove_beta_tester(email, app_name)
                return f"已成功从应用 {app_name} 的TestFlight测试组中移除用户 {email}"
            except ValueError as e:
                return str(e)
            except Exception as e:
                return f"移除TestFlight测试者失败: {str(e)}"

    def register_resources(self, mcp: Any) -> None:
        """注册TestFlight相关资源"""

        @mcp.resource("appstore://beta-testers")
        def get_beta_testers_resource() -> str:
            """获取TestFlight测试者资源"""
            try:
                apps = self.app_handler.get_apps()
                if not apps:
                    return "没有找到可用应用"

                all_testers = []
                for app in apps:
                    try:
                        testers = self.get_beta_testers_for_app(app.id)
                        for tester in testers:
                            all_testers.append(f"{tester.email} - {app.name}")
                    except Exception as e:
                        print(f"获取应用 {app.name} 的测试者失败: {str(e)}")
                        continue

                if not all_testers:
                    return "没有找到TestFlight测试者"

                return f"所有TestFlight测试者:\n" + "\n".join([f"- {tester}" for tester in all_testers])
            except Exception as e:
                return f"获取TestFlight测试者失败: {str(e)}"

    def register_prompts(self, mcp: Any) -> None:
        """注册TestFlight相关提示"""
        # TestFlight处理器暂时不需要特定的提示
        pass

    # =============================================================================
    # 业务逻辑方法
    # =============================================================================

    def get_beta_groups_for_app(self, app_id: str) -> List[BetaGroup]:
        """获取应用的TestFlight测试组"""
        response = self.client.make_api_request(f"apps/{app_id}/betaGroups")
        groups = []
        for group_data in response.get("data", []):
            group = BetaGroup.from_api_response(group_data)
            groups.append(group)
        return groups

    def get_beta_testers_for_app(self, app_id: str) -> List[BetaTester]:
        """获取应用的TestFlight测试者列表"""
        response = self.client.make_api_request(f"apps/{app_id}/betaTesters")
        testers = []
        for tester_data in response.get("data", []):
            tester = BetaTester.from_api_response(tester_data)
            testers.append(tester)
        return testers

    def find_beta_tester_by_email(self, email: str, app_name: str) -> Optional[BetaTester]:
        """根据邮箱查找TestFlight测试者"""
        app = self.app_handler.get_app_by_name(app_name)
        if not app:
            return None

        testers = self.get_beta_testers_for_app(app.id)
        for tester in testers:
            if tester.email.lower() == email.lower():
                return tester
        return None

    def add_beta_tester(self, email: str, first_name: str, beta_group_ids: List[str]) -> Dict[str, Any]:
        """添加TestFlight测试者"""
        last_name = "peropero"  # 默认姓氏
        data = {
            "data": {
                "type": "betaTesters",
                "attributes": {
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name
                },
                "relationships": {
                    "betaGroups": {
                        "data": [{"type": "betaGroups", "id": group_id} for group_id in beta_group_ids]
                    }
                }
            }
        }
        return self.client.make_api_request("betaTesters", method="POST", data=data)

    def remove_beta_tester(self, email: str, app_name: str) -> Dict[str, Any]:
        """从TestFlight中移除测试者"""
        tester = self.find_beta_tester_by_email(email, app_name)
        if not tester:
            raise ValueError(f"用户 {email} 不在应用 {app_name} 的TestFlight测试组中")

        tester_id = tester.id

        # 调用删除API
        return self.client.make_api_request(f"betaTesters/{tester_id}", method="DELETE")
