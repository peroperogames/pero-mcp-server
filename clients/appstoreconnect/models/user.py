"""
用户和团队相关数据模型
"""

from typing import List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """用户角色类型"""
    ADMIN = "ADMIN"
    FINANCE = "FINANCE"
    DEVELOPER = "DEVELOPER"
    MARKETING = "MARKETING"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"


# 角色映射字典
ROLE_MAPPING = {
    "管理员": UserRole.ADMIN.value,
    "财务": UserRole.FINANCE.value,
    "开发者": UserRole.DEVELOPER.value,
    "营销": UserRole.MARKETING.value,
    "客服": UserRole.CUSTOMER_SUPPORT.value
}


@dataclass
class TeamMember:
    """团队成员信息"""
    id: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]

    @property
    def full_name(self) -> str:
        """获取完整姓名"""
        return f"{self.first_name} {self.last_name}"

    @classmethod
    def from_api_response(cls, data: dict) -> 'TeamMember':
        """从 API 响应创建 TeamMember 实例"""
        attributes = data.get("attributes", {})
        relationships = data.get("relationships", {})
        visible_apps = relationships.get("visibleApps", {}).get("data", [])

        return cls(
            id=data.get("id", ""),
            email=attributes.get("username", ""),
            first_name=attributes.get("firstName", ""),
            last_name=attributes.get("lastName", ""),
            roles=[role.get("type", "") for role in visible_apps]
        )


@dataclass
class UserInvitation:
    """用户邀请信息"""
    id: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    expires: str

    @property
    def full_name(self) -> str:
        """获取完整姓名"""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_expired(self) -> bool:
        """检查邀请是否已过期"""
        try:
            expiry_date = datetime.fromisoformat(self.expires.replace('Z', '+00:00'))
            return datetime.now().replace(tzinfo=expiry_date.tzinfo) > expiry_date
        except:
            return False

    @classmethod
    def from_api_response(cls, data: dict) -> 'UserInvitation':
        """从 API 响应创建 UserInvitation 实例"""
        attributes = data.get("attributes", {})

        return cls(
            id=data.get("id", ""),
            email=attributes.get("email", ""),
            first_name=attributes.get("firstName", ""),
            last_name=attributes.get("lastName", ""),
            roles=attributes.get("roles", []),
            expires=attributes.get("expirationDate", "")
        )
