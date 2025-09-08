"""
App Store Connect 分析数据处理器 - 负责销售和下载数据分析
"""

import csv
import io
import gzip
from datetime import datetime, date, timedelta
from typing import Any, List, Optional, Dict
from ...i_mcp_handler import IMCPHandler
from ..models import (
    SalesReport, AnalyticsReportSegment, AppAnalyticsData,
    ReportFrequency, SalesReportType
)


class AnalyticsHandler(IMCPHandler):
    """分析数据处理器 - 负责销售报告、下载数据等分析功能"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册分析数据相关工具"""

        @mcp.tool("get_sales_report")
        def get_sales_report_tool(
            vendor_number: str,
            report_type: str = "SALES",
            report_subtype: str = "SUMMARY",
            frequency: str = "DAILY",
            report_date: str = ""
        ) -> str:
            """获取销售报告"""
            try:
                # 如果未提供日期，使用昨天的日期
                if not report_date:
                    report_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

                report_date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()

                report = self.get_sales_report(
                    vendor_number=vendor_number,
                    report_type=SalesReportType(report_type.upper()),
                    report_subtype=report_subtype,
                    frequency=ReportFrequency(frequency.upper()),
                    report_date=report_date_obj
                )

                if not report or not report.data_segments:
                    return f"未找到 {report_date} 的销售报告数据"

                # 按应用汇总数据
                app_summary = {}
                for segment in report.data_segments:
                    app_name = segment.app_name
                    if app_name not in app_summary:
                        app_summary[app_name] = {
                            'downloads': 0,
                            'proceeds': 0.0,
                            'countries': set()
                        }
                    app_summary[app_name]['downloads'] += segment.units
                    app_summary[app_name]['proceeds'] += segment.proceeds
                    app_summary[app_name]['countries'].add(segment.country_code)

                result = f"销售报告 - {report_date} ({frequency}):\n\n"
                for app_name, data in app_summary.items():
                    result += f"应用: {app_name}\n"
                    result += f"- 下载量: {data['downloads']:,}\n"
                    result += f"- 收入: ${data['proceeds']:,.2f}\n"
                    result += f"- 覆盖国家: {len(data['countries'])} 个\n\n"

                return result
            except Exception as e:
                return f"获取销售报告失败: {str(e)}"

        @mcp.tool("get_app_analytics")
        def get_app_analytics_tool(
            app_name: str,
            vendor_number: str,
            days: int = 7
        ) -> str:
            """获取应用分析数据（最近N天）"""
            try:
                analytics_data = self.get_app_analytics(app_name, vendor_number, days)

                if not analytics_data:
                    return f"未找到应用 {app_name} 最近 {days} 天的分析数据"

                total_downloads = sum(data.total_downloads for data in analytics_data)
                total_proceeds = sum(data.total_proceeds for data in analytics_data)

                result = f"应用分析 - {app_name} (最近 {days} 天):\n\n"
                result += f"总下载量: {total_downloads:,}\n"
                result += f"总收入: ${total_proceeds:,.2f}\n"
                result += f"平均日下载: {total_downloads/days:,.1f}\n"
                result += f"平均日收入: ${total_proceeds/days:,.2f}\n\n"

                # 按国家汇总
                country_downloads = {}
                country_proceeds = {}
                for data in analytics_data:
                    for country, downloads in data.downloads_by_country.items():
                        country_downloads[country] = country_downloads.get(country, 0) + downloads
                    for country, proceeds in data.proceeds_by_country.items():
                        country_proceeds[country] = country_proceeds.get(country, 0.0) + proceeds

                # 显示前5个国家
                top_countries = sorted(country_downloads.items(), key=lambda x: x[1], reverse=True)[:5]
                if top_countries:
                    result += "主要市场 (按下载量):\n"
                    for country, downloads in top_countries:
                        proceeds = country_proceeds.get(country, 0.0)
                        result += f"- {country}: {downloads:,} 下载, ${proceeds:,.2f}\n"

                return result
            except Exception as e:
                return f"获取应用分析数据失败: {str(e)}"

        @mcp.tool("get_top_countries")
        def get_top_countries_tool(
            vendor_number: str,
            report_date: str = "",
            top_n: int = 10
        ) -> str:
            """获取下载量最高的国家排行"""
            try:
                if not report_date:
                    report_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

                report_date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()

                report = self.get_sales_report(
                    vendor_number=vendor_number,
                    report_type=SalesReportType.SALES,
                    report_subtype="SUMMARY",
                    frequency=ReportFrequency.DAILY,
                    report_date=report_date_obj
                )

                if not report or not report.data_segments:
                    return f"未找到 {report_date} 的销售数据"

                # 按国家汇总
                country_data = {}
                for segment in report.data_segments:
                    country = segment.country_code
                    if country not in country_data:
                        country_data[country] = {'downloads': 0, 'proceeds': 0.0}
                    country_data[country]['downloads'] += segment.units
                    country_data[country]['proceeds'] += segment.proceeds

                # 排序并取前N个
                top_countries = sorted(
                    country_data.items(),
                    key=lambda x: x[1]['downloads'],
                    reverse=True
                )[:top_n]

                result = f"下载量排行榜 - {report_date} (前 {top_n} 名):\n\n"
                for i, (country, data) in enumerate(top_countries, 1):
                    result += f"{i}. {country}: {data['downloads']:,} 下载, ${data['proceeds']:,.2f}\n"

                return result
            except Exception as e:
                return f"获取国家排行失败: {str(e)}"

    def register_resources(self, mcp: Any) -> None:
        """注册分析数据相关资源"""

        @mcp.resource("appstore://analytics/summary")
        def get_analytics_summary_resource() -> str:
            """获取分析数据摘要资源"""
            try:
                # 这里需要vendor_number，从配置中获取
                vendor_number = getattr(self.client.config, 'vendor_number', None)
                if not vendor_number:
                    return "未配置vendor_number，无法获取分析数据"

                yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
                report_date_obj = datetime.strptime(yesterday, "%Y-%m-%d").date()

                report = self.get_sales_report(
                    vendor_number=vendor_number,
                    report_type=SalesReportType.SALES,
                    report_subtype="SUMMARY",
                    frequency=ReportFrequency.DAILY,
                    report_date=report_date_obj
                )

                if not report or not report.data_segments:
                    return f"未找到 {yesterday} 的分析数据"

                total_downloads = sum(seg.units for seg in report.data_segments)
                total_proceeds = sum(seg.proceeds for seg in report.data_segments)

                return f"分析摘要 ({yesterday}):\n总下载: {total_downloads:,}\n总收入: ${total_proceeds:,.2f}"
            except Exception as e:
                return f"获取分析摘要失败: {str(e)}"

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
- get_app_analytics: 获取应用分析数据
- get_top_countries: 获取国家排行榜

