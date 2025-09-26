"""
MCP处理器基础接口 - 定义注册工具、资源和提示的接口
"""

from abc import ABC, abstractmethod
from typing import Any


class IMCPHandler(ABC):
    """MCP处理器基础接口"""

    @abstractmethod
    def register_tools(self, mcp: Any) -> None:
        """注册工具到MCP实例"""
        pass

    @abstractmethod
    def register_resources(self, mcp: Any) -> None:
        """注册资源到MCP实例"""
        pass

    @abstractmethod
    def register_prompts(self, mcp: Any) -> None:
        """注册提示到MCP实例"""
        pass
