"""
Google Play Developer Reporting API 财务处理器 - 负责收入和财务数据分析
"""

import io
import os
import zipfile
from typing import Any

from ...mcp_handler_interface import IMCPHandler


class FinancialHandler(IMCPHandler):
    """财务处理器 - 负责收入报告、财务数据等分析功能"""

    def __init__(self, client):
        self.client = client

    def register_tools(self, mcp: Any) -> None:
        """注册财务分析相关工具"""

        @mcp.tool("get_googleplay_monthly_financial_report")
        def get_googleplay_monthly_financial_report_tool(target_month: str) -> str:
            """
            获取指定月份的Google Play财务收入报告。

            从Google Cloud Storage下载压缩的收入报告文件，文件包含详细的收入、税费和分成数据。

            Args:
                target_month (str): (Required) 目标月份，格式为 YYYYMM，例如 "202401"

            Returns:
                str: 下载结果的描述信息，包含文件大小和状态
            """
            return self.get_monthly_financial_report(target_month)

    def register_resources(self, mcp: Any) -> None:
        pass

    def register_prompts(self, mcp: Any) -> None:
        """注册财务分析相关提示"""

        @mcp.prompt("googleplay_financial_report")
        def googleplay_financial_report_prompt(
                target_month: str = "",
                report_type: str = ""
        ) -> str:
            """Google Play财务报告提示"""
            return f"""Google Play 财务报告助手

查询信息:
- 目标月份: {target_month}
- 报告类型: {report_type}

支持的操作:
- get_googleplay_monthly_financial_report: 获取月度财务收入报告

月份格式:
- 格式: YYYYMM (例如: 202401 表示 2024年1月)
- 示例: 202312, 202401, 202402

财务报告包含数据:
- 收入明细: 应用收入、内购收入、订阅收入
- 税费信息: 各地区税费扣除详情
- 分成数据: Google Play分成后的净收入
- 地区分布: 不同国家/地区的收入分布
- 货币信息: 多种货币的收入数据
- 时间维度: 按日期的详细收入记录

数据来源:
- Google Cloud Storage中的压缩财务报告文件
- 自动合并多个CSV文件的数据
- 包含完整的收入和税费计算

使用步骤:
1. 确保设置了GOOGLE_PLAY_CLOUD_STORAGE_BUCKET环境变量
2. 调用get_googleplay_monthly_financial_report工具
3. 提供YYYYMM格式的目标月份
4. 获取合并后的CSV格式财务数据

注意事项:
- 数据通常有1-2个月的延迟
- 报告文件较大，处理可能需要一些时间
- 包含敏感财务信息，请妥善保管
"""

    def get_monthly_financial_report(self, target_month: str) -> str:
        """
        获取指定月份的Google Play财务收入报告。

        从Google Cloud Storage下载压缩的收入报告文件，文件包含详细的收入、税费和分成数据。

        Args:
            target_month (str): (Required) 目标月份，格式为 YYYYMM，例如 "202401"

        Returns:
            str: 合并后的CSV内容
        """
        # 构建存储桶名称和对象名称
        bucket_suffix = os.getenv('GOOGLE_PLAY_CLOUD_STORAGE_BUCKET')
        if not bucket_suffix:
            return "缺少环境变量: GOOGLE_PLAY_CLOUD_STORAGE_BUCKET"

        bucket_name = f"pubsite_prod_{bucket_suffix}"
        prefix = f"earnings/earnings_{target_month}"

        # 下载文件
        files_dict = self.client.download_from_cloud_storage(bucket_name, prefix)

        if not files_dict:
            return f"未找到 {target_month} 月份的财务报告文件"

        merged_content = []
        csv_header = None
        processed_files = 0

        # 遍历下载的文件字典
        for filename, file_data in files_dict.items():
            try:
                # 确保file_data是字节类型
                if isinstance(file_data, str):
                    file_data = file_data.encode('utf-8')

                # 使用BytesIO创建文件对象
                with zipfile.ZipFile(io.BytesIO(file_data)) as zip_file:
                    # 遍历zip文件中的所有文件
                    for file_info in zip_file.infolist():
                        if file_info.filename.endswith('.csv'):
                            # 读取CSV文件内容
                            with zip_file.open(file_info) as csv_file:
                                content = csv_file.read().decode('utf-8')
                                lines = content.strip().split('\n')

                                if lines:
                                    # 处理第一个CSV文件，保存表头
                                    if csv_header is None:
                                        csv_header = lines[0]
                                        merged_content.extend(lines)
                                    else:
                                        # 跳过后续文件的表头，只添加数据行
                                        if lines[0] == csv_header:
                                            merged_content.extend(lines[1:])
                                        else:
                                            # 如果表头不同，包含表头信息
                                            merged_content.append(
                                                f"# 来自文件: {file_info.filename} (源文件: {filename})")
                                            merged_content.extend(lines)

                                    processed_files += 1

            except zipfile.BadZipFile:
                merged_content.append(f"# 错误: 无法解析zip文件 {filename}")
                continue
            except Exception as e:
                merged_content.append(f"# 错误处理文件 {filename}: {str(e)}")
                continue

        if not merged_content:
            return f"未找到任何CSV文件在 {target_month} 月份的财务报告中"

        # 添加汇总信息
        summary = f"# Google Play 财务报告 - {target_month}\n"
        summary += f"# 处理的文件数量: {processed_files}\n"
        summary += f"# 下载的zip文件数量: {len(files_dict)}\n"
        summary += f"# 总数据行数: {len(merged_content) - merged_content.count(csv_header) if csv_header else len(merged_content)}\n\n"

        return summary + '\n'.join(merged_content)
