"""
任务相关数据模型
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PollingTask:
    """轮询任务信息"""
    task_id: str
    email: str
    app_name: str
    start_time: datetime
    status: str
    max_duration_hours: int = 2
    poll_interval_minutes: int = 5

    @property
    def elapsed_minutes(self) -> float:
        """获取已运行时间（分钟）"""
        elapsed = datetime.now() - self.start_time
        return elapsed.total_seconds() / 60

    @property
    def remaining_minutes(self) -> float:
        """获取剩余时间（分钟）"""
        max_duration_seconds = self.max_duration_hours * 3600
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        remaining_seconds = max(0.0, max_duration_seconds - elapsed_seconds)
        return remaining_seconds / 60

    @property
    def is_expired(self) -> bool:
        """检查任务是否已过期"""
        return self.remaining_minutes <= 0
