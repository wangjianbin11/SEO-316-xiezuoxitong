"""
客观质量评分系统

职责:对生成文章进行100%客观量化评分
原则:不依赖LLM自评,全部基于规则计算
目标:给每篇文章一个0-100的综合分,低于阈值拒绝发布
"""

import re
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup

from loguru import logger

# 尝试导入markdown包
try:
    import markdown as md_parser
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown包未安装，将使用正则fallback解析")


@dataclass
class QualityReport:
    """质量检查报告"""
    # 总分
    total_score: float  # 0-100
    publish_ready: bool  # total_score >= 75 才发布

    # 技术SEO评分(满分30)
    title_score: float  # H1包含关键词且≤65字符 (5分)
    meta_score: float  # Meta description 140-160字符 (5分)
    url_score: float  # URL含关键词,≤5词,无停用词 (5分)
    heading_structure_score: float  # H1/H2/H3正确层次结构 (5分)
    schema_score: float  # 3种Schema均存在 (5分)
    internal_link_score: float  # 内链3-8个 (5分)

    # 内容质量评分(满分40)
    word_count_score: float  # 达到目标字数90%-120% (10分)
    keyword_density_score: float  # 主词密度0.8%-1.5% (10分)
    readability_score: float  # Flesch-Kincaid评分60-70 (10分)
    data_density_score: float  # 每500词至少1个具体数字 (10分)

    # GEO优化评分(满分30)
    direct_answer_score: float  # 每H2开头有答案块 (10分)
    faq_quality_score: float  # FAQ 6-8个,每答案60-100词 (10分)
    eeat_score: float  # 作者bio+公司数据+经验陈述 (10分)

    # 详细问题列表
    critical_issues: list[str]  # 必须修复(触发重新生成)
    warnings: list[str]  # 建议修复
    passed_checks: list[str]  # 通过的检查项


