# -*- coding: utf-8 -*-
"""
Platform Content Generator Module

生成不同平台的社交媒体内容
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import re
from urllib.parse import urlparse
from loguru import logger
from seo_gen.modules.llm import LLMClient


class PlatformContentGenerator:
    """平台内容生成器 - 支持多平台内容生成"""

    # 平台列表
    PLATFORMS = {
        "article": "文章",
        "tiktok": "TikTok",
        "youtube": "YouTube",
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
        "x": "X/Twitter",
        "reddit": "Reddit",
        "instagram": "Instagram",
        "pinterest": "Pinterest"
    }

    # 平台标准手册文件映射
    PLATFORM_GUIDES = {
        "tiktok": "platform_tiktok_guide.md",
        "youtube": "platform_youtube_guide.md",
        "facebook": "platform_facebook_guide.md",
        "linkedin": "platform_linkedin_guide.md",
        "x": "platform_x_guide.md",
        "reddit": "platform_reddit_guide.md",
        "instagram": "platform_instagram_guide.md",
        "pinterest": "platform_pinterest_guide.md",
    }

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize platform content generator

        Args:
            llm_client: LLM client
        """
        self.llm_client = llm_client
        self._guides_cache = {}  # 缓存已加载的指南

    async def fetch_url_content(self, url: str) -> str:
        """
        从网址抓取内容（用于二创）

        Args:
            url: 目标网址

        Returns:
            抓取的内容文本
        """
        try:
            # 验证URL格式
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                # 尝试添加 https://
                url = "https://" + url
                parsed = urlparse(url)

            if not parsed.scheme or not parsed.netloc:
                return "错误：无效的网址格式"

            # 尝试使用 Playwright 模拟浏览器（优先）
            try:
                result = await self._fetch_with_playwright(url)
                if result and not result.startswith("错误"):
                    return result
            except Exception as e:
                logger.warning(f"playwright failed: {e}")

            # 如果 Playwright 不可用，尝试使用 web-reader MCP 工具
            try:
                result = await self._fetch_with_web_reader(url)
                if result and not result.startswith("错误"):
                    return result
            except Exception as e:
                logger.warning(f"web-reader failed: {e}")

            # 最后使用 requests + BeautifulSoup 作为后备
            try:
                result = await self._fetch_with_requests(url)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"requests method failed: {e}")

            return "错误：无法抓取网址内容，请直接粘贴文案内容"

        except Exception as e:
            logger.error(f"Failed to fetch URL content: {e}")
            return f"错误：{str(e)}"

    async def _fetch_with_web_reader(self, url: str) -> str:
        """使用 web-reader MCP 工具抓取内容"""
        # 这里可以集成 MCP web-reader 工具
        # 由于 MCP 调用需要特定上下文，暂时使用 requests 作为后备
        raise NotImplementedError("MCP web-reader integration pending")

    async def _fetch_with_playwright(self, url: str) -> str:
        """
        使用 Playwright 模拟真实浏览器抓取内容
        支持 JavaScript 渲染和动态内容
        """
        try:
            from playwright.async_api import async_playwright, Error as PlaywrightError
        except ImportError:
            return "错误：Playwright 未安装，请运行: pip install playwright"

        USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"

        try:
            async with async_playwright() as p:
                # 启动浏览器（使用 chromium）
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox'
                    ]
                )

                # 创建新页面
                context = await browser.new_context(
                    user_agent=USER_AGENT,
                    viewport={'width': 1920, 'height': 1080},
                    locale='zh-CN'
                )

                page = await context.new_page()

                # 设置超时和等待策略
                page.set_default_timeout(30000)  # 30秒

                # 导航到目标网址
                await page.goto(url, wait_until='networkidle', timeout=30000)

                # 等待页面加载完成
                await page.wait_for_timeout(2000)  # 额外等待2秒确保动态内容加载

                # 提取页面内容
                # 尝试多种方法获取正文内容

                # 方法1：查找主要内容区域
                content_selectors = [
                    'article',
                    '[role="main"]',
                    'main',
                    '.post-content',
                    '.entry-content',
                    '.content',
                    '#content',
                    '.article-body',
                    '.post-body',
                    'article p',
                    '.markdown-body',
                    '.prose'
                ]

                content_text = None
                for selector in content_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            texts = []
                            for element in elements:
                                text = await element.inner_text()
                                if text and len(text.strip()) > 50:  # 至少50个字符
                                    texts.append(text.strip())
                            if texts:
                                content_text = "\n\n".join(texts)
                                break
                    except Exception:
                        continue

                    if content_text:
                        break

                # 方法2：如果没有找到特定区域，获取所有段落
                if not content_text:
                    paragraphs = await page.query_selector_all('p')
                    if paragraphs:
                        texts = []
                        for p in paragraphs:
                            text = await p.inner_text()
                            if text and len(text.strip()) > 20:
                                texts.append(text.strip())
                        content_text = "\n\n".join(texts)

                # 方法3：获取整个 body
                if not content_text:
                    content_text = await page.inner_text('body')

                # 清理内容
                if content_text:
                    # 移除多余空白
                    import re
                    content_text = re.sub(r'\n{3,}', '\n\n', content_text)
                    content_text = re.sub(r'\s{3,}', ' ', content_text)
                    content_text = content_text.strip()

                    # 提取标题
                    try:
                        title = await page.inner_text('title')
                        if title and title.strip():
                            content_text = f"{title.strip()}\n\n{content_text}"
                    except Exception:
                        pass

                    # 限制长度
                    content_text = content_text[:15000]

                await browser.close()
                return content_text or "错误：无法提取页面内容"

        except PlaywrightError as e:
            logger.warning(f"Playwright error: {e}")
            return f"错误：Playwright 执行失败 - {str(e)}"
        except Exception as e:
            logger.error(f"Playwright unexpected error: {e}")
            return f"错误：抓取过程异常 - {str(e)}"

    async def _fetch_with_requests(self, url: str) -> str:
        """使用 requests + BeautifulSoup 抓取内容"""
        import requests
        from bs4 import BeautifulSoup

        # 使用指定的 User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')

        # 移除脚本和样式
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # 尝试找到主要内容区域
        content_selectors = [
            'article',
            '[role="main"]',
            'main',
            '.post-content',
            '.entry-content',
            '.content',
            '#content',
            '.article-body',
            '.post-body'
        ]

        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            # 如果没找到主要内容区域，使用 body
            main_content = soup.find('body')

        if not main_content:
            # 提取标题和段落
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            paragraphs = soup.find_all('p')
            content = f"{title_text}\n\n" + "\n\n".join(p.get_text() for p in paragraphs)
        else:
            # 清理内容
            content = main_content.get_text(separator='\n', strip=True)

        # 清理多余空白
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = content.strip()

        return content[:10000]  # 限制长度

    def _load_platform_guide(self, platform: str) -> str:
        """
        加载平台标准手册

        Args:
            platform: 平台代码

        Returns:
            手册内容
        """
        if platform in self._guides_cache:
            return self._guides_cache[platform]

        guide_file = self.PLATFORM_GUIDES.get(platform)
        if not guide_file:
            return ""

        try:
            guide_path = Path("config/knowledge") / guide_file
            if guide_path.exists():
                content = guide_path.read_text(encoding="utf-8")
                self._guides_cache[platform] = content
                return content
        except Exception as e:
            logger.warning(f"Failed to load platform guide for {platform}: {e}")

        return ""

    async def generate_platform_content(
        self,
        platform: str,
        keyword: str,
        serp_data: Dict[str, Any],
        user_answers: Dict[str, str],
        mode: str = "original",  # original 或 rewrite
        reference_content: Optional[str] = None,  # 二创时的参考内容
        reference_url: Optional[str] = None,  # 二创时的参考网址
    ) -> Dict[str, Any]:
        """
        生成平台内容

        Args:
            platform: 平台代码
            keyword: 关键词
            serp_data: SERP 分析数据
            user_answers: 用户回答的策略问题
            mode: 创作模式 (original/rewrite)
            reference_content: 二创参考内容
            reference_url: 二创参考网址

        Returns:
            {
                "platform": str,
                "content": str,  # 生成的文案
                "hashtags": List[str],  # hashtag 列表
                "metadata": Dict,  # 额外元数据
                "copy_text": str  # 可复制的完整文本
            }
        """
        if platform not in self.PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}")

        # 文章使用原有流程
        if platform == "article":
            return await self._generate_article_content(
                keyword, serp_data, user_answers, mode, reference_content, reference_url
            )

        # 加载平台标准手册
        platform_guide = self._load_platform_guide(platform)

        # 生成平台内容
        result = await self._generate_social_content(
            platform,
            keyword,
            serp_data,
            user_answers,
            platform_guide,
            mode,
            reference_content,
            reference_url
        )

        return result

    async def _generate_article_content(
        self,
        keyword: str,
        serp_data: Dict[str, Any],
        user_answers: Dict[str, str],
        mode: str,
        reference_content: Optional[str],
        reference_url: Optional[str]
    ) -> Dict[str, Any]:
        """生成文章内容（原有流程）"""
        # 这里调用原有的文章生成流程
        # 暂时返回占位符，实际会集成到 workflow 中
        return {
            "platform": "article",
            "content": "[文章内容将通过原有流程生成]",
            "hashtags": [],
            "metadata": {},
            "copy_text": ""
        }

    async def _generate_social_content(
        self,
        platform: str,
        keyword: str,
        serp_data: Dict[str, Any],
        user_answers: Dict[str, str],
        platform_guide: str,
        mode: str,
        reference_content: Optional[str],
        reference_url: Optional[str]
    ) -> Dict[str, Any]:
        """生成社交媒体内容"""

        # 构建提示词
        if mode == "rewrite" and (reference_content or reference_url):
            prompt = self._build_rewrite_prompt(
                platform, keyword, serp_data, user_answers,
                platform_guide, reference_content, reference_url
            )
        else:
            prompt = self._build_original_prompt(
                platform, keyword, serp_data, user_answers, platform_guide
            )

        # 调用 LLM 生成
        messages = [
            {
                "role": "system",
                "content": f"""你是{self.PLATFORMS[platform]}内容创作专家。

{platform_guide}

请严格按照平台标准生成内容，确保符合平台调性和用户习惯。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = await self.llm_client.chat(messages, temperature=0.7)

        # 解析响应
        return self._parse_platform_response(platform, response)

    def _build_original_prompt(
        self,
        platform: str,
        keyword: str,
        serp_data: Dict[str, Any],
        user_answers: Dict[str, str],
        platform_guide: str
    ) -> str:
        """构建原创内容提示词"""
        prompt = f"""请为关键词 "{keyword}" 创建 {self.PLATFORMS[platform]} 内容。

## SERP 分析
{self._format_serp_data(serp_data)}

## 用户策略
{self._format_user_answers(user_answers)}

## 要求
1. 内容必须符合 {self.PLATFORMS[platform]} 平台特性
2. 参考 SERP 分析中的热门内容趋势
3. 融入用户选择的策略方向
4. 输出格式：包含以下部分
   - content: 主要文案内容
   - hashtags: 相关的 hashtag 列表（用逗号分隔）
   - hook: 开头钩子（如果适用）

请直接输出 JSON 格式：
{{
  "content": "文案内容",
  "hashtags": ["tag1", "tag2", "tag3"],
  "hook": "开头钩子（如适用）",
  "cta": "行动号召（如适用）"
}}"""
        return prompt

    def _build_rewrite_prompt(
        self,
        platform: str,
        keyword: str,
        serp_data: Dict[str, Any],
        user_answers: Dict[str, str],
        platform_guide: str,
        reference_content: Optional[str],
        reference_url: Optional[str]
    ) -> str:
        """构建二创内容提示词"""
        reference_section = ""
        if reference_url:
            reference_section = f"\n参考网址：{reference_url}\n（已自动抓取并分析该网址内容）"
        elif reference_content:
            reference_section = f"\n参考内容：\n{reference_content}\n"

        prompt = f"""请基于参考内容，为关键词 "{keyword}" 创作 {self.PLATFORMS[platform]} 二创内容。

## SERP 分析
{self._format_serp_data(serp_data)}

## 用户策略
{self._format_user_answers(user_answers)}

## 参考内容
{reference_section}

## 二创要求
1. 分析参考内容的结构、风格和核心观点
2. 结合 SERP 分析的热点趋势
3. 融入用户选择的策略方向
4. 创作出原创但更有价值的内容
5. 避免直接抄袭，要加入新的角度和见解
6. 保持 {self.PLATFORMS[platform]} 平台特性

请直接输出 JSON 格式：
{{
  "content": "二创文案内容",
  "hashtags": ["tag1", "tag2", "tag3"],
  "hook": "开头钩子（如适用）",
  "cta": "行动号召（如适用）",
  "inspiration": "说明从参考内容中获得了什么灵感"
}}"""
        return prompt

    def _format_serp_data(self, serp_data: Dict[str, Any]) -> str:
        """格式化 SERP 数据"""
        if not serp_data:
            return "暂无 SERP 数据"

        parts = []

        # 搜索意图
        if serp_data.get("searchIntent"):
            parts.append(f"搜索意图：{serp_data['searchIntent']}")

        # 相关搜索
        if serp_data.get("relatedSearches"):
            parts.append("相关搜索：")
            for search in serp_data["relatedSearches"][:5]:
                parts.append(f"  - {search}")

        # 热门结果标题
        if serp_data.get("results"):
            parts.append("热门标题：")
            for result in serp_data["results"][:5]:
                title = result.get("title", "")[:60]
                parts.append(f"  - {title}")

        return "\n".join(parts)

    def _format_user_answers(self, user_answers: Dict[str, str]) -> str:
        """格式化用户回答"""
        if not user_answers:
            return "暂无策略设置"

        parts = []
        for q_id, answer in user_answers.items():
            parts.append(f"Q{q_id} 答案：{answer}")

        return "\n".join(parts)

    def _parse_platform_response(self, platform: str, response: str) -> Dict[str, Any]:
        """解析平台响应"""
        import json
        import re

        # 尝试提取 JSON
        json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                content = data.get("content", response)
                hashtags = data.get("hashtags", [])
                hook = data.get("hook", "")
                cta = data.get("cta", "")

                # 构建可复制的完整文本
                copy_text = self._build_copy_text(platform, content, hashtags, hook, cta)

                return {
                    "platform": platform,
                    "content": content,
                    "hashtags": hashtags,
                    "hook": hook,
                    "cta": cta,
                    "metadata": {
                        "raw_response": response,
                        "inspiration": data.get("inspiration", "")
                    },
                    "copy_text": copy_text
                }
            except json.JSONDecodeError:
                pass

        # 如果无法解析 JSON，使用原始响应
        copy_text = self._build_copy_text(platform, response, [], "", "")
        return {
            "platform": platform,
            "content": response,
            "hashtags": [],
            "hook": "",
            "cta": "",
            "metadata": {"raw_response": response},
            "copy_text": copy_text
        }

    def _build_copy_text(
        self,
        platform: str,
        content: str,
        hashtags: List[str],
        hook: str,
        cta: str
    ) -> str:
        """构建可复制的完整文本"""
        parts = []

        if hook:
            parts.append(hook)

        parts.append(content)

        if cta:
            parts.append(f"\n\n{cta}")

        if hashtags:
            tag_str = " ".join(f"#{tag}" for tag in hashtags)
            parts.append(f"\n\n{tag_str}")

        return "\n".join(parts).strip()


# Global singleton
_platform_content_generator: Optional[PlatformContentGenerator] = None


def get_platform_content_generator() -> PlatformContentGenerator:
    """获取全局平台内容生成器单例"""
    global _platform_content_generator
    if _platform_content_generator is None:
        from seo_gen.modules.llm import get_llm_client
        _platform_content_generator = PlatformContentGenerator(get_llm_client())
    return _platform_content_generator
