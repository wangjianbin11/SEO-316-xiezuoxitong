# SEO Content Generator — 系统全面升级规格说明书 v3.0
# AI Coding Instruction Document — 直接交给 Claude Code / Cursor / Windsurf 执行

**文档版本**: v3.0  
**适用系统**: seo-content-generator (Python, 现有架构基础上升级)  
**升级目标**: 生成文章达到 Google 100分 + AI引用最大化 (GEO/AEO满分)  
**执行方式**: 将本文档完整粘贴给 AI 编程工具，逐模块执行  

---

## 一、总体升级目标与评分标准

本次升级的核心目标是让每篇生成的文章同时满足三个维度的最高标准：

**维度1 — Google 传统 SEO (目标分: 95+/100)**
- On-Page 技术满分：Title、Meta、URL、Schema、Core Web Vitals
- 内容质量满分：字数、关键词密度、可读性、E-E-A-T信号
- 结构满分：H1/H2/H3层次、内链、外链、图片ALT

**维度2 — GEO 生成式引擎优化 (目标分: 满分)**
- 被 Google AI Overview 摘录：直接答案块 + FAQ Schema
- 被 Perplexity 引用：数据密度 + 来源可信度
- 被 ChatGPT Browse 引用：权威性信号 + 结构清晰度
- 被 Claude、Gemini 引用：内容准确性 + E-E-A-T强度

**维度3 — 内容真实性与原创性 (目标分: 100/100)**
- AI检测概率 < 15%（Originality.ai标准）
- 包含真实业务数据（ASG运营数据）
- 包含真实经验陈述（Janson 8年经验）
- 无模板化表达，无AI常见套话

---

## 二、现有系统问题清单（必须全部修复）

### 🔴 P0 致命缺陷（不修复=系统无效）

**P0-1: 选词无真实数据**
- 当前状态：keyword_analyzer.py 用 LLM 猜 KD 和搜索量
- 风险：可能在 KD=80 的词上浪费全部资源
- 必须修复：接入 DataForSEO API 获取真实 KD、月搜索量、CPC

**P0-2: 竞品分析是假的**
- 当前状态：serp.py 只分析 Google API 返回的摘要片段
- 风险：content gap 分析无意义，生成内容无法超越竞品
- 必须修复：爬取竞品全文，提取 H2/H3 结构、字数、FAQ存在性

**P0-3: LLM JSON 解析无容错**
- 当前状态：直接 json.loads() LLM 输出
- 风险：LLM 偶尔加 Markdown 围栏导致整个流程崩溃
- 必须修复：robust JSON 提取 + 自动修复重试

### 🟠 P1 严重缺陷（影响文章质量上限）

**P1-1: 完全没有 Schema 标记生成**
- 缺少：FAQPage、Article、BreadcrumbList JSON-LD
- 影响：Google AI Overview 抓取概率降低 60%+

**P1-2: 没有直接答案块(Direct Answer Block)机制**
- 缺少：每个 H2 开头的独立可引用段落
- 影响：Perplexity、ChatGPT Browse 无法准确引用

**P1-3: 工作流无检查点**
- 当前状态：任何步骤失败 = 从零重跑
- 影响：API费用浪费 + 批量运行脆弱

**P1-4: 知识库是字符串匹配**
- 当前状态：if keyword_lower in content.lower()
- 影响：跨语言、同义词无法命中，知识库利用率低

**P1-5: 图片SEO完全缺失**
- 缺少：SEO文件名、ALT Text写入WP媒体库、尺寸规范

**P1-6: 内部链接是静态字典**
- 当前状态：KEYWORD_URL_MAPPING 手写字典
- 影响：超过50篇后维护成本爆炸

### 🟡 P2 重要优化（影响规模化能力）

**P2-1: 质量检测依赖LLM自评**（循环自评，不客观）
**P2-2: 批量逻辑在GUI层**（无法headless运行/接入n8n）
**P2-3: 没有发布追踪数据库**（重复生成同一关键词）
**P2-4: API无速率控制**（批量时触发429限速）
**P2-5: 没有Open Graph标签**（社交分享无预览图）

---

## 三、新增核心模块规格说明

### 模块A: keyword_data.py — 真实关键词数据客户端

```python
# 文件路径: src/seo_gen/modules/keyword_data.py

"""
职责：调用 DataForSEO API 获取真实关键词数据
替代：keyword_analyzer.py 中的 LLM 猜测逻辑
"""

from dataclasses import dataclass
from typing import Optional
import httpx
import base64

@dataclass
class KeywordMetrics:
    keyword: str
    monthly_volume: int           # 月均搜索量
    kd_score: float               # 关键词难度 0-100
    cpc: float                    # 每次点击成本（美元）
    competition_level: str        # low/medium/high
    serp_features: list[str]      # 存在的SERP特征
    data_source: str              # "dataforseo" 或 "llm_estimate"
    confidence: float             # 数据可信度 0-1

class KeywordDataClient:
    """DataForSEO API 客户端"""
    
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self, username: str, password: str):
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
    
    async def get_keyword_metrics(
        self, 
        keywords: list[str], 
        location_code: int = 2840,  # 2840=US, 2826=UK, 2156=CN
        language_code: str = "en"
    ) -> list[KeywordMetrics]:
        """
        批量获取关键词数据
        DataForSEO 端点：POST /keywords_data/google_ads/search_volume/live
        单次最多1000个关键词
        """
        # 实现批量查询，自动分批（每批≤1000）
        # 返回 KeywordMetrics 列表
        # 网络失败时 gracefully 返回 llm_estimate 填充的结果
        pass
    
    async def get_serp_features(self, keyword: str, location_code: int = 2840) -> dict:
        """
        获取关键词的 SERP 特征
        端点：POST /serp/google/organic/live/advanced
        返回：featured_snippet(bool), paa_box(bool), video_carousel(bool), 
               local_pack(bool), image_pack(bool), shopping(bool)
        """
        pass
    
    def _estimate_from_llm(self, keyword: str) -> KeywordMetrics:
        """DataForSEO 不可用时的 LLM 回退估算"""
        # 返回 data_source="llm_estimate", confidence=0.3
        pass

# config.py 需新增：
# DATAFORSEO_USERNAME = ""
# DATAFORSEO_PASSWORD = ""
# DATAFORSEO_LOCATION_CODE = 2840  # 默认US
```

**集成点**：在 `keyword_analyzer.py` 的 `classify()` 方法执行完 LLM 分类后，调用 `KeywordDataClient.get_keyword_metrics()`，结果合并到 `KeywordAnalysisResult`。KD > 45 且站点DA < 30 时，自动推荐低难度变体词。

---

### 模块B: competitor_scraper.py — 竞品全文爬取分析器