报告类型:
- SALES: 销售报告 (下载和购买)
- SUBSCRIPTION: 订阅报告
- NEWSSTAND: 报刊订阅报告

频率选项:
- DAILY: 日报告
- WEEKLY: 周报告  
- MONTHLY: 月报报告
- YEARLY: 年报告

使用步骤:
1. 确保已配置vendor_number
2. 选择要查询的应用和日期范围
3. 使用相应的工具获取分析数据

注意事项:
- 销售数据通常有1-2天延迟
- 需要有效的vendor_number才能获取数据
- 部分数据可能需要特定的权限
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
        report_date: date
    ) -> Optional[SalesReport]:
        """获取销售报告"""
        # 格式化日期
        if frequency == ReportFrequency.DAILY:
            date_str = report_date.strftime("%Y-%m-%d")
        elif frequency == ReportFrequency.WEEKLY:
            date_str = report_date.strftime("%Y-%m-%d")  # 周报告也使用相同格式
        elif frequency == ReportFrequency.MONTHLY:
            date_str = report_date.strftime("%Y-%m")
        else:  # YEARLY
            date_str = report_date.strftime("%Y")

        params = {
            "filter[frequency]": frequency.value,
            "filter[reportDate]": date_str,
            "filter[reportSubType]": report_subtype,
            "filter[reportType]": report_type.value,
            "filter[vendorNumber]": vendor_number
        }

        try:
            response = self.client.make_api_request("salesReports", method="GET")

            # 解析报告数据
            if not response.get("data"):
                return None

            # 假设返回的是压缩的CSV数据
            report_data = response["data"][0]
            if "attributes" in report_data and "content" in report_data["attributes"]:
                content = report_data["attributes"]["content"]

                # 解压缩数据（如果是gzip压缩的）
                try:
                    import base64
                    # 如果content是base64编码的
                    if isinstance(content, str):
                        decoded_content = base64.b64decode(content)
                        decompressed_data = gzip.decompress(decoded_content).decode('utf-8')
                    else:
                        decompressed_data = content
                except Exception:
                    # 如果不是压缩或编码的数据，直接使用
                    decompressed_data = content

                # 解析CSV数据
                segments = self._parse_sales_csv(decompressed_data)

                return SalesReport(
                    vendor_number=vendor_number,
                    report_type=report_type,
                    report_subtype=report_subtype,
                    date_type=frequency,
                    report_date=report_date,
                    data_segments=segments
                )
        except Exception as e:
            print(f"获取销售报告失败: {e}")
            return None

    def get_app_analytics(self, app_name: str, vendor_number: str, days: int = 7) -> List[AppAnalyticsData]:
        """获取应用分析数据（最近N天）"""
        analytics_data = []

        for i in range(days):
            report_date = date.today() - timedelta(days=i+1)

            report = self.get_sales_report(
                vendor_number=vendor_number,
                report_type=SalesReportType.SALES,
                report_subtype="SUMMARY",
                frequency=ReportFrequency.DAILY,
                report_date=report_date
            )

            if report:
                app_data = report.get_app_data(app_name)
                if app_data:
                    analytics_data.append(app_data)

        return analytics_data

    def _parse_sales_csv(self, csv_content: str) -> List[AnalyticsReportSegment]:
        """解析销售报告CSV数据"""
        segments = []

        csv_reader = csv.reader(io.StringIO(csv_content), delimiter='\t')

        # 跳过标题行
        next(csv_reader, None)

        for row in csv_reader:
            if len(row) >= 16:  # 确保有足够的列
                segment = AnalyticsReportSegment.from_data_row(row)
                segments.append(segment)

        return segments
