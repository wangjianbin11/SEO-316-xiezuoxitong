"""
竞品全文爬取分析器

职责:爬取 SERP 前5名文章全文,提取结构化竞品数据
这是 Content Gap 分析的真实数据来源
"""

import re
import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class CompetitorContent:
    """竞品内容数据"""
    url: str
    domain: str
    title: str
    h1: str
    h2_list: list[str]  # 所有H2标题(按顺序)
    h3_list: list[str]  # 所有H3标题
    word_count: int  # 正文字数(不含导航/页脚)
    full_text: str  # 清洁后的完整正文
    has_faq_section: bool  # 是否有FAQ章节
    has_comparison_table: bool  # 是否有对比表格
    has_numbered_list: bool  # 是否有编号列表(How-to格式)
    has_stats_data: bool  # 是否包含具体统计数字(%、数字)
    has_author_bio: bool  # 是否有作者介绍(E-E-A-T信号)
    has_schema_markup: bool  # 是否有Schema标记
    publish_date: Optional[str]  # 发布日期
    estimated_reading_time: int  # 预估阅读时间(分钟)
    internal_link_count: int  # 内链数量
    external_link_count: int  # 外链数量
    image_count: int  # 图片数量
    scrape_success: bool  # 爬取是否成功
    scrape_error: Optional[str]  # 失败原因


@dataclass
class CompetitorAnalysis:
    """竞品分析结果"""
    keyword: str
    total_scraped: int
    avg_word_count: int
    target_word_count: int  # 建议目标字数 = avg_top3 × 1.15 取整到最近500
    dominant_format: str  # listicle/how-to/guide/comparison
    dominant_content_type: str  # blog_post/landing_page/tool
    all_h2_topics: list[str]  # 竞品覆盖的所有H2话题(去重合并)
    uncovered_topics: list[str]  # 无竞品覆盖的话题(来自PAA)
    weakness_summary: str  # LLM生成的竞品弱点总结
    competitors: list[CompetitorContent]