```python
# 文件路径: src/seo_gen/modules/competitor_scraper.py

"""
职责：爬取 SERP 前5名文章全文，提取结构化竞品数据
这是 Content Gap 分析的真实数据来源
"""

from dataclasses import dataclass, field
from typing import Optional
import httpx
import asyncio
import random
from bs4 import BeautifulSoup

@dataclass
class CompetitorContent:
    url: str
    domain: str
    title: str
    h1: str
    h2_list: list[str]           # 所有H2标题（按顺序）
    h3_list: list[str]           # 所有H3标题
    word_count: int              # 正文字数（不含导航/页脚）
    full_text: str               # 清洁后的完整正文
    has_faq_section: bool        # 是否有FAQ章节
    has_comparison_table: bool   # 是否有对比表格
    has_numbered_list: bool      # 是否有编号列表（How-to格式）
    has_stats_data: bool         # 是否包含具体统计数字（%、数字）
    has_author_bio: bool         # 是否有作者介绍（E-E-A-T信号）
    has_schema_markup: bool      # 是否有Schema标记
    publish_date: Optional[str]  # 发布日期
    estimated_reading_time: int  # 预估阅读时间（分钟）
    internal_link_count: int     # 内链数量
    external_link_count: int     # 外链数量
    image_count: int             # 图片数量
    scrape_success: bool         # 爬取是否成功
    scrape_error: Optional[str]  # 失败原因

@dataclass
class CompetitorAnalysis:
    keyword: str
    total_scraped: int
    avg_word_count: int
    target_word_count: int       # 建议目标字数 = avg_top3 × 1.15 取整到最近500
    dominant_format: str         # listicle/how-to/guide/comparison
    dominant_content_type: str   # blog_post/landing_page/tool
    all_h2_topics: list[str]     # 竞品覆盖的所有H2话题（去重合并）
    uncovered_topics: list[str]  # 无竞品覆盖的话题（来自PAA）
    weakness_summary: str        # LLM生成的竞品弱点总结
    competitors: list[CompetitorContent]

class CompetitorScraper:
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    
    SKIP_DOMAINS = [
        "youtube.com", "amazon.com", "reddit.com", "quora.com",
        "wikipedia.org", "linkedin.com", "facebook.com", "twitter.com"
    ]
    
    async def scrape_top_results(
        self, 
        urls: list[str], 
        max_count: int = 5
    ) -> list[CompetitorContent]:
        """
        爬取竞品全文
        规则：
        - 跳过 SKIP_DOMAINS 中的域名
        - 请求间隔随机 1.5-3.0 秒（防反爬）
        - 超时 12 秒
        - 失败时跳过，不中断整体流程
        - User-Agent 轮换
        - 单篇文章 < 300 字视为失败
        """
        pass
    
    def extract_content(self, html: str, url: str) -> CompetitorContent:
        """
        从 HTML 提取结构化内容
        
        正文提取优先级：
        1. <article> 标签
        2. <main> 标签
        3. class/id 包含 "content", "post", "entry", "article" 的 <div>
        4. 字符数最多的顶级 <div>
        
        必须移除：<nav>, <header>, <footer>, <aside>, <script>, <style>,
                  <form>, [class*="sidebar"], [class*="comment"], [class*="ad"]
        
        检测 FAQ：寻找 H2/H3 包含 "faq", "frequently", "questions" 或
                  包含多个 <details> 标签
        
        检测统计数据：正则匹配 \d+%|\d+,\d+|\$\d+|€\d+
        
        检测作者介绍：寻找 [class*="author"], [itemprop="author"],
                     rel="author" 元素
        """
        pass
    
    async def analyze_competitors(
        self, 
        keyword: str,
        urls: list[str],
        paa_questions: list[str],
        llm_client  # LLM客户端引用，用于生成弱点总结
    ) -> CompetitorAnalysis:
        """
        完整竞品分析流程：
        1. 爬取所有URL
        2. 计算聚合统计数据
        3. 合并所有H2话题并去重
        4. 对比PAA问题找出未覆盖话题
        5. 调用LLM生成弱点总结（输入：所有竞品的H2列表+字数+有无FAQ）
        """
        pass
```

**集成点**：在 `serp.py` 的 `analyze_serp()` 完成后，自动调用 `CompetitorScraper.analyze_competitors()`，结果存入 `SerpAnalysis.competitor_analysis` 字段。在 `content.py` Prompt 构建时注入竞品H2话题列表和弱点总结。

---

### 模块C: geo_optimizer.py — GEO/AEO 内容优化引擎

**这是本次升级最核心的新模块。** 专门负责将生成的内容转化为 AI 引擎可引用的格式。

```python
# 文件路径: src/seo_gen/modules/geo_optimizer.py

"""
职责：将 content.py 生成的文章进行 GEO/AEO 二次优化
目标：最大化被 Google AI Overview、Perplexity、ChatGPT、Claude 等引用的概率

GEO 优化的科学原理：
- AI引擎优先引用包含"直接答案"结构的段落（query → direct answer → context）
- AI引擎优先引用包含具体数字和统计数据的内容
- AI引擎优先引用有明确来源归属的内容
- AI引擎优先引用结构化（FAQ、列表、定义框）内容
- AI引擎通过 Schema 标记理解内容语义类型
"""

from dataclasses import dataclass
from typing import Optional
import re
import json

@dataclass
class DirectAnswerBlock:
    """直接答案块 — GEO核心单元"""
    trigger_heading: str          # 触发该答案的H2/H3标题
    direct_answer: str            # 50-80字的直接答案（必须自成一体，不依赖上下文）
    supporting_context: str       # 100-200字的支撑解释
    data_point: Optional[str]     # 具体数据点（如有）
    citation_ready: bool          # 是否满足AI引用格式要求

@dataclass
class GEOScore:
    """GEO优化评分"""
    total_score: float            # 0-100总分
    answer_density_score: float   # 答案密度 (25分)
    data_richness_score: float    # 数据丰富度 (20分)
    structure_clarity_score: float # 结构清晰度 (20分)
    eeat_signal_score: float      # E-E-A-T信号 (20分)
    schema_coverage_score: float  # Schema覆盖度 (15分)
    recommendations: list[str]    # 具体改进建议

class GEOOptimizer:
    
    # AI引擎无法引用的表达模式（必须重写）
    UNCITABLE_PATTERNS = [
        r"in today's .{0,20} world",
        r"it's worth noting that",
        r"as we can see",
        r"there are many (factors|reasons|ways)",
        r"in conclusion",
        r"furthermore|moreover|additionally",
        r"needless to say",
        r"it goes without saying",
    ]
    
    # AI引擎偏好引用的结构模式（必须保留和增强）
    CITABLE_PATTERNS = {
        "definition": r"^(a|an|the) .{10,50} is (a|an|the)",  # "A dropshipping agent is..."
        "direct_answer": r"^(yes|no|the answer is|in short)",  # 直接回答问题
        "data_point": r"\d+[\.,]\d*\s*(%|percent|orders|days|USD|\$)",  # 具体数字
        "experience_claim": r"(based on|from our|in our|we've processed|our data shows)",  # 经验陈述
    }
    
    def analyze_geo_score(self, article: dict) -> GEOScore:
        """
        对文章进行GEO评分
        
        答案密度评分(25分)：
        - 检查每个H2章节开头是否有50-80字的独立直接答案块
        - 每有1个合格答案块 +5分，最多5个(25分)
        
        数据丰富度评分(20分)：
        - 统计全文具体数字出现次数（%、具体数量、日期）
        - 0个=0分，1-3个=5分，4-7个=12分，8+=20分
        - 包含ASG专有数据（"Based on X orders"）额外+3分
        
        结构清晰度评分(20分)：
        - H1/H2/H3层次完整 +5分
        - FAQ章节存在且≥5个Q&A +5分
        - 无孤立段落（每H2有≥2个子段落）+5分
        - 无超过400字的连续正文（有视觉分隔）+5分
        
        E-E-A-T信号评分(20分)：
        - 包含作者bio（含职位、经验年数）+5分
        - 包含"Based on our [N] orders/clients/experience" +5分
        - 包含公司具体数据（ASG统计数字）+5分
        - 包含具体地理/操作细节（东莞仓库、具体工厂类型）+5分
        
        Schema覆盖度评分(15分)：
        - Article Schema存在 +5分
        - FAQPage Schema存在且与正文FAQ匹配 +5分
        - BreadcrumbList Schema存在 +3分
        - Author/Person Schema存在 +2分
        """
        pass
    
    def inject_direct_answer_blocks(self, article: dict, llm_client) -> dict:
        """
        为每个H2章节生成并注入直接答案块
        
        每个直接答案块规格：
        - 第一句：直接回答H2标题隐含的问题（句式：[主语] [谓语] [关键信息]）
        - 第二句：量化或具体化（包含数字、条件、时间）
        - 第三句（可选）：关键区别或注意事项
        - 总长度：50-80词（英文）
        - 必须自成一体：删除前后所有文字后，该块仍然有意义
        - 禁止使用：代词（it/they/this/that）无清晰指代
        - 禁止使用：UNCITABLE_PATTERNS 中的任何表达
        
        HTML格式：
        <div class="geo-answer-block" itemscope itemtype="https://schema.org/Answer">
          <p itemprop="text">[直接答案文字]</p>
        </div>
        
        注入位置：每个<h2>标签后的第一个<p>标签之前
        """
        pass
    
    def rewrite_uncitable_sentences(self, text: str, llm_client) -> str:
        """
        检测并重写AI无法引用的表达
        
        检测：正则匹配 UNCITABLE_PATTERNS
        重写规则（调用LLM）：
        - "In today's competitive dropshipping landscape..." 
          → "Dropshipping agents handle sourcing, QC, and shipping for X orders daily."
        - "There are many factors to consider..."
          → "Three factors determine agent quality: [A], [B], and [C]."
        - "It's worth noting that..."  
          → 直接陈述事实，删除引导语
        """
        pass
    
    def enhance_data_density(self, article: dict) -> dict:
        """
        增强文章的数据密度
        
        扫描以下模式并标记为可强化位置：
        - "many sellers" → 建议替换为具体百分比
        - "often" / "usually" → 建议替换为频率数据
        - "takes time" → 建议替换为具体天数/小时数
        - "cost more" → 建议替换为具体金额范围
        
        ASG专有数据注入（优先使用，不需要引用来源）：
        - 日处理订单量：10,000-20,000
        - 服务国家：200+
        - 仓库数量：4个（深圳/东莞）
        - 工厂合作数：2,300+
        - SKU库：1.4M+
        - 成立时间：2019年
        - 团队规模：200+人
        - 创始人经验：8年
        
        数据注入句式模板（自然植入，不强硬）：
        - "Based on processing over [N] orders for Shopify sellers..."
        - "Across our [N] factory partners, we've found that..."
        - "In our Dongguan warehouse operations..."
        """
        pass
    
    def optimize_faq_for_ai(self, faq_list: list[dict]) -> list[dict]:
        """
        优化FAQ使其符合AI引用标准
        
        每个FAQ答案必须满足：
        1. 第一句直接回答问题（Yes/No/The answer is/[直接事实]）
        2. 答案60-100词（英文），不超过120词
        3. 必须自成一体（删除问题后仍有意义）
        4. 不引用"上文"/"下文"/"如前所述"
        5. 包含至少1个具体数字或时间
        6. 结尾可选：1句关于ASG的软性CTA（不强制）
        
        FAQ问题来源优先级：
        1. Google PAA（People Also Ask）— 最高优先
        2. Perplexity 对该关键词的相关问题
        3. Reddit/Quora 高赞问题
        4. 竞品FAQ章节中的问题
        
        每篇文章FAQ数量：6-8个（不少于6，不多于8）
        """
        pass
```

