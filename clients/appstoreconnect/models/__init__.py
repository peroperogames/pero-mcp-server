"""
AppStore Connect 数据模型统一导出
"""

# 配置模型
from .config import AppStoreConnectConfig

# 应用模型
from .app import App, Platform

# 用户模型
from .user import TeamMember, UserInvitation, UserRole, ROLE_MAPPING

# TestFlight模型
from .testflight import BetaGroup, BetaTester, BetaTesterState

# 设备模型
from .device import Device, DeviceClass, DeviceStatus, DevicePlatform

# 分析数据模型
from .analytics import (
    AnalyticsReportSegment, AppAnalyticsData, SalesReport,
    ReportFrequency, SalesReportType
)

# 本地化模型
from .localization import (
    AppStoreVersionLocalization, AppInfoLocalization, Screenshot, LocaleState
)

# 任务模型
from .task import PollingTask

__all__ = [
    # 配置模型
    'AppStoreConnectConfig',

    # 应用模型
    'App',
    'Platform',

    # 用户模型
    'TeamMember',
    'UserInvitation',
    'UserRole',
    'ROLE_MAPPING',

    # TestFlight模型
    'BetaGroup',
    'BetaTester',
    'BetaTesterState',

    # 设备模型
    'Device',
    'DeviceClass',
    'DeviceStatus',
    'DevicePlatform',

    # 分析数据模型
    'AnalyticsReportSegment',
    'AppAnalyticsData',
    'SalesReport',
    'ReportFrequency',
    'SalesReportType',

    # 本地化模型
    'AppStoreVersionLocalization',
    'AppInfoLocalization',
    'Screenshot',
    'LocaleState',

    # 任务模型
    'PollingTask'
]
