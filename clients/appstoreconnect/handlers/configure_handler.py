"""
App Store Connect 配置处理器 - 负责配置管理
"""

from typing import Any

from ...i_mcp_handler import IMCPHandler


class ConfigureHandler(IMCPHandler):
    """配置处理器 - 负责App Store Connect配置管理"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册配置相关工具"""
        pass

    def register_resources(self, mcp: Any) -> None:
        """注册配置相关资源"""
        # 配置处理器暂时不需要资源
        pass

    def register_prompts(self, mcp: Any) -> None:
        """注册配置相关提示"""
        pass