---

### 模块D: schema_generator.py — 结构化数据生成器

```python
# 文件路径: src/seo_gen/modules/schema_generator.py

"""
职责：生成所有 JSON-LD Schema 标记，注入 WordPress 文章
这是 GEO 优化最重要的技术层实现
"""

import json
from datetime import datetime

class SchemaGenerator:
    
    SITE_INFO = {
        "name": "ASG Dropshipping",
        "url": "https://asgdropshipping.com",
        "logo_url": "https://asgdropshipping.com/wp-content/uploads/asg-logo.png",
        "author_name": "Janson",
        "author_title": "CEO & Founder",
        "author_bio_url": "https://asgdropshipping.com/about/",
        "author_same_as": [
            "https://www.linkedin.com/in/janson-asg/",  # 如有请填写真实URL
        ]
    }
    
    def generate_article_schema(
        self,
        title: str,
        description: str,
        article_url: str,
        image_url: str,
        publish_date: str,  # ISO 8601: "2025-03-14T10:00:00+08:00"
        keywords: list[str],
        word_count: int,
        article_type: str   # "pillar" | "response" | "share"
    ) -> dict:
        """
        生成 Article / BlogPosting Schema
        
        article_type 映射：
        - pillar → @type: "Article"（权威性最高）
        - response → @type: "Article" with about.@type: "Question"
        - share → @type: "BlogPosting"
        
        必须包含字段：
        headline, description, author (Person), publisher (Organization + Logo),
        datePublished, dateModified, mainEntityOfPage (WebPage),
        image (ImageObject: url + width + height), keywords, wordCount,
        inLanguage, potentialAction (ReadAction)
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Article" if article_type in ["pillar", "response"] else "BlogPosting",
            "headline": title[:110],  # Google截断上限
            "description": description[:160],
            "url": article_url,
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": article_url
            },
            "image": {
                "@type": "ImageObject",
                "url": image_url,
                "width": 1200,
                "height": 630
            },
            "author": {
                "@type": "Person",
                "name": self.SITE_INFO["author_name"],
                "jobTitle": self.SITE_INFO["author_title"],
                "url": self.SITE_INFO["author_bio_url"],
                "sameAs": self.SITE_INFO["author_same_as"],
                "worksFor": {
                    "@type": "Organization",
                    "name": self.SITE_INFO["name"],
                    "url": self.SITE_INFO["url"]
                }
            },
            "publisher": {
                "@type": "Organization",
                "name": self.SITE_INFO["name"],
                "url": self.SITE_INFO["url"],
                "logo": {
                    "@type": "ImageObject",
                    "url": self.SITE_INFO["logo_url"],
                    "width": 600,
                    "height": 60
                }
            },
            "datePublished": publish_date,
            "dateModified": publish_date,
            "keywords": ", ".join(keywords[:10]),
            "wordCount": word_count,
            "inLanguage": "en-US",
            "potentialAction": {
                "@type": "ReadAction",
                "target": [article_url]
            }
        }
        return schema
    
    def generate_faq_schema(self, faq_list: list[dict]) -> dict:
        """
        生成 FAQPage Schema
        
        faq_list 格式：[{"question": str, "answer": str}]
        
        答案字段规则：
        - 纯文本，不含任何HTML标签
        - 最大500字符（Google截断）
        - 必须以完整句子结尾（不能半途截断）
        
        验证：
        - 问题数量 6-8个
        - 每个答案 60-120词
        - 答案不含HTML实体
        """
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": self._strip_html(item["answer"])[:500]
                    }
                }
                for item in faq_list
            ]
        }
    
    def generate_breadcrumb_schema(
        self, 
        article_title: str,
        article_url: str,
        category_name: str,
        category_url: str
    ) -> dict:
        """生成 BreadcrumbList Schema（3级：Home → Category → Article）"""
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": self.SITE_INFO["url"]
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": category_name,
                    "item": category_url
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": article_title,
                    "item": article_url
                }
            ]
        }
    
    def generate_how_to_schema(self, steps: list[dict], title: str, total_time: str) -> dict:
        """
        为 How-To 类型文章生成 HowTo Schema（触发 SERP 步骤卡片）
        仅在文章类型为 "response" 且H2包含步骤编号时生成
        
        steps 格式：[{"name": str, "text": str, "url": str}]
        total_time 格式：ISO 8601 Duration，如 "PT30M"（30分钟）
        """
        pass
    
    def generate_all_schemas(
        self, 
        article: dict,
        article_url: str,
        faq_list: list[dict],
        category_name: str = "Blog",
        publish_date: str = None
    ) -> str:
        """
        生成完整的 Schema 标记字符串，注入 <head>
        
        返回格式：
        <script type="application/ld+json">
        [
          {Article Schema},
          {FAQPage Schema},
          {BreadcrumbList Schema}
        ]
        </script>
        
        每个 Schema 生成后用 json.loads(json.dumps(schema)) 验证
        验证失败时 log warning，不抛出异常，跳过该Schema
        """
        schemas = []
        
        # 始终生成这三个
        article_schema = self.generate_article_schema(...)
        faq_schema = self.generate_faq_schema(faq_list)
        breadcrumb_schema = self.generate_breadcrumb_schema(...)
        
        schemas = [article_schema, faq_schema, breadcrumb_schema]
        
        # 条件生成HowTo Schema（仅How-to类文章）
        if self._is_howto_article(article):
            schemas.append(self.generate_how_to_schema(...))
        
        return f'<script type="application/ld+json">\n{json.dumps(schemas, ensure_ascii=False, indent=2)}\n</script>'
    
    def _strip_html(self, text: str) -> str:
        """移除HTML标签，保留纯文本"""
        return re.sub(r'<[^>]+>', '', text).strip()
    
    def _is_howto_article(self, article: dict) -> bool:
        """判断是否为How-To格式：标题包含Step/How to，或H2包含编号"""
        pass
```