class CompetitorScraper:
    """竞品爬取器"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]

    SKIP_DOMAINS = [
        "youtube.com", "amazon.com", "reddit.com", "quora.com",
        "wikipedia.org", "linkedin.com", "facebook.com", "twitter.com",
        "instagram.com", "pinterest.com", "tiktok.com"
    ]

    def __init__(self, timeout: float = 12.0, delay_min: float = 1.5, delay_max: float = 3.0):
        """
        初始化爬取器

        Args:
            timeout: 请求超时时间(秒)
            delay_min: 最小延迟(秒)
            delay_max: 最大延迟(秒)
        """
        self.timeout = timeout
        self.delay_min = delay_min
        self.delay_max = delay_max

    async def scrape_top_results(
        self,
        urls: list[str],
        max_count: int = 5
    ) -> list[CompetitorContent]:
        """
        爬取竞品全文

        规则:
        - 跳过 SKIP_DOMAINS 中的域名
        - 请求间隔随机 1.5-3.0 秒(防反爬)
        - 超时 12 秒
        - 失败时跳过,不中断整体流程
        - User-Agent 轮换
        - 单篇文章 < 300 字视为失败

        Args:
            urls: URL列表
            max_count: 最多爬取数量

        Returns:
            竞品内容列表
        """
        results = []
        scraped_count = 0

        for url in urls:
            if scraped_count >= max_count:
                break

            # 检查是否在跳过列表中
            domain = urlparse(url).netloc
            if any(skip_domain in domain for skip_domain in self.SKIP_DOMAINS):
                logger.debug(f"Skipping domain: {domain}")
                continue

            # 随机延迟
            if scraped_count > 0:
                delay = random.uniform(self.delay_min, self.delay_max)
                logger.debug(f"Waiting {delay:.1f}s before next request...")
                await asyncio.sleep(delay)

            # 爬取
            try:
                content = await self._scrape_single(url)
                if content and content.scrape_success:
                    results.append(content)
                    scraped_count += 1
                    logger.info(f"✓ Scraped ({scraped_count}/{max_count}): {domain} - {content.word_count} words")
                else:
                    logger.warning(f"✗ Failed to scrape: {url}")
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue

        logger.info(f"Scraping complete: {len(results)}/{max_count} successful")
        return results

    async def _scrape_single(self, url: str) -> Optional[CompetitorContent]:
        """爬取单个URL"""
        try:
            # 随机选择 User-Agent
            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                html = response.text
                return self.extract_content(html, url)

        except httpx.TimeoutException:
            logger.warning(f"Timeout scraping {url}")
            return self._create_failed_content(url, "Timeout")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            return self._create_failed_content(url, f"HTTP {e.response.status_code}")
        except Exception as e:
            logger.warning(f"Error scraping {url}: {e}")
            return self._create_failed_content(url, str(e))

    def extract_content(self, html: str, url: str) -> CompetitorContent:
        """
        从 HTML 提取结构化内容

        正文提取优先级:
        1. <article> 标签
        2. <main> 标签
        3. class/id 包含 "content", "post", "entry", "article" 的 <div>
        4. 字符数最多的顶级 <div>

        必须移除:<nav>, <header>, <footer>, <aside>, <script>, <style>,
                  <form>, [class*="sidebar"], [class*="comment"], [class*="ad"]

        检测 FAQ:寻找 H2/H3 包含 "faq", "frequently", "questions" 或
                  包含多个 <details> 标签

        检测统计数据:正则匹配 \\d+%|\\d+,\\d+|\\$\\d+|€\\d+

        检测作者介绍:寻找 [class*="author"], [itemprop="author"],
                     rel="author" 元素
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            domain = urlparse(url).netloc

            # 移除不需要的元素
            for tag in soup.select('nav, header, footer, aside, script, style, form, [class*="sidebar"], [class*="comment"], [class*="ad"], [class*="menu"], [class*="navigation"]'):
                tag.decompose()

            # 提取标题
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()

            # 提取 H1
            h1 = ""
            h1_tag = soup.find('h1')
            if h1_tag:
                h1 = h1_tag.get_text().strip()

            # 查找主内容区域
            main_content = None
            for selector in ['article', 'main', '[class*="content"]', '[class*="post"]', '[class*="entry"]', '[class*="article"]']:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # 如果没找到,使用最大的 div
            if not main_content:
                divs = soup.find_all('div')
                if divs:
                    main_content = max(divs, key=lambda d: len(d.get_text()))

            if not main_content:
                return self._create_failed_content(url, "No main content found")

            # 提取 H2 和 H3
            h2_list = [h2.get_text().strip() for h2 in main_content.find_all('h2')]
            h3_list = [h3.get_text().strip() for h3 in main_content.find_all('h3')]

            # 提取正文
            full_text = main_content.get_text(separator=' ', strip=True)
            word_count = len(full_text.split())

            # 检查是否太短
            if word_count < 300:
                return self._create_failed_content(url, f"Content too short: {word_count} words")

            # 检测 FAQ
            has_faq = self._detect_faq(main_content, h2_list, h3_list)

            # 检测对比表格
            has_comparison_table = len(main_content.find_all('table')) > 0

            # 检测编号列表
            has_numbered_list = len(main_content.find_all('ol')) > 0

            # 检测统计数据
            has_stats_data = bool(re.search(r'\d+[.,]?\d*\s*(%|percent|\$|€|USD|orders|days|hours)', full_text))

            # 检测作者介绍
            has_author_bio = bool(
                soup.select('[class*="author"], [itemprop="author"], [rel="author"]')
            )

            # 检测 Schema 标记
            has_schema_markup = bool(soup.find('script', type='application/ld+json'))

            # 提取发布日期
            publish_date = self._extract_publish_date(soup)

            # 预估阅读时间(250词/分钟)
            estimated_reading_time = max(1, word_count // 250)

            # 统计链接
            all_links = main_content.find_all('a', href=True)
            internal_links = [a for a in all_links if domain in a['href'] or a['href'].startswith('/')]
            external_links = [a for a in all_links if a not in internal_links and not a['href'].startswith('#')]

            # 统计图片
            image_count = len(main_content.find_all('img'))

            return CompetitorContent(
                url=url,
                domain=domain,
                title=title,
                h1=h1,
                h2_list=h2_list,
                h3_list=h3_list,
                word_count=word_count,
                full_text=full_text[:5000],  # 只保留前5000字符
                has_faq_section=has_faq,
                has_comparison_table=has_comparison_table,
                has_numbered_list=has_numbered_list,
                has_stats_data=has_stats_data,
                has_author_bio=has_author_bio,
                has_schema_markup=has_schema_markup,
                publish_date=publish_date,
                estimated_reading_time=estimated_reading_time,
                internal_link_count=len(internal_links),
                external_link_count=len(external_links),
                image_count=image_count,
                scrape_success=True,
                scrape_error=None
            )

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return self._create_failed_content(url, str(e))

    def _detect_faq(self, content, h2_list: list[str], h3_list: list[str]) -> bool:
        """检测是否有FAQ章节"""
        # 检查标题
        faq_keywords = ['faq', 'frequently', 'questions', 'q&a', 'q & a']
        all_headings = h2_list + h3_list
        for heading in all_headings:
            if any(kw in heading.lower() for kw in faq_keywords):
                return True

        # 检查 details 标签(常用于FAQ)
        if len(content.find_all('details')) >= 3:
            return True

        return False

    def _extract_publish_date(self, soup) -> Optional[str]:
        """提取发布日期"""
        # 尝试多种方式提取日期
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'meta[name="date"]',
            'time[datetime]',
            '[class*="publish"], [class*="date"]'
        ]

        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date_str = elem.get('content') or elem.get('datetime') or elem.get_text()
                if date_str:
                    return date_str.strip()[:10]  # 只保留日期部分

        return None

    def _create_failed_content(self, url: str, error: str) -> CompetitorContent:
        """创建失败的内容对象"""
        domain = urlparse(url).netloc
        return CompetitorContent(
            url=url,
            domain=domain,
            title="",
            h1="",
            h2_list=[],
            h3_list=[],
            word_count=0,
            full_text="",
            has_faq_section=False,
            has_comparison_table=False,
            has_numbered_list=False,
            has_stats_data=False,
            has_author_bio=False,
            has_schema_markup=False,
            publish_date=None,
            estimated_reading_time=0,
            internal_link_count=0,
            external_link_count=0,
            image_count=0,
            scrape_success=False,
            scrape_error=error
        )

    async def analyze_competitors(
        self,
        keyword: str,
        urls: list[str],
        paa_questions: list[str],
        llm_client: Any = None
    ) -> CompetitorAnalysis:
        """
        完整竞品分析流程:
        1. 爬取所有URL
        2. 计算聚合统计数据
        3. 合并所有H2话题并去重
        4. 对比PAA问题找出未覆盖话题
        5. 调用LLM生成弱点总结(输入:所有竞品的H2列表+字数+有无FAQ)

        Args:
            keyword: 关键词
            urls: 竞品URL列表
            paa_questions: PAA问题列表
            llm_client: LLM客户端(可选)

        Returns:
            竞品分析结果
        """
        # 1. 爬取竞品
        logger.info(f"Starting competitor analysis for: {keyword}")
        competitors = await self.scrape_top_results(urls, max_count=5)

        if not competitors:
            logger.warning("No competitors scraped successfully")
            return self._create_empty_analysis(keyword)

        # 2. 计算统计数据
        successful_competitors = [c for c in competitors if c.scrape_success]
        total_scraped = len(successful_competitors)

        if total_scraped == 0:
            return self._create_empty_analysis(keyword)

        word_counts = [c.word_count for c in successful_competitors]
        avg_word_count = sum(word_counts) // len(word_counts)

        # 计算目标字数:前3名平均 × 1.15,取整到最近500
        top3_avg = sum(sorted(word_counts, reverse=True)[:3]) // min(3, len(word_counts))
        target_word_count = round((top3_avg * 1.15) / 500) * 500

        # 3. 合并所有H2话题
        all_h2_topics = []
        for comp in successful_competitors:
            all_h2_topics.extend(comp.h2_list)

        # 去重(保持顺序)
        seen = set()
        unique_h2_topics = []
        for topic in all_h2_topics:
            topic_lower = topic.lower().strip()
            if topic_lower and topic_lower not in seen:
                seen.add(topic_lower)
                unique_h2_topics.append(topic)

        # 4. 找出未覆盖的PAA话题
        uncovered_topics = []
        for paa in paa_questions:
            paa_lower = paa.lower()
            # 检查是否有H2覆盖了这个问题
            covered = any(
                self._topics_similar(paa_lower, h2.lower())
                for h2 in unique_h2_topics
            )
            if not covered:
                uncovered_topics.append(paa)

        # 5. 判断主导格式
        dominant_format = self._determine_dominant_format(successful_competitors)
        dominant_content_type = "blog_post"  # 简化处理

        # 6. 生成弱点总结(如果有LLM)
        weakness_summary = ""
        if llm_client:
            weakness_summary = await self._generate_weakness_summary(
                successful_competitors,
                unique_h2_topics,
                llm_client
            )

        return CompetitorAnalysis(
            keyword=keyword,
            total_scraped=total_scraped,
            avg_word_count=avg_word_count,
            target_word_count=target_word_count,
            dominant_format=dominant_format,
            dominant_content_type=dominant_content_type,
            all_h2_topics=unique_h2_topics,
            uncovered_topics=uncovered_topics,
            weakness_summary=weakness_summary,
            competitors=competitors
        )

    def _topics_similar(self, topic1: str, topic2: str) -> bool:
        """判断两个话题是否相似"""
        # 简单的相似度判断:提取关键词
        words1 = set(re.findall(r'\w+', topic1.lower()))
        words2 = set(re.findall(r'\w+', topic2.lower()))

        # 移除停用词
        stop_words = {'the', 'a', 'an', 'is', 'are', 'what', 'how', 'why', 'when', 'where', 'who', 'to', 'for', 'of', 'in', 'on', 'at'}
        words1 -= stop_words
        words2 -= stop_words

        if not words1 or not words2:
            return False

        # 计算交集比例
        intersection = words1 & words2
        union = words1 | words2
        similarity = len(intersection) / len(union) if union else 0

        return similarity > 0.4

    def _determine_dominant_format(self, competitors: list[CompetitorContent]) -> str:
        """判断主导格式"""
        format_scores = {
            'listicle': 0,
            'how-to': 0,
            'guide': 0,
            'comparison': 0
        }

        for comp in competitors:
            # 检查标题和H1
            title_lower = (comp.title + " " + comp.h1).lower()

            if any(word in title_lower for word in ['best', 'top', 'list']):
                format_scores['listicle'] += 1

            if any(word in title_lower for word in ['how to', 'guide', 'tutorial', 'step']):
                format_scores['how-to'] += 1

            if any(word in title_lower for word in ['complete', 'ultimate', 'comprehensive']):
                format_scores['guide'] += 1

            if any(word in title_lower for word in ['vs', 'versus', 'comparison', 'compare']):
                format_scores['comparison'] += 1

            # 检查内容特征
            if comp.has_numbered_list:
                format_scores['how-to'] += 0.5

            if comp.has_comparison_table:
                format_scores['comparison'] += 0.5

        # 返回得分最高的格式
        dominant = max(format_scores.items(), key=lambda x: x[1])
        return dominant[0] if dominant[1] > 0 else 'guide'

    async def _generate_weakness_summary(
        self,
        competitors: list[CompetitorContent],
        h2_topics: list[str],
        llm_client: Any
    ) -> str:
        """使用LLM生成竞品弱点总结"""
        try:
            # 构建提示
            comp_summary = "\n".join([
                f"- {c.domain}: {c.word_count} words, FAQ: {c.has_faq_section}, Stats: {c.has_stats_data}"
                for c in competitors[:5]
            ])

            h2_summary = "\n".join([f"- {h2}" for h2 in h2_topics[:15]])

            prompt = f"""Analyze these competitor articles and identify their weaknesses:

Competitors:
{comp_summary}

Common H2 Topics:
{h2_summary}

Provide a brief summary (2-3 sentences) of:
1. What content gaps exist
2. What could be improved (depth, data, structure)
3. What unique angle we can take

Keep it concise and actionable."""

            messages = [
                {"role": "system", "content": "You are an SEO content strategist analyzing competitor weaknesses."},
                {"role": "user", "content": prompt}
            ]

            response = await llm_client.chat(messages, temperature=0.7)
            return response.strip()

        except Exception as e:
            logger.warning(f"Failed to generate weakness summary: {e}")
            return "Unable to generate weakness summary."

    def _create_empty_analysis(self, keyword: str) -> CompetitorAnalysis:
        """创建空的分析结果"""
        return CompetitorAnalysis(
            keyword=keyword,
            total_scraped=0,
            avg_word_count=2000,  # 默认值
            target_word_count=2500,
            dominant_format="guide",
            dominant_content_type="blog_post",
            all_h2_topics=[],
            uncovered_topics=[],
            weakness_summary="No competitor data available.",
            competitors=[]
        )
