"""
飞书集成模块

与飞书多维表格集成，读取关键词和更新状态
"""

from typing import Any, Optional

import httpx
from loguru import logger

from seo_gen.config import settings


class FeishuClient:
    """飞书 API 客户端"""

    def __init__(self):
        """初始化飞书客户端"""
        self.app_id = settings.feishu_app_id
        self.app_secret = settings.feishu_app_secret
        self.app_token = settings.feishu_bitable_app_token
        self.table_id = settings.feishu_bitable_table_id

        self._access_token: Optional[str] = None
        self._client = httpx.AsyncClient(timeout=30.0)

        if not all([self.app_id, self.app_secret]):
            logger.warning("飞书配置不完整")
            self._configured = False
        else:
            self._configured = True

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()

    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self._access_token:
            return self._access_token

        if not self._configured:
            raise ValueError("飞书未配置")

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        response = await self._client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        self._access_token = data.get("tenant_access_token")

        if not self._access_token:
            raise ValueError("获取飞书访问令牌失败")

        return self._access_token

    async def get_records(
        self,
        filter_status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
       获取多维表格记录

        Args:
            filter_status: 按状态筛选

        Returns:
            记录列表
        """
        if not self._configured:
            logger.warning("飞书未配置，返回空列表")
            return []

        access_token = await self._get_access_token()

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"

        params = {
            "page_size": 100,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        try:
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            records = data.get("data", {}).get("items", [])

            logger.info(f"从飞书获取 {len(records)} 条记录")
            return records

        except Exception as e:
            logger.error(f"获取飞书记录失败: {e}")
            return []

    async def update_record(
        self,
        record_id: str,
        fields: dict[str, Any],
    ) -> bool:
        """
        更新记录

        Args:
            record_id: 记录 ID
            fields: 要更新的字段

        Returns:
            是否成功
        """
        if not self._configured:
            return False

        access_token = await self._get_access_token()

        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "fields": fields,
        }

        try:
            response = await self._client.put(url, json=payload, headers=headers)
            response.raise_for_status()

            logger.info(f"飞书记录更新成功: record_id={record_id}")
            return True

        except Exception as e:
            logger.error(f"更新飞书记录失败: {e}")
            return False

    async def mark_as_published(
        self,
        record_id: str,
        wp_link: str,
        md_link: Optional[str] = None,
    ) -> bool:
        """
        标记记录为已发布

        Args:
            record_id: 记录 ID
            wp_link: WordPress 文章链接
            md_link: Markdown 文件链接（可选）

        Returns:
            是否成功
        """
        fields = {
            "状态": "已发布",
            "WordPress链接": wp_link,
        }

        if md_link:
            fields["文章内容(md链接)"] = md_link

        return await self.update_record(record_id, fields)

    def sync_get_records(
        self,
        filter_status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """同步版本"""
        import asyncio

        return asyncio.run(self.get_records(filter_status))


# 全局单例
_feishu_client: Optional[FeishuClient] = None


def get_feishu_client() -> FeishuClient:
    """获取全局飞书客户端单例"""
    global _feishu_client
    if _feishu_client is None:
        _feishu_client = FeishuClient()
    return _feishu_client
