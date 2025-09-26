"""
Pero MCP Server - FastMCP 中转站，支持依赖注入
"""

import importlib
import inspect
from pathlib import Path
from typing import List, Type

import dotenv
from fastmcp import FastMCP

from clients.mcp_client_interface import IMCPClient


class PeroMCPServer:
    """Pero MCP Server - FastMCP，支持依赖注入"""

    def __init__(self, name: str = "Pero MCP Server", client_classes: List[Type[IMCPClient]] = None,
                 auto_discover: bool = True):
        """初始化 Pero MCP Server

        Args:
            name: 服务器名称
            client_classes: 客户端类列表，将自动实例化并注册
            auto_discover: 是否自动发现客户端（如果client_classes为空时）
        """
        self.mcp = FastMCP(name)
        self.clients: List[IMCPClient] = []

        # dotenv加载环境变量
        dotenv.load_dotenv()

        # 如果没有提供客户端类且启用自动发现，则自动发现
        if not client_classes and auto_discover:
            client_classes = self.discover_mcp_clients()

        # 自动注册提供的客户端类
        if client_classes:
            self.register_clients(client_classes)

    @classmethod
    def discover_mcp_clients(cls) -> List[Type[IMCPClient]]:
        """自动发现所有MCP客户端类"""
        client_classes = []

        # 获取clients目录路径
        # 使用__file__的父目录来找到clients目录
        current_file = Path(__file__)
        clients_dir = current_file.parent / "clients"

        if not clients_dir.exists():
            print(f"警告: clients目录不存在: {clients_dir}")
            return client_classes

        print("正在自动发现MCP客户端...")

        # 遍历clients目录下的所有子目录
        for subdir in clients_dir.iterdir():
            if subdir.is_dir() and subdir.name != "__pycache__":
                # 查找该目录下的所有Python文件
                for py_file in subdir.glob("*.py"):
                    if py_file.name.startswith("__"):
                        continue

                    # 构建模块路径
                    module_path = f"clients.{subdir.name}.{py_file.stem}"

                    try:
                        # 动态导入模块
                        module = importlib.import_module(module_path)

                        # 检查模块中的所有类
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            # 检查是否继承自IMCPClient且不是接口本身
                            if (issubclass(obj, IMCPClient) and
                                    obj != IMCPClient and
                                    not inspect.isabstract(obj)):
                                client_classes.append(obj)
                                print(f"发现客户端: {name} ({module_path})")

                    except ImportError as e:
                        print(f"导入模块失败 {module_path}: {e}")
                    except Exception as e:
                        print(f"处理模块失败 {module_path}: {e}")

        return client_classes

    def register_clients(self, client_classes: List[Type[IMCPClient]]) -> None:
        """批量注册多个客户端类

        Args:
            client_classes: 客户端类列表（不是实例）
        """
        print(f"开始批量注册 {len(client_classes)} 个客户端...")

        for client_class in client_classes:
            # 实例化客户端
            client = client_class()

            print(f"正在注册 {client.get_name()} 客户端...")

            # 注册工具、资源和提示
            client.register_tools(self.mcp)
            client.register_resources(self.mcp)
            client.register_prompts(self.mcp)

            # 保存客户端引用
            self.clients.append(client)

            print(f"{client.get_name()} 客户端注册完成")

        print("所有客户端注册完成")

    def get_registered_services(self) -> List[str]:
        """获取已注册的服务名称列表

        Returns:
            已注册服务的名称列表
        """
        return [client.get_name() for client in self.clients]

    def run_with_stdio(self) -> None:
        """使用STDIO传输启动服务器"""
        registered_services = self.get_registered_services()
        if registered_services:
            print(f"启动 {self.mcp.name} 服务器 (STDIO 模式)，已注册客户端: {', '.join(registered_services)}")
        else:
            print(f"启动 {self.mcp.name} 服务器 (STDIO 模式)（无注册客户端）")

        self.mcp.run()

    def run_with_http(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """使用HTTP传输启动服务器

        Args:
            host: 服务器主机地址
            port: 端口号
        """
        registered_services = self.get_registered_services()
        if registered_services:
            print(f"启动 {self.mcp.name} 服务器在端口 {port}，已注册客户端: {', '.join(registered_services)}")
        else:
            print(f"启动 {self.mcp.name} 服务器在端口 {port}（无注册客户端）")

        self.mcp.settings.host = host
        self.mcp.settings.port = port
        self.mcp.run("streamable-http")

    def run(self, transport: str = "stdio", host: str = "0.0.0.0", port: int = 8000) -> None:
        """启动服务器（兼容性方法）

        Args:
            transport: 传输方式，'stdio' 或 'http'
            host: 服务器主机地址（仅HTTP模式）
            port: 端口号（仅HTTP模式）
        """
        if transport == "http":
            self.run_with_http(host, port)
        else:
            self.run_with_stdio()

    @classmethod
    def create_and_run(cls, name: str = "Pero MCP Server", transport: str = "stdio",
                       host: str = "0.0.0.0", port: int = 8000) -> None:
        """创建服务器实例并启动（便捷方法）

        Args:
            name: 服务器名称
            transport: 传输方式，'stdio' 或 'http'
            host: 服务器主机地址（仅HTTP模式）
            port: 端口号（仅HTTP模式）
        """
        print("正在初始化 Pero MCP Server...")

        # 创建服务器实例（自动发现客户端）
        server = cls(name=name)

        if not server.clients:
            print("未发现任何MCP客户端!")
            exit(1)

        print(f"已加载 {len(server.clients)} 个客户端")

        # 启动服务器
        server.run(transport, host, port)


def main():
    """主函数 - 包入口点"""
    import sys
    import argparse

    def parse_args():
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="Pero MCP Server",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
使用示例:
  pero-mcp-server                           # 使用STDIO模式启动（默认）
  pero-mcp-server --transport http          # 使用HTTP模式启动
  pero-mcp-server --http --port 8080        # 使用HTTP模式在8080端口启动
  pero-mcp-server --name "我的服务器"        # 自定义服务器名称
            """
        )

        parser.add_argument(
            "--name", "-n",
            default="Pero MCP Server",
            help="服务器名称 (默认: Pero MCP Server)"
        )

        parser.add_argument(
            "--transport", "-t",
            choices=["stdio", "http"],
            default="stdio",
            help="传输方式 (默认: stdio)"
        )

        parser.add_argument(
            "--http",
            action="store_const",
            const="http",
            dest="transport",
            help="使用HTTP传输模式 (等同于 --transport http)"
        )

        parser.add_argument(
            "--host",
            default="0.0.0.0",
            help="HTTP服务器主机地址 (默认: 0.0.0.0，仅HTTP模式有效)"
        )

        parser.add_argument(
            "--port", "-p",
            type=int,
            default=8000,
            help="HTTP服务器端口 (默认: 8000，仅HTTP模式有效)"
        )

        return parser.parse_args()

    args = parse_args()

    print(f"=== {args.name} ===")
    print(f"传输方式: {args.transport.upper()}")

    if args.transport == "http":
        print(f"服务地址: http://{args.host}:{args.port}")

    print("-" * 50)

    try:
        # 创建并启动服务器
        PeroMCPServer.create_and_run(
            name=args.name,
            transport=args.transport,
            host=args.host,
            port=args.port
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
