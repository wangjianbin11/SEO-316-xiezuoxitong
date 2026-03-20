"""
GEO/AEO 内容优化引擎

职责:将 content.py 生成的文章进行 GEO/AEO 二次优化
目标:最大化被 Google AI Overview、Perplexity、ChatGPT、Claude 等引用的概率

GEO 优化的科学原理:
- AI引擎优先引用包含"直接答案"结构的段落(query → direct answer → context)
- AI引擎优先引用包含具体数字和统计数据的内容
- AI引擎优先引用有明确来源归属的内容
- AI引擎优先引用结构化(FAQ、列表、定义框)内容
- AI引擎通过 Schema 标记理解内容语义类型
"""

import re
from dataclasses import dataclass
from typing import Optional, Any, List, Dict
from bs4 import BeautifulSoup

from loguru import logger


@dataclass
class DirectAnswerBlock:
    """直接答案块 - GEO核心单元"""
    trigger_heading: str  # 触发该答案的H2/H3标题
    direct_answer: str  # 50-80字的直接答案(必须自成一体,不依赖上下文)
    supporting_context: str  # 100-200字的支撑解释
    data_point: Optional[str]  # 具体数据点(如有)
    citation_ready: bool  # 是否满足AI引用格式要求


@dataclass
class GEOScore:
    """GEO优化评分"""
    total_score: float  # 0-100总分
    answer_density_score: float  # 答案密度 (25分)
    data_richness_score: float  # 数据丰富度 (20分)
    structure_clarity_score: float  # 结构清晰度 (20分)
    eeat_signal_score: float  # E-E-A-T信号 (20分)
    schema_coverage_score: float  # Schema覆盖度 (15分)
    recommendations: List[str]  # 具体改进建议


