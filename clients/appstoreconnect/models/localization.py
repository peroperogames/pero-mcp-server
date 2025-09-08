"""
本地化相关数据模型
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class LocaleState(Enum):
    """本地化状态枚举"""
    PREPARE_FOR_SUBMISSION = "PREPARE_FOR_SUBMISSION"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    REJECTED = "REJECTED"
    READY_FOR_SALE = "READY_FOR_SALE"
    PROCESSING_FOR_APP_STORE = "PROCESSING_FOR_APP_STORE"


@dataclass
class AppStoreVersionLocalization:
    """App Store版本本地化信息"""
    id: str
    locale: str
    description: Optional[str] = None
    keywords: Optional[str] = None
    marketing_url: Optional[str] = None
    promotional_text: Optional[str] = None
    support_url: Optional[str] = None
    whats_new: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'AppStoreVersionLocalization':
        """从API响应创建AppStoreVersionLocalization对象"""
        attributes = data.get("attributes", {})

        return cls(
            id=data["id"],
            locale=attributes.get("locale", ""),
            description=attributes.get("description"),
            keywords=attributes.get("keywords"),
            marketing_url=attributes.get("marketingUrl"),
            promotional_text=attributes.get("promotionalText"),
            support_url=attributes.get("supportUrl"),
            whats_new=attributes.get("whatsNew")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "locale": self.locale,
            "description": self.description,
            "keywords": self.keywords,
            "marketing_url": self.marketing_url,
            "promotional_text": self.promotional_text,
            "support_url": self.support_url,
            "whats_new": self.whats_new
        }


@dataclass
class AppInfoLocalization:
    """应用信息本地化"""
    id: str
    locale: str
    name: Optional[str] = None
    subtitle: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    privacy_choices_url: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'AppInfoLocalization':
        """从API响应创建AppInfoLocalization对象"""
        attributes = data.get("attributes", {})

        return cls(
            id=data["id"],
            locale=attributes.get("locale", ""),
            name=attributes.get("name"),
            subtitle=attributes.get("subtitle"),
            privacy_policy_url=attributes.get("privacyPolicyUrl"),
            privacy_choices_url=attributes.get("privacyChoicesUrl")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "locale": self.locale,
            "name": self.name,
            "subtitle": self.subtitle,
            "privacy_policy_url": self.privacy_policy_url,
            "privacy_choices_url": self.privacy_choices_url
        }


@dataclass
class Screenshot:
    """应用截图"""
    id: str
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    source_file_checksum: Optional[str] = None
    image_asset: Optional[Dict[str, Any]] = None
    asset_delivery_state: Optional[str] = None
    upload_operations: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Screenshot':
        """从API响应创建Screenshot对象"""
        attributes = data.get("attributes", {})

        return cls(
            id=data["id"],
            file_size=attributes.get("fileSize"),
            file_name=attributes.get("fileName"),
            source_file_checksum=attributes.get("sourceFileChecksum"),
            image_asset=attributes.get("imageAsset"),
            asset_delivery_state=attributes.get("assetDeliveryState"),
            upload_operations=attributes.get("uploadOperations")
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "file_size": self.file_size,
            "file_name": self.file_name,
            "source_file_checksum": self.source_file_checksum,
            "image_asset": self.image_asset,
            "asset_delivery_state": self.asset_delivery_state,
            "upload_operations": self.upload_operations
        }
