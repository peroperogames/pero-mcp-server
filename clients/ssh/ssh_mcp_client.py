"""
SSH MCP 客户端 - 整合了客户端和服务器功能
"""

import os
import paramiko
from typing import Optional
from io import StringIO

from ..i_mcp_client import IMCPClient
from .models import SSHConfig


class SSHMCPClient(IMCPClient):
    """SSH MCP 客户端 - 实现 IMCPClient 接口"""

    def __init__(self):
        """初始化客户端"""
        self.config = None
        self.ssh_client = None

    @classmethod
    def _load_config_from_env(cls) -> Optional[SSHConfig]:
        """从环境变量加载SSH配置"""
        hostname = os.getenv('SSH_HOST')
        username = os.getenv('SSH_USERNAME')
        port = int(os.getenv('SSH_PORT', '22'))
        password = os.getenv('SSH_PASSWORD')
        private_key_path = os.getenv('SSH_PRIVATE_KEY_PATH')
        private_key_content = os.getenv('SSH_PRIVATE_KEY_CONTENT')
        timeout = int(os.getenv('SSH_TIMEOUT', '30'))

        if not all([hostname, username]):
            return None

        if not any([password, private_key_path, private_key_content]):
            return None

        try:
            return SSHConfig(
                hostname=hostname,
                username=username,
                port=port,
                password=password,
                private_key_path=private_key_path,
                private_key_content=private_key_content,
                timeout=timeout
            )
        except ValueError:
            return None

    def _create_ssh_client(self):
        """创建SSH客户端连接"""
        if not self.config:
            self.config = self._load_config_from_env()

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            auth_kwargs = {
                'hostname': self.config.hostname,
                'port': self.config.port,
                'username': self.config.username,
                'timeout': self.config.timeout
            }

            if self.config.password:
                auth_kwargs['password'] = self.config.password
            elif self.config.private_key_content:
                private_key = paramiko.RSAKey.from_private_key(StringIO(self.config.private_key_content))
                auth_kwargs['pkey'] = private_key
            elif self.config.private_key_path:
                auth_kwargs['key_filename'] = self.config.private_key_path

            client.connect(**auth_kwargs)
            return client

        except Exception as e:
            client.close()
            raise e

    def connect(self) -> str:
        """建立SSH连接"""
        try:
            if self.ssh_client:
                self.ssh_client.close()

            self.ssh_client = self._create_ssh_client()
            return f"已成功连接到 {self.config.username}@{self.config.hostname}:{self.config.port}"
        except Exception as e:
            return f"SSH连接失败: {str(e)}"

    def disconnect(self) -> str:
        """断开SSH连接"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
            return "SSH连接已断开"
        return "没有活动的SSH连接"

    def execute_command(self, command: str) -> str:
        """执行SSH命令"""
        if not self.ssh_client:
            connect_result = self.connect()
            if "失败" in connect_result:
                return connect_result

        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')

            result = f"命令: {command}\n"
            if output:
                result += f"输出:\n{output}\n"
            if error:
                result += f"错误:\n{error}"

            return result.strip()
        except Exception as e:
            return f"命令执行失败: {str(e)}"

    def list_files(self, path: str = ".") -> str:
        """列出远程目录文件"""
        command = f"ls -la '{path}'"
        return self.execute_command(command)

    def get_system_info(self) -> str:
        """获取远程系统信息"""
        commands = [
            "uname -a",
            "cat /etc/os-release 2>/dev/null || cat /etc/redhat-release 2>/dev/null || echo 'Unknown OS'",
            "df -h",
            "free -h",
            "uptime"
        ]

        results = []
        for cmd in commands:
            result = self.execute_command(cmd)
            results.append(result)

        return "\n" + "="*50 + "\n".join(results)

    def register_tools(self, mcp) -> None:
        """注册SSH工具到FastMCP实例"""

        @mcp.tool("configure_ssh")
        def configure_ssh(hostname: str, username: str, port: int = 22, password: Optional[str] = None,
                         private_key_path: Optional[str] = None, private_key_content: Optional[str] = None,
                         timeout: int = 30) -> str:
            """配置新的SSH连接"""
            self.config = SSHConfig(
                hostname=hostname,
                username=username,
                port=port,
                password=password,
                private_key_path=private_key_path,
                private_key_content=private_key_content,
                timeout=timeout
            )
            return f"SSH配置已成功设置: {username}@{hostname}:{port}"

        @mcp.tool("ssh_connect")
        def ssh_connect() -> str:
            """建立SSH连接"""
            return self.connect()

        @mcp.tool("ssh_disconnect")
        def ssh_disconnect() -> str:
            """断开SSH连接"""
            return self.disconnect()

        @mcp.tool("ssh_execute")
        def ssh_execute(command: str) -> str:
            """执行SSH命令"""
            return self.execute_command(command)

        @mcp.tool("ssh_list_files")
        def ssh_list_files(path: str = ".") -> str:
            """列出远程目录文件"""
            return self.list_files(path)

        @mcp.tool("ssh_system_info")
        def ssh_system_info() -> str:
            """获取远程系统信息"""
            return self.get_system_info()

    def register_resources(self, mcp) -> None:
        """注册SSH资源到FastMCP实例"""

        @mcp.resource("ssh://status")
        def ssh_status_resource() -> str:
            """SSH连接状态"""
            if not self.config:
                self.config = self._load_config_from_env()

            status = f"SSH配置: {self.config.username}@{self.config.hostname}:{self.config.port}\n"
            status += f"连接状态: {'已连接' if self.ssh_client else '未连接'}"
            return status

        @mcp.resource("ssh://config")
        def ssh_config_resource() -> str:
            """SSH配置信息"""
            if not self.config:
                self.config = self._load_config_from_env()

            return f"""SSH配置信息:
主机名: {self.config.hostname}
用户名: {self.config.username}
端口: {self.config.port}
超时: {self.config.timeout}秒
认证方式: {'密码' if self.config.password else ('私钥文件' if self.config.private_key_path else '私钥内容')}"""

    def register_prompts(self, mcp) -> None:
        """注册SSH提示到FastMCP实例"""

        @mcp.prompt("ssh_troubleshoot")
        def ssh_troubleshoot_prompt(issue: str = "") -> str:
            """SSH故障排除提示"""
            return f"""SSH连接故障排除助手

当前问题: {issue}

请尝试以下步骤:
1. 检查SSH配置是否正确
2. 验证网络连接
3. 确认SSH服务是否运行
4. 检查认证凭据
5. 查看防火墙设置

使用可用的SSH工具来诊断问题:
- ssh_connect: 测试连接
- ssh_execute: 执行命令
- ssh_system_info: 获取系统信息"""

        @mcp.prompt("remote_admin")
        def remote_admin_prompt(task: str = "") -> str:
            """远程管理助手提示"""
            return f"""远程服务器管理助手

任务: {task}

我可以帮助您:
1. 执行系统命令
2. 检查系统状态
3. 管理文件和目录
4. 监控系统资源
5. 故障排除

请告诉我您需要执行什么操作，我会使用SSH工具来帮您完成。"""
