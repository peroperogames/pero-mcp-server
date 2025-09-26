"""
Google Play Developer Reporting API MCP 客户端 - 重构为中转站模式
"""
import json
import os
import tempfile
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from .models.config import GooglePlayConfig
from ..mcp_client_interface import IMCPClient


class GooglePlayMCPClient(IMCPClient):
    """Google Play Developer Reporting API MCP 客户端 - 作为中转站协调各个处理器"""

    def __init__(self):
        """初始化客户端和各个处理器"""
        self.config = None
        self._storage_service = None
        # 调用父类的初始化方法来自动发现处理器
        super().__init__()

    # =============================================================================
    # 配置和基础服务方法 - 供handler调用
    # =============================================================================

    def set_config(self, config: GooglePlayConfig) -> None:
        """设置配置"""
        self.config = config
        self._init_services()

    def _load_config_from_env(self) -> Optional[GooglePlayConfig]:
        """从环境变量加载Google Play配置，从.env中读取JSON字段并组装服务账号配置"""
        # 从环境变量读取服务账号JSON的各个字段
        service_account_json = {
            "type": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_TYPE', 'service_account'),
            "project_id": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_PROJECT_ID'),
            "private_key_id": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_PRIVATE_KEY_ID'),
            "private_key": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_PRIVATE_KEY'),
            "client_email": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_CLIENT_EMAIL'),
            "client_id": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_CLIENT_ID'),
            "auth_uri": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
            "token_uri": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
            "auth_provider_x509_cert_url": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL',
                                                     'https://www.googleapis.com/oauth2/v1/certs'),
            "client_x509_cert_url": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL'),
            "universe_domain": os.getenv('GOOGLE_PLAY_SERVICE_ACCOUNT_UNIVERSE_DOMAIN', 'googleapis.com')
        }

        package_name = os.getenv('GOOGLE_PLAY_PACKAGE_NAME')

        # 检查必需的字段
        required_fields = ['project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
        missing_fields = [field for field in required_fields if not service_account_json[field]]

        if missing_fields:
            print(
                f"缺少必需的环境变量: {', '.join(f'GOOGLE_PLAY_SERVICE_ACCOUNT_{field.upper()}' for field in missing_fields)}")
            return None

        try:
            # 处理私钥格式 - 将 \n 转换为真正的换行符
            if service_account_json['private_key'] and '\\n' in service_account_json['private_key']:
                service_account_json['private_key'] = service_account_json['private_key'].replace('\\n', '\n')

            # 创建临时JSON文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(service_account_json, temp_file, indent=2)
                temp_service_account_file = temp_file.name

            config = GooglePlayConfig(
                service_account_file=temp_service_account_file,
                package_name=package_name
            )
            return config
        except Exception as e:
            print(f"从环境变量创建Google Play配置失败: {e}")
            return None

    def _init_services(self) -> None:
        """初始化Google API服务"""
        if not self.config:
            return

        try:
            # 加载服务账号凭证
            credentials = service_account.Credentials.from_service_account_file(
                self.config.service_account_file,
                scopes=[
                    'https://www.googleapis.com/auth/devstorage.read_only'
                ]
            )

            # 初始化Google Cloud Storage服务（用于下载报告文件）
            self._storage_service = build('storage', 'v1', credentials=credentials)

        except Exception as e:
            print(f"初始化Google API服务失败: {e}")
            self._storage_service = None

    def _ensure_authenticated(self) -> bool:
        """确保已认证"""
        if not self.config:
            self.config = self._load_config_from_env()
            if not self.config:
                return False

        if not self._storage_service:
            self._init_services()

        return self._storage_service is not None

    def list_cloud_storage_objects(self, bucket_name: str, prefix: str) -> Optional[list]:
        """
        列出 Google Cloud Storage 存储桶中的对象

        Args:
            bucket_name: 存储桶名称，通常格式为 'pubsite_prod_rev_...'
            prefix: 对象前缀，通常格式为 'earnings/earnings_YYYYMM.zip'

        Returns:
            包含对象信息的列表，如果列表失败则返回 None

        Raises:
            Exception: 当认证失败或其他错误时抛出异常
        """
        # 确保客户端已认证
        if not self._ensure_authenticated():
            raise Exception("Google Play 客户端认证失败")

        if not self._storage_service:
            raise Exception("Google Cloud Storage 服务未初始化")

        try:
            print(f"尝试访问存储桶: {bucket_name}")
            print(f"查找前缀: {prefix}")

            # 列出存储桶中的对象
            objects_request = self._storage_service.objects().list(
                bucket=bucket_name,
                prefix=prefix
            )
            objects_response = objects_request.execute()

            items = objects_response.get('items', [])
            print(f"存储桶中找到的文件: {len(items)} 个")

            if not items:
                print("未找到匹配的文件")
                return None

            # 显示找到的文件
            for item in items:
                print(f"  - {item['name']}")

            return items

        except Exception as e:
            print(f"列出文件时出错: {e}")
            raise Exception(f"从 Google Cloud Storage 列出文件失败: {e}")

    def download_from_cloud_storage(self, bucket_name: str, prefix: str) -> Optional[dict]:
        """
        从 Google Cloud Storage 下载财务报告文件

        Args:
            bucket_name: 存储桶名称，通常格式为 'pubsite_prod_rev_...'
            prefix: 对象前缀，通常格式为 'earnings/earnings_YYYYMM.zip'

        Returns:
            包含所有文件内容的字典，格式为 {filename: file_content_bytes}，如果下载失败则返回 None

        Raises:
            Exception: 当认证失败或其他错误时抛出异常
        """
        # 确保客户端已认证
        if not self._ensure_authenticated():
            raise Exception("Google Play 客户端认证失败")

        if not self._storage_service:
            raise Exception("Google Cloud Storage 服务未初始化")

        try:
            # 获取要下载的文件列表
            items = self.list_cloud_storage_objects(bucket_name, prefix)

            if not items:
                return None

            # 下载所有匹配的文件
            downloaded_files = {}
            for item in items:
                object_name = item['name']

                print(f"开始下载文件: {object_name}")

                try:
                    # 下载文件内容
                    media_request = self._storage_service.objects().get_media(
                        bucket=bucket_name,
                        object=object_name
                    )

                    # 执行下载请求
                    file_content = media_request.execute()

                    # 使用文件名作为键存储文件内容
                    filename = object_name.split('/')[-1]  # 获取文件名部分
                    downloaded_files[filename] = file_content

                    print(f"文件 {filename} 下载成功，大小: {len(file_content)} 字节")

                except Exception as file_error:
                    print(f"下载文件 {object_name} 时出错: {file_error}")
                    # 继续下载其他文件，不中断整个过程

            if downloaded_files:
                print(f"总共成功下载 {len(downloaded_files)} 个文件")
                return downloaded_files
            else:
                print("没有文件下载成功")
                return None

        except Exception as e:
            print(f"下载文件时出错: {e}")
            raise Exception(f"从 Google Cloud Storage 下载文件失败: {e}")
