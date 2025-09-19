"""
TestFlight相关数据模型
"""

from dataclasses import dataclass
from enum import Enum


class BetaTesterState(Enum):
    """测试者状态"""
    NOT_INVITED = "NOT_INVITED"
    INVITED = "INVITED"
    ACCEPTED = "ACCEPTED"
    INSTALLED = "INSTALLED"
    REVOKED = "REVOKED"


@dataclass
class BetaGroup:
    """测试组信息"""
    id: str
    name: str
    is_internal_group: bool

    @property
    def group_type(self) -> str:
        """获取组类型描述"""
        return "内部" if self.is_internal_group else "外部"

    @classmethod
    def from_api_response(cls, data: dict) -> 'BetaGroup':
        """从 API 响应创建 BetaGroup 实例"""
        attributes = data.get("attributes", {})

        return cls(
            id=data.get("id", ""),
            name=attributes.get("name", ""),
            is_internal_group=attributes.get("isInternalGroup", False)
        )


@dataclass
class BetaTester:
    """测试者信息"""
    id: str
    email: str
    first_name: str
    last_name: str
    state: BetaTesterState

    @property
    def full_name(self) -> str:
        """获取完整姓名"""
        return f"{self.first_name} {self.last_name}"

    @property
    def state_description(self) -> str:
        """获取状态描述"""
        state_map = {
            BetaTesterState.NOT_INVITED: "未邀请",
            BetaTesterState.INVITED: "已邀请",
            BetaTesterState.ACCEPTED: "已接受",
            BetaTesterState.INSTALLED: "已安装",
            BetaTesterState.REVOKED: "已撤销",

        }
        return state_map.get(self.state, "未知状态")

    @classmethod
    def from_api_response(cls, data: dict) -> 'BetaTester':
        """从 API 响应创建 BetaTester 实例"""
        attributes = data.get("attributes", {})
        state_str = attributes.get("state", "NOT_INVITED")

        try:
            state = BetaTesterState(state_str)
        except ValueError:
            state = BetaTesterState.NOT_INVITED

        return cls(
            id=data.get("id", ""),
            email=attributes.get("email", ""),
            first_name=attributes.get("firstName", ""),
            last_name=attributes.get("lastName", ""),
            state=state
        )
