"""
App Store Connect 用户管理处理器 - 负责团队成员和邀请管理
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Any, List, Callable, Dict
from ...i_mcp_handler import IMCPHandler
from ..models import TeamMember, UserInvitation, ROLE_MAPPING


class UserHandler(IMCPHandler):
    """用户管理处理器 - 负责团队成员、邀请等用户相关操作"""

    def __init__(self, client, app_handler, testflight_handler):
        self.client = client
        self.app_handler = app_handler
        self.testflight_handler = testflight_handler
        self._polling_tasks = {}  # 存储正在进行的轮询任务
        self._status_callbacks = {}  # 存储状态回调函数

    def register_tools(self, mcp: Any) -> None:
        """注册用户管理相关工具"""

        @mcp.tool("get_team_members")
        def get_team_members_tool() -> str:
            """
            获取App Store Connect团队成员列表

            Returns:
                str: 团队成员列表，包括成员邮箱、全名等信息
            """
            try:
                members = self.get_team_members()
                return f"团队共有 {len(members)} 名成员:\n" + "\n".join([f"- {m.email} ({m.full_name})" for m in members])
            except Exception as e:
                return f"获取团队成员失败: {str(e)}"

        @mcp.tool("check_user_invitations")
        def check_invitations_tool() -> str:
            """
            检查App Store Connect中待处理的用户邀请

            Returns:
                str: 待处理邀请列表，包括被邀请者邮箱、角色、状态、过期时间等信息
            """
            try:
                invitations = self.get_user_invitations()
                if not invitations:
                    return "当前没有待处理的邀请"

                result = f"待处理邀请 ({len(invitations)} 个):\n"
                for inv in invitations:
                    status = "已过期" if inv.is_expired else "有效"
                    result += f"- {inv.email} ({inv.full_name}) - 角色: {', '.join(inv.roles)} - 状态: {status} - 过期时间: {inv.expires}\n"
                return result
            except Exception as e:
                return f"获取邀请列表失败: {str(e)}"

        @mcp.tool("invite_user_with_polling")
        def invite_user_with_polling_tool(email: str, app_name: str, role: str = "CUSTOMER_SUPPORT") -> str:
            """
            邀请用户加入团队并异步等待其接受邀请后添加到TestFlight（带轮询监控）

            Args:
                email (str): 被邀请用户的邮箱地址
                app_name (str): 要添加TestFlight权限的应用名称
                role (str, optional): 用户在团队中的角色，默认为"CUSTOMER_SUPPORT"
                    可选值: "ADMIN", "APP_MANAGER", "DEVELOPER", "MARKETING", "SALES", "CUSTOMER_SUPPORT"

            Returns:
                str: 邀请操作的结果信息，包括邀请状态和后续操作说明
            """
            # 从邮箱自动提取用户名
            first_name = email.split('@')[0]

            # 使用角色映射
            mapped_role = ROLE_MAPPING.get(role, role.upper())
            roles = [mapped_role]

            # 定义状态回调函数（简单打印，实际使用中可以记录到日志）
            def status_callback(user_email: str, status: str):
                print(f"[轮询状态] {user_email}: {status}")

            return self.invite_user_and_wait_for_testflight(email, first_name, app_name, roles, status_callback)

        @mcp.tool("get_polling_status")
        def get_polling_status_tool(email: Optional[str] = None) -> str:
            """
            获取用户邀请轮询任务的状态

            Args:
                email (str, optional): 要查询状态的用户邮箱，默认为None（获取所有任务状态）

            Returns:
                str: 轮询任务状态信息，包括任务进度、当前状态等
            """
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
                return f"获取轮询状��失败: {str(e)}"

        @mcp.tool("cancel_polling_task")
        def cancel_polling_task_tool(email: str) -> str:
            """
            取消指定用户的轮询任务

            Args:
                email (str): 要取消轮询任务的用户邮箱地址

            Returns:
                str: 取消操作的结果信息
            """
            try:
                return self.cancel_polling_task(email)
            except Exception as e:
                return f"取消轮询任务失败: {str(e)}"

        @mcp.tool("remove_team_member")
        def remove_team_member_tool(email: str) -> str:
            """
            从App Store Connect团队中移除指定成员

            Args:
                email (str): 要移除的团队成员邮箱地址

            Returns:
                str: 移除操作的结果信息
            """
            try:
                self.remove_team_member(email)
                return f"已成功从团队中移除用户 {email}"
            except ValueError as e:
                return str(e)
            except Exception as e:
                return f"移除团队成员失败: {str(e)}"

        @mcp.tool("remove_user_completely")
        def remove_user_completely_tool(email: str, app_name: str) -> str:
            """
            完全移除用户（同时从团队和TestFlight中移除）

            Args:
                email (str): 要移除的用户邮箱地址
                app_name (str): 要从TestFlight中移除的应用名称

            Returns:
                str: 完全移除操作的详细结果信息，包括团队和TestFlight的移除状态
            """
            try:
                return self.remove_user_completely(email, app_name)
            except Exception as e:
                return f"完全移除用户失败: {str(e)}"

    def register_resources(self, mcp: Any) -> None:
        """注册用户管理相关资源"""

        @mcp.resource("appstore://team-members")
        def get_team_members_resource() -> str:
            """获取团队成员资源"""
            try:
                members = self.get_team_members()
                return f"团队成员列表:\n" + "\n".join([f"- {m.email} ({m.full_name})" for m in members])
            except Exception as e:
                return f"获取团队成员失败: {str(e)}"

        @mcp.resource("appstore://invitations")
        def get_invitations_resource() -> str:
            """获取邀请列表资源"""
            try:
                invitations = self.get_user_invitations()
                if not invitations:
                    return "当前没有待处理的邀请"
                return f"待处理邀请:\n" + "\n".join([f"- {inv.email} ({inv.full_name})" for inv in invitations])
            except Exception as e:
                return f"获取邀请列表失败: {str(e)}"

    def register_prompts(self, mcp: Any) -> None:
        """注册用户管理相关提示"""

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
    # 业务逻辑方法
    # =============================================================================

    def get_team_members(self) -> List[TeamMember]:
        """获取团队成员"""
        response = self.client.make_api_request("users")
        members = []
        for user_data in response.get("data", []):
            member = TeamMember.from_api_response(user_data)
            members.append(member)
        return members

    def get_user_invitations(self) -> List[UserInvitation]:
        """获取用户邀请列表"""
        response = self.client.make_api_request("userInvitations")
        invitations = []
        for invitation_data in response.get("data", []):
            invitation = UserInvitation.from_api_response(invitation_data)
            invitations.append(invitation)
        return invitations

    def check_user_in_team(self, email: str) -> Optional[TeamMember]:
        """检查用户是否已在团队中"""
        members = self.get_team_members()
        for member in members:
            if member.email.lower() == email.lower():
                return member
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
        return self.client.make_api_request("userInvitations", method="POST", data=data)

    def remove_team_member(self, email: str) -> Dict[str, Any]:
        """从团队中移除成员"""
        # 首先获取用户信息
        member = self.check_user_in_team(email)
        if not member:
            raise ValueError(f"用户 {email} 不在团队中")

        user_id = member.id

        # 调用删除API
        return self.client.make_api_request(f"users/{user_id}", method="DELETE")

    def remove_user_completely(self, email: str, app_name: str) -> str:
        """完全移除用户（从团队和TestFlight中移除）"""
        results = []

        try:
            # 1. 从TestFlight中移除
            try:
                self.testflight_handler.remove_beta_tester(email, app_name)
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
                app = self.app_handler.get_app_by_name(app_name)
                if not app:
                    return f"未找到应用: {app_name}"

                beta_groups = self.testflight_handler.get_beta_groups_for_app(app.id)
                internal_groups = [group for group in beta_groups if group.is_internal_group]

                if not internal_groups:
                    return f"警告: 应用 {app_name} 没有内部测试组"

                default_group = internal_groups[0]
                try:
                    self.testflight_handler.add_beta_tester(email, first_name, [default_group.id])
                    return f"用户 {email} 已在团队中，已直接添加到TestFlight测试组: {default_group.name}"
                except Exception as e:
                    if "already exists" in str(e).lower():
                        return f"用户 {email} 已在团队和TestFlight测试组中"
                    else:
                        return f"添加TestFlight测试者失败: {str(e)}"

            # 2. 获取应用信息
            app = self.app_handler.get_app_by_name(app_name)
            if not app:
                return f"未找到应用: {app_name}"

            # 3. 邀请用户到团队
            try:
                self.invite_user_to_team(email, first_name, roles, [app.id])
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

    def _poll_user_acceptance(self, email: str, first_name: str, app_name: str,
                             max_duration_hours: int = 2, poll_interval_minutes: int = 5,
                             status_callback: Optional[Callable[[str, str], None]] = None) -> None:
        """轮询检查用户是否接受邀请并加入团队"""
        def polling_thread():
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=max_duration_hours)
            poll_interval = timedelta(minutes=poll_interval_minutes)

            pool_task_id = f"{email}_{int(time.time())}"

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
                                app = self.app_handler.get_app_by_name(app_name)
                                if not app:
                                    if status_callback:
                                        status_callback(email, f"错误: 未找到应用 {app_name}")
                                    return

                                beta_groups = self.testflight_handler.get_beta_groups_for_app(app.id)
                                internal_groups = [group for group in beta_groups if group.is_internal_group]

                                if not internal_groups:
                                    if status_callback:
                                        status_callback(email, f"警告: 应用 {app_name} 没有内部测试组")
                                    return

                                default_group = internal_groups[0]
                                self.testflight_handler.add_beta_tester(email, first_name, [default_group.id])

                                if status_callback:
                                    status_callback(email, f"成功: 用户 {email} 已添加到TestFlight测试组 {default_group.name}")

                            except Exception as e:
                                if "already exists" in str(e).lower():
                                    if status_callback:
                                        status_callback(email, f"用户 {email} 已在TestFlight测试组中")
                                else:
                                    if status_callback:
                                        status_callback(email, f"添加TestFlight测试者失败: {str(e)}")

                            # 任务完成，清理
                            if pool_task_id in self._polling_tasks:
                                del self._polling_tasks[pool_task_id]
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
                if pool_task_id in self._polling_tasks:
                    del self._polling_tasks[pool_task_id]
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
