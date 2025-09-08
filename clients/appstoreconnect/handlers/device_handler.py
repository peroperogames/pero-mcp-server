"""
App Store Connect 设备管理处理器 - 负责iOS设备注册和管理
"""

from typing import Any, List, Optional
from ...i_mcp_handler import IMCPHandler
from ..models import Device, DeviceClass, DeviceStatus, DevicePlatform


class DeviceHandler(IMCPHandler):
    """设备管理处理器 - 负责iOS设备的注册、查询和管理"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册设备管理相关工具"""

        @mcp.tool("list_devices")
        def list_devices_tool(
            device_class: Optional[str] = None,
            status: Optional[str] = None,
            platform: Optional[str] = None,
            limit: int = 100
        ) -> str:
            """获取设备列表"""
            try:
                devices = self.list_devices(
                    device_class=DeviceClass(device_class) if device_class else None,
                    status=DeviceStatus(status) if status else None,
                    platform=DevicePlatform(platform) if platform else None,
                    limit=limit
                )

                if not devices:
                    return "当前没有注册的设备"

                result = f"找到 {len(devices)} 个设备:\n"
                for device in devices:
                    status_text = "启用" if device.status == DeviceStatus.ENABLED else "禁用"
                    result += f"- {device.name} ({device.device_class.value}) - {device.platform.value} - {status_text}\n"
                    result += f"  UDID: {device.udid}\n"
                    if device.model:
                        result += f"  型号: {device.model}\n"
                    if device.added_date:
                        result += f"  添加时间: {device.added_date.strftime('%Y-%m-%d %H:%M')}\n"
                    result += "\n"

                return result
            except Exception as e:
                return f"获取设备列表失败: {str(e)}"

        @mcp.tool("register_device")
        def register_device_tool(name: str, udid: str, platform: str) -> str:
            """注册新设备"""
            try:
                device = self.register_device(name, udid, DevicePlatform(platform.upper()))
                return f"设备注册成功:\n" + \
                       f"- 名称: {device.name}\n" + \
                       f"- UDID: {device.udid}\n" + \
                       f"- 平台: {device.platform.value}\n" + \
                       f"- 设备类别: {device.device_class.value}"
            except Exception as e:
                return f"设备注册失败: {str(e)}"

        @mcp.tool("update_device")
        def update_device_tool(device_id: str, name: Optional[str] = None, status: Optional[str] = None) -> str:
            """更新设备信息"""
            try:
                device = self.update_device(
                    device_id,
                    name=name,
                    status=DeviceStatus(status.upper()) if status else None
                )
                status_text = "启用" if device.status == DeviceStatus.ENABLED else "禁用"
                return f"设备更新成功:\n" + \
                       f"- 名称: {device.name}\n" + \
                       f"- 状态: {status_text}\n" + \
                       f"- UDID: {device.udid}"
            except Exception as e:
                return f"设备更新失败: {str(e)}"

        @mcp.tool("find_device_by_udid")
        def find_device_by_udid_tool(udid: str) -> str:
            """根据UDID查找设备"""
            try:
                device = self.find_device_by_udid(udid)
                if not device:
                    return f"未找到UDID为 {udid} 的设备"

                status_text = "启用" if device.status == DeviceStatus.ENABLED else "禁用"
                result = f"找到设备:\n" + \
                        f"- 名称: {device.name}\n" + \
                        f"- UDID: {device.udid}\n" + \
                        f"- 平台: {device.platform.value}\n" + \
                        f"- 设备类别: {device.device_class.value}\n" + \
                        f"- 状态: {status_text}"

                if device.model:
                    result += f"\n- 型号: {device.model}"
                if device.added_date:
                    result += f"\n- 添加时间: {device.added_date.strftime('%Y-%m-%d %H:%M')}"

                return result
            except Exception as e:
                return f"查找设备失败: {str(e)}"

    def register_resources(self, mcp: Any) -> None:
        """注册设备管理相关资源"""

        @mcp.resource("appstore://devices")
        def get_devices_resource() -> str:
            """获取设备列表资源"""
            try:
                devices = self.list_devices()
                if not devices:
                    return "当前没有注册的设备"

                return f"设备列表 ({len(devices)} 个):\n" + "\n".join([
                    f"- {device.name} ({device.device_class.value}) - {device.platform.value}"
                    for device in devices
                ])
            except Exception as e:
                return f"获取设备列表失败: {str(e)}"

    def register_prompts(self, mcp: Any) -> None:
        """注册设备管理相关提示"""

        @mcp.prompt("appstore_device_management")
        def appstore_device_management_prompt(
            operation: str = "",
            device_name: str = "",
            udid: str = "",
            platform: str = ""
        ) -> str:
            """App Store Connect设备管理提示"""
            return f"""App Store Connect 设备管理助手

操作信息:
- 操作类型: {operation}
- 设备名称: {device_name}
- UDID: {udid}
- 平台: {platform}

支持的操作类型:
- list_devices: 获取设备列表
- register_device: 注册新设备
- update_device: 更新设备信息
- find_device_by_udid: 根据UDID查找设备

支持的平台:
- IOS: iOS设备 (iPhone/iPad)
- MAC_OS: macOS设备
- TV_OS: Apple TV设备
- WATCH_OS: Apple Watch设备

设备类别:
- IPHONE: iPhone设备
- IPAD: iPad设备
- APPLE_WATCH: Apple Watch
- APPLE_TV: Apple TV
- MAC: Mac电脑

使用步骤:
1. 获取设备UDID (通过Xcode或iTunes)
2. 使用register_device注册设备
3. 设备会自动用于开发和测试

注意事项:
- 每个开发者账户有设备数量限制
- UDID必须准确无误
- 注册后的设备可用于TestFlight测试
"""

    # =============================================================================
    # 业务逻辑方法
    # =============================================================================

    def list_devices(
        self,
        device_class: Optional[DeviceClass] = None,
        status: Optional[DeviceStatus] = None,
        platform: Optional[DevicePlatform] = None,
        limit: int = 100
    ) -> List[Device]:
        """获取设备列表"""
        params = {"limit": min(limit, 200)}

        # 添加过滤条件
        if device_class:
            params["filter[deviceClass]"] = device_class.value
        if status:
            params["filter[status]"] = status.value
        if platform:
            params["filter[platform]"] = platform.value

        response = self.client.make_api_request("devices", method="GET")
        devices = []
        for device_data in response.get("data", []):
            device = Device.from_api_response(device_data)
            devices.append(device)
        return devices

    def register_device(self, name: str, udid: str, platform: DevicePlatform) -> Device:
        """注册新设备"""
        data = {
            "data": {
                "type": "devices",
                "attributes": {
                    "name": name,
                    "udid": udid,
                    "platform": platform.value
                }
            }
        }

        response = self.client.make_api_request("devices", method="POST", data=data)
        return Device.from_api_response(response["data"])

    def update_device(
        self,
        device_id: str,
        name: Optional[str] = None,
        status: Optional[DeviceStatus] = None
    ) -> Device:
        """更新设备信息"""
        attributes = {}
        if name:
            attributes["name"] = name
        if status:
            attributes["status"] = status.value

        data = {
            "data": {
                "type": "devices",
                "id": device_id,
                "attributes": attributes
            }
        }

        response = self.client.make_api_request(f"devices/{device_id}", method="PATCH", data=data)
        return Device.from_api_response(response["data"])

    def find_device_by_udid(self, udid: str) -> Optional[Device]:
        """根据UDID查找设备"""
        try:
            response = self.client.make_api_request("devices", method="GET")

            # 在返回的设备列表中查找匹配的UDID
            for device_data in response.get("data", []):
                device_udid = device_data.get("attributes", {}).get("udid")
                if device_udid == udid:
                    return Device.from_api_response(device_data)
            return None
        except Exception:
            return None

    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """根据设备ID获取设备信息"""
        try:
            response = self.client.make_api_request(f"devices/{device_id}")
            return Device.from_api_response(response["data"])
        except Exception:
            return None
