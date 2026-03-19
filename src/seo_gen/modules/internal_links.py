"""
内部链接管理模块

从网站地图获取内部链接，用于文章内部链接优化
- 自动匹配相关文章
- 3-5 个内部链接
- 链接关键词加粗+橘色
"""

import re
import httpx
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path

from loguru import logger

REQUEST_TIMEOUT = 15.0

# ASG 网站地图中的文章列表（定期更新）
SITEMAP_URLS = [
    "https://asgdropshipping.com/where-are-coach-bags-made/",
    "https://asgdropshipping.com/how-to-dropshipping-coach/",
    "https://asgdropshipping.com/how-long-is-dropshipping-ethical/",
    "https://asgdropshipping.com/what-does-mean-what-does-documents-against-payment-mean/",
    "https://asgdropshipping.com/where-where-shein-clothing-is-made/",
    "https://asgdropshipping.com/how-to-how-to-get-shorter-aliexpress-shipping-times/",
    "https://asgdropshipping.com/what-is-1688-vs-taobao-a-comprehensive-comparison/",
    "https://asgdropshipping.com/how-to-comprehensive-guide-to-asian-size-conversions-to-us/",
    "https://asgdropshipping.com/what-is-what-is-mass-production-the-ultimate-guide/",
    "https://asgdropshipping.com/what-is-dropshipping-tariffs/",
    "https://asgdropshipping.com/how-to-dropshipping-fitness-products/",
    "https://asgdropshipping.com/how-to-shopify-dropshipping-store/",
    "https://asgdropshipping.com/what-is-dropshipping-paypal/",
    "https://asgdropshipping.com/how-to-temu-for-dropshipping/",
    "https://asgdropshipping.com/how-to-handle-returns-in-dropshipping/",
    "https://asgdropshipping.com/does-work-does-walmart-allow-dropshipping/",
    "https://asgdropshipping.com/how-to-walmart-for-dropshipping/",
    "https://asgdropshipping.com/what-is-wholesale-makeup-from-china/",
    "https://asgdropshipping.com/how-to-china-wholesale-websites/",
    "https://asgdropshipping.com/what-is-international-warehouse-shein/",
    "https://asgdropshipping.com/how-to-find-a-niche-for-dropshipping/",
    "https://asgdropshipping.com/how-to-fob-meaning-2/",
    "https://asgdropshipping.com/how-to-returns-work-with-dropshipping/",
    "https://asgdropshipping.com/what-is-walmart-account-for-dropshipping/",
    "https://asgdropshipping.com/how-to-dropshipping-product-box/",
    "https://asgdropshipping.com/how-to-best-shoes-manufacturer-china/",
    "https://asgdropshipping.com/what-is-dropshipping-business-for-sales-tax/",
    "https://asgdropshipping.com/how-to-dropshipping-site-can-be-used-for-tiktok/",
    "https://asgdropshipping.com/how-to-ai-with-dropshipping/",
    "https://asgdropshipping.com/what-is-besides-dropshipping/",
    "https://asgdropshipping.com/how-long-permit-number-dropshipping/",
    "https://asgdropshipping.com/how-to-dropshipping-stores-in-south-africa/",
    "https://asgdropshipping.com/how-to-facebook-page-for-dropshipping/",
    "https://asgdropshipping.com/how-to-llc-high-ticket-dropshipping/",
    "https://asgdropshipping.com/how-to-account-in-cj-dropshipping/",
    "https://asgdropshipping.com/how-to-private-suppliers-for-dropshipping/",
    "https://asgdropshipping.com/what-is-my-dropshipping-store/",
    "https://asgdropshipping.com/how-to-dropshipping-ads-2025/",
    "https://asgdropshipping.com/where-to-best-ecommerce-platform-for-dropshipping/",
    "https://asgdropshipping.com/where-are-best-drop-shipping-websites/",
    "https://asgdropshipping.com/do-you-need-dropshipping-spy-tools/",
    "https://asgdropshipping.com/do-you-need-best-dropshipping-app/",
    # 常见主题文章
    "https://asgdropshipping.com/how-to-start-dropshipping/",
    "https://asgdropshipping.com/best-dropshipping-suppliers/",
    "https://asgdropshipping.com/dropshipping-agent/",
    "https://asgdropshipping.com/cj-dropshipping-review/",
    "https://asgdropshipping.com/aliexpress-dropshipping/",
    "https://asgdropshipping.com/shopify-dropshipping/",
    "https://asgdropshipping.com/woocommerce-dropshipping/",
    "https://asgdropshipping.com/tiktok-shop-dropshipping/",
    "https://asgdropshipping.com/quality-control-dropshipping/",
    "https://asgdropshipping.com/shipping-from-china/",
    "https://asgdropshipping.com/sourcing-agent-china/",
    "https://asgdropshipping.com/china-wholesale/",
    "https://asgdropshipping.com/1688-agent/",
    "https://asgdropshipping.com/taobao-agent/",
]