---

### 模块E: quality_checker.py — 客观质量评分系统

```python
# 文件路径: src/seo_gen/modules/quality_checker.py

"""
职责：对生成文章进行100%客观量化评分
原则：不依赖LLM自评，全部基于规则计算
目标：给每篇文章一个0-100的综合分，低于阈值拒绝发布
"""

import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class QualityReport:
    # 总分
    total_score: float              # 0-100
    publish_ready: bool             # total_score >= 75 才发布
    
    # 技术SEO评分（满分30）
    title_score: float              # H1包含关键词且≤65字符 (5分)
    meta_score: float               # Meta description 140-160字符 (5分)
    url_score: float                # URL含关键词，≤5词，无停用词 (5分)
    heading_structure_score: float  # H1/H2/H3正确层次结构 (5分)
    schema_score: float             # 3种Schema均存在 (5分)
    internal_link_score: float      # 内链3-8个 (5分)
    
    # 内容质量评分（满分40）
    word_count_score: float         # 达到目标字数90%-120% (10分)
    keyword_density_score: float    # 主词密度0.8%-1.5% (10分)
    readability_score: float        # Flesch-Kincaid评分60-70 (10分)
    data_density_score: float       # 每500词至少1个具体数字 (10分)
    
    # GEO优化评分（满分30）
    direct_answer_score: float      # 每H2开头有答案块 (10分)
    faq_quality_score: float        # FAQ 6-8个，每答案60-100词 (10分)
    eeat_score: float               # 作者bio+公司数据+经验陈述 (10分)
    
    # 详细问题列表
    critical_issues: list[str]      # 必须修复（触发重新生成）
    warnings: list[str]             # 建议修复
    passed_checks: list[str]        # 通过的检查项

class QualityChecker:
    
    # 阈值配置
    MIN_PUBLISH_SCORE = 75          # 低于此分数拒绝发布，触发重新生成
    REGENERATE_THRESHOLD = 60       # 低于此分数触发完全重新生成（不仅仅是优化）
    MAX_KEYWORD_DENSITY = 0.015     # 1.5%（防堆砌）
    MIN_KEYWORD_DENSITY = 0.008     # 0.8%
    TARGET_READABILITY_MIN = 55     # Flesch-Kincaid最低（太难）
    TARGET_READABILITY_MAX = 75     # Flesch-Kincaid最高（太简单）
    
    def check(self, article: dict, target_word_count: int, primary_keyword: str) -> QualityReport:
        """
        执行完整质量检查
        
        调用顺序：
        1. check_technical_seo()
        2. check_content_quality()
        3. check_geo_optimization()
        4. 汇总评分，生成报告
        5. 如果 total_score < MIN_PUBLISH_SCORE，在 critical_issues 中列明原因
        """
        pass
    
    def check_technical_seo(self, article: dict, primary_keyword: str) -> dict:
        """
        技术SEO检查（满分30）
        
        Title检查：
        - 主词出现在前60字符 → +3分
        - 总长度50-65字符 → +2分
        
        Meta Description检查：
        - 包含主词 → +3分
        - 长度140-160字符 → +2分
        
        URL检查：
        - 包含主词 → +2分
        - 长度≤5词 → +2分
        - 全小写，用连字符 → +1分
        
        Heading结构检查：
        - 只有1个H1 → +2分
        - H2数量4-10个 → +2分
        - 没有H3直接在H1下（需要先有H2）→ +1分
        
        Schema检查（调用schema_generator验证）：
        - Article Schema存在且有效 → +2分
        - FAQPage Schema存在且有效 → +2分
        - BreadcrumbList Schema存在 → +1分
        
        内链检查：
        - 内链3-8个 → +5分
        - 内链2个或9个 → +3分
        - 内链<2或>9 → +0分
        """
        pass
    
    def check_content_quality(
        self, 
        article: dict, 
        target_word_count: int,
        primary_keyword: str
    ) -> dict:
        """
        内容质量检查（满分40）
        
        字数检查：
        - 实际字数 / 目标字数
        - 90%-110% → +10分
        - 80%-120% → +6分
        - 70%-130% → +3分
        - 其他 → +0分
        
        关键词密度：
        - 密度 = 主词出现次数 / 总词数
        - 0.8%-1.5% → +10分
        - 0.5%-2.0% → +6分
        - 0.3%-2.5% → +3分
        - <0.3%或>2.5% → 0分（严重问题）
        
        可读性评分（Flesch-Kincaid Reading Ease）：
        公式：206.835 - 1.015×(总词数/总句数) - 84.6×(总音节数/总词数)
        英文音节数估算：用正则统计元音组合
        - 60-70分 → +10分（理想范围）
        - 50-80分 → +6分
        - 40-90分 → +3分
        
        数据密度：
        - 计算每500词中包含具体数字的句子数
        - ≥2个/500词 → +10分
        - 1个/500词 → +6分
        - <1个/500词 → +3分
        """
        pass
    
    def check_geo_optimization(self, article: dict) -> dict:
        """
        GEO优化检查（满分30）
        
        直接答案块检查：
        - 统计含 class="geo-answer-block" 的div数量
        - 数量 = H2数量 → +10分
        - 数量 ≥ H2数量×0.7 → +7分
        - 数量 ≥ H2数量×0.5 → +4分
        - 数量 < H2数量×0.5 → +0分
        
        FAQ质量检查：
        - FAQ问题数6-8个 → +4分
        - 每个FAQ答案60-120词 → +3分/个，最多+4分
        - FAQ Schema与正文FAQ条目匹配 → +2分
        
        E-E-A-T检查：
        - 包含作者bio（词数>50词）→ +3分
        - 正文包含"Based on our"/"In our warehouse"等经验陈述 → +3分（每种+1，最多+3）
        - 正文包含ASG具体数字（10000+/2300+/200+ etc）→ +2分
        - 正文包含具体地理信息（Dongguan/Shenzhen/Guangdong）→ +2分
        """
        pass
    
    def calculate_keyword_density(self, text: str, keyword: str) -> float:
        """计算关键词密度（考虑词组和变体）"""
        words = re.findall(r'\b\w+\b', text.lower())
        keyword_words = keyword.lower().split()
        # 词组匹配（连续词）
        text_lower = text.lower()
        count = len(re.findall(re.escape(keyword.lower()), text_lower))
        return count / max(len(words), 1)
    
    def calculate_flesch_kincaid(self, text: str) -> float:
        """计算 Flesch-Kincaid 可读性评分"""
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        sentences = re.split(r'[.!?]+', clean_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        words = re.findall(r'\b[a-zA-Z]+\b', clean_text)
        
        if not sentences or not words:
            return 50.0
        
        total_syllables = sum(self._count_syllables(word) for word in words)
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(100, score))
    
    def _count_syllables(self, word: str) -> int:
        """英文单词音节数估算"""
        word = word.lower()
        if len(word) <= 3:
            return 1
        vowels = re.findall(r'[aeiouy]+', word)
        count = len(vowels)
        if word.endswith('e') and count > 1:
            count -= 1
        return max(1, count)
```

---

### 模块F: checkpoint.py — 工作流检查点管理器