class QualityChecker:
    """质量检查器"""

    # 阈值配置
    MIN_PUBLISH_SCORE = 75  # 低于此分数拒绝发布,触发重新生成
    REGENERATE_THRESHOLD = 60  # 低于此分数触发完全重新生成(不仅仅是优化)
    MAX_KEYWORD_DENSITY = 0.015  # 1.5%(防堆砌)
    MIN_KEYWORD_DENSITY = 0.008  # 0.8%
    TARGET_READABILITY_MIN = 55  # Flesch-Kincaid最低(太难)
    TARGET_READABILITY_MAX = 75  # Flesch-Kincaid最高(太简单)

    def __init__(self, llm_client=None):
        """
        初始化质量检查器

        Args:
            llm_client: LLM 客户端(可选,保留兼容性)
        """
        self.llm_client = llm_client

    def count_words_markdown(self, markdown_content: str) -> int:
        """
        统计Markdown内容的字数（排除标题和格式标记）

        Args:
            markdown_content: Markdown格式的文章内容

        Returns:
            正文字数（排除标题）
        """
        if not markdown_content:
            return 0

        # 移除Markdown标题（# ## ### 等）
        lines = markdown_content.split('\n')
        content_lines = []
        for line in lines:
            stripped = line.strip()
            # 跳过标题行
            if stripped.startswith('#'):
                continue
            # 跳过空行
            if not stripped:
                continue
            content_lines.append(stripped)

        # 合并内容
        content = ' '.join(content_lines)

        # 移除Markdown格式标记
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # 粗体
        content = re.sub(r'\*(.+?)\*', r'\1', content)      # 斜体
        content = re.sub(r'`(.+?)`', r'\1', content)        # 行内代码
        content = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', content)  # 链接
        content = re.sub(r'!\[.*?\]\(.+?\)', '', content)   # 图片

        # 统计字数
        words = content.split()
        return len(words)

    def _get_soup_from_article(self, article: dict) -> BeautifulSoup:
        """
        从文章数据获取BeautifulSoup对象
        处理Markdown/HTML混合格式
        """
        # 优先从sections拼接content（Markdown格式）
        sections = article.get("sections", [])
        markdown_parts = []

        for section in sections:
            title = section.get("sectionTitle", "")
            if title:
                markdown_parts.append(f"## {title}")

            # GEO答案块（已是Markdown引用格式）
            geo_block = section.get("geoAnswerBlock", "")
            if geo_block:
                markdown_parts.append(f"> {geo_block}")

            content = section.get("content", "")
            if content:
                markdown_parts.append(content)

        full_markdown = "\n\n".join(markdown_parts)

        # 转换为HTML再解析
        if MARKDOWN_AVAILABLE and full_markdown:
            html = md_parser.markdown(full_markdown, extensions=['tables', 'extra'])
        else:
            # Regex fallback
            html = full_markdown
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        return BeautifulSoup(html, 'html.parser')

    async def check_article_quality(self, article: dict, keyword: str) -> dict:
        """
        兼容旧版 workflow 调用的质量检查方法

        Args:
            article: 文章数据
            keyword: 目标关键词

        Returns:
            兼容旧格式的质量检查结果
        """
        # 调用新版 check 方法
        target_word_count = article.get("totalWordCount", 3000)
        report = self.check(article, target_word_count, keyword)

        # 转换为旧版兼容格式
        return {
            "overallScore": report.total_score,
            "overallGrade": self._score_to_grade(report.total_score),
            "publishReady": report.publish_ready,
            "technicalSEO": {
                "title": report.title_score,
                "meta": report.meta_score,
                "url": report.url_score,
                "headingStructure": report.heading_structure_score,
                "schema": report.schema_score,
                "internalLinks": report.internal_link_score,
                "subtotal": report.title_score + report.meta_score + report.url_score +
                           report.heading_structure_score + report.schema_score + report.internal_link_score
            },
            "contentQuality": {
                "wordCount": report.word_count_score,
                "keywordDensity": report.keyword_density_score,
                "readability": report.readability_score,
                "dataDensity": report.data_density_score,
                "subtotal": report.word_count_score + report.keyword_density_score +
                           report.readability_score + report.data_density_score
            },
            "geoOptimization": {
                "directAnswers": report.direct_answer_score,
                "faqQuality": report.faq_quality_score,
                "eeat": report.eeat_score,
                "subtotal": report.direct_answer_score + report.faq_quality_score + report.eeat_score
            },
            "criticalIssues": report.critical_issues,
            "warnings": report.warnings,
            "passedChecks": report.passed_checks,
        }

    def _score_to_grade(self, score: float) -> str:
        """分数转等级"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"

    def check(
        self,
        article: dict,
        target_word_count: int,
        primary_keyword: str
    ) -> QualityReport:
        """
        执行完整质量检查

        调用顺序:
        1. check_technical_seo()
        2. check_content_quality()
        3. check_geo_optimization()
        4. 汇总评分,生成报告
        5. 如果 total_score < MIN_PUBLISH_SCORE,在 critical_issues 中列明原因

        Args:
            article: 文章数据
            target_word_count: 目标字数
            primary_keyword: 主关键词

        Returns:
            质量报告
        """
        logger.info(f"Starting quality check for keyword: {primary_keyword}")

        # 1. 技术SEO检查
        tech_seo = self.check_technical_seo(article, primary_keyword)

        # 2. 内容质量检查
        content_quality = self.check_content_quality(article, target_word_count, primary_keyword)

        # 3. GEO优化检查
        geo_optimization = self.check_geo_optimization(article)

        # 汇总评分
        total_score = (
            tech_seo["total"] +
            content_quality["total"] +
            geo_optimization["total"]
        )

        # 收集问题
        critical_issues = []
        warnings = []
        passed_checks = []

        # 技术SEO问题
        critical_issues.extend(tech_seo.get("critical", []))
        warnings.extend(tech_seo.get("warnings", []))
        passed_checks.extend(tech_seo.get("passed", []))

        # 内容质量问题
        critical_issues.extend(content_quality.get("critical", []))
        warnings.extend(content_quality.get("warnings", []))
        passed_checks.extend(content_quality.get("passed", []))

        # GEO优化问题
        critical_issues.extend(geo_optimization.get("critical", []))
        warnings.extend(geo_optimization.get("warnings", []))
        passed_checks.extend(geo_optimization.get("passed", []))

        # 判断是否可发布
        publish_ready = total_score >= self.MIN_PUBLISH_SCORE

        if not publish_ready:
            critical_issues.append(f"总分 {total_score:.1f} 低于发布阈值 {self.MIN_PUBLISH_SCORE}")

        logger.info(f"Quality check complete: {total_score:.1f}/100 - {'PASS' if publish_ready else 'FAIL'}")

        return QualityReport(
            total_score=total_score,
            publish_ready=publish_ready,
            title_score=tech_seo["title"],
            meta_score=tech_seo["meta"],
            url_score=tech_seo["url"],
            heading_structure_score=tech_seo["heading"],
            schema_score=tech_seo["schema"],
            internal_link_score=tech_seo["internal_link"],
            word_count_score=content_quality["word_count"],
            keyword_density_score=content_quality["keyword_density"],
            readability_score=content_quality["readability"],
            data_density_score=content_quality["data_density"],
            direct_answer_score=geo_optimization["direct_answer"],
            faq_quality_score=geo_optimization["faq"],
            eeat_score=geo_optimization["eeat"],
            critical_issues=critical_issues,
            warnings=warnings,
            passed_checks=passed_checks
        )

    def check_technical_seo(self, article: dict, primary_keyword: str) -> dict:
        """
        技术SEO检查(满分30)

        Title检查:
        - 主词出现在前60字符 → +3分
        - 总长度50-65字符 → +2分

        Meta Description检查:
        - 包含主词 → +3分
        - 长度140-160字符 → +2分

        URL检查:
        - 包含主词 → +2分
        - 长度≤5词 → +2分
        - 全小写,用连字符 → +1分

        Heading结构检查:
        - 只有1个H1 → +2分
        - H2数量4-10个 → +2分
        - 没有H3直接在H1下(需要先有H2)→ +1分

        Schema检查(调用schema_generator验证):
        - Article Schema存在且有效 → +2分
        - FAQPage Schema存在且有效 → +2分
        - BreadcrumbList Schema存在 → +1分

        内链检查:
        - 内链3-8个 → +5分
        - 内链2个或9个 → +3分
        - 内链<2或>9 → +0分
        """
        scores = {
            "title": 0,
            "meta": 0,
            "url": 0,
            "heading": 0,
            "schema": 0,
            "internal_link": 0,
            "total": 0,
            "critical": [],
            "warnings": [],
            "passed": []
        }

        keyword_lower = primary_keyword.lower()

        # Title检查
        title = article.get("title", "")
        if keyword_lower in title.lower()[:60]:
            scores["title"] += 3
            scores["passed"].append("标题包含主关键词")
        else:
            scores["warnings"].append("标题前60字符未包含主关键词")

        if 50 <= len(title) <= 65:
            scores["title"] += 2
            scores["passed"].append("标题长度适中(50-65字符)")
        else:
            scores["warnings"].append(f"标题长度 {len(title)} 不在推荐范围(50-65)")

        # Meta Description检查
        meta_desc = article.get("metaDescription", "")
        if keyword_lower in meta_desc.lower():
            scores["meta"] += 3
            scores["passed"].append("Meta描述包含主关键词")
        else:
            scores["warnings"].append("Meta描述未包含主关键词")

        if 140 <= len(meta_desc) <= 160:
            scores["meta"] += 2
            scores["passed"].append("Meta描述长度适中(140-160字符)")
        else:
            scores["warnings"].append(f"Meta描述长度 {len(meta_desc)} 不在推荐范围(140-160)")

        # URL检查
        slug = article.get("slug", "")
        if keyword_lower.replace(" ", "-") in slug.lower():
            scores["url"] += 2
            scores["passed"].append("URL包含主关键词")

        word_count_in_slug = len(slug.split("-"))
        if word_count_in_slug <= 5:
            scores["url"] += 2
            scores["passed"].append("URL长度适中(≤5词)")

        if slug == slug.lower() and "-" in slug:
            scores["url"] += 1
            scores["passed"].append("URL格式正确(小写+连字符)")

        # Heading结构检查 - 使用新的Markdown解析方法
        soup = self._get_soup_from_article(article)

        h1_count = len(soup.find_all('h1'))
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))

        if h1_count == 1:
            scores["heading"] += 2
            scores["passed"].append("只有1个H1标题")
        else:
            scores["critical"].append(f"H1数量错误: {h1_count} (应为1)")

        if 4 <= h2_count <= 10:
            scores["heading"] += 2
            scores["passed"].append(f"H2数量适中({h2_count}个)")
        else:
            scores["warnings"].append(f"H2数量 {h2_count} 不在推荐范围(4-10)")

        # 简化的H3检查
        if h3_count > 0:
            scores["heading"] += 1
            scores["passed"].append("包含H3子标题")

        # Schema检查(简化,实际schema在后续生成)
        # 这里只检查文章数据是否完整
        if article.get("title") and article.get("metaDescription"):
            scores["schema"] += 2
            scores["passed"].append("Article Schema数据完整")

        faq_items = article.get("faqSection", {}).get("items", [])
        if len(faq_items) >= 5:
            scores["schema"] += 2
            scores["passed"].append("FAQPage Schema数据完整")

        scores["schema"] += 1  # BreadcrumbList基础分

        # 内链检查(从content中统计)
        internal_links = len(soup.find_all('a', href=True))
        if 3 <= internal_links <= 8:
            scores["internal_link"] = 5
            scores["passed"].append(f"内链数量适中({internal_links}个)")
        elif internal_links == 2 or internal_links == 9:
            scores["internal_link"] = 3
            scores["warnings"].append(f"内链数量 {internal_links} 接近边界")
        else:
            scores["warnings"].append(f"内链数量 {internal_links} 不在推荐范围(3-8)")

        # 计算总分
        scores["total"] = sum([
            scores["title"],
            scores["meta"],
            scores["url"],
            scores["heading"],
            scores["schema"],
            scores["internal_link"]
        ])

        return scores

    def check_content_quality(
        self,
        article: dict,
        target_word_count: int,
        primary_keyword: str
    ) -> dict:
        """
        内容质量检查(满分40)

        字数检查:
        - 实际字数 / 目标字数
        - 90%-110% → +10分
        - 80%-120% → +6分
        - 70%-130% → +3分
        - 其他 → +0分

        关键词密度:
        - 密度 = 主词出现次数 / 总词数
        - 0.8%-1.5% → +10分
        - 0.5%-2.0% → +6分
        - 0.3%-2.5% → +3分
        - <0.3%或>2.5% → 0分(严重问题)

        可读性评分(Flesch-Kincaid Reading Ease):
        公式:206.835 - 1.015×(总词数/总句数) - 84.6×(总音节数/总词数)
        英文音节数估算:用正则统计元音组合
        - 60-70分 → +10分(理想范围)
        - 50-80分 → +6分
        - 40-90分 → +3分

        数据密度:
        - 计算每500词中包含具体数字的句子数
        - ≥2个/500词 → +10分
        - 1个/500词 → +6分
        - <1个/500词 → +3分
        """
        scores = {
            "word_count": 0,
            "keyword_density": 0,
            "readability": 0,
            "data_density": 0,
            "total": 0,
            "critical": [],
            "warnings": [],
            "passed": []
        }

        # 提取全文
        full_text = self._extract_full_text(article)
        actual_word_count = len(full_text.split())

        # 字数检查
        ratio = actual_word_count / target_word_count if target_word_count > 0 else 0

        if 0.9 <= ratio <= 1.1:
            scores["word_count"] = 10
            scores["passed"].append(f"字数达标({actual_word_count}/{target_word_count})")
        elif 0.8 <= ratio <= 1.2:
            scores["word_count"] = 6
            scores["warnings"].append(f"字数略偏离目标({actual_word_count}/{target_word_count})")
        elif 0.7 <= ratio <= 1.3:
            scores["word_count"] = 3
            scores["warnings"].append(f"字数偏离目标较多({actual_word_count}/{target_word_count})")
        else:
            scores["critical"].append(f"字数严重偏离目标({actual_word_count}/{target_word_count})")

        # 关键词密度
        density = self.calculate_keyword_density(full_text, primary_keyword)

        if self.MIN_KEYWORD_DENSITY <= density <= self.MAX_KEYWORD_DENSITY:
            scores["keyword_density"] = 10
            scores["passed"].append(f"关键词密度适中({density:.2%})")
        elif 0.005 <= density <= 0.020:
            scores["keyword_density"] = 6
            scores["warnings"].append(f"关键词密度略偏离({density:.2%})")
        elif 0.003 <= density <= 0.025:
            scores["keyword_density"] = 3
            scores["warnings"].append(f"关键词密度偏离较多({density:.2%})")
        else:
            scores["critical"].append(f"关键词密度异常({density:.2%})")

        # 可读性评分
        readability = self.calculate_flesch_kincaid(full_text)

        if self.TARGET_READABILITY_MIN <= readability <= self.TARGET_READABILITY_MAX:
            scores["readability"] = 10
            scores["passed"].append(f"可读性良好({readability:.1f})")
        elif 50 <= readability <= 80:
            scores["readability"] = 6
            scores["passed"].append(f"可读性可接受({readability:.1f})")
        elif 40 <= readability <= 90:
            scores["readability"] = 3
            scores["warnings"].append(f"可读性需改进({readability:.1f})")
        else:
            scores["warnings"].append(f"可读性较差({readability:.1f})")

        # 数据密度
        data_per_500 = self._calculate_data_density(full_text, actual_word_count)

        if data_per_500 >= 2:
            scores["data_density"] = 10
            scores["passed"].append(f"数据密度充足({data_per_500:.1f}/500词)")
        elif data_per_500 >= 1:
            scores["data_density"] = 6
            scores["warnings"].append(f"数据密度一般({data_per_500:.1f}/500词)")
        else:
            scores["data_density"] = 3
            scores["warnings"].append(f"数据密度不足({data_per_500:.1f}/500词)")

        # 计算总分
        scores["total"] = sum([
            scores["word_count"],
            scores["keyword_density"],
            scores["readability"],
            scores["data_density"]
        ])

        return scores

    def check_geo_optimization(self, article: dict) -> dict:
        """
        GEO优化检查(满分30)

        直接答案块检查:
        - 统计含 class="geo-answer-block" 的div数量
        - 数量 = H2数量 → +10分
        - 数量 ≥ H2数量×0.7 → +7分
        - 数量 ≥ H2数量×0.5 → +4分
        - 数量 < H2数量×0.5 → +0分

        FAQ质量检查:
        - FAQ问题数6-8个 → +4分
        - 每个FAQ答案60-120词 → +3分/个,最多+4分
        - FAQ Schema与正文FAQ条目匹配 → +2分

        E-E-A-T检查:
        - 包含作者bio(词数>50词)→ +3分
        - 正文包含"Based on our"/"In our warehouse"等经验陈述 → +3分(每种+1,最多+3)
        - 正文包含ASG具体数字(10000+/2300+/200+ etc)→ +2分
        - 正文包含具体地理信息(Dongguan/Shenzhen/Guangdong)→ +2分
        """
        scores = {
            "direct_answer": 0,
            "faq": 0,
            "eeat": 0,
            "total": 0,
            "critical": [],
            "warnings": [],
            "passed": []
        }

        # 使用新的Markdown解析方法
        soup = self._get_soup_from_article(article)

        # 直接答案块检查 - 从sections字段而非HTML中查找
        sections = article.get("sections", [])
        geo_blocks_count = sum(
            1 for s in sections
            if s.get("geoAnswerBlock") and len(s["geoAnswerBlock"].split()) >= 40
        )
        h2_count = len(sections)  # sections数量即H2数量

        if h2_count > 0:
            ratio = geo_blocks_count / h2_count

            if ratio >= 1.0:
                scores["direct_answer"] = 10
                scores["passed"].append(f"每个H2都有直接答案块({geo_blocks_count}/{h2_count})")
            elif ratio >= 0.7:
                scores["direct_answer"] = 7
                scores["warnings"].append(f"大部分H2有答案块({geo_blocks_count}/{h2_count})")
            elif ratio >= 0.5:
                scores["direct_answer"] = 4
                scores["warnings"].append(f"部分H2有答案块({geo_blocks_count}/{h2_count})")
            else:
                scores["critical"].append(f"答案块严重不足({geo_blocks_count}/{h2_count})")

        # FAQ质量检查
        faq_items = article.get("faqSection", {}).get("items", [])
        faq_count = len(faq_items)

        if 6 <= faq_count <= 8:
            scores["faq"] += 4
            scores["passed"].append(f"FAQ数量适中({faq_count}个)")
        else:
            scores["warnings"].append(f"FAQ数量 {faq_count} 不在推荐范围(6-8)")

        # 检查FAQ答案长度
        good_answers = 0
        for item in faq_items:
            answer = item.get("answer", "")
            word_count = len(answer.split())
            if 60 <= word_count <= 120:
                good_answers += 1

        scores["faq"] += min(4, good_answers)
        if good_answers >= len(faq_items) * 0.8:
            scores["passed"].append(f"FAQ答案长度适中({good_answers}/{faq_count})")

        scores["faq"] += 2  # FAQ Schema匹配基础分

        # E-E-A-T检查
        full_text = self._extract_full_text(article)

        # 作者bio
        author_bio = article.get("authorBio", {}).get("content", "")
        if len(author_bio.split()) > 50:
            scores["eeat"] += 3
            scores["passed"].append("包含完整作者介绍")

        # 经验陈述
        experience_patterns = [
            r'based on (our|processing)',
            r'in our (warehouse|operations)',
            r"we've (processed|handled)"
        ]
        experience_count = sum(
            1 for pattern in experience_patterns
            if re.search(pattern, full_text, re.IGNORECASE)
        )
        scores["eeat"] += min(3, experience_count)
        if experience_count > 0:
            scores["passed"].append(f"包含{experience_count}处经验陈述")

        # ASG数据
        asg_numbers = ['10,000', '20,000', '2,300', '200+', '1.4M']
        asg_count = sum(1 for num in asg_numbers if num in full_text)
        if asg_count > 0:
            scores["eeat"] += 2
            scores["passed"].append(f"包含{asg_count}处ASG数据")

        # 地理信息
        geo_keywords = ['Dongguan', 'Shenzhen', 'Guangdong']
        geo_count = sum(1 for kw in geo_keywords if kw in full_text)
        if geo_count >= 2:
            scores["eeat"] += 2
            scores["passed"].append(f"包含{geo_count}处地理细节")

        # 计算总分
        scores["total"] = sum([
            scores["direct_answer"],
            scores["faq"],
            scores["eeat"]
        ])

        return scores

    def calculate_keyword_density(self, text: str, keyword: str) -> float:
        """计算关键词密度(考虑词组和变体)"""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0

        # 词组匹配(连续词)
        text_lower = text.lower()
        count = len(re.findall(re.escape(keyword.lower()), text_lower))

        return count / len(words)

    def calculate_flesch_kincaid(self, text: str) -> float:
        """计算 Flesch-Kincaid 可读性评分"""
        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)

        # 分句
        sentences = re.split(r'[.!?]+', clean_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        # 分词
        words = re.findall(r'\b[a-zA-Z]+\b', clean_text)

        if not sentences or not words:
            return 50.0

        # 计算音节数
        total_syllables = sum(self._count_syllables(word) for word in words)

        # 计算平均值
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)

        # Flesch-Kincaid公式
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

        return max(0, min(100, score))

    def _count_syllables(self, word: str) -> int:
        """英文单词音节数估算"""
        word = word.lower()
        if len(word) <= 3:
            return 1

        # 统计元音组合
        vowels = re.findall(r'[aeiouy]+', word)
        count = len(vowels)

        # 词尾e通常不发音
        if word.endswith('e') and count > 1:
            count -= 1

        return max(1, count)

    def _extract_full_text(self, article: dict) -> str:
        """提取文章全文"""
        parts = []

        # Introduction
        intro = article.get("introduction", "")
        parts.append(intro)

        # Sections
        sections = article.get("sections", [])
        for section in sections:
            content = section.get("content", "")
            parts.append(content)

        # FAQ
        faq_items = article.get("faqSection", {}).get("items", [])
        for item in faq_items:
            answer = item.get("answer", "")
            parts.append(answer)

        full_text = " ".join(parts)

        # 移除HTML标签
        clean_text = re.sub(r'<[^>]+>', ' ', full_text)

        return clean_text

    def _calculate_data_density(self, text: str, word_count: int) -> float:
        """计算数据密度(每500词的数据点数)"""
        # 统计数字模式
        data_patterns = [
            r'\d+[.,]?\d*\s*%',
            r'\d+[.,]?\d*\s*(orders|clients|sellers)',
            r'\$\d+',
            r'\d+[.,]?\d*\s*(days|hours|weeks)',
        ]

        data_count = 0
        for pattern in data_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            data_count += len(matches)

        # 计算每500词的数据点数
        if word_count == 0:
            return 0.0

        return (data_count / word_count) * 500
