"""
分析数据相关模型
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


class ReportFrequency(Enum):
    """报告频率枚举"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SalesReportType(Enum):
    """销售报告类型枚举"""
    SALES = "SALES"
    NEWSSTAND = "NEWSSTAND"
    SUBSCRIPTION = "SUBSCRIPTION"
    SUBSCRIPTION_EVENT = "SUBSCRIPTION_EVENT"


class FinanceReportType(Enum):
    """财务报告类型枚举"""
    FINANCIAL = "FINANCIAL"


class FinanceReportRegion(Enum):
    """财务报告区域枚举"""
    ZZ = "ZZ"  # Worldwide


@dataclass
class AnalyticsReportSegment:
    """分析报告段数据"""
    app_name: str
    app_apple_id: str
    units: int
    proceeds: float
    country_code: str
    currency_code: str

    @classmethod
    def from_data_row(cls, data: List[str]) -> 'AnalyticsReportSegment':
        """从数据行创建分析报告段"""
        return cls(
            app_name=data[4] if len(data) > 4 else "",
            app_apple_id=data[3] if len(data) > 3 else "",
            units=int(data[7]) if len(data) > 7 and data[7].isdigit() else 0,
            proceeds=float(data[8]) if len(data) > 8 and data[8].replace('.', '').isdigit() else 0.0,
            country_code=data[13] if len(data) > 13 else "",
            currency_code=data[15] if len(data) > 15 else ""
        )


@dataclass
class FinanceReportSegment:
    """财务报告段数据"""
    start_date: str
    end_date: str
    usd_proceeds: float
    proceeds: float
    currency_code: str
    country_code: str

    @classmethod
    def from_data_row(cls, data: List[str]) -> 'FinanceReportSegment':
        """从财务报告数据行创建段"""
        return cls(
            start_date=data[0] if len(data) > 0 else "",
            end_date=data[1] if len(data) > 1 else "",
            usd_proceeds=float(data[5]) if len(data) > 5 and data[5].replace('.', '').replace('-',
                                                                                              '').isdigit() else 0.0,
            proceeds=float(data[6]) if len(data) > 6 and data[6].replace('.', '').replace('-', '').isdigit() else 0.0,
            currency_code=data[3] if len(data) > 3 else "",
            country_code=data[2] if len(data) > 2 else ""
        )


@dataclass
class AppAnalyticsData:
    """应用分析数据"""
    app_id: str
    app_name: str
    total_downloads: int
    total_proceeds: float
    downloads_by_country: Dict[str, int]
    proceeds_by_country: Dict[str, float]
    report_date: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "app_name": self.app_name,
            "total_downloads": self.total_downloads,
            "total_proceeds": self.total_proceeds,
            "downloads_by_country": self.downloads_by_country,
            "proceeds_by_country": self.proceeds_by_country,
            "report_date": self.report_date
        }


@dataclass
class SalesReport:
    """销售报告"""
    vendor_number: str
    report_type: SalesReportType
    report_subtype: str
    date_type: ReportFrequency
    report_date: str
    data_segments: List[AnalyticsReportSegment]

    def get_app_data(self, app_name: str) -> Optional[AppAnalyticsData]:
        """获取特定应用的分析数据"""
        app_segments = [seg for seg in self.data_segments if seg.app_name == app_name]
        if not app_segments:
            return None

        total_downloads = sum(seg.units for seg in app_segments)
        total_proceeds = sum(seg.proceeds for seg in app_segments)

        downloads_by_country = {}
        proceeds_by_country = {}

        for seg in app_segments:
            country = seg.country_code
            downloads_by_country[country] = downloads_by_country.get(country, 0) + seg.units
            proceeds_by_country[country] = proceeds_by_country.get(country, 0.0) + seg.proceeds

        return AppAnalyticsData(
            app_id=app_segments[0].app_apple_id,
            app_name=app_name,
            total_downloads=total_downloads,
            total_proceeds=total_proceeds,
            downloads_by_country=downloads_by_country,
            proceeds_by_country=proceeds_by_country,
            report_date=self.report_date
        )


@dataclass
class FinanceReport:
    """财务报告"""
    vendor_number: str
    report_type: FinanceReportType
    report_subtype: str
    date_type: ReportFrequency
    report_date: str
    data_segments: List[FinanceReportSegment]

    def get_total_proceeds(self) -> float:
        """计算报告中所有段的总收益"""
        return sum(segment.proceeds for segment in self.data_segments)

    def get_total_usd_proceeds(self) -> float:
        """计算报告中所有段的总美元收益"""
        return sum(segment.usd_proceeds for segment in self.data_segments)

    def get_segment_data(self, country_code: str) -> Optional[FinanceReportSegment]:
        """获取特定国家/地区的财务数据段"""
        for segment in self.data_segments:
            if segment.country_code == country_code:
                return segment
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "vendor_number": self.vendor_number,
            "report_type": self.report_type.value,
            "report_subtype": self.report_subtype,
            "date_type": self.date_type.value,
            "report_date": self.report_date,
            "data_segments": [segment.to_dict() for segment in self.data_segments]
        }