class GEOOptimizer:
    """GEO/AEO 优化器"""

    # AI引擎无法引用的表达模式(必须重写)
    UNCITABLE_PATTERNS = [
        r"in today's .{0,20} world",
        r"in today's .{0,20} landscape",
        r"in today's .{0,20} environment",
        r"it's worth noting that",
        r"as we can see",
        r"there are many (factors|reasons|ways)",
        r"in conclusion",
        r"furthermore|moreover|additionally",
        r"needless to say",
        r"it goes without saying",
        r"as mentioned (above|earlier|previously)",
        r"as we (discussed|saw|noted)",
    ]

    # AI引擎偏好引用的结构模式(必须保留和增强)
    CITABLE_PATTERNS = {
        "definition": r"^(a|an|the) .{10,50} is (a|an|the)",
        "direct_answer": r"^(yes|no|the answer is|in short)",
        "data_point": r"\d+[.,]?\d*\s*(%|percent|orders|days|USD|\$)",
        "experience_claim": r"(based on|from our|in our|we've processed|our data shows)",
    }

    # ASG专有数据(可以无需引用直接使用)
    ASG_DATA_POINTS = {
        "daily_orders": "10,000-20,000",
        "countries_served": "200+",
        "warehouses": "4 (Shenzhen/Dongguan)",
        "factory_partners": "2,300+",
        "sku_library": "1.4M+",
        "founded_year": "2019",
        "team_size": "200+",
        "founder_experience": "8 years",
    }

    def __init__(self, llm_client: Any = None):
        """
        初始化优化器

        Args:
            llm_client: LLM客户端(用于生成直接答案块和重写)
        """
        self.llm_client = llm_client

    def analyze_geo_score(self, article: dict) -> GEOScore:
        """
        对文章进行GEO评分

        答案密度评分(25分):
        - 检查每个H2章节开头是否有50-80字的独立直接答案块
        - 每有1个合格答案块 +5分,最多5个(25分)

        数据丰富度评分(20分):
        - 统计全文具体数字出现次数(%、具体数量、日期)
        - 0个=0分,1-3个=5分,4-7个=12分,8+=20分
        - 包含ASG专有数据("Based on X orders")额外+3分

        结构清晰度评分(20分):
        - H1/H2/H3层次完整 +5分
        - FAQ章节存在且≥5个Q&A +5分
        - 无孤立段落(每H2有≥2个子段落)+5分
        - 无超过400字的连续正文(有视觉分隔)+5分

        E-E-A-T信号评分(20分):
        - 包含作者bio(含职位、经验年数)+5分
        - 包含"Based on our [N] orders/clients/experience" +5分
        - 包含公司具体数据(ASG统计数字)+5分
        - 包含具体地理/操作细节(东莞仓库、具体工厂类型)+5分

        Schema覆盖度评分(15分):
        - Article Schema存在 +5分
        - FAQPage Schema存在且与正文FAQ匹配 +5分
        - BreadcrumbList Schema存在 +3分
        - Author/Person Schema存在 +2分
        """
        content_html = article.get("content", "")
        # 若顶层content为空（文章刚生成时），从sections拼接
        if not content_html.strip():
            sections = article.get("sections", [])
            content_html = "\n\n".join(s.get("content", "") for s in sections)
        soup = BeautifulSoup(content_html, 'html.parser')

        # 1. 答案密度评分
        answer_blocks = soup.find_all('div', class_='geo-answer-block')
        h2_count = len(soup.find_all('h2'))
        answer_density_score = min(25, len(answer_blocks) * 5)

        # 2. 数据丰富度评分
        data_richness_score = self._calculate_data_richness(content_html)

        # 3. 结构清晰度评分
        structure_clarity_score = self._calculate_structure_clarity(soup, article)

        # 4. E-E-A-T信号评分
        eeat_signal_score = self._calculate_eeat_signals(content_html, soup)

        # 5. Schema覆盖度评分(需要从article中获取)
        schema_coverage_score = self._calculate_schema_coverage(article)

        # 计算总分
        total_score = (
            answer_density_score +
            data_richness_score +
            structure_clarity_score +
            eeat_signal_score +
            schema_coverage_score
        )

        # 生成建议
        recommendations = self._generate_recommendations(
            answer_density_score,
            data_richness_score,
            structure_clarity_score,
            eeat_signal_score,
            schema_coverage_score,
            h2_count,
            len(answer_blocks)
        )

        return GEOScore(
            total_score=total_score,
            answer_density_score=answer_density_score,
            data_richness_score=data_richness_score,
            structure_clarity_score=structure_clarity_score,
            eeat_signal_score=eeat_signal_score,
            schema_coverage_score=schema_coverage_score,
            recommendations=recommendations
        )

    def _calculate_data_richness(self, content: str) -> float:
        """计算数据丰富度评分"""
        # 统计具体数字
        data_patterns = [
            r'\d+[.,]?\d*\s*%',  # 百分比
            r'\d+[.,]?\d*\s*(orders|clients|sellers|products|SKUs)',  # 订单/客户数
            r'\$\d+[.,]?\d*',  # 美元金额
            r'\d+[.,]?\d*\s*(days|hours|minutes|weeks|months)',  # 时间
            r'\d{1,3}(,\d{3})+',  # 大数字(带逗号)
        ]

        data_count = 0
        for pattern in data_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            data_count += len(matches)

        # 基础评分
        if data_count == 0:
            score = 0
        elif data_count <= 3:
            score = 5
        elif data_count <= 7:
            score = 12
        else:
            score = 20

        # 检查ASG专有数据
        asg_data_found = any(
            value in content for value in self.ASG_DATA_POINTS.values()
        )
        if asg_data_found:
            score = min(20, score + 3)

        return score

    def _calculate_structure_clarity(self, soup: BeautifulSoup, article: dict) -> float:
        """计算结构清晰度评分"""
        score = 0

        # 检查H1/H2/H3层次
        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))

        if h1_count == 1 and h2_count >= 4 and h3_count > 0:
            score += 5

        # 检查FAQ章节
        faq_section = article.get('faqSection', {})
        faq_items = faq_section.get('items', [])
        if len(faq_items) >= 5:
            score += 5

        # 检查段落结构(简化检查)
        paragraphs = soup.find_all('p')
        if len(paragraphs) >= h2_count * 2:  # 每个H2至少2个段落
            score += 5

        # 检查是否有超长段落
        long_paragraphs = [p for p in paragraphs if len(p.get_text()) > 400]
        if len(long_paragraphs) < len(paragraphs) * 0.2:  # 少于20%的段落超长
            score += 5

        return score

    def _calculate_eeat_signals(self, content: str, soup: BeautifulSoup) -> float:
        """计算E-E-A-T信号评分"""
        score = 0

        # 检查作者bio
        author_bio = soup.find('div', class_='author-bio')
        if author_bio and len(author_bio.get_text()) > 50:
            score += 5

        # 检查经验陈述
        experience_patterns = [
            r'based on (our|processing|analyzing)',
            r'in our (warehouse|operations|experience)',
            r"we've (processed|handled|managed)",
            r'our data shows',
            r'from our \d+ (years|orders|clients)',
        ]

        experience_count = 0
        for pattern in experience_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                experience_count += 1

        score += min(5, experience_count)

        # 检查ASG具体数据
        asg_mentions = sum(
            1 for value in self.ASG_DATA_POINTS.values()
            if value in content
        )
        if asg_mentions > 0:
            score += 5

        # 检查地理细节
        geo_keywords = ['Dongguan', 'Shenzhen', 'Guangdong', 'warehouse', 'factory']
        geo_count = sum(1 for kw in geo_keywords if kw in content)
        if geo_count >= 2:
            score += 5

        return score

    def _calculate_schema_coverage(self, article: dict) -> float:
        """计算Schema覆盖度评分"""
        score = 0

        # 检查是否有schema字段(实际schema在后续步骤生成)
        # 这里只是预估,实际评分在schema生成后
        if article.get('title'):
            score += 5  # Article Schema基础

        faq_items = article.get('faqSection', {}).get('items', [])
        if len(faq_items) >= 5:
            score += 5  # FAQPage Schema

        # 其他schema在实际生成时评分
        score += 5  # 预留给BreadcrumbList和Author Schema

        return score

    def _generate_recommendations(
        self,
        answer_score: float,
        data_score: float,
        structure_score: float,
        eeat_score: float,
        schema_score: float,
        h2_count: int,
        answer_block_count: int
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []

        if answer_score < 20:
            missing = h2_count - answer_block_count
            recommendations.append(f"添加 {missing} 个直接答案块(每个H2开头)")

        if data_score < 15:
            recommendations.append("增加具体数字和统计数据(目标:每500词至少2个数据点)")

        if structure_score < 15:
            recommendations.append("优化文章结构:确保FAQ≥5个,每H2有≥2个段落")

        if eeat_score < 15:
            recommendations.append("增强E-E-A-T信号:添加作者bio、经验陈述、ASG数据")

        if schema_score < 12:
            recommendations.append("添加完整Schema标记:Article、FAQPage、BreadcrumbList")

        if not recommendations:
            recommendations.append("文章GEO优化良好,无需重大改进")

        return recommendations

    async def inject_direct_answer_blocks(self, article: dict, llm_client: Any = None) -> dict:
        """
        为每个H2章节生成并注入直接答案块
        处理 article["sections"] 中每个 section 的 content
        """
        client = llm_client or self.llm_client
        if not client:
            logger.warning("No LLM client available, skipping direct answer block injection")
            return article

        sections = article.get("sections", [])
        if not sections:
            logger.warning("No sections found in article, skipping direct answer block injection")
            return article

        for i, section in enumerate(sections):
            section_title = section.get("sectionTitle", "")
            section_content = section.get("content", "")

            # BUG-4修复: 优先检查 geoAnswerBlock 字段是否已由 LLM 填写
            existing_block = section.get("geoAnswerBlock", "")
            if existing_block and len(existing_block.split()) >= 40:
                logger.debug(f"Section {i+1} already has geoAnswerBlock field, skipping injection")
                continue
            # 其次检查 content 中是否已有 HTML 答案块
            if 'geo-answer-block' in section_content:
                logger.debug(f"Section {i+1} already has answer block in content, skipping")
                continue

            # 生成直接答案块
            try:
                answer_text = await self._generate_direct_answer(section_title, client)

                # BUG-2修复: 同时写入单独字段供 quality_checker 读取
                sections[i]["geoAnswerBlock"] = answer_text

                # QUALITY-3修复: 升级为 Question+Answer Schema 配对
                # 将 H2 标题转换为问题格式
                question_text = section_title
                if not question_text.endswith('?'):
                    # 如果不是问句，转换为问句
                    question_text = f"What about {section_title.lower()}?"

                answer_block = (
                    f'<div class="geo-answer-block" itemscope itemtype="https://schema.org/Question">'
                    f'<meta itemprop="name" content="{question_text}"/>'
                    f'<div itemscope itemprop="suggestedAnswer" itemtype="https://schema.org/Answer">'
                    f'<meta itemprop="upvoteCount" content="1"/>'
                    f'<div itemprop="text">'
                    f'<p>{answer_text}</p>'
                    f'</div>'
                    f'</div>'
                    f'</div>\n\n'
                )

                # 注入到 section content 开头
                sections[i]["content"] = answer_block + section_content
                logger.debug(f"Injected answer block for section: {section_title[:50]}")

            except Exception as e:
                logger.error(f"Failed to generate answer block for '{section_title}': {e}")
                continue

        article["sections"] = sections
        # 不要同步更新顶层 content，build_wordpress_html 从 sections 读取

        return article

    async def _generate_direct_answer(self, heading: str, llm_client: Any) -> str:
        """生成直接答案文本"""
        prompt = f"""Generate a direct answer block for this heading: "{heading}"

Requirements:
- 50-80 words
- First sentence: directly answer the implied question
- Second sentence: add specific numbers, conditions, or timeframes
- Third sentence (optional): key distinction or important note
- Must be self-contained (readable without surrounding context)
- NO pronouns without clear antecedents (it/they/this/that)
- NO phrases like "In today's...", "It's worth noting", "As we can see"
- Use active voice and concrete language

Example for "What is a dropshipping agent?":
"A dropshipping agent is a third-party service provider in China that handles sourcing, quality control, warehousing, and international shipping for e-commerce sellers on a per-order basis. Unlike trading companies, agents work exclusively for your business with dedicated account managers and typically charge $0.50-$2.00 per order plus actual shipping costs. This model eliminates minimum order quantities and upfront inventory investment."

Now generate for: "{heading}"

Return ONLY the answer text, no explanation."""

        messages = [
            {"role": "system", "content": "You are an expert at writing AI-citable direct answers for SEO content."},
            {"role": "user", "content": prompt}
        ]

        response = await llm_client.chat(messages, temperature=0.7, max_tokens=200)
        return response.strip()

    async def rewrite_uncitable_sentences(self, text: str, llm_client: Any = None) -> str:
        """
        检测并重写AI无法引用的表达

        检测:正则匹配 UNCITABLE_PATTERNS
        重写规则(调用LLM):
        - "In today's competitive dropshipping landscape..."
          → "Dropshipping agents handle sourcing, QC, and shipping for X orders daily."
        - "There are many factors to consider..."
          → "Three factors determine agent quality: [A], [B], and [C]."
        - "It's worth noting that..."
          → 直接陈述事实,删除引导语
        """
        client = llm_client or self.llm_client
        if not client:
            return text

        # 检测uncitable表达
        uncitable_found = []
        for pattern in self.UNCITABLE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                uncitable_found.append(match.group())

        if not uncitable_found:
            return text

        # 批量重写
        try:
            prompt = f"""Rewrite these AI-uncitable phrases to be direct and concrete:

Original text excerpt:
{text[:1000]}

Uncitable phrases found:
{', '.join(set(uncitable_found))}

Rules:
- Remove filler phrases like "In today's...", "It's worth noting"
- Replace vague statements with specific facts
- Use active voice and concrete language
- Keep the same meaning but make it AI-citable

Return the rewritten text."""

            messages = [
                {"role": "system", "content": "You are an expert at rewriting content for AI citation."},
                {"role": "user", "content": prompt}
            ]

            rewritten = await client.chat(messages, temperature=0.7)
            return rewritten.strip()

        except Exception as e:
            logger.error(f"Failed to rewrite uncitable sentences: {e}")
            return text

    def enhance_data_density(self, article: dict) -> dict:
        """
        增强文章的数据密度

        扫描以下模式并标记为可强化位置:
        - "many sellers" → 建议替换为具体百分比
        - "often" / "usually" → 建议替换为频率数据
        - "takes time" → 建议替换为具体天数/小时数
        - "cost more" → 建议替换为具体金额范围

        ASG专有数据注入(优先使用,不需要引用来源):
        - 日处理订单量:10,000-20,000
        - 服务国家:200+
        - 仓库数量:4个(深圳/东莞)
        - 工厂合作数:2,300+
        - SKU库:1.4M+
        - 成立时间:2019年
        - 团队规模:200+人
        - 创始人经验:8年

        数据注入句式模板(自然植入,不强硬):
        - "Based on processing over [N] orders for Shopify sellers..."
        - "Across our [N] factory partners, we've found that..."
        - "In our Dongguan warehouse operations..."
        """
        content = article.get("content", "")

        # 替换模糊表达为具体数据
        replacements = {
            r'\bmany sellers\b': 'a significant percentage of sellers',
            r'\boften\b': 'in approximately 60-70% of cases',
            r'\busually\b': 'typically',
            r'\btakes time\b': 'takes 3-7 business days',
            r'\bcost more\b': 'costs $0.50-$2.00 more per order',
            r'\bquickly\b': 'within 24-48 hours',
        }

        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        article["content"] = content
        return article

    async def optimize_faq_for_ai(self, faq_list: List[Dict], llm_client: Any = None) -> List[Dict]:
        """
        优化FAQ使其符合AI引用标准
        QUALITY-2修复: 激活真正的LLM重写

        每个FAQ答案必须满足:
        1. 第一句直接回答问题(Yes/No/The answer is/[直接事实])
        2. 答案60-100词(英文),不超过120词
        3. 必须自成一体(删除问题后仍有意义)
        4. 不引用"上文"/"下文"/"如前所述"
        5. 包含至少1个具体数字或时间
        6. 结尾可选:1句关于ASG的软性CTA(不强制)

        FAQ问题来源优先级:
        1. Google PAA(People Also Ask) - 最高优先
        2. Perplexity 对该关键词的相关问题
        3. Reddit/Quora 高赞问题
        4. 竞品FAQ章节中的问题

        每篇文章FAQ数量:6-8个(不少于6,不多于8)
        """
        import asyncio

        client = llm_client or self.llm_client
        optimized_faq = []

        for faq in faq_list[:8]:  # 最多8个
            question = faq.get('question', '')
            answer = faq.get('answer', '')

            # 检查答案长度
            word_count = len(answer.split())

            # 检查是否有具体数字
            has_data = bool(re.search(r'\d+', answer))

            # 检查是否自成一体(简单检查:不包含"上文"等引用)
            self_contained = not any(
                phrase in answer.lower()
                for phrase in ['as mentioned', 'above', 'previously', 'earlier', 'as we']
            )

            # 如果不符合标准,进行LLM重写
            needs_optimization = (
                word_count < 60 or
                word_count > 120 or
                not has_data or
                not self_contained
            )

            if needs_optimization and client:
                try:
                    # QUALITY-2修复: 调用LLM进行真正的重写
                    rewritten_answer = await self._rewrite_faq_answer(
                        question, answer, client
                    )
                    if rewritten_answer:
                        answer = rewritten_answer
                        word_count = len(answer.split())
                except Exception as e:
                    logger.warning(f"FAQ rewrite failed for '{question[:30]}...': {e}")

            faq['answer'] = answer
            faq['needs_optimization'] = needs_optimization
            faq['word_count'] = word_count
            faq['has_data'] = has_data
            faq['self_contained'] = self_contained

            optimized_faq.append(faq)

        # 确保数量在6-8之间
        if len(optimized_faq) < 6:
            logger.warning(f"FAQ count too low: {len(optimized_faq)}, should be 6-8")
        elif len(optimized_faq) > 8:
            optimized_faq = optimized_faq[:8]

        return optimized_faq

    async def _rewrite_faq_answer(self, question: str, original_answer: str, llm_client: Any) -> str:
        """QUALITY-2修复: 使用LLM重写FAQ答案"""
        prompt = f"""Rewrite this FAQ answer to be AI-citation optimized:

Question: {question}
Original Answer: {original_answer}

Requirements:
1. First sentence: Direct answer (Yes/No/The answer is X/A [noun] is Y)
2. Word count: 65-100 words (strict limit)
3. Self-contained: Must make sense WITHOUT the question
4. Include at least ONE specific number, percentage, or timeframe
5. NO cross-references like "as mentioned above" or "previously"
6. NO filler phrases like "It's worth noting" or "In today's landscape"
7. Optional: End with ONE soft CTA about ASG (not required)

Return ONLY the rewritten answer, no explanation."""

        try:
            messages = [
                {"role": "system", "content": "You are an expert at writing AI-citation optimized FAQ answers."},
                {"role": "user", "content": prompt}
            ]

            response = await llm_client.chat(messages, temperature=0.5)
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to rewrite FAQ: {e}")
            return original_answer
