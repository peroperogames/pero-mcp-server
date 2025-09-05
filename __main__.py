#!/usr/bin/env python3
"""
Pero MCP Server 模块入口点
当使用 'python -m pero_mcp_server' 或直接运行时执行此文件
支持命令行参数和直接Python调用
"""

import sys
import argparse
from pero_mcp_server import PeroMCPServer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Pero MCP Server - FastMCP 中转站",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m pero_mcp_server                    # 使用STDIO模式启动（默认）
  python -m pero_mcp_server --transport http   # 使用HTTP模式启动
  python -m pero_mcp_server --http --port 8080 # 使用HTTP模式在8080端口启动
  python -m pero_mcp_server --name "我的服务器" # 自定义服务器名称
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


def main():
    """主函数"""
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


def run_stdio(name: str = "Pero MCP Server"):
    """便捷函数：启动STDIO模式服务器

    Args:
        name: 服务器名称
    """
    server = PeroMCPServer(name=name)
    server.run_with_stdio()


def run_http(name: str = "Pero MCP Server", host: str = "0.0.0.0", port: int = 8000):
    """便捷函数：启动HTTP模式服务器

    Args:
        name: 服务器名称
        host: 主机地址
        port: 端口号
    """
    server = PeroMCPServer(name=name)
    server.run_with_http(host, port)


if __name__ == "__main__":
    main()
