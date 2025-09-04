"""
App Store Connect MCP 客户端 - 整合了客户端和服务器功能
"""

import os
import jwt
import time
import requests
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable

from ..i_mcp_client import IMCPClient
from .models import AppStoreConnectConfig


class AppStoreConnectMCPClient(IMCPClient):
    """App Store Connect MCP 客户端 - 实现 IMCPClient 接口"""

    def __init__(self):
        """初始化客户端"""
        self.config = None
        self._polling_tasks = {}  # 存储正在进行的轮询任务
        self._status_callbacks = {}  # 存储状态回调函数

    # =============================================================================
    # MCP 接口方法 - 对外提供的主要接口
    # =============================================================================

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

        @mcp.tool("check_user_invitations")
        def check_invitations_tool() -> str:
            """检查待处理的用户邀请"""
            try:
                invitations = self.get_user_invitations()
                if not invitations:
                    return "当前没有待处理的邀请"

                result = f"待处理邀请 ({len(invitations)} 个):\n"
                for inv in invitations:
                    result += f"- {inv['email']} ({inv['first_name']} {inv['last_name']}) - 角色: {', '.join(inv['roles'])} - 过期时间: {inv['expires']}\n"
                return result
            except Exception as e:
                return f"获取邀请列表失败: {str(e)}"

        @mcp.tool("get_beta_groups")
        def get_beta_groups_tool(app_name: str) -> str:
            """获取应用的TestFlight测试组列表"""
            try:
                app = self.get_app_by_name(app_name)
                if not app:
                    return f"未找到应用: {app_name}"

                groups = self.get_beta_groups_for_app(app["id"])
                if not groups:
                    return f"应用 {app_name} 没有TestFlight测试组"

                result = f"应用 {app_name} 的测试组:\n"
                for group in groups:
                    group_type = "内部" if group["is_internal_group"] else "外部"
                    result += f"- {group['name']} ({group_type}测试组)\n"

                return result
            except Exception as e:
                return f"获取测试组失败: {str(e)}"

        @mcp.tool("invite_user_with_polling")
        def invite_user_with_polling_tool(email: str, app_name: str, role: str = "CUSTOMER_SUPPORT") -> str:
            """邀请用户加入团队并异步等待其接受邀请后添加到TestFlight（带轮询监控）"""
            # 从邮箱自动提取用户名
            first_name = self._extract_first_name_from_email(email)

            # 角色映射
            role_mapping = {
                "管理员": "ADMIN",
                "财务": "FINANCE",
                "开发者": "DEVELOPER",
                "营销": "MARKETING",
                "客服": "CUSTOMER_SUPPORT"
            }

            mapped_role = role_mapping.get(role, role.upper())
            roles = [mapped_role]

            # 定义状态回调函数（简单打印，实际使用中可以记录到日志）
            def status_callback(user_email: str, status: str):
                print(f"[轮询状态] {user_email}: {status}")

            return self.invite_user_and_wait_for_testflight(email, first_name, app_name, roles, status_callback)

        @mcp.tool("get_polling_status")
        def get_polling_status_tool(email: Optional[str] = None) -> str:
            """获取轮询任务状态"""
            try:
                status = self.get_polling_status(email)

                if email:
                    # 单个用户状态
                    if 'error' in status:
                        return status['error']
                    else:
                        return f"用户 {status['email']} 的轮询状态:\n" + \
                               f"- 任务ID: {status['task_id']}\n" + \
                               f"- 应用: {status['app_name']}\n" + \
                               f"- 状态: {status['status']}\n" + \
                               f"- 已运行: {status['elapsed_minutes']:.0f} 分钟\n" + \
                               f"- 线程活跃: {'是' if status['thread_alive'] else '否'}"
                else:
                    # 所有任务状态
                    if status['total_count'] == 0:
                        return "当前没有运行中的轮询任务"

                    result = f"运行中的轮询任务 ({status['total_count']} 个):\n"
                    for task_id, task_info in status['tasks'].items():
                        result += f"- {task_info['email']} ({task_info['app_name']}) - " + \
                                f"状态: {task_info['status']} - " + \
                                f"运行: {task_info['elapsed_minutes']:.0f}分钟 - " + \
                                f"活跃: {'是' if task_info['thread_alive'] else '否'}\n"
                    return result

            except Exception as e:
                return f"获取轮询状态失败: {str(e)}"

        @mcp.tool("cancel_polling_task")
        def cancel_polling_task_tool(email: str) -> str:
            """取消指定用户的轮询任务"""
            try:
                return self.cancel_polling_task(email)
            except Exception as e:
                return f"取消轮询任务失败: {str(e)}"

        @mcp.tool("remove_team_member")
        def remove_team_member_tool(email: str) -> str:
            """从团队中移除成员"""
            try:
                self.remove_team_member(email)
                return f"已成功从团队中移除用户 {email}"
            except ValueError as e:
                return str(e)
            except Exception as e:
                return f"移除团队成员失败: {str(e)}"

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

        @mcp.tool("remove_user_completely")
        def remove_user_completely_tool(email: str, app_name: str) -> str:
            """完全移除用户（从团队和TestFlight中移除）"""
            try:
                return self.remove_user_completely(email, app_name)
            except Exception as e:
                return f"完全移除用户失败: {str(e)}"

        @mcp.tool("get_beta_testers")
        def get_beta_testers_tool(app_name: str) -> str:
            """获取应用的TestFlight测试者列表"""
            try:
                app = self.get_app_by_name(app_name)
                if not app:
                    return f"未找到应用: {app_name}"

                testers = self.get_beta_testers_for_app(app["id"])
                if not testers:
                    return f"应用 {app_name} 没有TestFlight测试者"

                result = f"应用 {app_name} 的TestFlight测试者 ({len(testers)} 个):\n"
                for tester in testers:
                    result += f"- {tester['email']} ({tester['first_name']} {tester['last_name']}) - 状态: {tester['state']}\n"

                return result
            except Exception as e:
                return f"获取TestFlight测试者失败: {str(e)}"

    def register_resources(self, mcp) -> None:
        """注册App Store Connect资源到FastMCP实例"""

        @mcp.resource("appstore://apps")
        def get_apps_resource() -> str:
            """获取应用列表资源"""
            try:
                apps = self.get_apps()
                return f"应用列表:\n" + "\n".join([f"- {app['name']} ({app['bundle_id']})" for app in apps])
            except Exception as e:
                return f"获取应用列表失败: {str(e)}"

        @mcp.resource("appstore://team-members")
        def get_team_members_resource() -> str:
            """获取团队成员资源"""
            try:
                members = self.get_team_members()
                return f"团队成员列表:\n" + "\n".join([f"- {m['email']} ({m['first_name']} {m['last_name']})" for m in members])
            except Exception as e:
                return f"获取团队成员失败: {str(e)}"

        @mcp.resource("appstore://invitations")
        def get_invitations_resource() -> str:
            """获取邀请列表资源"""
            try:
                invitations = self.get_user_invitations()
                if not invitations:
                    return "当前没有待处理的邀请"
                return f"待处理邀请:\n" + "\n".join([f"- {inv['email']} ({inv['first_name']} {inv['last_name']})" for inv in invitations])
            except Exception as e:
                return f"获取邀请列表失败: {str(e)}"

        @mcp.resource("appstore://beta-testers")
        def get_beta_testers_resource() -> str:
            """获取TestFlight测试者资源"""
            try:
                apps = self.get_apps()
                if not apps:
                    return "没有找到可用应用"

                all_testers = []
                for app in apps:
                    try:
                        testers = self.get_beta_testers_for_app(app["id"])
                        for tester in testers:
                            all_testers.append(f"{tester['email']} - {app['name']}")
                    except:
                        continue

                if not all_testers:
                    return "没有找到TestFlight测试者"

                return f"所有TestFlight测试者:\n" + "\n".join([f"- {tester}" for tester in all_testers])
            except Exception as e:
                return f"获取TestFlight测试者失败: {str(e)}"

    def register_prompts(self, mcp) -> None:
        """注册App Store Connect提示到FastMCP实例"""

        @mcp.prompt("appstore_invite_user")
        def appstore_invite_user_prompt(email: str = "", name: str = "", app_name: str = "", role: str = "") -> str:
            """App Store Connect邀请用户提示"""
            return f"""App Store Connect 用户邀请助手

邀请信息:
- 邮箱: {email}
- 姓名: {name}
- 应用: {app_name}
- 角色: {role}

支持的角色类型:
- 管理员 (ADMIN): 完全访问权限
- 财务 (FINANCE): 财务和销售报告访问
- 开发者 (DEVELOPER): 开发和测试访问
- 营销 (MARKETING): 营销和应用商店访问
- 客服 (CUSTOMER_SUPPORT): 客户支持访问

使用步骤:
1. 确认用户信息正确
2. 选择合适的角色
3. 使用 invite_user_to_team 工具发送邀请
4. 用户会自动添加到TestFlight内部测试组

注意事项:
- 邀请邮件会发送到用户邮箱
- 用户需要接受邀请才能加入团队
- TestFlight会自动添加到第一个内部测试组
"""

        @mcp.prompt("appstore_troubleshoot")
        def appstore_troubleshoot_prompt(issue: str = "") -> str:
            """App Store Connect故障排除提示"""
            return f"""App Store Connect 故障排除助手

当前问题: {issue}

常见问题排查:

1. 认证问题:
   - 检查 API Key ID 是否正确
   - 验证 Issuer ID 是否匹配
   - 确认私钥格式是否正确 (ES256)
   - 检查令牌是否过期

2. 权限问题:
   - 确认 API Key 具有足够权限
   - 检查应用访问权限
   - 验证团队成员权限

3. 邀请问题:
   - 确认邮箱地址正确
   - 检查用户是否已在团队中
   - 验证应用名称是否存在
   - 确认角色类型是否支持

4. TestFlight问题:
   - 检查应用是否有内部测试组
   - 确认测试组设置正确
   - 验证用户邮箱格式

诊断工具:
- get_apps: 查看可用应用
- get_team_members: 查看当前团队成员
- check_user_invitations: 查看待处理邀请
- get_beta_groups: 查看TestFlight测试组
"""

        @mcp.prompt("appstore_setup_guide")
        def appstore_setup_guide_prompt() -> str:
            """App Store Connect设置指南"""
            return """App Store Connect 设置指南

初始配置:
1. 登录 App Store Connect
2. 进入 用户和访问 > 密钥
3. 创建新的 API 密钥
4. 下载私钥文件 (.p8)
5. 记录 Key ID 和 Issuer ID

环境变量配置:
```bash
export APPSTORE_KEY_ID="your_key_id"
export APPSTORE_ISSUER_ID="your_issuer_id"
export APPSTORE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
export APPSTORE_APP_ID="your_app_id"  # 可选
```

或使用工具配置:
```
configure_appstore(
    key_id="your_key_id",
    issuer_id="your_issuer_id",
    private_key="your_private_key",
    app_id="your_app_id"
)
```

权限要求:
- API Key 需要 "Admin" 或 "App Manager" 角色
- 确保对目标应用有访问权限

常用工作流:
1. 配置认证信息
2. 获取应用列表确认访问
3. 邀请用户并设置TestFlight
4. 检查邀请状态
"""

        @mcp.prompt("appstore_remove_user")
        def appstore_remove_user_prompt(email: str = "", app_name: str = "", operation: str = "") -> str:
            """App Store Connect移除用户提示"""
            return f"""App Store Connect 用户移除助手

移除信息:
- 用户邮箱: {email}
- 应用名称: {app_name}  
- 操作类型: {operation}

支持的移除操作:
- remove_team_member: 仅从团队中移除用户
- remove_testflight_tester: 仅从TestFlight测试组中移除用户
- remove_user_completely: 完全移除用户（从团队和TestFlight中移除）

使用步骤:
1. 确认用户邮箱正确
2. 选择合适的移除操作
3. 如果是TestFlight相关操作，确认应用名称
4. 使用相应的工具执行移除操作

注意事项:
- 移除操作不可逆，请谨慎操作
- 从团队移除用户会自动撤销其所有权限
- 从TestFlight移除仅影响测试访问权限
- 完全移除会同时处理团队和TestFlight权限

安全提示:
⚠️ 移除用户前请确认：
- 用户确实不再需要访问权限
- 已通知相关人员此操作
- 备份重要的用户相关数据（如测试反馈）

移除后果:
- 用户将无法访问App Store Connect
- 用户将无法下载TestFlight构建版本
- 用户的测试数据和反馈将被保留
"""

    # =============================================================================
    # 核心业务方法 - App Store Connect API 操作
    # =============================================================================

    def get_apps(self) -> List[Dict[str, str]]:
        """获取应用列表"""
        response = self._make_api_request("apps")
        apps = []
        for app in response.get("data", []):
            # 安全地获取属性，避免KeyError
            attributes = app.get("attributes", {})
            apps.append({
                "id": app.get("id", ""),
                "name": attributes.get("name", "未知应用"),
                "bundle_id": attributes.get("bundleId", ""),
                "platform": attributes.get("platform", "UNKNOWN")
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

    def get_user_invitations(self) -> List[Dict[str, Any]]:
        """获取用户邀请列表"""
        response = self._make_api_request("userInvitations")
        invitations = []
        for invitation in response.get("data", []):
            invitations.append({
                "id": invitation["id"],
                "email": invitation["attributes"]["email"],
                "first_name": invitation["attributes"]["firstName"],
                "last_name": invitation["attributes"]["lastName"],
                "roles": invitation["attributes"]["roles"],
                "expires": invitation["attributes"]["expirationDate"]
            })
        return invitations

    def get_app_by_name(self, app_name: str) -> Optional[Dict[str, str]]:
        """根据应用名称获取应用信息"""
        apps = self.get_apps()
        for app in apps:
            if app["name"].lower() == app_name.lower():
                return app
        return None

    def get_beta_groups_for_app(self, app_id: str) -> List[Dict[str, Any]]:
        """获取应用的TestFlight测试组"""
        response = self._make_api_request(f"apps/{app_id}/betaGroups")
        groups = []
        for group in response.get("data", []):
            groups.append({
                "id": group["id"],
                "name": group["attributes"]["name"],
                "is_internal_group": group["attributes"]["isInternalGroup"]
            })
        return groups

    def get_beta_testers_for_app(self, app_id: str) -> List[Dict[str, Any]]:
        """获取应用的TestFlight测试者列表"""
        response = self._make_api_request(f"apps/{app_id}/betaTesters")
        testers = []
        for tester in response.get("data", []):
            testers.append({
                "id": tester["id"],
                "email": tester["attributes"]["email"],
                "first_name": tester["attributes"]["firstName"],
                "last_name": tester["attributes"]["lastName"],
                "state": tester["attributes"]["state"]
            })
        return testers

    def check_user_in_team(self, email: str) -> Optional[Dict[str, Any]]:
        """检查用户是否已在团队中"""
        members = self.get_team_members()
        for member in members:
            if member["email"].lower() == email.lower():
                return member
        return None

    def find_beta_tester_by_email(self, email: str, app_name: str) -> Optional[Dict[str, Any]]:
        """根据邮箱查找TestFlight测试者"""
        app = self.get_app_by_name(app_name)
        if not app:
            return None

        testers = self.get_beta_testers_for_app(app["id"])
        for tester in testers:
            if tester["email"].lower() == email.lower():
                return tester
        return None

    def invite_user_to_team(self, email: str, first_name: str, roles: List[str], apps: List[str]) -> Dict[str, Any]:
        """邀请用户加入团队"""
        last_name = "peropero"  # 默认姓氏
        data = {
            "data": {
                "type": "userInvitations",
                "attributes": {
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "roles": roles,
                    "allAppsVisible": False
                },
                "relationships": {
                    "visibleApps": {
                        "data": [{"type": "apps", "id": app_id} for app_id in apps]
                    }
                }
            }
        }
        return self._make_api_request("userInvitations", method="POST", data=data)

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
        return self._make_api_request("betaTesters", method="POST", data=data)

    def remove_team_member(self, email: str) -> Dict[str, Any]:
        """从团队中移除成员"""
        # 首先获取用户信息
        member = self.check_user_in_team(email)
        if not member:
            raise ValueError(f"用户 {email} 不在团队中")

        user_id = member["id"]

        # 调用删除API
        return self._make_api_request(f"users/{user_id}", method="DELETE")

    def remove_beta_tester(self, email: str, app_name: str) -> Dict[str, Any]:
        """从TestFlight中移除测试者"""
        tester = self.find_beta_tester_by_email(email, app_name)
        if not tester:
            raise ValueError(f"用户 {email} 不在应用 {app_name} 的TestFlight测试组中")

        tester_id = tester["id"]

        # 调用删除API
        return self._make_api_request(f"betaTesters/{tester_id}", method="DELETE")

    def remove_user_completely(self, email: str, app_name: str) -> str:
        """完全移除用户（从团队和TestFlight中移除）"""
        results = []

        try:
            # 1. 从TestFlight中移除
            try:
                self.remove_beta_tester(email, app_name)
                results.append(f"已从应用 {app_name} 的TestFlight测试组中移除用户 {email}")
            except ValueError as e:
                if "不在应用" in str(e):
                    results.append(f"用户 {email} 未在应用 {app_name} 的TestFlight测试组中")
                else:
                    results.append(f"从TestFlight移除用户失败: {str(e)}")
            except Exception as e:
                results.append(f"从TestFlight移除用户失败: {str(e)}")

            # 2. 从团队中移除
            try:
                self.remove_team_member(email)
                results.append(f"已从团队中移除用户 {email}")
            except ValueError as e:
                if "不在团队中" in str(e):
                    results.append(f"用户 {email} 未在团队中")
                else:
                    results.append(f"从团队移除用户失败: {str(e)}")
            except Exception as e:
                results.append(f"从团队移除用户失败: {str(e)}")

            return "\n".join(results)

        except Exception as e:
            return f"移除用户过程中发生错误: {str(e)}"

    def invite_user_and_wait_for_testflight(self, email: str, first_name: str, app_name: str,
                                           roles: List[str], status_callback: Optional[Callable[[str, str], None]] = None) -> str:
        """邀请用户加入团队，并异步等待其接受邀请后添加到TestFlight"""
        try:
            # 1. 检查用户是否已在团队中
            existing_member = self.check_user_in_team(email)
            if existing_member:
                # 用户已在团队中，直接添加到TestFlight
                app = self.get_app_by_name(app_name)
                if not app:
                    return f"未找到应用: {app_name}"

                beta_groups = self.get_beta_groups_for_app(app["id"])
                internal_groups = [group for group in beta_groups if group["is_internal_group"]]

                if not internal_groups:
                    return f"警告: 应用 {app_name} 没有内部测试组"

                default_group = internal_groups[0]
                try:
                    self.add_beta_tester(email, first_name, [default_group["id"]])
                    return f"用户 {email} 已在团队中，已直接添加到TestFlight测试组: {default_group['name']}"
                except Exception as e:
                    if "already exists" in str(e).lower():
                        return f"用户 {email} 已在团队和TestFlight测试组中"
                    else:
                        return f"添加TestFlight测试者失败: {str(e)}"

            # 2. 获取应用信息
            app = self.get_app_by_name(app_name)
            if not app:
                return f"未找到应用: {app_name}"

            # 3. 邀请用户到团队
            try:
                self.invite_user_to_team(email, first_name, roles, [app["id"]])
            except Exception as e:
                return f"邀请用户失败: {str(e)}"

            # 4. 启动异步轮询监控
            self._poll_user_acceptance(email, first_name, app_name, status_callback=status_callback)

            return f"已邀请用户 {email} 加入团队（角色: {', '.join(roles)}），正在后台监控用户接受邀请状态。监控时间最长2小时，每5分钟检查一次。"

        except Exception as e:
            return f"操作失败: {str(e)}"

    def get_polling_status(self, email: Optional[str] = None) -> Dict[str, Any]:
        """获取轮询任务状态"""
        if email:
            # 查找指定用户的任务
            for task_id, task_info in self._polling_tasks.items():
                if task_info['email'].lower() == email.lower():
                    elapsed = datetime.now() - task_info['start_time']
                    return {
                        'task_id': task_id,
                        'email': task_info['email'],
                        'app_name': task_info['app_name'],
                        'status': task_info['status'],
                        'elapsed_minutes': elapsed.total_seconds() // 60,
                        'thread_alive': task_info['thread'].is_alive()
                    }
            return {'error': f'未找到用户 {email} 的轮询任务'}
        else:
            # 返回所有任务状态
            tasks = {}
            for task_id, task_info in self._polling_tasks.items():
                elapsed = datetime.now() - task_info['start_time']
                tasks[task_id] = {
                    'email': task_info['email'],
                    'app_name': task_info['app_name'],
                    'status': task_info['status'],
                    'elapsed_minutes': elapsed.total_seconds() // 60,
                    'thread_alive': task_info['thread'].is_alive()
                }
            return {'tasks': tasks, 'total_count': len(tasks)}

    def cancel_polling_task(self, email: str) -> str:
        """取消指定用户的轮询任务"""
        task_to_remove = None
        for task_id, task_info in self._polling_tasks.items():
            if task_info['email'].lower() == email.lower():
                task_to_remove = task_id
                break

        if task_to_remove:
            del self._polling_tasks[task_to_remove]
            if email in self._status_callbacks:
                del self._status_callbacks[email]
            return f"已取消用户 {email} 的轮询任务"
        else:
            return f"未找到用户 {email} 的轮询任务"

    # =============================================================================
    # 私有辅助方法 - 内部使用的工具方法
    # =============================================================================

    def _load_config_from_env(self) -> Optional[AppStoreConnectConfig]:
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

        app_id = os.getenv('APPSTORE_APP_ID')

        if not all([key_id, issuer_id, private_key]):
            return None

        return AppStoreConnectConfig(
            key_id=key_id,
            issuer_id=issuer_id,
            private_key=private_key,
            app_id=app_id
        )

    @classmethod
    def _load_private_key_from_file(cls) -> Optional[str]:
        """从文件加载私钥"""
        key_path = os.getenv('APPSTORE_PRIVATE_KEY_PATH')
        if key_path and os.path.exists(key_path):
            try:
                with open(key_path, 'r') as f:
                    return f.read()
            except Exception:
                pass
        return None

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

    @classmethod
    def _extract_first_name_from_email(cls, email: str) -> str:
        """从邮箱地址提取用户名作为first_name"""
        try:
            return email.split('@')[0]
        except:
            return "User"  # 默认值

    def _poll_user_acceptance(self, email: str, first_name: str, app_name: str,
                             max_duration_hours: int = 2, poll_interval_minutes: int = 5,
                             status_callback: Optional[Callable[[str, str], None]] = None) -> None:
        """轮询检查用户是否接受邀请并加入团队"""
        def polling_thread():
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=max_duration_hours)
            poll_interval = timedelta(minutes=poll_interval_minutes)

            task_id = f"{email}_{int(time.time())}"

            try:
                if status_callback:
                    status_callback(email, f"开始轮询检查用户 {email} 是否接受邀请")

                while datetime.now() < end_time:
                    try:
                        # 检查用户是否已在团队中
                        member = self.check_user_in_team(email)
                        if member:
                            if status_callback:
                                status_callback(email, f"用户 {email} 已接受邀请并加入团队")

                            # 用户已加入团队，现在添加到TestFlight
                            try:
                                app = self.get_app_by_name(app_name)
                                if not app:
                                    if status_callback:
                                        status_callback(email, f"错误: 未找到应用 {app_name}")
                                    return

                                beta_groups = self.get_beta_groups_for_app(app["id"])
                                internal_groups = [group for group in beta_groups if group["is_internal_group"]]

                                if not internal_groups:
                                    if status_callback:
                                        status_callback(email, f"警告: 应用 {app_name} 没有内部测试组")
                                    return

                                default_group = internal_groups[0]
                                self.add_beta_tester(email, first_name, [default_group["id"]])

                                if status_callback:
                                    status_callback(email, f"成功: 用户 {email} 已添加到TestFlight测试组 {default_group['name']}")

                            except Exception as e:
                                if "already exists" in str(e).lower():
                                    if status_callback:
                                        status_callback(email, f"用户 {email} 已在TestFlight测试组中")
                                else:
                                    if status_callback:
                                        status_callback(email, f"添加TestFlight测试者失败: {str(e)}")

                            # 任务完成，清理
                            if task_id in self._polling_tasks:
                                del self._polling_tasks[task_id]
                            return

                        # 用户还未接受邀请，继续等待
                        elapsed = datetime.now() - start_time
                        remaining = end_time - datetime.now()

                        if status_callback:
                            status_callback(email, f"用户 {email} 尚未接受邀请。已等待: {elapsed.seconds//60}分钟，剩余: {remaining.seconds//60}分钟")

                        # 等待下一次轮询
                        time.sleep(poll_interval.total_seconds())

                    except Exception as e:
                        if status_callback:
                            status_callback(email, f"轮询检查时发生错误: {str(e)}")
                        time.sleep(poll_interval.total_seconds())

                # 超时
                if status_callback:
                    status_callback(email, f"超时: 用户 {email} 在 {max_duration_hours} 小时内未接受邀请")

            finally:
                # 清理任务
                if task_id in self._polling_tasks:
                    del self._polling_tasks[task_id]
                if email in self._status_callbacks:
                    del self._status_callbacks[email]

        # 启动轮询线程
        task_id = f"{email}_{int(time.time())}"
        thread = threading.Thread(target=polling_thread, daemon=True)
        thread.start()

        self._polling_tasks[task_id] = {
            'thread': thread,
            'email': email,
            'app_name': app_name,
            'start_time': datetime.now(),
            'status': 'polling'
        }

        if status_callback:
            self._status_callbacks[email] = status_callback