```python
# 文件路径: src/seo_gen/modules/checkpoint.py

"""
职责：为工作流提供检查点，允许从失败处恢复
防止API费用浪费，支持断点续跑
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

@dataclass
class CheckpointMeta:
    stage: int
    stage_name: str
    keyword: str
    timestamp: str
    duration_seconds: float
    success: bool
    error_message: Optional[str]

class CheckpointManager:
    
    STAGE_NAMES = {
        0: "keyword_classification",
        1: "knowledge_base_loading",
        2: "serp_analysis",
        3: "competitor_scraping",
        4: "keyword_data",
        5: "title_generation",
        6: "outline_generation",
        7: "content_generation",
        8: "geo_optimization",
        9: "quality_check",
        10: "image_generation",
        11: "schema_generation",
        12: "wordpress_publish"
    }
    
    def __init__(self, base_output_dir: str, keyword: str):
        self.keyword_slug = re.sub(r'[^\w-]', '-', keyword.lower()).strip('-')
        self.checkpoint_dir = Path(base_output_dir) / self.keyword_slug / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, stage: int, data: Any, duration_seconds: float = 0) -> None:
        """
        保存阶段结果
        文件名：stage_{n:02d}_{stage_name}.json
        同时写入元数据：timestamp, duration, success
        """
        stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")
        filepath = self.checkpoint_dir / f"stage_{stage:02d}_{stage_name}.json"
        
        checkpoint = {
            "meta": {
                "stage": stage,
                "stage_name": stage_name,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration_seconds, 2),
                "success": True
            },
            "data": data
        }
        
        filepath.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
    
    def load(self, stage: int) -> Optional[Any]:
        """读取阶段结果，不存在返回None"""
        stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")
        filepath = self.checkpoint_dir / f"stage_{stage:02d}_{stage_name}.json"
        
        if not filepath.exists():
            return None
        
        data = json.loads(filepath.read_text())
        return data.get("data")
    
    def get_resume_stage(self) -> int:
        """返回最后成功完成的阶段+1，0=从头开始"""
        for stage in range(max(self.STAGE_NAMES.keys()), -1, -1):
            if self.load(stage) is not None:
                return stage + 1
        return 0
    
    def clear(self) -> None:
        """清除所有检查点（强制重新运行）"""
        for f in self.checkpoint_dir.glob("*.json"):
            f.unlink()
    
    def is_complete(self) -> bool:
        """检查是否所有阶段都已完成"""
        return self.get_resume_stage() > max(self.STAGE_NAMES.keys())
    
    def get_summary(self) -> dict:
        """返回当前进度摘要"""
        completed = []
        for stage in self.STAGE_NAMES:
            if self.load(stage) is not None:
                completed.append(self.STAGE_NAMES[stage])
        return {
            "keyword": self.keyword_slug,
            "completed_stages": completed,
            "resume_from": self.get_resume_stage(),
            "is_complete": self.is_complete()
        }
```

---

### 模块G: article_tracker.py — 发布追踪数据库

```python
# 文件路径: src/seo_gen/modules/article_tracker.py

"""
职责：追踪已发布文章，防止重复生成，支持排名回填
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

class ArticleTracker:
    
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS published_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        keyword_slug TEXT NOT NULL UNIQUE,
        article_title TEXT,
        article_type TEXT,
        word_count INTEGER,
        wordpress_url TEXT,
        wp_post_id INTEGER,
        wp_post_status TEXT DEFAULT 'draft',
        published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_updated DATETIME,
        quality_score REAL,
        geo_score REAL,
        gsc_clicks INTEGER DEFAULT 0,
        gsc_impressions INTEGER DEFAULT 0,
        gsc_avg_position REAL DEFAULT 0,
        gsc_last_synced DATETIME,
        generation_cost_usd REAL,
        notes TEXT
    )
    """
    
    def __init__(self, db_path: str = "./seo_tracker.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.CREATE_TABLE_SQL)
            conn.commit()
    
    def is_published(self, keyword: str) -> bool:
        """检查是否已发布（使用slug防止大小写/空格差异）"""
        slug = self._to_slug(keyword)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM published_articles WHERE keyword_slug = ?", (slug,)
            ).fetchone()
        return row is not None
    
    def mark_published(
        self,
        keyword: str,
        article_title: str,
        article_type: str,
        word_count: int,
        wordpress_url: str,
        wp_post_id: int,
        quality_score: float = 0,
        geo_score: float = 0,
        generation_cost_usd: float = 0
    ) -> None:
        slug = self._to_slug(keyword)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO published_articles
                (keyword, keyword_slug, article_title, article_type, word_count,
                 wordpress_url, wp_post_id, quality_score, geo_score, 
                 generation_cost_usd, published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (keyword, slug, article_title, article_type, word_count,
                  wordpress_url, wp_post_id, quality_score, geo_score,
                  generation_cost_usd, datetime.now().isoformat()))
            conn.commit()
    
    def get_all(self) -> list[dict]:
        """获取所有已发布文章，按发布时间倒序"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM published_articles ORDER BY published_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]
    
    def _to_slug(self, keyword: str) -> str:
        import re
        return re.sub(r'[^\w-]', '-', keyword.lower().strip()).strip('-')
```

---

## 四、现有模块必须修改的部分

### 4.1 content.py — Prompt 引擎升级

在 `_build_prompt()` 方法中，必须加入以下新规则（在现有规则基础上补充）：

```python
GEO_WRITING_RULES = """
## 🎯 GEO写作规则（AI引用优化 — 最高优先级）

### 规则G1: 直接答案块（每个H2必须）
每个H2章节的第一段必须是"直接答案块"：
- 格式：<div class="geo-answer-block"><p>[答案]</p></div>
- 内容：用1-2句话直接回答该H2标题隐含的问题
- 字数：50-80词（英文）
- 要求：删掉文章其他所有内容后，该块仍然有意义
- 禁止：代词无清晰指代（it/they/this指代不明）
- 禁止：引导语（"It's important to note that..."）
- 示例正确：
  "A China-based dropshipping agent handles sourcing, QC, packaging, 
   and international shipping for your Shopify store on a per-order basis—
   with no minimum order requirements. Unlike trading companies, agents 
   assign a dedicated account manager accountable for your supply chain."
- 示例错误：
  "There are many things to consider when choosing a dropshipping agent.
   In today's competitive landscape, it's important to understand..."

### 规则G2: 数据优先原则
每500词中至少包含2个具体数字。优先使用ASG专有数据：
- "Based on processing 5M+ Shopify orders from our Dongguan warehouses..."
- "Across our 2,300+ factory partners in Guangdong..."
- "With 200+ staff and 4 warehouses in Shenzhen and Dongguan..."
- "Our average processing time is [X] days for standard orders..."
禁止使用模糊表达：many/often/usually/quickly/soon → 全部替换为具体数字

### 规则G3: 自成一体原则
每个H2章节必须可以独立阅读（被AI摘录后仍有意义）：
- 不引用"如上所述"/"正如前面提到"
- 不使用指代不明的"it"/"they"/"this approach"
- 每个章节开头重申关键上下文

### 规则G4: 句子多样性（防AI检测）
段落内句子长度必须多样化：
- 短句（5-10词）：用于强调关键点
- 中句（15-25词）：标准解释
- 长句（25-40词）：复杂论点或多层条件
禁止连续3句相同长度

### 规则G5: 禁用表达清单
以下表达一律禁止（AI内容典型特征）：
- "In today's [X] landscape/world/environment"
- "It's worth noting that"
- "Moreover/Furthermore/Additionally"（段落开头）
- "In conclusion/To summarize"
- "game-changer/revolutionary/cutting-edge/seamless"
- "As we can see/As mentioned above"
- "needless to say/it goes without saying"

### 规则G6: E-E-A-T植入公式
每800词植入至少2条经验陈述，使用以下公式之一：
公式A："Based on [具体数量] orders we've processed for [类型] sellers, [具体发现]."
公式B："In our [地点] warehouse operations, we've seen [具体情况] in [X]% of cases."
公式C："After [X] years working directly with [类型] factories in [地区], [具体洞察]."
公式D："Our [职位] team has [具体工作内容]—here's what that experience tells us about [话题]."
"""

FAQ_WRITING_RULES = """
## 📋 FAQ写作规则（AEO优化）

每个FAQ答案必须：
1. 第一句：直接回答（Yes/No/数字/核心事实）
2. 第二三句：必要背景和具体化
3. 第四句（可选）：实际操作建议
4. 字数：65-100词（英文）
5. 语气：专业直接，不用"Great question!"等
6. 结尾可选：1句软性CTA，不强制

FAQ问题来源（按优先级）：
1. Google PAA：{paa_questions}
2. 竞品FAQ问题：{competitor_faq_questions}

FAQ数量：必须6-8个，不少不多

示例正确FAQ答案（针对"How much does a dropshipping agent charge?"）：
"Most China-based dropshipping agents charge a handling fee of $0.50–$2.00 
per order, plus actual shipping costs. The fee covers sorting, quality inspection, 
custom packaging, and label printing. ASG charges a flat per-order handling fee 
with no subscription cost—full pricing is available on request for sellers 
processing 50+ daily orders."（88词，自成一体，含具体数字，含软CTA）

示例错误FAQ答案：
"Great question! It really depends on many factors. Generally speaking, agents 
can charge varying amounts depending on the services included..."（模糊无数据）
"""
```