# 关键词到URL的映射（用于智能匹配）
KEYWORD_URL_MAPPING = {
    # Dropshipping 基础
    "dropshipping": "https://asgdropshipping.com/how-to-start-dropshipping/",
    "start dropshipping": "https://asgdropshipping.com/how-to-start-dropshipping/",
    "dropshipping business": "https://asgdropshipping.com/how-to-start-dropshipping/",
    "dropshipping ethical": "https://asgdropshipping.com/how-long-is-dropshipping-ethical/",

    # 平台相关
    "shopify dropshipping": "https://asgdropshipping.com/how-to-shopify-dropshipping-store/",
    "shopify store": "https://asgdropshipping.com/how-to-shopify-dropshipping-store/",
    "walmart dropshipping": "https://asgdropshipping.com/how-to-walmart-for-dropshipping/",
    "walmart allow dropshipping": "https://asgdropshipping.com/does-work-does-walmart-allow-dropshipping/",
    "temu dropshipping": "https://asgdropshipping.com/how-to-temu-for-dropshipping/",
    "tiktok shop": "https://asgdropshipping.com/how-to-dropshipping-site-can-be-used-for-tiktok/",

    # 供应商相关
    "dropshipping suppliers": "https://asgdropshipping.com/best-dropshipping-suppliers/",
    "cj dropshipping": "https://asgdropshipping.com/how-to-account-in-cj-dropshipping/",
    "aliexpress": "https://asgdropshipping.com/how-to-how-to-get-shorter-aliexpress-shipping-times/",
    "aliexpress shipping": "https://asgdropshipping.com/how-to-how-to-get-shorter-aliexpress-shipping-times/",
    "private suppliers": "https://asgdropshipping.com/how-to-private-suppliers-for-dropshipping/",
    "dropshipping agent": "https://asgdropshipping.com/dropshipping-agent/",

    # 中国采购
    "china wholesale": "https://asgdropshipping.com/how-to-china-wholesale-websites/",
    "wholesale from china": "https://asgdropshipping.com/what-is-wholesale-makeup-from-china/",
    "1688": "https://asgdropshipping.com/what-is-1688-vs-taobao-a-comprehensive-comparison/",
    "taobao": "https://asgdropshipping.com/what-is-1688-vs-taobao-a-comprehensive-comparison/",
    "sourcing agent": "https://asgdropshipping.com/sourcing-agent-china/",

    # 物流和退货
    "returns": "https://asgdropshipping.com/how-to-handle-returns-in-dropshipping/",
    "handle returns": "https://asgdropshipping.com/how-to-handle-returns-in-dropshipping/",
    "shipping from china": "https://asgdropshipping.com/shipping-from-china/",
    "international warehouse": "https://asgdropshipping.com/what-is-international-warehouse-shein/",

    # 产品和利基
    "find a niche": "https://asgdropshipping.com/how-to-find-a-niche-for-dropshipping/",
    "niche for dropshipping": "https://asgdropshipping.com/how-to-find-a-niche-for-dropshipping/",
    "fitness products": "https://asgdropshipping.com/how-to-dropshipping-fitness-products/",

    # 工具和营销
    "dropshipping ads": "https://asgdropshipping.com/how-to-dropshipping-ads-2025/",
    "facebook page": "https://asgdropshipping.com/how-to-facebook-page-for-dropshipping/",
    "dropshipping tools": "https://asgdropshipping.com/do-you-need-dropshipping-spy-tools/",
    "dropshipping app": "https://asgdropshipping.com/do-you-need-best-dropshipping-app/",
    "ai with dropshipping": "https://asgdropshipping.com/how-to-ai-with-dropshipping/",

    # 质量控制
    "quality control": "https://asgdropshipping.com/quality-control-dropshipping/",

    # 术语
    "fob meaning": "https://asgdropshipping.com/how-to-fob-meaning-2/",
    "tariffs": "https://asgdropshipping.com/what-is-dropshipping-tariffs/",
    "paypal": "https://asgdropshipping.com/what-is-dropshipping-paypal/",
    "sales tax": "https://asgdropshipping.com/what-is-dropshipping-business-for-sales-tax/",

    # 品牌原产地
    "shein clothing": "https://asgdropshipping.com/where-where-shein-clothing-is-made/",
    "coach bags": "https://asgdropshipping.com/where-are-coach-bags-made/",
    "lululemon made": "https://asgdropshipping.com/what-is-where-is-lululemon-made/",

    # 尺码
    "asian size": "https://asgdropshipping.com/how-to-comprehensive-guide-to-asian-size-conversions-to-us/",
    "size conversion": "https://asgdropshipping.com/how-to-comprehensive-guide-to-asian-size-conversions-to-us/",
}


