"""
App Store Connect 分析数据处理器 - 负责销售和下载数据分析
"""

import csv
import io
import gzip
from typing import Any, List, Optional
from ...i_mcp_handler import IMCPHandler
from ..models import (AnalyticsReportSegment,
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
            report_type: str = "SALES",
            report_subtype: str = "SUMMARY",
            frequency: str = "DAILY",
            report_date: str = ""
        ) -> str:
            """
            获取App Store Connect销售报告

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

        try:
            # 销售报告API通常返回压缩文件，不是JSON
            response = self.client.make_api_request("salesReports", method="GET", data=data, expect_json=False)

            # 检查响应类型并处理
            if "raw_content" in response:
                # 处理二进制内容（可能是gzip压缩的CSV）
                raw_content = response["raw_content"]
                content_type = response.get("content_type", "")

                print(f"收到二进制内容，类型: {content_type}")

                # 尝试解压缩
                try:
                    if "gzip" in content_type or raw_content.startswith(b'\x1f\x8b'):
                        # 这是gzip压缩的内容
                        import gzip
                        decompressed_data = gzip.decompress(raw_content).decode('utf-8')
                        print(f"成功解压缩，数据长度: {len(decompressed_data)} 字符")
                        print(f"解压后内容前200字符: {decompressed_data[:200]}")
                    else:
                        # 可能是未压缩的文本
                        decompressed_data = raw_content.decode('utf-8')
                        print(f"未压缩文本，长度: {len(decompressed_data)} 字符")
                        print(f"内容前200字符: {decompressed_data[:200]}")

                except Exception as decompress_error:
                    print(f"解压缩失败: {decompress_error}")
                    # 尝试直接作为文本处理
                    try:
                        decompressed_data = raw_content.decode('utf-8')
                        print(f"作为UTF-8文本处理，长度: {len(decompressed_data)} 字符")
                    except:
                        print(f"无法解码为文本，原始内容: {raw_content[:100]}")
                        return None

            elif "text_content" in response:
                # 文本内容
                decompressed_data = response["text_content"]
                print(f"收到文本内容，长度: {len(decompressed_data)} 字符")
                print(f"内容前200字符: {decompressed_data[:200]}")

            elif "data" in response:
                # 标准JSON响应
                if not response.get("data"):
                    print("API返回了空的数据数组")
                    return None

                # 处理JSON格式的报告数据
                report_data = response["data"][0]
                if "attributes" in report_data and "content" in report_data["attributes"]:
                    content = report_data["attributes"]["content"]

                    # 处理base64编码的内容
                    try:
                        import base64
                        if isinstance(content, str):
                            decoded_content = base64.b64decode(content)
                            decompressed_data = gzip.decompress(decoded_content).decode('utf-8')
                        else:
                            decompressed_data = content
                    except Exception as e:
                        decompressed_data = content
                        print(f"数据解压失败，使用原始内容: {e}")
                else:
                    print("JSON响应中缺少content字段")
                    return None
            else:
                print(f"未知的响应格式: {response}")
                return None

            return decompressed_data
        except Exception as e:
            print(f"获取销售报告失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    @classmethod
    def _parse_sales_csv(cls, csv_content: str) -> List[AnalyticsReportSegment]:
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