### 4.2 serp.py — SERP分析扩展

在 `analyze_intent()` 方法返回后，新增：

```python
async def get_paa_questions(self, keyword: str) -> list[str]:
    """
    提取 People Also Ask 问题
    方法：从 Google Custom Search API 结果的 relatedQuestions 字段提取
    如果API不返回PAA，使用以下回退方案：
    - 调用 DataForSEO SERP API（/serp/google/organic/live/advanced）
    - 从result中提取 people_also_ask 字段
    返回：最多10个PAA问题字符串列表
    """
    pass

async def get_related_searches(self, keyword: str) -> list[str]:
    """
    提取相关搜索词（Related Searches）
    用于：扩展LSI关键词，强化文章的语义覆盖
    """
    pass
```

### 4.3 llm.py — JSON解析强化

在 LLM 响应处理处新增 `extract_json()` 函数：

```python
def extract_json(text: str) -> dict | list:
    """
    从LLM响应中提取JSON，处理所有常见格式问题
    
    策略（按顺序尝试）：
    1. 直接 json.loads(text)
    2. 去除 ```json ... ``` 围栏后解析
    3. 去除 ``` ... ``` 围栏后解析
    4. 正则提取第一个 { 到最后一个 }
    5. 正则提取第一个 [ 到最后一个 ]
    6. 所有策略失败：抛出 JSONExtractionError
    
    自动修复重试（JSONExtractionError时）：
    发送修复提示："Your previous response was not valid JSON. 
    Respond with ONLY the raw JSON object. No markdown, no explanation.
    Previous response: {failed_response[:500]}"
    最多重试2次
    
    失败日志：写入 outputs/errors/json_failures_{timestamp}.log
    """
    strategies = [
        lambda t: json.loads(t),
        lambda t: json.loads(re.sub(r'^```json\s*|\s*```$', '', t.strip())),
        lambda t: json.loads(re.sub(r'^```\s*|\s*```$', '', t.strip())),
        lambda t: json.loads(re.search(r'\{.*\}', t, re.DOTALL).group()),
        lambda t: json.loads(re.search(r'\[.*\]', t, re.DOTALL).group()),
    ]
    
    for strategy in strategies:
        try:
            return strategy(text)
        except (json.JSONDecodeError, AttributeError):
            continue
    
    raise JSONExtractionError(f"Cannot extract JSON from: {text[:200]}")

class JSONExtractionError(Exception):
    pass
```

### 4.4 wordpress.py — 发布增强

`publish_article()` 方法需要新增以下功能：

```python
def publish_article_enhanced(
    self, 
    article_html: str,
    schema_markup: str,          # 新增：Schema JSON-LD 字符串
    meta_title: str,
    meta_description: str,
    og_image_url: str,           # 新增：Open Graph 图片URL
    primary_keyword: str,
    article_data: dict,
    post_status: str = "draft"   # 始终先发草稿，人工确认后发布
) -> dict:
    """
    发布增强版
    
    新增注入内容（在 article_html 顶部）：
    1. Schema JSON-LD（在 <!-- SCHEMA_START --> 注释后）
    2. Open Graph 标签（通过 Yoast SEO / RankMath API 设置，如果安装了插件）
    
    WordPress REST API 额外字段：
    {
        "title": meta_title,
        "content": schema_markup + article_html,
        "status": post_status,
        "meta": {
            "_yoast_wpseo_title": meta_title,         # Yoast SEO
            "_yoast_wpseo_metadesc": meta_description,
            "_yoast_wpseo_focuskw": primary_keyword,
            "_rankmath_focus_keyword": primary_keyword, # RankMath
        },
        "slug": article_data.get("slug"),
    }
    
    发布成功后：
    - 记录到 ArticleTracker
    - 返回 {"post_id": X, "url": "https://...", "edit_url": "https://.../wp-admin/..."}
    """
    pass
```

### 4.5 workflow.py — 工作流重构

新增检查点集成和质量门控：

```python
async def run(
    self, 
    keyword: str,
    resume: bool = True,         # True=从断点恢复，False=全新开始
    force_publish: bool = False  # True=忽略质量分数强制发布
) -> WorkflowResult:
    """
    主工作流入口
    
    流程：
    0. 初始化 CheckpointManager
    1. 检查 ArticleTracker.is_published() → 已发布则跳过
    2. 如果 resume=True，从 checkpoint.get_resume_stage() 开始
    3. 逐阶段执行，每阶段：
       a. 检查检查点（跳过已完成阶段）
       b. 执行阶段逻辑
       c. 保存检查点
       d. 如果失败：记录错误，停止流程（不继续）
    4. 完成后执行 QualityChecker.check()
    5. 如果 quality_score < 75 且 force_publish=False：
       触发重新优化（最多1次）或拒绝发布
    6. 发布到 WordPress（草稿状态）
    7. 记录到 ArticleTracker
    8. 返回 WorkflowResult
    """
    
    # 检查是否重复
    tracker = ArticleTracker()
    if tracker.is_published(keyword):
        return WorkflowResult(
            status="skipped",
            reason="already_published",
            existing_url=tracker.get_url(keyword)
        )
    
    checkpoint = CheckpointManager(self.output_dir, keyword)
    if not resume:
        checkpoint.clear()
    
    resume_from = checkpoint.get_resume_stage() if resume else 0
    
    # 执行各阶段...
```

---

## 五、图片 SEO 升级规格

### image.py 修改要求

```python
# 图片文件名规则（替换现有UUID命名）
def _generate_seo_filename(self, keyword: str, index: int, image_type: str) -> str:
    """
    SEO友好文件名
    封面图：{keyword-slug}-featured-image.webp
    章节图：{keyword-slug}-{index}-{section-slug}.webp
    """
    slug = re.sub(r'[^\w]', '-', keyword.lower()).strip('-')
    slug = re.sub(r'-+', '-', slug)  # 合并多个连字符
    
    if image_type == "cover":
        return f"{slug}-featured-image.webp"
    else:
        return f"{slug}-section-{index}.webp"

# ALT Text 生成规则（不依赖LLM，用规则生成）
def _generate_alt_text(self, keyword: str, section_title: str = None, image_type: str = "cover") -> str:
    """
    ALT Text规则：
    - 封面图："{Primary Keyword} - Complete Guide | ASG Dropshipping"
    - 章节图："{Section Title} - {Primary Keyword}"
    - 最大100字符
    - 不以"image of"/"picture of"开头
    - 不纯堆砌关键词
    """
    if image_type == "cover":
        alt = f"{keyword.title()} - Complete Guide | ASG Dropshipping"
    else:
        alt = f"{section_title} - {keyword.title()}"
    return alt[:100]

# 图片尺寸规范（在DALL-E prompt中明确指定）
IMAGE_DIMENSIONS = {
    "cover": {"width": 1200, "height": 630, "aspect": "1.91:1"},  # Open Graph标准
    "section": {"width": 800, "height": 450, "aspect": "16:9"},   # 章节图
}

# WordPress媒体库元数据写入（现有代码缺失）
async def upload_with_metadata(
    self, 
    image_data: bytes,
    filename: str,
    alt_text: str,
    title: str,
    caption: str
) -> dict:
    """
    上传图片到WordPress并写入完整SEO元数据
    
    步骤1：POST /wp-json/wp/v2/media（multipart上传）
    步骤2：PATCH /wp-json/wp/v2/media/{id}（写入元数据）
    元数据字段：alt_text, title, caption, description
    """
    pass
```

