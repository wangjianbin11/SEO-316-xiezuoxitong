"""
内容生成模块 v2.0

根据 SERP 分析和知识库生成 SEO 优化的文章内容
- 纯英文输出，2500-3000 字符控制
- 支持 6-9 个章节的动态生成
- E-E-A-T 优化
- WordPress 发布格式
- 更自然的内容结构，避免固定模板
- 支持三种文章类型：顶梁柱型、回答型、分享型
"""

import random
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from seo_gen.config import settings
from seo_gen.modules.knowledge import KnowledgeBase
from seo_gen.modules.llm import LLMClient


# 文章类型对应的模板文件名
ARTICLE_TYPE_TEMPLATES = {
    "pillar": "ASG-顶梁柱SEO文章写作提示词-终极单体版.md",
    "response": "ASG-回答型SEO文章写作提示词-终极单体版.md",
    "share": "ASG-SEO文章写作提示词-分享型.md",
}

# ASG案例库路径（修正路径）
ASG_CASE_LIBRARY_PATH = Path("/Users/apple/Documents/新的网站内容生成/asg-faq-matrix-geo_副本")

# 备选案例库路径
ASG_CASE_LIBRARY_ALT_PATH = Path("/Users/apple/Documents/cc-工作流/asg-faq-matrix-geo")

# 文章类型对应的目标字数
ARTICLE_TYPE_WORD_COUNTS = {
    "pillar": "4000-6000",
    "response": "3000-4000",
    "share": "3000-4000",
}

# 文章类型对应的推荐章节数
ARTICLE_TYPE_SECTIONS = {
    "pillar": 9,    # 顶梁柱型需要更多章节，深度覆盖
    "response": 7,  # 回答型适中
    "share": 6,     # 分享型较少，以列表为主
}

# GEO 写作规则（AI引用优化）
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

