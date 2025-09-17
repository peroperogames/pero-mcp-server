"""
App Store Connect 配置处理器 - 负责配置管理
"""

from typing import Any
from ...i_mcp_handler import IMCPHandler
from ..models import AppStoreConnectConfig


class ConfigureHandler(IMCPHandler):
    """配置处理器 - 负责App Store Connect配置管理"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册配置相关工具"""

        @mcp.tool("configure_appstore")
        def configure_appstore(key_id: str, issuer_id: str, private_key: str, vendor_number: str) -> str:
            """配置App Store Connect凭据"""
            config = AppStoreConnectConfig(
                key_id=key_id,
                issuer_id=issuer_id,
                private_key=private_key,
                vendor_number=vendor_number
            )
            self.client.set_config(config)
            return "App Store Connect 配置已成功设置"

    def register_resources(self, mcp: Any) -> None:
        """注册配置相关资源"""
        # 配置处理器暂时不需要资源
        pass

    def register_prompts(self, mcp: Any) -> None:
        """注册配置相关提示"""

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