---

## 六、新增 Prompt 模板 — 完整文章写作 System Prompt

以下是升级后 `content.py` 中 LLM 文章写作的完整 System Prompt 模板：

```python
ARTICLE_WRITING_SYSTEM_PROMPT = """
You are Janson, CEO and founder of ASG Dropshipping (东莞市安速供应链管理有限公司), 
writing expert-level content for the company blog at asgdropshipping.com.

## YOUR IDENTITY & AUTHORITY
- 8+ years operating in China's dropshipping agent ecosystem
- Founded ASG in 2019, now processing 10,000-20,000 Shopify orders daily
- 4 warehouses in Dongguan and Shenzhen, 200+ staff
- Direct relationships with 2,300+ factories across Guangdong province
- 1.4M+ SKU library, serving sellers in 200+ countries
- You write from firsthand operational experience, not theory

## TARGET READER
{customer_persona}

## ARTICLE SPECIFICATIONS
Type: {article_type} ({word_count_target} words, {section_count} sections)
Primary keyword: {primary_keyword}
Secondary keywords: {secondary_keywords}
Competitor average word count: {competitor_avg_words}
Mandatory H2 sections: {mandatory_sections}
Content gaps to fill: {gap_topics}

## COMPANY CONTEXT FOR NATURAL INTEGRATION
{company_intro}
Relevant case studies: {case_studies}
Relevant FAQs: {faq_snippets}

## ABSOLUTE WRITING RULES

### INTRO (150-200 words, STRICT FORMULA)
Paragraph 1 (HOOK): Open with the reader's exact problem—the specific frustration 
that made them search this keyword. DO NOT start with "In today's..."
Paragraph 2 (AGITATE): Quantify the cost of that problem with a specific number.
Paragraph 3 (PROMISE): State exactly what this article delivers after reading.
Paragraph 4 (CREDIBILITY): One sentence E-E-A-T signal with specific operational data.
Example: "We've processed over 500,000 orders for Shopify sellers in this exact 
situation—from our Dongguan warehouse. Here's what we've learned."

### EACH H2 SECTION (MANDATORY STRUCTURE)
Element 1: DIRECT ANSWER BLOCK (50-80 words)
  → Wrap in: <div class="geo-answer-block"><p>[answer]</p></div>
  → Must answer the H2 heading's implied question directly
  → Must be self-contained (readable without surrounding text)
  → Must contain at least 1 specific number or time reference
  
Element 2: SUPPORTING CONTENT (based on section requirements)
  → Minimum 2 paragraphs after the answer block
  → Max 80 words per paragraph
  → Varied sentence length (5-10 / 15-25 / 25-40 words, mixed)

### DATA INTEGRATION RULES
MANDATORY: ≥2 specific numbers per 500 words
PREFERRED sources (use these naturally, no citation needed):
  - "processing 10,000–20,000 orders daily from our Dongguan warehouses"
  - "working with 2,300+ factory partners across Guangdong"
  - "managing 1.4M+ SKUs for 200+ countries"
  - "[specific percentage] of our clients who switched from [X] to [Y] saw..."
  
VAGUE → SPECIFIC rewrites:
  "takes a while" → "typically 3-7 business days"
  "cost more" → "adds $0.50-$1.50 per order"
  "many sellers" → "73% of Shopify sellers (based on our client data)"
  "often fail" → "fail in 34% of cases without QC protocols"

### BANNED EXPRESSIONS (will trigger rewrite)
- "In today's [X] landscape/world/environment"
- "It's worth noting that" / "It should be noted"
- "Moreover" / "Furthermore" / "Additionally" (as sentence starters)
- "In conclusion" / "To summarize" / "In summary"
- "game-changer" / "revolutionary" / "seamless" / "cutting-edge"
- "As we can see" / "As mentioned above" / "As previously discussed"
- "needless to say" / "it goes without saying"
- "Great question!" or any hollow affirmations

### FAQ SECTION (MANDATORY, FINAL H2)
- 6-8 questions (not fewer, not more)
- Sources: use PAA questions provided: {paa_questions}
- Each answer format:
  Sentence 1: Direct answer (yes/no/specific fact)
  Sentence 2-3: Essential context with specific detail
  Sentence 4 (optional): Practical implication or soft CTA
  Length: 65-100 words per answer
- Wrap in proper HTML:
  <h3>[Question]</h3>
  <p>[Answer]</p>

### INTERNAL LINKS (3-5 links)
Use these anchor texts and URLs:
{internal_links}
Place naturally within relevant sentences. Avoid "click here" anchors.

### EXTERNAL LINKS (2-3 links)
Link to authoritative non-competitor sources:
- Official statistics (Statista, eMarketer)
- Industry reports (Shopify annual report, etc.)
- Government trade data (Chinese customs, WTO)
Never link to competitors or low-authority sites.

### AUTHOR BIO (end of article, 60-80 words)
<div class="author-bio" itemscope itemtype="https://schema.org/Person">
  <strong itemprop="name">Janson</strong>
  <span itemprop="jobTitle">, Founder & CEO of ASG Dropshipping</span>
  <p itemprop="description">[Bio content: mention 8+ years experience, 
  ASG's operational scale, specific expertise relevant to this article topic, 
  and one concrete achievement]</p>
</div>

## OUTPUT FORMAT (STRICT JSON)
Return ONLY this JSON structure, no markdown, no explanation:
{
  "keyword": "string",
  "title": "string (50-65 chars, primary keyword in first 55 chars)",
  "h1": "string (can differ slightly from title)",
  "metaDescription": "string (145-160 chars, contains primary keyword)",
  "slug": "string (3-5 words, hyphenated, no stop words)",
  "featuredImage": {
    "alt": "string",
    "caption": "string",
    "prompt": "string (DALL-E prompt for 1200x630 image)"
  },
  "introduction": "string (150-200 words, formula above)",
  "keyTakeaways": ["string × 4-5 items"],
  "sections": [
    {
      "sectionIndex": 1,
      "sectionTitle": "string (H2 text)",
      "directAnswerBlock": "string (50-80 words, for geo-answer-block div)",
      "content": "string (HTML formatted section content, includes H3s if needed)",
      "image": {
        "alt": "string",
        "caption": "string",
        "prompt": "string (DALL-E prompt for 800x450 image)"
      },
      "wordCount": 0
    }
  ],
  "faqSection": {
    "sectionTitle": "Frequently Asked Questions",
    "items": [
      {
        "question": "string",
        "answer": "string (65-100 words)"
      }
    ]
  },
  "authorBio": {
    "name": "Janson",
    "title": "Founder & CEO, ASG Dropshipping",
    "content": "string (60-80 words)"
  },
  "sources": [
    {"title": "string", "url": "string", "publisher": "string"}
  ],
  "qualityChecklist": {
    "wordCount": 0,
    "directAnswerBlockCount": 0,
    "specificNumberCount": 0,
    "bannedExpressionsFound": [],
    "faqCount": 0
  }
}
"""
```

---

## 七、工作流执行顺序（升级后完整版）

