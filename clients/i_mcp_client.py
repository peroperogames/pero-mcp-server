"""
MCP 客户端接口
"""

from abc import ABC, abstractmethod
from typing import Any


class IMCPClient(ABC):
    """MCP 功能客户端接口"""

    @abstractmethod
    def register_tools(self, mcp: Any) -> None:
        """注册工具到FastMCP实例

        Args:
            mcp: FastMCP实例
        """
        pass

    @abstractmethod
    def register_resources(self, mcp: Any) -> None:
        """注册资源到FastMCP实例

        Args:
            mcp: FastMCP实例
        """
        pass

    @abstractmethod
    def register_prompts(self, mcp: Any) -> None:
        """注册提示到FastMCP实例

        Args:
            mcp: FastMCP实例
        """
        pass

    def get_name(self) -> str:
        """获取客户端名称

        Returns:
            客户端名称
        """
        return self.__class__.__name__.replace("MCPClient", "").replace("MCP", "")
