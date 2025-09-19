"""
App Store Connect 本地化管理处理器 - 负责应用商店本地化内容管理
"""

from typing import Any, List, Optional, Dict

from ...i_mcp_handler import IMCPHandler
from ..models import AppStoreVersionLocalization, AppInfoLocalization, Screenshot


class LocalizationHandler(IMCPHandler):
    """本地化管理处理器 - 负责应用商店描述、关键词、截图等本地化内容"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册本地化管理相关工具"""

        @mcp.tool("get_app_localizations")
        def get_app_localizations_tool(app_id: str) -> str:
            """
            获取指定应用的本地化信息

            Args:
                app_id (str): 应用的唯一标识符ID

            Returns:
                str: 应用的本地化信息列表，包括各语言的应用名称、副标题、隐私政策等
            """
            try:
                localizations = self.get_app_info_localizations(app_id)
                if not localizations:
                    return f"应用 {app_id} 没有本地化信息"

                result = f"应用本地化信息 ({len(localizations)} 个语言):\n\n"
                for loc in localizations:
                    result += f"语言: {loc.locale}\n"
                    if loc.name:
                        result += f"- 应用名称: {loc.name}\n"
                    if loc.subtitle:
                        result += f"- 副标题: {loc.subtitle}\n"
                    if loc.privacy_policy_url:
                        result += f"- 隐私政策: {loc.privacy_policy_url}\n"
                    result += "\n"

                return result
            except Exception as e:
                return f"获取应用本地化信息失败: {str(e)}"

        @mcp.tool("get_version_localizations")
        def get_version_localizations_tool(version_id: str) -> str:
            """
            获取指定版本的本地化信息

            Args:
                version_id (str): 应用版本的唯一标识符ID

            Returns:
                str: 版本的本地化信息列表，包括各语言的描述、关键词、新功能介绍等
            """
            try:
                localizations = self.get_version_localizations(version_id)
                if not localizations:
                    return f"版本 {version_id} 没有本地化信息"

                result = f"版本本地化信息 ({len(localizations)} 个语言):\n\n"
                for loc in localizations:
                    result += f"语言: {loc.locale}\n"
                    if loc.description:
                        result += f"- 描述: {loc.description[:100]}{'...' if len(loc.description) > 100 else ''}\n"
                    if loc.keywords:
                        result += f"- 关键词: {loc.keywords}\n"
                    if loc.whats_new:
                        result += f"- 新功能: {loc.whats_new[:100]}{'...' if len(loc.whats_new) > 100 else ''}\n"
                    if loc.promotional_text:
                        result += f"- 推广文本: {loc.promotional_text[:100]}{'...' if len(loc.promotional_text) > 100 else ''}\n"
                    if loc.marketing_url:
                        result += f"- 营销网址: {loc.marketing_url}\n"
                    if loc.support_url:
                        result += f"- 支持网址: {loc.support_url}\n"
                    result += "\n"

                return result
            except Exception as e:
                return f"获取版本本地化信息失败: {str(e)}"

        @mcp.tool("update_version_localization")
        def update_version_localization_tool(
            localization_id: str,
            description: Optional[str] = None,
            keywords: Optional[str] = None,
            whats_new: Optional[str] = None,
            promotional_text: Optional[str] = None,
            marketing_url: Optional[str] = None,
            support_url: Optional[str] = None
        ) -> str:
            """
            更新指定版本的本地化信息

            Args:
                localization_id (str): 本地化记录的唯一标识符ID
                description (str, optional): 应用描述，默认为None（不更改）
                keywords (str, optional): 关键词列表，用逗号分隔，默认为None（不更改）
                whats_new (str, optional): 新功能介绍文本，默认为None（不更改）
                promotional_text (str, optional): 推广文本，默认为None（不更改）
                marketing_url (str, optional): 营销网址，默认为None（不更改）
                support_url (str, optional): 支持网址，默认为None（不更改）

            Returns:
                str: 更新操作的结果信息，包括更新成功的字段列表
            """
            try:
                updates = {}
                if description is not None:
                    updates["description"] = description
                if keywords is not None:
                    updates["keywords"] = keywords
                if whats_new is not None:
                    updates["whatsNew"] = whats_new
                if promotional_text is not None:
                    updates["promotionalText"] = promotional_text
                if marketing_url is not None:
                    updates["marketingUrl"] = marketing_url
                if support_url is not None:
                    updates["supportUrl"] = support_url

                if not updates:
                    return "没有提供要更新的内容"

                localization = self.update_version_localization(localization_id, updates)

                result = f"版本本地化更新成功 (语言: {localization.locale}):\n"
                for field, value in updates.items():
                    display_name = {
                        "description": "描述",
                        "keywords": "关键词",
                        "whatsNew": "新功能",
                        "promotionalText": "推广文本",
                        "marketingUrl": "营销网址",
                        "supportUrl": "支持网址"
                    }.get(field, field)

                    if len(str(value)) > 100:
                        result += f"- {display_name}: {str(value)[:100]}...\n"
                    else:
                        result += f"- {display_name}: {value}\n"

                return result
            except Exception as e:
                return f"更新版本本地化信息失败: {str(e)}"

        @mcp.tool("get_app_screenshots")
        def get_app_screenshots_tool(localization_id: str) -> str:
            """
            获取指定本地化版本的应用截图列表

            Args:
                localization_id (str): 本地化记录的唯一标识符ID

            Returns:
                str: 应用截图列表，包括截图ID、文件名、文件大小、状态等信息
            """
            try:
                screenshots = self.get_app_screenshots(localization_id)
                if not screenshots:
                    return f"本地化 {localization_id} 没有截图"

                result = f"应用截图 ({len(screenshots)} 张):\n\n"
                for i, screenshot in enumerate(screenshots, 1):
                    result += f"{i}. 截图 ID: {screenshot.id}\n"
                    if screenshot.file_name:
                        result += f"   文件名: {screenshot.file_name}\n"
                    if screenshot.file_size:
                        result += f"   文件大小: {screenshot.file_size:,} 字节\n"
                    if screenshot.asset_delivery_state:
                        result += f"   状态: {screenshot.asset_delivery_state}\n"
                    result += "\n"

                return result
            except Exception as e:
                return f"获取应用截图失败: {str(e)}"

        @mcp.tool("get_supported_locales")
        def get_supported_locales_tool() -> str:
            """
            获取App Store Connect支持的所有本地化语言/地区列表

            Returns:
                str: 按语言分组的支持语言/地区列表，便于选择合适的本地化目标
            """
            locales = self.get_supported_locales()

            result = "App Store 支持的语言/地区:\n\n"

            # 按地区分组
            regions = {
                "zh": "中文",
                "en": "英语",
                "ja": "日语",
                "ko": "韩语",
                "es": "西班牙语",
                "fr": "法语",
                "de": "德语",
                "it": "意大利语",
                "pt": "葡萄牙语",
                "ru": "俄语",
                "ar": "阿拉伯语",
                "hi": "印地语",
                "th": "泰语",
                "vi": "越南语",
                "tr": "土耳其语",
                "nl": "荷兰语",
                "sv": "瑞典语",
                "da": "丹麦语",
                "fi": "芬兰语",
                "no": "挪威语",
                "pl": "波兰语",
                "cs": "捷克语",
                "sk": "斯洛伐克语",
                "hu": "匈牙利语",
                "ro": "罗马尼亚语",
                "hr": "克罗地亚语",
                "uk": "乌克兰语",
                "he": "希伯来语",
                "ca": "加泰罗尼亚语",
                "el": "希腊语",
                "bg": "保加利亚语",
                "lt": "立陶宛语",
                "lv": "拉脱维亚语",
                "et": "爱沙尼亚语",
                "sl": "斯洛文尼亚语",
                "mt": "马耳他语",
                "ga": "爱尔兰语",
                "cy": "威尔士语"
            }

            for locale_code, locale_name in regions.items():
                matching_locales = [loc for loc in locales if loc.startswith(locale_code)]
                if matching_locales:
                    result += f"{locale_name}:\n"
                    for locale in sorted(matching_locales):
                        result += f"  - {locale}\n"
                    result += "\n"

            return result

    def register_resources(self, mcp: Any) -> None:
        """注册本地化管理相关资源"""

        @mcp.resource("appstore://localization/supported")
        def get_supported_locales_resource() -> str:
            """获取支持的本地化语言资源"""
            locales = self.get_supported_locales()
            return f"支持的语言/地区 ({len(locales)} 个):\n" + "\n".join([f"- {locale}" for locale in sorted(locales)])

    def register_prompts(self, mcp: Any) -> None:
        """注册本地化管理相关提示"""

        @mcp.prompt("appstore_localization")
        def appstore_localization_prompt(
            operation: str = "",
            app_id: str = "",
            locale: str = "",
            content_type: str = ""
        ) -> str:
            """App Store Connect本地化管理提示"""
            return f"""App Store Connect 本地化管理助手

操作信息:
- 操作类型: {operation}
- 应用ID: {app_id}
- 语言地区: {locale}
- 内容类型: {content_type}

支持的操作类型:
- get_app_localizations: 获取应用本地化信息
- get_version_localizations: 获取版本本地化信息
- update_version_localization: 更新版本本地化
- get_app_screenshots: 获取应用截图
- get_supported_locales: 获取支持的语言列表

本地化内容类型:
- 应用信息本地化:
  * 应用名称 (name)
  * 副标题 (subtitle)
  * 隐私政策网址 (privacy_policy_url)

- 版本信息本地化:
  * 应用描述 (description)
  * 关键词 (keywords)
  * 新功能介绍 (whats_new)
  * 推广文本 (promotional_text)
  * 营销网址 (marketing_url)
  * 支持网址 (support_url)

- 视觉素材:
  * 应用截图
  * 应用预览视频

常用语言代码:
- zh-Hans: 简体中文
- zh-Hant: 繁体中文
- en-US: 美国英语
- ja: 日语
- ko: 韩语
- es-ES: 西班牙语
- fr-FR: 法语
- de-DE: 德语

使用步骤:
1. 获取应用的当前本地化信息
2. 选择要更新的语言和内容类型
3. 使用相应工具更新本地化内容
4. 验证更新结果

注意事项:
- 应用描述最多4000字符
- 关键词用逗号分隔，最多100字符
- 推广文本最多170字符
- 新功能介绍最多4000字符
"""

    # =============================================================================
    # 业务逻辑方法
    # =============================================================================

    def get_app_info_localizations(self, app_id: str) -> List[AppInfoLocalization]:
        """获取应用信息本地化列表"""
        response = self.client.make_api_request(f"apps/{app_id}/appInfos")

        if not response.get("data"):
            return []

        app_info_id = response["data"][0]["id"]

        # 获取应用信息的本地化内容
        localization_response = self.client.make_api_request(f"appInfos/{app_info_id}/appInfoLocalizations")

        localizations = []
        for loc_data in localization_response.get("data", []):
            localization = AppInfoLocalization.from_api_response(loc_data)
            localizations.append(localization)

        return localizations

    def get_version_localizations(self, version_id: str) -> List[AppStoreVersionLocalization]:
        """获取版本本地化列表"""
        response = self.client.make_api_request(f"appStoreVersions/{version_id}/appStoreVersionLocalizations")

        localizations = []
        for loc_data in response.get("data", []):
            localization = AppStoreVersionLocalization.from_api_response(loc_data)
            localizations.append(localization)

        return localizations

    def update_version_localization(self, localization_id: str, updates: Dict[str, str]) -> AppStoreVersionLocalization:
        """更新版本本地化信息"""
        data = {
            "data": {
                "type": "appStoreVersionLocalizations",
                "id": localization_id,
                "attributes": updates
            }
        }

        response = self.client.make_api_request(
            f"appStoreVersionLocalizations/{localization_id}",
            method="PATCH",
            data=data
        )

        return AppStoreVersionLocalization.from_api_response(response["data"])

    def get_app_screenshots(self, localization_id: str) -> List[Screenshot]:
        """获取应用截图列表"""
        response = self.client.make_api_request(f"appStoreVersionLocalizations/{localization_id}/appScreenshotSets")

        screenshots = []
        for screenshot_set in response.get("data", []):
            screenshot_set_id = screenshot_set["id"]

            # 获取截图集中的截图
            screenshot_response = self.client.make_api_request(f"appScreenshotSets/{screenshot_set_id}/appScreenshots")

            for screenshot_data in screenshot_response.get("data", []):
                screenshot = Screenshot.from_api_response(screenshot_data)
                screenshots.append(screenshot)

        return screenshots

    @classmethod
    def get_supported_locales(cls) -> List[str]:
        """获取支持的本地化语言列表"""
        # App Store Connect 支持的主要语言地区代码
        return [
            "ar", "ca", "cs", "da", "de-DE", "el", "en-AU", "en-CA", "en-GB", "en-US",
            "es-ES", "es-MX", "fi", "fr-CA", "fr-FR", "he", "hi", "hr", "hu", "id",
            "it", "ja", "ko", "ms", "nl-NL", "no", "pl", "pt-BR", "pt-PT", "ro",
            "ru", "sk", "sv", "th", "tr", "uk", "vi", "zh-Hans", "zh-Hant"
        ]