```
Stage 0:  ArticleTracker.is_published() → 已发布跳过
Stage 1:  KeywordDataClient.get_keyword_metrics() → 获取真实KD/搜索量
Stage 2:  ContentClassifier.classify() → 文章类型分类（使用真实数据辅助）
Stage 3:  ASGKnowledgeBase.get_context() → 向量语义搜索知识库
Stage 4:  SerpAnalyzer.analyze_serp() → 获取前100条结果+PAA
Stage 5:  CompetitorScraper.analyze_competitors() → 爬取前5名全文
Stage 6:  TitleGenerator.generate() → 生成5个候选标题+择优
Stage 7:  OutlineGenerator.generate() → 基于竞品分析生成大纲
Stage 8:  ContentGenerator.generate_article() → 使用升级版Prompt生成全文
Stage 9:  GEOOptimizer.inject_direct_answer_blocks() → 注入答案块
Stage 10: GEOOptimizer.optimize_faq_for_ai() → FAQ优化
Stage 11: QualityChecker.check() → 客观评分（<75分触发重优化，最多1次）
Stage 12: SchemaGenerator.generate_all_schemas() → 生成Schema标记
Stage 13: ImageGenerator.generate_all() → 生成封面+章节图（SEO文件名）
Stage 14: InternalLinkManager.inject_links() → 注入内链
Stage 15: WordPressPublisher.publish_article_enhanced() → 发布草稿
Stage 16: ArticleTracker.mark_published() → 记录追踪
Stage 17: CheckpointManager.clear() → 清理临时检查点

每个Stage完成后：CheckpointManager.save(stage, data)
任何Stage失败：停止，记录错误，支持 resume=True 恢复
```

---

## 八、config.py 新增配置项

```python
# 在 config.py 末尾新增以下配置，现有配置保持不变

# === DataForSEO ===
DATAFORSEO_USERNAME = os.getenv("DATAFORSEO_USERNAME", "")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "")
DATAFORSEO_LOCATION_CODE = int(os.getenv("DATAFORSEO_LOCATION_CODE", "2840"))  # 2840=US

# === 向量知识库 ===
USE_VECTOR_SEARCH = os.getenv("USE_VECTOR_SEARCH", "false").lower() == "true"
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# === 质量控制 ===
MIN_PUBLISH_SCORE = float(os.getenv("MIN_PUBLISH_SCORE", "75"))
ALLOW_FORCE_PUBLISH = os.getenv("ALLOW_FORCE_PUBLISH", "false").lower() == "true"

# === 追踪数据库 ===
TRACKER_DB_PATH = os.getenv("TRACKER_DB_PATH", "./seo_tracker.db")

# === 文章追踪 ===
ARTICLE_BASE_OUTPUT_DIR = os.getenv("ARTICLE_OUTPUT_DIR", "./outputs")

# === Schema ===
AUTHOR_NAME = os.getenv("AUTHOR_NAME", "Janson")
AUTHOR_TITLE = os.getenv("AUTHOR_TITLE", "CEO & Founder")
SITE_NAME = os.getenv("SITE_NAME", "ASG Dropshipping")
SITE_URL = os.getenv("SITE_URL", "https://asgdropshipping.com")
SITE_LOGO_URL = os.getenv("SITE_LOGO_URL", "https://asgdropshipping.com/wp-content/uploads/asg-logo.png")

# === 图片 ===
COVER_IMAGE_WIDTH = 1200
COVER_IMAGE_HEIGHT = 630
SECTION_IMAGE_WIDTH = 800
SECTION_IMAGE_HEIGHT = 450

# === 速率控制 ===
GOOGLE_API_MAX_QPS = float(os.getenv("GOOGLE_API_MAX_QPS", "2"))
LLM_MAX_RPM = int(os.getenv("LLM_MAX_RPM", "5"))
IMAGE_MAX_CONCURRENT = int(os.getenv("IMAGE_MAX_CONCURRENT", "1"))
COMPETITOR_SCRAPE_DELAY_MIN = float(os.getenv("SCRAPE_DELAY_MIN", "1.5"))
COMPETITOR_SCRAPE_DELAY_MAX = float(os.getenv("SCRAPE_DELAY_MAX", "3.0"))
```

---

## 九、.env.example 模板

```bash
# LLM API（现有）
LLM_API_BASE=https://openrouter.ai/api/v1
LLM_API_KEY=your_openrouter_key
LLM_MODEL=anthropic/claude-sonnet-4-5  # 推荐使用最新Sonnet

# Google Search API（现有）
GOOGLE_SEARCH_API_KEY=your_google_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id

# WordPress（现有）
WORDPRESS_SITE_URL=https://asgdropshipping.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_app_password

# Image Generation（现有）
IMAGE_API_BASE=https://openrouter.ai/api/v1
IMAGE_API_KEY=your_key
IMAGE_MODEL=openai/dall-e-3

# DataForSEO（新增）
DATAFORSEO_USERNAME=your_email@example.com
DATAFORSEO_PASSWORD=your_dataforseo_password
DATAFORSEO_LOCATION_CODE=2840

# 质量控制（新增）
MIN_PUBLISH_SCORE=75
ALLOW_FORCE_PUBLISH=false

# 向量搜索（新增，可选）
USE_VECTOR_SEARCH=false
VECTOR_DB_PATH=./chroma_db

# 站点信息（新增）
AUTHOR_NAME=Janson
SITE_NAME=ASG Dropshipping
SITE_URL=https://asgdropshipping.com
SITE_LOGO_URL=https://asgdropshipping.com/wp-content/uploads/asg-logo.png
```

---

## 十、新增 Python 依赖

```txt
# requirements.txt 新增（不修改现有依赖）
beautifulsoup4>=4.12.0    # 竞品内容爬取
lxml>=5.0.0               # BS4解析器（更快）
# chromadb>=0.4.0         # 向量知识库（USE_VECTOR_SEARCH=true时安装）
# sentence-transformers>=2.6.0  # 向量Embedding（USE_VECTOR_SEARCH=true时安装）
```

---

## 十一、执行优先级与顺序

**给AI编程工具的执行指令：**

请按以下顺序执行，每完成一个模块后通知我确认再继续：

```
Step 1:  实现 llm.py 的 extract_json() + JSONExtractionError（30分钟）
          → 立即降低崩溃率，最低成本最高回报

Step 2:  实现 checkpoint.py + 集成到 workflow.py（45分钟）
          → 保护后续所有API费用

Step 3:  实现 competitor_scraper.py（60分钟）
          → 竞品真实数据是一切内容优化的基础

Step 4:  实现 geo_optimizer.py（90分钟）
          → 核心GEO优化能力

Step 5:  实现 schema_generator.py（45分钟）
          → Schema标记，直接影响AI引用率

Step 6:  修改 content.py 注入新Prompt规则（45分钟）
          → 写作质量根本改善

Step 7:  实现 quality_checker.py（60分钟）
          → 质量门控，防止低分内容发布

Step 8:  实现 keyword_data.py + DataForSEO集成（45分钟）
          → 选词策略从盲打变为数据驱动

Step 9:  实现 article_tracker.py + 集成（30分钟）
          → 防重复，规模化必须

Step 10: 图片SEO升级（image.py + wordpress.py）（30分钟）
          → 图片SEO补全

Step 11: 整体联调测试（用一个真实关键词跑完整流程）（60分钟）
```

**总预计工时：约9小时（分2-3天执行）**

---

## 十二、验收标准

每篇生成文章发布前，必须通过以下全部检查：

### 自动检查（QualityChecker 执行）
- [ ] 总质量分 ≥ 75/100
- [ ] 主词密度 0.8%-1.5%
- [ ] 每H2开头有 geo-answer-block
- [ ] FAQ 6-8个，每答案60-100词
- [ ] Article + FAQPage + BreadcrumbList Schema 均存在且有效
- [ ] 内链 3-8个
- [ ] 字数在目标的90%-120%
- [ ] 封面图1200×630，章节图800×450
- [ ] 图片均有SEO文件名和ALT Text

### 人工检查（发布草稿后人工确认）
- [ ] Intro不以"In today's"开头
- [ ] 无banned表达清单中的词汇
- [ ] 至少有2处ASG专有数据引用
- [ ] 作者Bio完整且自然
- [ ] 所有外链打开有效

### GEO验收（发布后1周内用Perplexity测试）
- [ ] Perplexity 搜索主词时，文章内容出现在AI答案中
- [ ] Google 搜索主词时，检查是否触发AI Overview
- [ ] 验证 Schema 有效性：https://validator.schema.org/

---

*文档结束 — 版本 v3.0 — 2026-03-15*
*作者：Claude for Janson / ASG Dropshipping*
*下一步：将本文档完整粘贴到 Claude Code 或 Cursor，执行 Step 1 开始*
