"""
App Store Connect 分析数据处理器 - 负责销售和下载数据分析
"""

from typing import Any, Optional

from ..models import (ReportFrequency, SalesReportType)
from ...i_mcp_handler import IMCPHandler


class AnalyticsHandler(IMCPHandler):
    """分析数据处理器 - 负责销售报告、下载数据等分析功能"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册分析数据相关工具"""

        @mcp.tool("get_sales_report")
        def get_sales_report_tool(
                report_type: str = "SALES",
                report_subtype: str = "SUMMARY",
                frequency: str = "DAILY",
                report_date: str = ""
        ) -> str:
            """
            下载销售和趋势报告，下载根据您指定的标准过滤的销售和趋势报告。

            Args:
                report_type (str): (Required) The report to download. For more details on each report type see Download and view reports.
                    Possible Values: SALES, PRE_ORDER, NEWSSTAND, SUBSCRIPTION, SUBSCRIPTION_EVENT, SUBSCRIBER, SUBSCRIPTION_OFFER_CODE_REDEMPTION, INSTALLS, FIRST_ANNUAL, WIN_BACK_ELIGIBILITY
                report_subtype (str): (Required) The report sub type to download. For a list of values, see Allowed values based on sales report type table below.
                    Possible Values: SUMMARY, DETAILED, SUMMARY_INSTALL_TYPE, SUMMARY_TERRITORY, SUMMARY_CHANNEL
                frequency (str): (Required) Frequency of the report to download. For a list of values, see Allowed values based on sales report type table below.
                    Possible Values: DAILY, WEEKLY, MONTHLY, YEARLY
                report_date (str): 报告日期，如果是月报告，则格式为YYYY-MM, 如果是日报告，报告格式为YYYY-MM-DD，
                    The report date to download. Specify the date in the YYYY-MM-DD format for all report frequencies except DAILY, which doesn’t require a date. For more information, see report availability and storage.
            Returns:
                str: 销售报告内容
            """
            try:
                if not self.client.config:
                    self.client.config = self.client.load_config_from_env()

                # 这里需要vendor_number，从配置中获取
                vendor_number = getattr(self.client.config, 'vendor_number', None)
                if not vendor_number:
                    return "未配置vendor_number，无法获取分析数据"

                report = self.get_sales_report(
                    vendor_number=vendor_number,
                    report_type=SalesReportType(report_type.upper()),
                    report_subtype=report_subtype,
                    frequency=ReportFrequency(frequency.upper()),
                    report_date=report_date
                )
                return report
            except Exception as e:
                return f"获取销售报告失败: {str(e)}"

        @mcp.tool("get_finance_report")
        def get_finance_report_tool(
                region_code: str = "ZZ",
                report_date: str = ""
        ) -> str:
            """
            下载财务报告，获取特定时期的收入和税务信息。

            Args:
                region_code (str): (Required) 报告区域代码。通常使用 "ZZ" 表示全球报告。
                    The region code for the finance report. Use "ZZ" for worldwide reports.
                report_date (str): (Required) 报告日期，格式为 YYYY-MM。
                    The report date in YYYY-MM format. Finance reports are typically available monthly.
            Returns:
                str: 财务报告内容
            """
            try:
                if not self.client.config:
                    self.client.config = self.client.load_config_from_env()

                # 这里需要vendor_number，从配置中获取
                vendor_number = getattr(self.client.config, 'vendor_number', None)
                if not vendor_number:
                    return "未配置vendor_number，无法获取财务数据"

                if not report_date:
                    return "请提供报告日期，格式为 YYYY-MM"

                report = self.get_finance_report(
                    vendor_number=vendor_number,
                    region_code=region_code,
                    report_date=report_date
                )
                return report
            except Exception as e:
                return f"获取财务报告失败: {str(e)}"

    def register_resources(self, mcp: Any) -> None:
        """注册分析数据相关资源"""
        pass

    def register_prompts(self, mcp: Any) -> None:
        """注册分析数据相关提示"""

        @mcp.prompt("appstore_analytics")
        def appstore_analytics_prompt(
                operation: str = "",
                app_name: str = "",
                vendor_number: str = "",
                date_range: str = ""
        ) -> str:
            """App Store Connect分析数据提示"""
            return f"""App Store Connect 分析数据助手

查询信息:
- 操作类型: {operation}
- 应用名称: {app_name}
- 供应商编号: {vendor_number}
- 日期范围: {date_range}

支持的操作类型:
- get_sales_report: 获取销售报告
- get_finance_report: 获取财务报告
- get_app_analytics: 获取应用分析数据
- get_top_countries: 获取国家排行榜

销售报告类型:
- SALES: 销售报告 (下载和购买)
- SUBSCRIPTION: 订阅报告
- NEWSSTAND: 报刊订阅报告

财务报告:
- FINANCIAL: 财务报告 (收入和税务信息)
- 区域代码: ZZ (全球报告)
- 报告频率: 月度 (YYYY-MM 格式)

频率选项 (销售报告):
- DAILY: 日报告
- WEEKLY: 周报告  
- MONTHLY: 月报报告
- YEARLY: 年报告

使用步骤:
1. 确保已配置vendor_number
2. 选择要查询的应用和日期范围
3. 使用相应的工具获取分析数据

财务报告使用示例:
- get_finance_report(region_code="ZZ", report_date="2024-08")

注意事项:
- 销售数据通常有1-2天延迟
- 财务数据通常有更长的延迟，按月提供
- 需要有效的vendor_number才能获取数据
- 部分数据可能需要特定的权限
- 财务报告包含收入、税务和汇率信息
"""

    # =============================================================================
    # 业务逻辑方法
    # =============================================================================

    def get_sales_report(
            self,
            vendor_number: str,
            report_type: SalesReportType,
            report_subtype: str,
            frequency: ReportFrequency,
            report_date: str
    ) -> Optional[str]:
        """获取销售报告"""
        data = {
            "filter[frequency]": frequency.value,
            "filter[reportDate]": report_date,
            "filter[reportSubType]": report_subtype,
            "filter[reportType]": report_type.value,
            "filter[vendorNumber]": vendor_number
        }

        # 销售报告API通常返回压缩文件，不是JSON
        response = self.client.make_api_request("salesReports", method="GET", data=data)

        # 处理二进制内容（可能是gzip压缩的CSV）
        raw_content = response["raw_content"]

        # gzip解压缩
        import gzip
        decompressed_data = gzip.decompress(raw_content).decode('utf-8')
        print(f"成功解压缩，数据长度: {len(decompressed_data)} 字符")
        print(f"解压后内容前200字符: {decompressed_data[:200]}")

        return decompressed_data

    def get_finance_report(
            self,
            vendor_number: str,
            region_code: str,
            report_date: str
    ) -> Optional[str]:
        """获取财务报告"""
        data = {
            "filter[regionCode]": region_code,
            "filter[reportDate]": report_date,
            "filter[reportType]": "FINANCIAL",
            "filter[vendorNumber]": vendor_number
        }

        # 财务报告API通常返回压缩文件，不是JSON
        response = self.client.make_api_request("financeReports", method="GET", data=data)

        # 处理二进制内容（可能是gzip压缩的CSV）
        raw_content = response["raw_content"]

        # gzip解压缩
        import gzip
        decompressed_data = gzip.decompress(raw_content).decode('utf-8')
        print(f"成功解压缩财务报告，数据长度: {len(decompressed_data)} 字符")
        print(f"解压后财务报告内容前200字符: {decompressed_data[:200]}")

        return decompressed_data
