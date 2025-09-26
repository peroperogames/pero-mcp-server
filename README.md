<div align="center">

# 🚀 Pero MCP Server

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-orange.svg)](https://modelcontextprotocol.io/)
[![SSH](https://img.shields.io/badge/Feature-SSH-red.svg)](#ssh-客户端)
[![App Store](https://img.shields.io/badge/Feature-App%20Store%20Connect-lightblue.svg)](#app-store-connect-集成)

*一个功能强大的 Model Context Protocol (MCP) 服务器*

**集成多种功能 • SSH 连接管理 • App Store Connect API 集成**

---

</div>

## ✨ 功能特性

<table>
<tr>
<td width="50%">

### 🔐 SSH 客户端

- 🔗 **SSH 连接管理** - 安全的远程连接
- ⚡ **远程命令执行** - 快速执行远程操作
- 📁 **文件传输功能** - 双向文件传输支持

</td>
<td width="50%">

### 🍎 App Store Connect 集成

- 📱 **应用列表获取** - 管理你的应用
- 👥 **团队成员管理** - 协作团队管理
- 🧪 **TestFlight 管理工具** - 测试版本管理

</td>
</tr>
</table>

## 🛠️ 安装和配置

### 📋 环境要求

- ![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python) Python 3.8+
- 📦 相关依赖包（见 requirements.txt）

### 💻 安装依赖

```bash
pip install -r requirements.txt
```

## ⚙️ MCP 客户端配置

在你的 MCP 客户端（如 Claude Desktop）配置文件中添加以下配置：

### 📡 传输方式配置说明

MCP 服务器支持多种传输方式，可以通过以下参数进行配置：

<summary>🔧 传输参数说明</summary>

| 参数名         | 描述              | 默认值       | 示例                       |
|-------------|-----------------|-----------|--------------------------|
| `transport` | 传输协议类型          | `stdio`   | `stdio`, `http`          |
| `host`      | 服务器主机地址（HTTP模式） | `0.0.0.0` | `127.0.0.1`, `localhost` |
| `port`      | 服务器端口（HTTP模式）   | `8000`    | `8000`, `8080`           |

**📋 传输方式说明：**

- 🔤 **stdio** (默认)：标准输入输出方式，适合本地开发和测试
- 🌐 **http**：streamable-http 方式，适合网络通信和远程访问

### 🏠 本地开发环境配置

```json
{
	"servers": {
		"pero-mcp-server-local": {
			"command": "python",
			"args": [
				"path/to/pero-mcp-server"
			],
			"env": {
				"SSH_HOST": "your_ssh_host",
				"SSH_USERNAME": "your_username",
				"SSH_PORT": "22",
				"SSH_PASSWORD": "your_password",
				"APPSTORE_KEY_ID": "your_key_id",
				"APPSTORE_ISSUER_ID": "your_issuer_id",
				"APPSTORE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nyour_private_key_content\n-----END PRIVATE KEY-----"
			}
		}
	}
}
```

### 🌐 远程生产环境配置

```json
{
	"servers": {
		"pero-mcp-server-remote": {
			"command": "uvx",
			"args": [
				"--from",
				"git+https://github.com/peroperogames/pero-mcp-server",
				"pero-mcp-server"
			],
			"env": {
				"SSH_HOST": "your_production_ssh_host",
				"SSH_USERNAME": "your_ssh_username",
				"SSH_PORT": "22",
				"SSH_PASSWORD": "your_ssh_password",
				"APPSTORE_KEY_ID": "your_appstore_key_id",
				"APPSTORE_ISSUER_ID": "your_appstore_issuer_id",
				"APPSTORE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\nyour_private_key_content\n-----END PRIVATE KEY-----"
			}
		}
	}
}
```

> - 🔄 无需本地安装和配置，自动获取最新代码
> - 🏭 适合生产环境或团队协作使用

## 📝 环境变量说明

<details>
<summary>🔐 SSH 配置</summary>

| 变量名            | 描述            | 示例              |
|----------------|---------------|-----------------|
| `SSH_HOST`     | SSH 服务器主机地址   | `192.168.1.100` |
| `SSH_USERNAME` | SSH 用户名       | `admin`         |
| `SSH_PORT`     | SSH 端口（默认 22） | `22`            |
| `SSH_PASSWORD` | SSH 密码        | `your_password` |

</details>

<details>
<summary>🍎 App Store Connect 配置</summary>

| 变量名                    | 描述                          | 必需 |
|------------------------|-----------------------------|----|
| `APPSTORE_KEY_ID`      | App Store Connect API 密钥 ID | ✅  |
| `APPSTORE_ISSUER_ID`   | 发行者 ID                      | ✅  |
| `APPSTORE_PRIVATE_KEY` | 私钥内容（完整的 PEM 格式）            | ✅  |
| `APPSTORE_APP_ID`      | 应用 ID                       | ❌  |

</details>

## 🔧 可用工具

<div align="center">

| 分类               | 工具名称                 | 功能描述                       |
|------------------|----------------------|----------------------------|
| 🔐 **SSH**       | `ssh_connect`        | 🔗 建立 SSH 连接               |
| 🔐 **SSH**       | `ssh_execute`        | ⚡ 执行远程命令                   |
| 🔐 **SSH**       | `ssh_upload`         | ⬆️ 上传文件                    |
| 🔐 **SSH**       | `ssh_download`       | ⬇️ 下载文件                    |
| 🍎 **App Store** | `configure_appstore` | ⚙️ 配置 App Store Connect 凭据 |
| 🍎 **App Store** | `get_apps`           | 📱 获取应用列表                  |
| 🍎 **App Store** | `get_team_members`   | 👥 获取团队成员信息                |

</div>

## 📚 可用资源

### 🔐 SSH 资源

- `ssh://status` - 📊 SSH 连接状态
- `ssh://info` - ℹ️ SSH 连接信息

### 🍎 App Store Connect 资源

- `appstore://apps` - 📱 应用列表
- `appstore://members` - 👥 团队成员列表

## 💡 可用提示模板

### 🔐 SSH 提示

- `ssh_troubleshoot` - 🔧 SSH 连接故障排除

### 🍎 App Store Connect 提示

- `manage_testflight` - 🧪 TestFlight 管理操作

## 🚀 使用示例

启动服务器后，你可以在 MCP 客户端中使用以下命令：

```python
# 🔐 SSH 操作
ssh_connect()
ssh_execute(command="ls -la")

# 🍎 App Store Connect 操作
get_apps()
get_team_members()
```

## 👨‍💻 开发指南

### 📁 项目结构

```
pero-mcp-server/
├── 📄 pero_mcp_server.py          # 主服务器入口文件
├── ⚙️ pyproject.toml              # 项目配置文件
├── 📦 requirements.txt            # Python依赖包
├── 📖 README.md                   # 项目说明文档
├── 📝 .env.example                # 环境变量示例文件
├── 🚫 .gitignore                  # Git忽略文件配置
├── 🐍 .venv/                      # Python虚拟环境
└── 📂 clients/                    # MCP客户端实现
    ├── 🔧 __init__.py
    ├── 🎯 i_mcp_client.py        # 客户端接口定义
    ├── 🔐 ssh/                   # SSH客户端模块
    │   ├── 🔧 __init__.py
    │   ├── 💻 ssh_mcp_client.py  # SSH MCP客户端实现
    │   └── 📊 models.py          # SSH数据模型
    └── 🍎 appstoreconnect/       # App Store Connect客户端模块
        ├── 🔧 __init__.py
        ├── 📱 appstore_connect_mcp_client.py  # App Store Connect MCP客户端
        └── 📊 models.py          # App Store Connect数据模型
```

### 🔧 开发环境设置

<details>
<summary>点击展开详细步骤</summary>

1. **📥 克隆项目**
   ```bash
   git clone <repository-url>
   cd pero-mcp-server
   ```

2. **🐍 创建虚拟环境**
   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Linux/macOS
   source .venv/bin/activate
   ```

3. **📦 安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **⚙️ 设置环境变量**
   创建 `.env` 文件或在系统中设置环境变量：
   ```bash
   SSH_HOST=your_ssh_host
   SSH_USERNAME=your_username
   SSH_PORT=22
   SSH_PASSWORD=your_password
   APPSTORE_KEY_ID=your_key_id
   APPSTORE_ISSUER_ID=your_issuer_id
   APPSTORE_PRIVATE_KEY=your_private_key
   ```

</details>

### 🏗️ 代码架构

#### 1. 📦 客户端架构 (clients/)

- **🎯 i_mcp_client.py**: 定义了MCP客户端的通用接口
- **🔐 ssh/**: SSH功能的客户端实现，包含SSH连接管理和远程操作
- **🍎 appstoreconnect/**: App Store Connect功能的客户端实现，处理App Store API交互

#### 2. 🚀 主服务器 (pero_mcp_server.py)

- 🔧 集成所有客户端组件
- 🎯 提供统一的MCP服务器入口
- ⚡ 处理工具调用、资源访问和提示模板
- 🔄 管理不同客户端之间的协调

### 📜 开发规范

<details>
<summary>🎨 代码风格</summary>

- ✅ 使用Python类型提示
- 📝 遵循PEP 8代码规范
- 🏷️ 使用有意义的变量和函数名
- 📖 添加适当的文档字符串

</details>

<details>
<summary>⚠️ 错误处理</summary>

- 🛡️ 使用适当的异常处理
- 💬 提供清晰的错误消息
- 📋 记录关键操作的日志

</details>

<details>
<summary>🧪 测试</summary>

- ✅ 为新功能编写单元测试
- 🔍 确保现有测试通过
- 🎯 测试错误情况和边界条件

</details>

### ➕ 添加新功能

要添加新功能，需要实现 `IMCPClient` 接口。以下是完整的实现步骤：

<details>
<summary>🛠️ 第一步：创建客户端类</summary>

```python
from clients.mcp_client_interface import IMCPClient
from typing import Any
import mcp.types as types


class YourNewMCPClient(IMCPClient):
    """你的新功能客户端"""

    def __init__(self):
        """初始化客户端"""
        # 初始化你的客户端状态
        pass

    def register_tools(self, mcp: Any) -> None:
        """注册工具到FastMCP实例"""

        @mcp.tool()
        async def your_new_tool(arguments: dict) -> list[types.TextContent]:
            """
            你的新工具描述

            Args:
                arguments: 工具参数字典

            Returns:
                工具执行结果
            """
            # 实现你的工具逻辑
            result = await self._execute_your_logic(arguments)
            return [types.TextContent(type="text", text=result)]

    def register_resources(self, mcp: Any) -> None:
        """注册资源到FastMCP实例"""

        @mcp.resource("your_scheme://your_resource")
        async def read_your_resource(uri: str) -> str:
            """
            读取你的资源

            Args:
                uri: 资源URI

            Returns:
                资源内容
            """
            # 处理资源读取逻辑
            return await self._read_resource_content(uri)

    def register_prompts(self, mcp: Any) -> None:
        """注册提示模板到FastMCP实例"""

        @mcp.prompt()
        async def your_prompt_template(arguments: dict) -> types.PromptMessage:
            """
            你的提示模板

            Args:
                arguments: 提示参数

            Returns:
                提示消息
            """
            # 生成提示内容
            content = await self._generate_prompt_content(arguments)
            return types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=content)
            )

    async def _execute_your_logic(self, arguments: dict) -> str:
        """实现你的具体业务逻辑"""
        # 在这里实现你的功能逻辑
        pass

    async def _read_resource_content(self, uri: str) -> str:
        """读取资源内容的具体实现"""
        # 在这里实现资源读取逻辑
        pass

    async def _generate_prompt_content(self, arguments: dict) -> str:
        """生成提示内容的具体实现"""
        # 在这里实现提示生成逻辑
        pass
```

</details>

<details>
<summary>📁 第二步：放置客户端文件</summary>

由于项目具有自发现机制，你只需要将新客户端放在正确的位置即可：

为新功能创建独立的模块目录：

```
clients/
└── yournew/                    # 你的新功能模块
    ├── __init__.py
    ├── your_new_mcp_client.py  # 主客户端实现
    ├── models.py               # 数据模型（如果需要）
    └── utils.py                # 工具函数（如果需要）
```

**🔍 自动发现机制**

服务器会自动扫描 `clients/` 目录下的所有子目录，查找继承自 `IMCPClient` 的类并自动注册。你无需手动修改主服务器代码。

</details>

<details>
<summary>🚀 第三步：重启服务器</summary>

完成客户端实现后，重启MCP服务器即可自动加载新功能：

```bash
python pero_mcp_server.py
```

服务器启动时会自动发现并注册你的新客户端。

</details>

#### 2. 🎯 IMCPClient接口说明

`IMCPClient` 是所有MCP客户端必须实现的抽象基类，包含以下方法：

- **`register_tools(mcp)`** 🔧: 注册工具函数，这些工具可以被MCP客户端调用执行特定操作
- **`register_resources(mcp)`** 📚: 注册资源处理器，用于提供可读取的数据资源
- **`register_prompts(mcp)`** 💡: 注册提示模板，用于生成特定场景的提示内容
- **`get_name()`** 🏷️: 获取客户端名称（已提供默认实现）

#### 3. 🌟 实现最佳实践

<details>
<summary>⚠️ 错误处理</summary>

```python
async def your_tool(self, arguments: dict) -> list[types.TextContent]:
    try:
        result = await self._execute_logic(arguments)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        error_msg = f"执行失败: {str(e)}"
        return [types.TextContent(type="text", text=error_msg)]
```

</details>

<details>
<summary>✅ 参数验证</summary>

```python
def _validate_arguments(self, arguments: dict, required_fields: list) -> None:
    """验证必需参数"""
    missing_fields = [field for field in required_fields if field not in arguments]
    if missing_fields:
        raise ValueError(f"缺少必需参数: {', '.join(missing_fields)}")
```

</details>

<details>
<summary>📋 日志记录</summary>

```python
import logging

logger = logging.getLogger(__name__)

async def your_tool(self, arguments: dict) -> list[types.TextContent]:
    logger.info(f"执行工具: {arguments}")
    # ...implementation...
    logger.info("工具执行完成")
```

</details>

## 🔐 安全注意事项

> ⚠️ **重要提醒**：
> - 🚫 不要在代码库中提交真实的密码、私钥等敏感信息
> - 🛡️ 建议使用环境变量或安全的配置管理工具
> - 🔄 定期更换 SSH 密码和 API 密钥
> - 🔒 确保私钥文件的权限设置正确

---

<div align="center">

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目！

[![Contributors](https://img.shields.io/github/contributors/peroperogames/pero-mcp-server.svg)](https://github.com/peroperogames/pero-mcp-server/graphs/contributors)

## 💬 支持

如果您在使用过程中遇到问题，请通过 [GitHub Issues](https://github.com/peroperogames/pero-mcp-server/issues) 反馈。

---

*Made with ❤️ by peropero*

</div>
