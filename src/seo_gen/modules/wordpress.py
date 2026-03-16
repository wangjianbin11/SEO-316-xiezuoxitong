"""
WordPress 发布模块 - 升级版

支持 HTML 格式文章直接发布
"""

import base64
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger

from seo_gen.config import settings


class WordPressPublisher:
    """WordPress 发布器 - HTML 格式支持"""

    def __init__(self):
        """初始化 WordPress 发布器"""
        self.site_url = settings.wordpress_site_url.rstrip("/")
        self.username = settings.wordpress_username
        self.app_password = settings.wordpress_app_password

        self._configured = all([self.site_url, self.username, self.app_password])

        if not self._configured:
            logger.warning("WordPress not configured, publishing disabled")

        self.client = httpx.AsyncClient(
            auth=(self.username, self.app_password),
            headers={"Content-Type": "application/json"},
            timeout=60.0,
        )

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        alt_text: str = "",
    ) -> Optional[dict[str, Any]]:
        """
        上传图片到 WordPress 媒体库

        Args:
            image_data: 图片二进制数据
            filename: 文件名
            alt_text: 替代文本

        Returns:
            图片信息字典 {"id": int, "url": str}，失败返回 None
        """
        if not self._configured:
            logger.warning("WordPress not configured, skipping image upload")
            return None

        url = f"{self.site_url}/wp-json/wp/v2/media"

        # Build multipart/form-data
        files = {
            "file": (filename, image_data, "image/png"),
        }

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "image/png",
        }

        try:
            logger.info(f"Uploading image: {filename}")
            response = await self.client.post(
                url,
                content=image_data,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            media_id = data.get("id")
            media_url = data.get("source_url", "")

            # Update alt text
            if media_id and alt_text:
                await self._update_media_alt(media_id, alt_text)

            logger.info(f"Image uploaded successfully: media_id={media_id}, url={media_url}")
            return {"id": media_id, "url": media_url}

        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return None

    async def _update_media_alt(self, media_id: int, alt_text: str):
        """更新媒体文件的 alt text"""
        url = f"{self.site_url}/wp-json/wp/v2/media/{media_id}"
        try:
            await self.client.post(url, json={"alt_text": alt_text})
        except Exception as e:
            logger.warning(f"Failed to update alt text: {e}")

    async def publish_article(
        self,
        title: str,
        content: str,  # HTML format
        excerpt: str,
        slug: str,
        meta_description: str = "",
        featured_media_id: Optional[int] = None,
        status: str = "draft",
    ) -> Optional[int]:
        """
        发布文章到 WordPress（HTML 格式）

        Args:
            title: 文章标题
            content: 文章 HTML 内容
            excerpt: 文章摘要
            slug: URL slug
            meta_description: Meta 描述
            featured_media_id: 特色图片 ID
            status: 文章状态 (draft, publish, pending)

        Returns:
            文章 ID，失败返回 None
        """
        if not self._configured:
            logger.warning("WordPress not configured, skipping article publish")
            return None

        url = f"{self.site_url}/wp-json/wp/v2/posts"

        payload = {
            "title": title,
            "content": content,
            "excerpt": excerpt,
            "slug": slug,
            "status": status,
            "meta": {
                "focus_keyword": meta_description[:50] if meta_description else "",
                "_yoast_wpseo_metadesc": meta_description,
            },
        }

        if featured_media_id:
            payload["featured_media"] = featured_media_id

        try:
            logger.info(f"Publishing article: {title}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            post_id = data.get("id")
            post_link = data.get("link")

            logger.info(f"Article published successfully: post_id={post_id}, link={post_link}")
            return post_id

        except Exception as e:
            logger.error(f"Article publish failed: {e}")
            return None

    async def update_article(
        self,
        post_id: int,
        content: str = None,
        status: str = None,
    ) -> bool:
        """
        更新已发布的文章

        Args:
            post_id: 文章 ID
            content: 更新的 HTML 内容
            status: 文章状态

        Returns:
            是否成功
        """
        if not self._configured:
            return False

        url = f"{self.site_url}/wp-json/wp/v2/posts/{post_id}"

        payload = {}
        if content:
            payload["content"] = content
        if status:
            payload["status"] = status

        try:
            logger.info(f"Updating article: post_id={post_id}")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            logger.info(f"Article updated successfully: post_id={post_id}")
            return True

        except Exception as e:
            logger.error(f"Article update failed: {e}")
            return False

    async def publish_full_article(
        self,
        article: dict[str, Any],
        html_content: str,
        cover_image_data: bytes = None,
        section_images: dict[str, bytes] = None,
        status: str = "draft",
    ) -> Optional[dict[str, Any]]:
        """
        发布完整文章（包含图片上传）

        Args:
            article: 文章数据
            html_content: HTML 格式内容
            cover_image_data: 封面图二进制数据
            section_images: 板块配图字典
            status: 文章状态

        Returns:
            发布结果 {"post_id": int, "link": str, "media_ids": dict}
        """
        if not self._configured:
            logger.warning("WordPress not configured")
            return None

        result = {
            "post_id": None,
            "link": "",
            "media_ids": {},
        }

        try:
            # 1. 上传封面图
            featured_media_id = None
            if cover_image_data:
                featured_media_id = await self.upload_image(
                    cover_image_data,
                    filename=f"{article.get('slug', 'article')}_cover.png",
                    alt_text=article.get("title", ""),
                )
                if featured_media_id:
                    result["media_ids"]["cover"] = featured_media_id

            # 2. 上传板块配图
            section_media_ids = {}
            if section_images:
                for key, img_data in section_images.items():
                    media_id = await self.upload_image(
                        img_data,
                        filename=f"{article.get('slug', 'article')}_{key}.png",
                        alt_text=f"{article.get('title', '')} - {key}",
                    )
                    if media_id:
                        section_media_ids[key] = media_id

                result["media_ids"]["sections"] = section_media_ids

            # 3. 发布文章
            post_id = await self.publish_article(
                title=article.get("title", ""),
                content=html_content,
                excerpt=article.get("metaDescription", "")[:150],
                slug=article.get("slug", ""),
                meta_description=article.get("metaDescription", ""),
                featured_media_id=featured_media_id,
                status=status,
            )

            if post_id:
                result["post_id"] = post_id
                result["link"] = f"{self.site_url}/?p={post_id}"
                logger.info(f"Full article published: post_id={post_id}")

            return result

        except Exception as e:
            logger.error(f"Full article publish failed: {e}")
            return result


# Global singleton
_wordpress_publisher: Optional[WordPressPublisher] = None


def get_wordpress_publisher() -> WordPressPublisher:
    """Get global WordPress publisher singleton"""
    global _wordpress_publisher
    if _wordpress_publisher is None:
        _wordpress_publisher = WordPressPublisher()
    return _wordpress_publisher
