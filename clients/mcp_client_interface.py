"""
MCP 客户端接口
"""

import importlib
import inspect
import pkgutil
from abc import ABC
from typing import Any, Dict

from .mcp_handler_interface import IMCPHandler


class IMCPClient(ABC):
    """MCP 功能客户端接口"""

    def __init__(self):
        """初始化客户端并自动发现处理器"""
        self.handlers = self._auto_discover_handlers()

    def _auto_discover_handlers(self) -> Dict[str, IMCPHandler]:
        """通过反射自动发现并实例化所有处理器"""
        handlers = {}

        # 动态获取当前类所在模块的路径，然后添加.handlers
        current_module = self.__class__.__module__  # 例如: clients.appstoreconnect.appstore_connect_mcp_client
        # 提取包路径（移除文件名部分）
        package_path = '.'.join(current_module.split('.')[:-1])  # clients.appstoreconnect
        handlers_package = f"{package_path}.handlers"

        try:
            # 导入handlers包
            handlers_module = importlib.import_module(handlers_package)
            handlers_path = handlers_module.__path__

            # 遍历handlers包中的所有模块
            for _, module_name, _ in pkgutil.iter_modules(handlers_path):
                if module_name.startswith('_'):  # 跳过私有模块
                    continue

                try:
                    # 动态导入模块
                    full_module_name = f"{handlers_package}.{module_name}"
                    module = importlib.import_module(full_module_name)

                    # 检查模块中的所有类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # 检查是否是IMCPHandler的子类且不是抽象类
                        if (issubclass(obj, IMCPHandler) and
                                obj != IMCPHandler and
                                not inspect.isabstract(obj)):
                            # 实例化处理器
                            handler_instance = obj(self)
                            handlers[name] = handler_instance

                            print(f"自动注册处理器: {name}")

                except ImportError as e:
                    print(f"导入模块 {module_name} 失败: {e}")
                    continue

        except ImportError as e:
            print(f"导入handlers包失败: {e}")

        return handlers

    def register_tools(self, mcp: Any) -> None:
        """注册所有工具到FastMCP实例

        Args:
            mcp: FastMCP实例
        """
        for handler in self.handlers.values():
            handler.register_tools(mcp)

    def register_resources(self, mcp: Any) -> None:
        """注册所有资源到FastMCP实例

        Args:
            mcp: FastMCP实例
        """
        for handler in self.handlers.values():
            handler.register_resources(mcp)

    def register_prompts(self, mcp: Any) -> None:
        """注册所有提示到FastMCP实例

        Args:
            mcp: FastMCP实例
        """
        for handler in self.handlers.values():
            handler.register_prompts(mcp)

    def get_name(self) -> str:
        """获取客户端名称

        Returns:
            客户端名称
        """
        return self.__class__.__name__.replace("MCPClient", "").replace("MCP", "")