class InternalLinkManager:
    """内部链接管理器"""

    def __init__(self):
        """初始化内部链接管理器"""
        self.sitemap_urls = SITEMAP_URLS
        self.keyword_mapping = KEYWORD_URL_MAPPING
        self.session = None
        self.http_client = None

    async def _init_http_client(self):
        """初始化 HTTP 客户端（用于链接检测）"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                follow_redirects=True,
            )

    def get_relevant_internal_links(
        self,
        keyword: str,
        article_title: str,
        article_content: str,
        count: int = 3,
        exclude_urls: list[str] = None,
    ) -> list[dict]:
        """
        获取相关的内部链接

        Args:
            keyword: 主关键词
            article_title: 文章标题
            article_content: 文章内容
            count: 需要的链接数量（默认3个）
            exclude_urls: 要排除的URL列表

        Returns:
            内部链接列表 [{"keyword": "xxx", "url": "xxx", "anchor_text": "xxx"}, ...]
        """
        exclude_urls = exclude_urls or []
        relevant_links = []

        # 将内容和标题合并进行分析
        full_text = f"{article_title} {article_content}".lower()

        # 遍历关键词映射，找到相关链接
        for kw, url in self.keyword_mapping.items():
            if url in exclude_urls:
                continue

            # 检查关键词是否与文章主题相关
            kw_lower = kw.lower()
            keyword_lower = keyword.lower()

            # 相关性判断：
            # 1. 关键词包含主关键词的某个词
            # 2. 或者文章内容中提到了这个词
            is_related = (
                kw_lower in keyword_lower or
                keyword_lower in kw_lower or
                kw_lower in full_text or
                any(word in full_text for word in kw_lower.split() if len(word) > 3)
            )

            if is_related and url not in [l["url"] for l in relevant_links]:
                # 生成锚文本
                anchor_text = self._generate_anchor_text(kw, article_content)

                relevant_links.append({
                    "keyword": kw,
                    "url": url,
                    "anchor_text": anchor_text,
                })

                if len(relevant_links) >= count:
                    break

        # 如果相关链接不够，从热门文章中补充
        if len(relevant_links) < count:
            for url in self.sitemap_urls:
                if url in exclude_urls:
                    continue
                if url in [l["url"] for l in relevant_links]:
                    continue

                # 从URL生成关键词
                kw = self._extract_keyword_from_url(url)
                anchor_text = self._generate_anchor_text(kw, article_content)

                relevant_links.append({
                    "keyword": kw,
                    "url": url,
                    "anchor_text": anchor_text,
                })

                if len(relevant_links) >= count:
                    break

        logger.info(f"Found {len(relevant_links)} relevant internal links for keyword: {keyword}")
        return relevant_links[:count]

    def _generate_anchor_text(self, keyword: str, article_content: str) -> str:
        """生成自然的锚文本"""
        # 清理关键词
        kw = keyword.strip()

        # 如果关键词太短或太泛，添加上下文
        if len(kw.split()) == 1:
            anchor_options = [
                f"{kw}",
                f"{kw} guide",
                f"best {kw}",
                f"{kw} tips",
                f"learn about {kw}",
            ]
            return anchor_options[0]

        return kw

    def _extract_keyword_from_url(self, url: str) -> str:
        """从URL提取关键词"""
        path = urlparse(url).path.strip("/")
        # 移除常见前缀
        path = re.sub(r'^(how-to-|what-is-|where-|does-|why-)', '', path)
        # 替换连字符为空格
        kw = path.replace("-", " ").strip()
        return kw

    def format_internal_link(
        self,
        text: str,
        url: str,
        style: str = "html",
    ) -> str:
        """
        格式化内部链接

        Args:
            text: 锚文本
            url: 链接URL
            style: 格式风格 (html/markdown)

        Returns:
            格式化的链接
        """
        if style == "html":
            # 内部链接：橘色加粗
            return f'<a href="{url}" style="color: #FF8C00; font-weight: bold; text-decoration: underline;">{text}</a>'
        else:
            # Markdown 格式（存储用）
            return f'**{text}** ([internal]({url}))'

    def format_external_link(
        self,
        text: str,
        url: str,
        style: str = "html",
    ) -> str:
        """
        格式化外部链接

        Args:
            text: 锚文本
            url: 链接URL
            style: 格式风格 (html/markdown)

        Returns:
            格式化的链接
        """
        if style == "html":
            # 外部链接：蓝色加粗，新窗口打开
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="color: #0066CC; font-weight: bold; text-decoration: underline;">{text}</a>'
        else:
            # Markdown 格式
            return f'**{text}** ([external]({url}))'

    def format_keyword_highlight(self, text: str, style: str = "html") -> str:
        """
        格式化关键词高亮

        Args:
            text: 关键词文本
            style: 格式风格 (html/markdown)

        Returns:
            格式化的关键词
        """
        if style == "html":
            # 关键词：蓝色加粗
            return f'<span style="color: #0066CC; font-weight: bold;">{text}</span>'
        else:
            return f'**{text}**'

    async def validate_links_with_check(self, links: list) -> dict:
        """
        验证所有链接的可访问性（新增：在生成链接后检测）

        Args:
            links: 链接列表 [{"keyword": "xxx", "url": "xxx", ...}]

        Returns:
            {
                "total": int,
                "accessible": int,
                "inaccessible": int,
                "results": list of validation results,
                "errors": list of error messages
            }
        """
        results = []
        accessible_count = 0
        inaccessible_count = 0
        errors = []

        logger.info(f"Starting link validation with accessibility check: {len(links)} links")

        # 检测所有链接
        for i, link in enumerate(links, 1):
            url = link.get("url", "")
            result = await self._check_url_accessible(url)

            if result["accessible"]:
                accessible_count += 1
                logger.info(f"  [{i}/{len(links)}] OK: {url} ({result['status']}) - Content length: {result['content_length']}")
            else:
                inaccessible_count += 1
                error_msg = result["error"]
                if result["content_length"] == 0:
                    error_msg += " - Empty page"
                errors.append(error_msg)
                logger.warning(f"  [{i}/{len(links)}] FAIL: {url} - {error_msg}")

        # 如果所有链接都检查完，关闭 HTTP 客户端
        await self._close_http_client()

        summary = {
            "total": len(links),
            "accessible": accessible_count,
            "inaccessible": inaccessible_count,
            "results": results,
            "errors": errors,
        }

        logger.info(f"Link validation complete: {accessible_count}/{len(links)} accessible")
        return summary

    async def _close_http_client(self):
        """关闭 HTTP 客户端"""
        if self.http_client:
            await self.http_client.aclose()


# 全局单例
_internal_link_manager: Optional[InternalLinkManager] = None


def get_internal_link_manager() -> InternalLinkManager:
    """获取全局内部链接管理器单例"""
    global _internal_link_manager
    if _internal_link_manager is None:
        _internal_link_manager = InternalLinkManager()
    return _internal_link_manager
