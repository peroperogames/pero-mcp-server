"""
App Store Connect TestFlight处理器 - 负责测试组和测试者管理
"""

from typing import Any, List, Dict, Optional

from ..models import BetaGroup, BetaTester
from ...mcp_handler_interface import IMCPHandler


class TestFlightHandler(IMCPHandler):
    """TestFlight处理器 - 负责测试组、测试者等TestFlight相关操作"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册 AppStore TestFlight相关工具"""

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
                app = self.client.handlers["AppHandler"].get_app_by_name(app_name)
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
            获取 AppStore 指定应用的TestFlight测试者列表

            Args:
                app_name (str): 应用名称，用于查找对应的应用

            Returns:
                str: TestFlight测试者列表，包括测试者邮箱、状态、加入时间等信息
            """
            try:
                app = self.client.handlers["AppHandler"].get_app_by_name(app_name)
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
            """AppStore 从TestFlight测试组中移除测试者"""
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
            """AppStore 获取TestFlight测试者资源"""
            try:
                apps = self.client.handlers["AppHandler"].get_apps()
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
        try:
            # 首先获取应用的所有测试组
            groups = self.get_beta_groups_for_app(app_id)
            if not groups:
                print(f"应用 {app_id} 没有找到任何测试组")
                return []

            print(f"找到 {len(groups)} 个测试组，开始获取测试者...")

            unique_testers = {}  # 用于去重，key 为 email

            # 遍历每个测试组，获取其中的测试者
            for group in groups:
                try:
                    print(f"正在获取测试组 '{group.name}' (ID: {group.id}) 的测试者...")

                    # 获取该测试组的所有测试者
                    group_testers = self.get_beta_testers_for_group(group.id)

                    # 添加到去重字典中
                    for tester in group_testers:
                        unique_testers[tester.email] = tester

                    print(f"测试组 '{group.name}' 有 {len(group_testers)} 个测试者")

                except Exception as group_error:
                    print(f"获取测试组 '{group.name}' (ID: {group.id}) 的测试者失败: {str(group_error)}")
                    # 继续处理下一个测试组，不中断整个流程
                    continue

            # 转换为列表并返回
            all_testers = list(unique_testers.values())
            print(f"总共获取到 {len(all_testers)} 个唯一的测试者")

            return all_testers

        except Exception as e:
            print(f"获取应用 {app_id} 的测试者失败: {str(e)}")
            raise Exception(f"无法获取应用 {app_id} 的测试者列表: {str(e)}")

    def get_beta_testers_for_group(self, group_id: str) -> List[BetaTester]:
        """获取指定测试组的测试人员列表"""
        try:
            response = self.client.make_api_request(
                f"betaGroups/{group_id}/betaTesters",
                method="GET",
                data={
                    "fields[betaTesters]": "email,firstName,lastName,state",
                    "limit": "200"  # 设置分页限制
                }
            )

            testers = []
            for tester_data in response.get("data", []):
                tester = BetaTester.from_api_response(tester_data)
                testers.append(tester)

            return testers

        except Exception as e:
            print(f"获取测试组 {group_id} 的测试者失败: {str(e)}")
            raise Exception(f"无法获取测试组 {group_id} 的测试者列表: {str(e)}")

    def find_beta_tester_by_email(self, email: str, app_name: str) -> Optional[BetaTester]:
        """根据邮箱查找TestFlight测试者"""
        app = self.client.handlers["AppHandler"].get_app_by_name(app_name)
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
