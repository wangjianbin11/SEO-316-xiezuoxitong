"""
SEO Content Writer Skill

基于 aaron-he-zhu/seo-geo-claude-skills 的 seo-content-writer 技能
- 关键词优化
- 标题生成（5种公式）
- Meta 描述
- H1/H2/H3 层级结构
- Featured Snippet 优化
- 内部/外部链接
- 可读性增强
"""

from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class SEOContentConfig:
    """SEO 内容配置"""
    primary_keyword: str
    secondary_keywords: list[str]
    target_word_count: int = 2500
    content_type: str = "blog"  # blog, guide, landing_page, etc.
    target_audience: str = "dropshippers"
    search_intent: str = "informational"  # informational, commercial, transactional
    tone: str = "professional"
    cta_goal: str = "learn_more"


class SEOContentWriter:
    """
    SEO 内容写作器

    基于 12 步工作流：
    1. 收集需求
    2. 加载 CORE-EEAT 质量约束
    3. 研究和规划
    4. 创建优化标题
    5. 编写 Meta 描述
    6. 构建内容结构
    7. 应用 On-Page SEO 最佳实践
    8. 添加内部/外部链接
    9. 最终 SEO 审查
    """

    # 5 种标题公式
    TITLE_FORMULAS = [
        "How to [Do X] in [Year]: [Subtitle]",
        "[Number] [Adjective] [Noun] in [Year]",
        "[Question]? [Answer Hint]",
        "[Option A] vs [Option B]: [Decision Criterion]",
        "The Ultimate [Topic] Guide for [Audience]",
    ]

    # Power Words 列表
    POWER_WORDS = [
        "Ultimate", "Complete", "Comprehensive", "Essential", "Proven",
        "Best", "Top", "Critical", "Effective", "Strategic",
        "Step-by-Step", "Guide", "Tips", "Strategies", "Secrets",
    ]

    def __init__(self):
        """初始化 SEO 内容写作器"""
        pass

    def generate_title_options(
        self,
        keyword: str,
        count: int = 5,
        year: int = 2026,
    ) -> list[dict]:
        """
        生成标题选项

        Args:
            keyword: 主关键词
            count: 生成数量
            year: 年份

        Returns:
            标题选项列表
        """
        titles = []

        # 公式 1: How to
        titles.append({
            "title": f"How to {keyword.title()} in {year}: The Complete Guide",
            "formula": "How to + Year + Guide",
            "keyword_position": "front",
            "chars": len(f"How to {keyword.title()} in {year}: The Complete Guide"),
        })

        # 公式 2: Number list
        titles.append({
            "title": f"7 {keyword.title()} Strategies That Work in {year}",
            "formula": "Number + Strategies + Year",
            "keyword_position": "front",
            "chars": len(f"7 {keyword.title()} Strategies That Work in {year}"),
        })

        # 公式 3: Question
        titles.append({
            "title": f"What is {keyword.title()}? Everything You Need to Know",
            "formula": "Question + Answer Hint",
            "keyword_position": "middle",
            "chars": len(f"What is {keyword.title()}? Everything You Need to Know"),
        })

        # 公式 4: Ultimate Guide
        titles.append({
            "title": f"The Ultimate {keyword.title()} Guide for E-commerce Sellers",
            "formula": "Ultimate + Audience",
            "keyword_position": "front",
            "chars": len(f"The Ultimate {keyword.title()} Guide for E-commerce Sellers"),
        })

        # 公式 5: Comparison (if applicable)
        titles.append({
            "title": f"{keyword.title()}: A Strategic Guide to Boosting Your Business",
            "formula": "Topic + Benefit",
            "keyword_position": "front",
            "chars": len(f"{keyword.title()}: A Strategic Guide to Boosting Your Business"),
        })

        return titles[:count]

    def generate_meta_description(
        self,
        keyword: str,
        title: str,
        content_type: str = "blog",
    ) -> str:
        """
        生成 Meta 描述

        要求：
        - 150-160 字符
        - 包含主关键词
        - 包含 CTA
        - 引人注目

        Args:
            keyword: 主关键词
            title: 文章标题
            content_type: 内容类型

        Returns:
            Meta 描述
        """
        meta_templates = [
            f"Discover everything about {keyword} in this comprehensive guide. Learn proven strategies, expert tips, and actionable steps to succeed. Start reading now!",
            f"Looking for {keyword} strategies? This guide covers everything from basics to advanced tactics. Get expert insights and boost your business today.",
            f"Master {keyword} with our step-by-step guide. Packed with real examples, data, and pro tips from industry experts. Read the full article.",
        ]

        return meta_templates[0]

    def get_seo_checklist(self) -> dict:
        """
        获取 SEO 检查清单

        Returns:
            SEO 检查项字典
        """
        return {
            "keyword_placement": {
                "title": "主关键词在标题中",
                "h1": "主关键词在 H1 中",
                "first_100_words": "主关键词在前 100 词中",
                "h2s": "主关键词在至少一个 H2 中",
                "conclusion": "主关键词在结论中",
            },
            "content_quality": {
                "word_count": "字数达标 (2500-3000)",
                "readability": "段落 3-5 句",
                "bullet_points": "使用项目符号",
                "bold_key_phrases": "关键短语加粗",
            },
            "links": {
                "internal_links": "2-5 个内部链接",
                "external_links": "2-3 个权威外部链接",
            },
            "technical": {
                "meta_description": "Meta 描述 150-160 字符",
                "faq_section": "FAQ 部分 (3+ 问题)",
                "featured_snippet": "Featured Snippet 优化",
            },
        }

    def get_core_eeat_prewrite_checklist(self) -> list[dict]:
        """
        获取 CORE-EEAT 预写检查清单

        这些是写作时需要遵循的 16 项高权重标准

        Returns:
            检查项列表
        """
        return [
            {"id": "C01", "standard": "Intent Alignment", "description": "标题承诺必须与内容交付匹配"},
            {"id": "C02", "standard": "Direct Answer", "description": "核心答案在前 150 词内"},
            {"id": "C06", "standard": "Audience Targeting", "description": "说明'本文适合谁'"},
            {"id": "C10", "standard": "Semantic Closure", "description": "结论回答开篇问题 + 下一步"},
            {"id": "O01", "standard": "Heading Hierarchy", "description": "H1→H2→H3，不跳级"},
            {"id": "O02", "standard": "Summary Box", "description": "包含 TL;DR 或 Key Takeaways"},
            {"id": "O06", "standard": "Section Chunking", "description": "每节单一主题；段落 3-5 句"},
            {"id": "O09", "standard": "Information Density", "description": "无废话；术语一致"},
            {"id": "R01", "standard": "Data Precision", "description": "≥5 个带单位的精确数字"},
            {"id": "R02", "standard": "Citation Density", "description": "每 500 词 ≥1 个外部引用"},
            {"id": "R04", "standard": "Evidence-Claim Mapping", "description": "每个声明都有证据支持"},
            {"id": "R07", "standard": "Entity Precision", "description": "人名/机构名/产品名完整"},
            {"id": "C03", "standard": "Query Coverage", "description": "覆盖 ≥3 个查询变体"},
            {"id": "O08", "standard": "Anchor Navigation", "description": "带跳转链接的目录"},
            {"id": "O10", "standard": "Multimedia Structure", "description": "图片/视频有说明文字"},
            {"id": "E07", "standard": "Practical Tools", "description": "包含可下载模板/检查清单"},
        ]

    def build_content_prompt_enhancement(
        self,
        keyword: str,
        config: Optional[SEOContentConfig] = None,
    ) -> str:
        """
        构建内容生成的 SEO 增强提示

        将 SEO 最佳实践集成到 AI 提示中

        Args:
            keyword: 主关键词
            config: SEO 配置

        Returns:
            增强的提示文本
        """
        config = config or SEOContentConfig(
            primary_keyword=keyword,
            secondary_keywords=[],
        )

        enhancement = f"""
## SEO Content Writing Standards (CORE-EEAT Framework)

### Keyword Placement Requirements:
- Primary keyword "{keyword}" must appear in:
  - Title (preferably at start)
  - H1 heading
  - First 100 words of introduction
  - At least one H2 section
  - Conclusion paragraph
- Keyword density: 1-2% (natural, not forced)
- Use semantic variations and LSI keywords naturally

### Content Structure Requirements:
- H1 → H2 → H3 hierarchy (no level skipping)
- Include Key Takeaways / TL;DR summary box
- Each paragraph: 3-5 sentences
- Use bullet points for lists
- Bold key phrases for scanability

### Link Requirements:
- Internal links: 2-5 relevant internal links
- External links: 2-3 authoritative sources with citations
- All claims backed by evidence with source links

### Featured Snippet Optimization:
- Include FAQ section with 3+ questions (40-60 word answers)
- Add comparison tables where relevant
- Structure how-to steps with numbered lists
- Provide clear definitions (25-50 words, standalone)

### Data Requirements:
- At least 5 specific statistics with sources
- Specific numbers, percentages, and metrics
- Cite authoritative sources (e.g., "According to [Source]...")
- Include year for time-sensitive data (2026)

### CORE-EEAT Pre-Write Checklist (16 items to apply):
| ID | Standard | How to Apply |
|----|----------|-------------|
| C01 | Intent Alignment | Title promise must match content delivery |
| C02 | Direct Answer | Core answer in first 150 words |
| C06 | Audience Targeting | State "this article is for..." |
| C10 | Semantic Closure | Conclusion answers opening question + next steps |
| O01 | Heading Hierarchy | H1→H2→H3, no level skipping |
| O02 | Summary Box | Include TL;DR or Key Takeaways |
| O06 | Section Chunking | Each section single topic; paragraphs 3–5 sentences |
| O09 | Information Density | No filler; consistent terminology |
| R01 | Data Precision | ≥5 precise numbers with units |
| R02 | Citation Density | ≥1 external citation per 500 words |
| R04 | Evidence-Claim Mapping | Every claim backed by evidence |
| R07 | Entity Precision | Full names for people/orgs/products |
| C03 | Query Coverage | Cover ≥3 query variants |
| O08 | Anchor Navigation | Table of contents with jump links |
| O10 | Multimedia Structure | Images/videos have captions |
| E07 | Practical Tools | Include templates, checklists, or calculators |
"""
        return enhancement


# 全局单例
_seo_content_writer: Optional[SEOContentWriter] = None


def get_seo_content_writer() -> SEOContentWriter:
    """获取全局 SEO 内容写作器单例"""
    global _seo_content_writer
    if _seo_content_writer is None:
        _seo_content_writer = SEOContentWriter()
    return _seo_content_writer