# FAQ 写作规则（AEO优化）
FAQ_WRITING_RULES = """
## 📋 FAQ写作规则（AEO优化）

每个FAQ答案必须：
1. 第一句：直接回答（Yes/No/数字/核心事实）
2. 第二三句：必要背景和具体化
3. 第四句（可选）：实际操作建议
4. 字数：65-100词（英文）
5. 语气：专业直接，不用"Great question!"等
6. 结尾可选：1句软性CTA，不强制

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



class ContentGenerator:
    """SEO 内容生成器 - 升级版 v2.0"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
    ):
        """
        初始化内容生成器

        Args:
            llm_client: LLM 客户端
            knowledge_base: 知识库
        """
        self.llm_client = llm_client
        self.knowledge_base = knowledge_base

    def _load_type_template(self, article_type: str) -> str:
        """
        加载指定类型的提示词模板

        Args:
            article_type: 文章类型 (pillar/response/share)

        Returns:
            模板内容，如果找不到则返回空字符串
        """
        template_name = ARTICLE_TYPE_TEMPLATES.get(article_type)
        if not template_name:
            return ""

        # 尝试多个可能的路径
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / template_name,  # 项目根目录
            Path(__file__).parent.parent.parent / "templates" / template_name,
            Path(__file__).parent.parent.parent / template_name,
            Path(template_name),  # 当前工作目录
        ]

        for path in possible_paths:
            if path.exists():
                logger.info(f"Loaded article type template from: {path}")
                return path.read_text(encoding="utf-8")

        logger.warning(f"Article type template not found: {template_name}")
        return ""

    def _select_relevant_case(self, title: str, keyword: str) -> str:
        """
        从ASG案例库中选择一个相关的真实案例

        Args:
            title: 文章标题
            keyword: 目标关键词

        Returns:
            案例内容文本，如果找不到则返回空字符串
        """
        try:
            # 尝试多个案例库路径
            case_library_paths = [
                ASG_CASE_LIBRARY_PATH,
                ASG_CASE_LIBRARY_ALT_PATH,
            ]

            case_files = []
            library_path = None

            for path in case_library_paths:
                if path.exists():
                    case_files = list(path.glob("ASG成功案例库-*.md"))
                    if case_files:
                        library_path = path
                        logger.info(f"Found case library at: {path}")
                        break

            if not case_files:
                logger.warning("No case files found in any ASG case library path")
                return ""

            # 基于关键词相关性选择最匹配的案例
            keyword_lower = keyword.lower()
            best_case_file = None
            best_score = 0

            # 关键词与案例主题的映射
            topic_keywords = {
                "dropshipping": ["dropshipping", "一件代发", "代发", "fulfillment"],
                "supplier": ["supplier", "供应商", "sourcing", "采购", "工厂"],
                "quality": ["quality", "质量", "质检", "qc", "inspection"],
                "shipping": ["shipping", "物流", "发货", "配送", "delivery", "logistics"],
                "marketing": ["marketing", "营销", "推广", "广告", "tiktok", "facebook"],
                "shopify": ["shopify", "店铺", "store", "电商"],
                "product": ["product", "产品", "选品", "product research", "products", "item", "goods", "sourcing"],
                "brand": ["brand", "品牌", "branding"],
                "legit": ["legit", "legitimate", "prc", "china", "chinese", "safe"],
                "made": ["made", "manufactured", "production", "factory", "origin"],
            }

            # 确定关键词属于哪个主题
            matched_topics = []
            for topic, keywords in topic_keywords.items():
                if any(kw in keyword_lower for kw in keywords):
                    matched_topics.append(topic)

            # 遍历所有案例文件，找出最匹配的
            for case_file in case_files:
                try:
                    content = case_file.read_text(encoding="utf-8").lower()
                    score = 0

                    # 计算相关性分数
                    if keyword_lower in content:
                        score += 10  # 直接匹配关键词

                    for topic in matched_topics:
                        for kw in topic_keywords.get(topic, []):
                            if kw in content:
                                score += 2

                    if score > best_score:
                        best_score = score
                        best_case_file = case_file

                except Exception as e:
                    logger.warning(f"Error reading case file {case_file}: {e}")
                    continue

            # 如果没有找到高分的，随机选择一个
            if not best_case_file or best_score < 5:
                best_case_file = random.choice(case_files)
                logger.info(f"No highly relevant case found, using random: {best_case_file.name}")
            else:
                logger.info(f"Selected relevant case: {best_case_file.name} (score: {best_score})")

            # 读取并返回案例内容
            case_content = best_case_file.read_text(encoding="utf-8")
            return case_content

        except Exception as e:
            logger.error(f"Error selecting ASG case: {e}")
            return ""

    def _get_type_specific_instructions(self, article_type: str) -> str:
        """
        获取类型特定的写作指令

        Args:
            article_type: 文章类型

        Returns:
            类型特定的指令字符串
        """
        instructions = {
            "pillar": """
ARTICLE TYPE: Pillar Post (顶梁柱型)
This is a comprehensive, in-depth guide covering all aspects of the topic.
- Target word count: 4000-6000 words
- Structure: H1 → Introduction → Featured Answer → Table of Contents → 3 deep-dive H2 sections (each with 3-5 H3 subsections) → Conclusion → FAQ
- Focus on establishing authority and expertise
- Include detailed explanations, examples, and actionable insights
- Use subheadings extensively to create a clear hierarchy
""",
            "response": """
ARTICLE TYPE: Response Post (回答型)
This is a direct answer to a specific question, solving a concrete problem.
- Target word count: 3000-4000 words
- Structure: H1 → Introduction → Core Answer (featured snippet bait) → Reading Guide → H2 deep-dive → 2-3 H3 groups → Conclusion → FAQ
- Start with a clear, direct answer to the main question
- Focus on practical, actionable solutions
- Keep the content focused and avoid tangential topics
- Use step-by-step explanations where appropriate
""",
            "share": """
ARTICLE TYPE: Share Post (分享型)
This is a list-based, comparison, or ranking article designed to be shareable.
- Target word count: 3000-4000 words
- Structure: H1 → Introduction → Quick Answer → H2 numbered list (4-8 items) → Conclusion → FAQ
- Use numbered lists, bullet points, and comparison tables
- Make content scannable and easy to digest
- Include specific data, statistics, or examples for each item
- Focus on helping readers make decisions or learn multiple tips quickly
""",
        }
        return instructions.get(article_type, "")

    def _build_context(self, keyword: str, serp_analysis: dict[str, Any], article_type: Optional[str] = None) -> str:
        """构建生成内容的上下文"""
        knowledge = self.knowledge_base.get_all() if self.knowledge_base else {}

        # 获取类型特定指令
        type_instructions = ""
        if article_type:
            type_instructions = self._get_type_specific_instructions(article_type)

        return f"""
# Author Background (Janson - ASG CEO)
{knowledge.get('janson_jieshao', '')}

# Target Audience
{knowledge.get('kehuhuaxiang', '')}

# Company Background
{knowledge.get('qiyejieshao', '')}

# Business Process
{knowledge.get('yewuliucheng', '')}

# Writing Guidelines
{knowledge.get('xiezuojianyi', '')}

# GEO Strategy (AI-Optimized Content Framework)
{knowledge.get('geo_strategy', '')}

{GEO_WRITING_RULES}

{FAQ_WRITING_RULES}

# Current Keyword Analysis
Keyword: {keyword}
Search Intent: {serp_analysis.get('searchIntent', 'informational')}
Primary Intent: {serp_analysis.get('primaryIntent', 'share')}

# Article Type Instructions
{type_instructions}
"""

    async def generate_article(
        self,
        keyword: str,
        slug: str,
        serp_analysis: dict[str, Any],
        structure_analysis: Optional[dict[str, Any]] = None,
        article_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        生成完整文章（2500-3000字符，纯英文，动态章节）

        Args:
            keyword: 关键词
            slug: URL slug
            serp_analysis: SERP 分析结果
            structure_analysis: 结构分析结果（包含推荐章节数量）
            article_type: 文章类型 (pillar/response/share)，影响内容结构

        Returns:
            完整文章数据
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")

        logger.info(f"Starting article generation: {keyword}, type: {article_type}")

        # 选择相关的ASG案例
        case_content = self._select_relevant_case(keyword, keyword)

        context = self._build_context(keyword, serp_analysis, article_type)
        primary_intent = serp_analysis.get("primaryIntent", "share")

        # 根据文章类型确定推荐的章节数量
        if article_type and article_type in ARTICLE_TYPE_SECTIONS:
            default_sections = ARTICLE_TYPE_SECTIONS[article_type]
        else:
            default_sections = 7

        # 从结构分析获取推荐的章节数量（如果有的话优先使用）
        if structure_analysis:
            target_sections = structure_analysis.get("recommendedSectionCount", default_sections)
        else:
            target_sections = default_sections

        # 确保章节数在合理范围内
        target_sections = max(6, min(9, target_sections))

        # 根据章节数计算每个章节的字数
        total_words = 2800  # 总字数目标
        intro_words = 200    # 引言字数
        words_per_section = (total_words - intro_words) // target_sections

        messages = [
            {
                "role": "system",
                "content": f"""You are Janson, CEO of ASG dropshipping, an expert in cross-border e-commerce.

WRITING STYLE:
- First-person perspective with real experience and insights
- Data-driven with specific case studies and actionable advice
- Casual but professional tone
- No filler, every sentence adds value
- Follow Backlinko style

{context}

ARTICLE STRUCTURE (WordPress Ready) - DYNAMIC SECTION COUNT:
1. Featured Image - 1 hero image at the top (before introduction)
2. Introduction Paragraphs - 1-2 engaging opening paragraphs BEFORE Key Takeaways
3. Key Takeaways - 4-6 bullet points summarizing main points
4. Table of Contents (clickable anchor links)
5. Main Content ({target_sections} sections, varies naturally) with EMBEDDED citations and 3 images
6. Sources and Further Reading
7. Author Bio - Janson's profile with 100x100 image after conclusion - 10+ sources with descriptions (at the end)

⚠️ IMAGE REQUIREMENTS:
- **Featured Image**: 1 image at the very top (before introduction)
- **In-Content Images**: EXACTLY 3 images (no more, no less) distributed throughout the article
  - MUST have exactly 3 images in sections (not 1, not 2, but 3)
  - Place images strategically in sections 2, 4, and 6 (or evenly distributed)
  - Each image should have: alt text, caption, and be relevant to the section
- **CRITICAL**: Alt text MUST be SPECIFIC to the section content and keyword
  - NEVER use generic alt text patterns like:
    * "A screenshot of..." or "An image showing..."
    * "Infographic showing..." or "Infographic illustrating..."
    * "A diagram of..." or "A chart displaying..."
    * "Global warehouse distribution map..." or "Map showing..."
    * Any phrase starting with "A/An [noun] showing/illustrating/displaying..."
  - ALWAYS describe the actual visual content related to the specific section topic
  - GOOD examples (specific, descriptive):
    * "Quality inspection process with product testing stages"
    * "Supplier verification checklist with key criteria"
    * "Dropshipping fulfillment workflow diagram"
    * "Product sourcing strategy framework"
  - BAD examples (generic, forbidden):
    * "Infographic showing the components of a successful dropshipping store audit"
    * "A diagram illustrating the dropshipping process"
    * "An image showing quality control steps"
    * "Global warehouse distribution map showing local fulfillment centers"
- **CRITICAL**: Do NOT include image markdown syntax (like ![...](...)) in the section content
  - Images are added separately by the system
  - Just provide image metadata (alt, caption) in the JSON structure
  - NEVER write markdown image syntax in the "content" field

⚠️ AI SEARCH OPTIMIZATION & ASG CASE STUDY:
- **CRITICAL**: Include ONE relevant ASG case study from the case library in section 3 or 4
- **CRITICAL**: Select a case that matches the article topic (e.g., for logistics articles, use logistics cases; for marketing articles, use marketing cases)
- **CRITICAL**: Use REAL data from actual ASG customer cases - never fabricate numbers
- **CRITICAL**: Do NOT mention titles like "CEO", "Founder", or company leadership positions
- **CRITICAL**: Do NOT use phrases like "We implemented these exact strategies" or "Our approach focused on"
- **CRITICAL**: Do NOT use "GEO" as a section title or mention it in the article - it's a writing standard, not content
- **CRITICAL**: Do NOT create sections titled "GEO Optimization" or similar - integrate the principles naturally
- Format as a third-party success story with specific metrics
- Example structure:
  ```
  ### Real-World Success: [Customer Name]'s Results with ASG

  [Customer Name], a [background description], partnered with ASG Dropshipping and achieved:
  - [Specific metric 1 with real numbers]
  - [Specific metric 2 with real numbers]
  - [Specific metric 3 with real numbers]

  The approach included [specific methods used], demonstrating how [key insight].
  ```
- Use this as proof of expertise and authority
- Include specific metrics and results from real cases

⚠️ ASG CASE LIBRARY (Select ONE relevant case from below):
{case_content if case_content else "No case library available - skip case study section"}


⚠️ EXTERNAL LINKS REQUIREMENTS:
- **Minimum 5 external authoritative links** embedded in the content
- Link to: industry reports, research papers, authoritative blogs, tools, case studies
- Use natural anchor text (not "click here" or "read more")
- Format: [anchor text](https://external-url.com)
- Distribute links naturally across different sections
- **CRITICAL**: Link text should NOT be bold, keep normal font size
- **CRITICAL**: Links should blend naturally with surrounding text

⚠️ INTERNAL LINKS REQUIREMENTS:
- **3-5 internal links** to related ASG content
- Use descriptive anchor text
- Format: [descriptive text](internal-url)
- **CRITICAL**: Link text should NOT be bold, keep normal font size
- Distribute across different sections

⚠️ BOLD TEXT REQUIREMENTS:
- **Bold the target keyword and important related keywords** for SEO
- Bold should be used for emphasis on key concepts, not entire sentences
- Format: **keyword** or **important phrase**
- Bold text should be the SAME SIZE as regular text (no heading tags)
- Use bold 5-8 times throughout the article on strategic keywords
- **CRITICAL**: Do NOT bold link text - keep links and bold separate

⚠️ IMPORTANT - DYNAMIC SECTION COUNT:
- Target: {target_sections} main sections (NOT always 6)
- Section count should feel NATURAL for this topic
- Some topics need 6 sections, others need 7, 8, or 9
- Let the content's natural structure guide you
- AVOID forcing a template

SECTION COUNT GUIDELINES:
- 6 sections: Focused, single-aspect topics
- 7 sections: Standard comprehensive guides
- 8 sections: Topics with comparisons or multiple approaches
- 9 sections: Deep dives covering all angles

INTRODUCTION PARAGRAPHS REQUIREMENTS:
- Write 1-2 compelling opening paragraphs that hook the reader
- Place these AFTER the H1 title but BEFORE Key Takeaways
- Include: why this topic matters now, what readers will learn, a hook/statement
- Make it personal and engaging - "If you're running..." or "Here's the truth about..."
- 150-200 words total for the introduction
- CRITICAL: If writing 2 paragraphs, separate them with a BLANK LINE (double newline)

EMBEDDED CITATIONS REQUIREMENTS:
- Integrate source citations DIRECTLY into the section content where relevant
- Use inline citation format: `[Source Name](url)` or `According to [Source](url)...`
- Each section should have 1-2 embedded citations where relevant
- Don't cluster all citations at the end of sections - weave them naturally into sentences
- Still include the full "Sources and Further Reading" list at the end

FORMATTING REQUIREMENTS:
- CRITICAL: Add a BLANK LINE after EVERY paragraph (double newline between paragraphs)
- CRITICAL: In introduction, if 2 paragraphs, separate with BLANK LINE
- Use --- separator between major sections
- Include comparison tables where applicable
- Use bullet points and numbered lists for clarity
- Control image width to prevent overflow (max-width: 100%)

EXAMPLE PARAGRAPH SPACING:
Paragraph 1 content here.

(blank line required here)

Paragraph 2 content here.

(blank line required here)

E-E-A-T REQUIREMENTS:
- **Experience**: Include real case studies, specific numbers, before/after results
- **Expertise**: Use industry terminology, cite credible sources, show deep knowledge
- **Authoritativeness**: Reference ASG's track record, 1000+ clients served
- **Trustworthiness**: Accurate data, honest claims, source citations

IMPORTANT - YEAR REQUIREMENT:
- **Use 2026 as the current year ONLY when contextually appropriate**
- Include year for: trends, statistics, "best of" lists, comparisons, time-sensitive content
- Skip year for: evergreen guides, how-to articles, definitions, concepts, processes
- Title examples WITH year: "Best Dropshipping Suppliers 2026", "E-commerce Trends in 2026"
- Title examples WITHOUT year: "Complete Guide to Dropshipping", "How to Start an Online Store"
- Include up-to-date 2026 statistics and trends where applicable

WORD COUNT: ~2800 characters total (2500-3000 range)

SECTION TITLE GUIDELINES - AVOID TEMPLATES:
❌ Don't use: "Understanding X", "Why X Matters", "Introduction to X"
✅ Do use: Natural, engaging titles that fit the specific topic
✅ Examples:
   - "The Real Cost of Bad Quality (It's Higher Than You Think)"
   - "3 Pre-shipment Checks That Save Thousands in Returns"
   - "How Top Sellers Handle This Without Breaking a Sweat"

NATURAL STRUCTURE PRINCIPLES:
- Vary section length by importance (300-400 words each)
- Core concepts get longer sections
- Tips and summaries can be shorter
- Follow the topic's natural information hierarchy

OUTPUT FORMAT (JSON):
{{
  "keyword": "keyword",
  "title": "SEO-optimized title (50-60 chars)",
  "h1": "H1 heading",
  "metaDescription": "Meta description (150-160 chars)",
  "slug": "url-slug",
  "featuredImage": {{
    "alt": "Descriptive alt text with keyword",
    "caption": "Brief caption describing the image"
  }},
  "introduction": "1-2 engaging opening paragraphs (150-200 words) that hook the reader. CRITICAL: If 2 paragraphs, separate with a BLANK LINE (double newline \\n\\n). Place BEFORE Key Takeaways.",
  "keyTakeaways": [
    "Key point 1 - concise summary",
    "Key point 2 - concise summary",
    "Key point 3 - concise summary",
    "Key point 4 - concise summary",
    "Key point 5 - concise summary"
  ],
  "sections": [
    {{
      "sectionIndex": 1,
      "sectionTitle": "Natural H2 Title (not template-like)",
      "content": "Pure markdown content with H3 subsections (~{words_per_section} words). CRITICAL: Add a BLANK LINE after EVERY paragraph. Include 1-2 embedded citations like [Source Name](url) within the content where relevant. Use **bold** for target keyword and related keywords (5-8 times total in article). Include external links to authoritative sources. DO NOT include image markdown syntax - images are added separately.",
      "image": {{
        "alt": "Specific alt text describing the visual content",
        "caption": "Image caption"
      }}
    }}
  ],
  "authorBio": {{
    "name": "Janson",
    "title": "Founder & CEO, ASG Dropshipping",
    "image": {{
      "url": "https://asgdropshipping.com/wp-content/uploads/2024/01/janson-asg-ceo.png",
      "alt": "Janson - CEO of ASG Dropshipping",
      "size": "100x100"
    }},
    "bio": "With over 10 years in cross-border e-commerce, Janson has helped 1000+ businesses build successful dropshipping operations. As CEO of ASG Dropshipping, he specializes in supplier sourcing, quality control, and GEO optimization strategies.",
    "links": {{
      "linkedin": "https://linkedin.com/in/janson-asg",
      "company": "https://asgdropshipping.com"
    }}
  }},
  "sources": [
    {{"source": "Source Name", "url": "https://example.com", "description": "Brief description of the source content"}},
    {{"source": "Source Name", "url": "https://example.com", "description": "Brief description"}}
  ],
  "externalLinks": [
    {{"anchor": "natural anchor text", "url": "https://authoritative-site.com", "context": "where it appears in content"}},
    {{"anchor": "another anchor", "url": "https://research-site.com", "context": "section context"}}
  ],
  "actualSectionCount": {target_sections},
  "totalWordCount": 2800,
  "imageCount": 4,
  "externalLinkCount": 5
}}

SECTION STRUCTURE (NATURAL, NOT FIXED):
- Generate {target_sections} sections that feel natural for this topic
- Each section should have a clear purpose
- Avoid forcing content into a template
- Let the topic determine the structure

REQUIREMENTS:
- Pure English output only
- Include statistics, percentages, and specific numbers
- Add at least 10 credible source references with descriptions
- Use actual case studies when possible
- Write in pure markdown format
- CRITICAL: Add a BLANK LINE after EVERY paragraph (double newline \\n\\n)
- CRITICAL: If introduction has 2 paragraphs, separate with BLANK LINE
- Include comparison tables where relevant
- Use --- separator between major sections"""
            },
            {
                "role": "user",
                "content": f"""Generate a complete, E-E-A-T optimized article for the keyword: "{keyword}"

Slug: {slug}
Search Intent: {serp_analysis.get('searchIntent', 'informational')}
Article Type: {primary_intent}
Target Sections: {target_sections} (can adjust ±1 if topic naturally requires)
Total Word Target: 2500-3000 words

Requirements:
1. FEATURED IMAGE - 1 hero image at the very top with alt text, URL, and caption
2. Introduction - 1-2 engaging opening paragraphs (150-200 words) BEFORE Key Takeaways
3. Key Takeaways - 4-6 bullet points summarizing the main insights
4. Table of Contents - Clickable anchor links
5. {target_sections} main sections, ~{words_per_section} words each (varies by importance)
6. IN-CONTENT IMAGES - EXACTLY 3 images (no more, no less) distributed throughout sections
7. GEO CASE STUDY - Include ASG's GEO success story in section 3 or 4 with specific metrics
8. EXTERNAL LINKS - Minimum 5 authoritative external links (NOT bold, normal font size)
9. INTERNAL LINKS - 3-5 internal ASG links (NOT bold, normal font size)
10. BOLD KEYWORDS - Use **bold** for target keyword 5-8 times (NOT on links, same font size)
11. AUTHOR BIO - Janson's profile with 100x100 image after conclusion
12. Include comparison tables with data where applicable
13. EMBEDDED CITATIONS - Integrate 1-2 source citations directly into each section
14. Sources and Further Reading - At least 10 credible sources with descriptions
15. Use --- separator between major sections
16. CRITICAL: Add a BLANK LINE after EVERY paragraph
17. Pure English, WordPress-ready format

IMPORTANT - Images (EXACTLY 3):
- Featured image: At the very top (before H1)
- Image 1: In section 2 (middle of content)
- Image 2: In section 4 (middle of content)
- Image 3: In section 6 (middle of content)
- Each image needs: alt text and caption in the JSON structure
- **CRITICAL**: Do NOT write image markdown syntax ![...](...) in the content field
- Images are added separately by the system - just provide metadata in the "image" object
- NEVER include placeholder URLs or broken image links in the markdown content

IMPORTANT - GEO Case Study:
- Include in section 3 or 4 as a real-world example
- Must include ASG's specific results:
  * 300% increase in AI search engine citations
  * Featured in ChatGPT responses
  * 45% boost in organic traffic
- Link to: https://asgdropshipping.com/geo-optimization
- Use as proof of expertise and authority

IMPORTANT - Links (NOT Bold):
- External links: 5+ authoritative sources (research, reports, tools)
- Internal links: 3-5 ASG content links
- Use natural anchor text (e.g., "according to HubSpot research")
- **CRITICAL**: Link text should NOT be bold, keep normal font size
- **CRITICAL**: Links blend naturally with text
- Format: [anchor text](url)

IMPORTANT - Bold Text (NOT Links):
- Bold the target keyword "{keyword}" and related keywords 5-8 times total
- Use for emphasis on key concepts, not entire sentences
- **CRITICAL**: Do NOT bold link text - keep links and bold separate
- Bold text should be SAME SIZE as regular text
- Example: "When choosing **dropshipping suppliers**, focus on **product quality**"

IMPORTANT - Author Bio:
- Place after conclusion, before sources
- Include Janson's 100x100 image
- Brief bio (50-100 words) highlighting expertise
- Links to LinkedIn and company website

IMPORTANT - Paragraph Spacing:
- EVERY paragraph must end with a blank line (press Enter twice after each paragraph)
- If the introduction has 2 paragraphs, separate them with a blank line
- This creates proper spacing in WordPress: Paragraph 1 text\\n\\n\\nParagraph 2 text

IMPORTANT - Dynamic Structure:
- The introduction should be engaging and hook the reader immediately
- Embed citations naturally within sentences, not at the end of paragraphs
- Still include the full sources list at the end
- Generate {target_sections} sections that feel NATURAL for this specific topic
- Vary section lengths - some can be 350 words, others 400+ based on importance
- Use natural H2 titles, avoid template phrases like "Understanding X" or "Why X Matters"

Remember: The goal is to write like a real expert (Janson), not follow a template."""
            }
        ]

        result = await self.llm_client.chat_json(messages, temperature=0.7)

        # 记录生成的章节数量和字数
        sections_count = len(result.get("sections", []))
        logger.info(f"Article generation completed: {result.get('title')}, {sections_count} sections")

        return result

    async def generate_section_images(
        self,
        keyword: str,
        section_title: str,
        section_index: int,
    ) -> list[str]:
        """
        为单个板块生成六宫格配图描述（用于图片生成API）

        Args:
            keyword: 关键词
            section_title: 板块标题
            section_index: 板块序号

        Returns:
            9个图片描述列表
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")

        messages = [
            {
                "role": "system",
                "content": """You are an AI image prompt specialist. Generate 9 detailed image descriptions for a 3x3 grid layout (9-image collage).

OUTPUT FORMAT (JSON):
{
  "images": [
    {"index": 1, "prompt": "detailed image description"},
    {"index": 2, "prompt": "detailed image description"},
    ...
  ]
}

IMAGE PROMPT GUIDELINES:
- Professional, modern style
- Related to the section topic
- Flat design or illustration style
- Blue/white color scheme preferred
- No text overlay
- High quality, 16:9 aspect ratio
- Specific to e-commerce/dropshipping context"""
            },
            {
                "role": "user",
                "content": f"""Generate 9 image descriptions for a 3x3 grid collage.

Keyword: {keyword}
Section: {section_title}
Section Index: {section_index}

Each image should:
- Relate specifically to the section content
- Be professional and modern
- Work well in a collage/grid layout
- Support the article's E-E-A-T credibility"""
            }
        ]

        result = await self.llm_client.chat_json(messages, temperature=0.5)
        return result.get("images", [])

    def sync_generate_article(
        self,
        keyword: str,
        slug: str,
        serp_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """同步版本的文章生成"""
        import asyncio
        return asyncio.run(self.generate_article(keyword, slug, serp_analysis))

    def build_wordpress_html(
        self,
        article: dict[str, Any],
        cover_image_url: str = "",
        section_images: dict[str, str] = None,
        keyword: str = "",
        internal_links: list[dict] = None,
        external_links: list[dict] = None,
    ) -> str:
        """
        构建WordPress发布的HTML格式 - 升级版 v2.0

        Args:
            article: 文章数据
            cover_image_url: 封面图URL
            section_images: 板块配图URL字典 {section_index: image_url}
            keyword: 主关键词（用于高亮）
            internal_links: 内部链接列表 [{"keyword": "xxx", "url": "xxx"}, ...]
            external_links: 外部链接列表 [{"keyword": "xxx", "url": "xxx"}, ...]

        Returns:
            WordPress HTML格式字符串
        """
        from seo_gen.modules.internal_links import get_internal_link_manager

        link_manager = get_internal_link_manager()
        html_parts = []

        # ========== 第一张图片放在文章最开头 ==========
        if cover_image_url:
            html_parts.append('<figure class="cover-image" style="margin: 0 0 2em 0;">')
            html_parts.append(f'<img src="{cover_image_url}" alt="{article.get("title", "")}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;"/>')
            html_parts.append('</figure>')
            html_parts.append('')

        # Introduction (BEFORE Key Takeaways)
        if article.get("introduction"):
            intro_html = self._markdown_to_html(article["introduction"])
            # 处理引言中的链接和关键词
            intro_html = self._process_links_and_keywords(
                intro_html, keyword, internal_links, external_links, link_manager
            )
            html_parts.append('<div class="article-introduction">')
            html_parts.append(intro_html)
            html_parts.append('</div>')
            html_parts.append('<hr/>')

        # Key Takeaways
        if article.get("keyTakeaways"):
            html_parts.append('<hr/>')
            html_parts.append('<div class="key-takeaways">')
            html_parts.append('<h2>Key takeaways</h2>')
            html_parts.append('<ul>')
            for point in article["keyTakeaways"]:
                html_parts.append(f'<li>{point}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')
            html_parts.append('<hr/>')

        # Table of Contents
        html_parts.append('<div class="toc">')
        html_parts.append('<h3>Table of Contents</h3>')
        html_parts.append('<ol>')
        for section in article.get("sections", []):
            title = section.get("sectionTitle", "")
            slug = title.lower().replace(" ", "-").replace("?", "").replace(",", "")
            html_parts.append(f'<li><a href="#{slug}">{title}</a></li>')
        html_parts.append('</ol>')
        html_parts.append('</div>')
        html_parts.append('<hr/>')

        # ========== Related Articles 已移除 ==========

        # Main Content with Images (所有 section 图片都显示，第一张放在章节开头)
        for section in article.get("sections", []):
            idx = section.get("sectionIndex", 0)
            title = section.get("sectionTitle", "")
            content = section.get("content", "")
            slug = title.lower().replace(" ", "-").replace("?", "").replace(",", "")

            # Section with anchor and separator
            html_parts.append(f'<h2 id="{slug}">{title}</h2>')

            # Insert section image at the TOP of each section (置顶显示)
            # 所有有图片的 section 都在章节标题后立即显示图片
            if section_images and str(idx) in section_images:
                html_parts.append(f'<figure class="section-image" style="margin: 1em 0 2em 0;">')
                # 使用具体的描述性 alt text，不使用通用描述
                alt_text = f"{title} - Professional Guide"
                html_parts.append(f'<img src="{section_images[str(idx)]}" alt="{alt_text}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;"/>')
                html_parts.append(f'<figcaption style="text-align: center; color: #666; font-size: 0.9em; margin-top: 0.5em;">{title}</figcaption>')
                html_parts.append(f'</figure>')

            # Convert markdown to HTML with paragraph spacing
            content_html = self._markdown_to_html(content)

            # 处理内容中的链接和关键词
            content_html = self._process_links_and_keywords(
                content_html, keyword, internal_links, external_links, link_manager
            )

            html_parts.append(content_html)

        # ========== Janson 固定结尾（作者介绍） ==========
        html_parts.append('<hr/>')
        html_parts.append('<div class="author-bio" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2em; border-radius: 12px; margin: 2em 0; color: white;">')

        # 作者图片
        html_parts.append('<div style="text-align: center; margin-bottom: 1.5em;">')
        html_parts.append('<img src="https://asgdropshipping.com/wp-content/uploads/2024/01/janson-asg-ceo.png" alt="Janson - Founder & CEO of ASG Dropshipping" style="width: 120px; height: 120px; border-radius: 50%; border: 4px solid white; object-fit: cover;"/>')
        html_parts.append('</div>')

        # 作者介绍
        html_parts.append('<div style="text-align: center;">')
        html_parts.append('<h3 style="color: white; margin: 0 0 1em 0; font-size: 1.3em;">About the Author</h3>')
        html_parts.append('<p style="line-height: 1.8; margin: 0; font-size: 1em;">')
        html_parts.append('I am the Founder and CEO of <strong>ASG Dropshipping</strong>, a company that provides end-to-end supply chain and logistics services for global e-commerce sellers.')
        html_parts.append('</p>')
        html_parts.append('<p style="line-height: 1.8; margin: 1em 0 0 0; font-size: 1em;">')
        html_parts.append('With over <strong>8 years of experience</strong> in dropshipping and the Shopify ecosystem, I lead a team of more than <strong>200 professionals</strong>, working with over <strong>2,300 factories</strong> and managing a catalog of more than <strong>1.4 million products</strong>.')
        html_parts.append('</p>')
        html_parts.append('<p style="line-height: 1.8; margin: 1em 0 0 0; font-size: 1em;">')
        html_parts.append('I also serve as a guest professor at three universities in China, where I share practical insights on cross-border e-commerce, supply chain management, and global trade.')
        html_parts.append('</p>')
        html_parts.append('<p style="line-height: 1.8; margin: 1em 0 0 0; font-size: 1em; font-style: italic;">')
        html_parts.append('Outside of business, I\'m a rock singer and guitarist who enjoys performing on stage.')
        html_parts.append('</p>')
        html_parts.append('</div>')
        html_parts.append('</div>')

        # Sources Section (with descriptions)
        if article.get("sources"):
            html_parts.append('<hr/>')
            html_parts.append('<div class="sources">')
            html_parts.append('<h2>Sources and further reading (selected)</h2>')
            html_parts.append('<ul>')
            for source in article["sources"]:
                name = source.get("source", "")
                url = source.get("url", "")
                desc = source.get("description", "")
                # 外部链接用蓝色加粗
                source_link = link_manager.format_external_link(f"{name}", url, style="html")
                html_parts.append(f'<li>{source_link}: {desc}</li>')
            html_parts.append('</ul>')
            html_parts.append('</div>')

        return "\n".join(html_parts)

    def _process_links_and_keywords(
        self,
        html_content: str,
        keyword: str,
        internal_links: list[dict],
        external_links: list[dict],
        link_manager,
    ) -> str:
        """
        处理HTML内容中的链接和关键词

        - 关键词：蓝色加粗
        - 内部链接：橘色加粗
        - 外部链接：蓝色加粗
        """
        import re

        result = html_content

        # 1. 标记主关键词（蓝色加粗）- 只标记前3次出现
        if keyword:
            keyword_escaped = re.escape(keyword)
            keyword_pattern = rf'\b({keyword_escaped})\b'
            count = 0
            max_keyword_highlights = 3

            def replace_keyword(match):
                nonlocal count
                if count >= max_keyword_highlights:
                    return match.group(0)
                count += 1
                return link_manager.format_keyword_highlight(match.group(1), style="html")

            result = re.sub(keyword_pattern, replace_keyword, result, flags=re.IGNORECASE)

        # 2. 处理内部链接（橘色加粗）
        if internal_links:
            for link in internal_links[:3]:
                kw = link.get("keyword", "")
                url = link.get("url", "")
                if kw and url:
                    # 在内容中查找关键词
                    kw_escaped = re.escape(kw)
                    pattern = rf'\b({kw_escaped})\b'

                    def make_internal_replacer(url):
                        def replacer(match):
                            return link_manager.format_internal_link(match.group(1), url, style="html")
                        return replacer

                    # 只替换第一次出现
                    result = re.sub(pattern, make_internal_replacer(url), result, count=1, flags=re.IGNORECASE)

        # 3. 处理外部链接（蓝色加粗）
        if external_links:
            for link in external_links[:5]:
                kw = link.get("keyword", "")
                url = link.get("url", "")
                if kw and url:
                    kw_escaped = re.escape(kw)
                    pattern = rf'\b({kw_escaped})\b'

                    def make_external_replacer(url):
                        def replacer(match):
                            return link_manager.format_external_link(match.group(1), url, style="html")
                        return replacer

                    # 只替换第一次出现
                    result = re.sub(pattern, make_external_replacer(url), result, count=1, flags=re.IGNORECASE)

        return result

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML with proper spacing"""
        import re

        html = markdown

        # CRITICAL: Remove any markdown image syntax that AI might have incorrectly included
        # This prevents broken image links like ![...](image-placeholder-url)
        html = re.sub(r'!\[([^\]]*)\]\([^)]+\)(?:\s*"([^"]*)")?', '', html)
        # Clean up any resulting empty lines
        html = re.sub(r'\n{3,}', '\n\n', html)

        # Tables - convert before other processing
        # Match markdown tables and convert to HTML
        def convert_table(match):
            table_text = match.group(0)
            lines = table_text.strip().split('\n')
            if len(lines) < 2:
                return match.group(0)

            # Parse header
            header_cells = [cell.strip() for cell in lines[0].split('|')[1:-1]]
            header_row = '<tr>' + ''.join(f'<th>{cell}</th>' for cell in header_cells) + '</tr>'

            # Skip separator line (starts with |---)
            data_rows = []
            for line in lines[2:]:
                if line.strip().startswith('|'):
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if cells:
                        row = '<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>'
                        data_rows.append(row)

            return f'<table><thead>{header_row}</thead><tbody>{"".join(data_rows)}</tbody></table>'

        # Match tables (lines starting with | and containing |)
        html = re.sub(
            r'(?:^\|[^\n]+\n(?:\|[-:\s|]+\n)?(?:^\|[^\n]+\n?)+)',
            convert_table,
            html,
            flags=re.MULTILINE
        )

        # Headers (H1-H6) with spacing style - H6 first to avoid shorter patterns matching longer ones
        spacing_style = ' style="margin-top: 3rem; margin-bottom: 3rem;"'
        html = re.sub(r'^###### (.+)$', rf'<h6{spacing_style}>\1</h6>', html, flags=re.MULTILINE)
        html = re.sub(r'^##### (.+)$', rf'<h5{spacing_style}>\1</h5>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.+)$', rf'<h4{spacing_style}>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', rf'<h3{spacing_style}>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', rf'<h2{spacing_style}>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', rf'<h1{spacing_style}>\1</h1>', html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

        # Lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.+</li>\n?)+', r'<ul>\n\0</ul>', html)

        # Paragraphs with proper spacing (WordPress-compatible)
        # Split by double newline to get separate blocks
        lines = html.split("\n\n")
        paragraphs = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("<") and not line.startswith("|"):
                # Add inline style for WordPress paragraph spacing
                paragraphs.append(f'<p style="margin-top: 3rem; margin-bottom: 3rem;">{line}</p>')
            elif line:
                # Already has HTML tags (headings, tables, lists, etc.) - keep as is
                paragraphs.append(line)

        # Join with double newline to ensure proper paragraph spacing
        return "\n\n".join(paragraphs)


# Global singleton
_content_generator: Optional[ContentGenerator] = None


def get_content_generator() -> ContentGenerator:
    """Get global content generator singleton"""
    global _content_generator
    if _content_generator is None:
        _content_generator = ContentGenerator()
    return _content_generator
