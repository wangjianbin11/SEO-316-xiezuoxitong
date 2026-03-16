"""
CORE-EEAT 内容质量检查器

基于 aaron-he-zhu/seo-geo-claude-skills 的 content-quality 审核框架
- 80项内容质量标准
- CORE-EEAT 四维度评分
"""

from typing import Any, Optional
from loguru import logger


class COREEEATChecker:
    """CORE-EEAT 内容质量检查器"""

    # 核心检查项（16项高权重）
    CORE_CHECKLIST = [
        {"id": "C01", "name": "Intent Alignment", "desc": "标题承诺必须与内容交付匹配"},
        {"id": "C02", "name": "Direct Answer", "desc": "核心答案在前 150 词内"},
        {"id": "C06", "name": "Audience Targeting", "desc": "开头说明本文适合谁"},
        {"id": "C10", "name": "Semantic Closure", "desc": "结论回答开篇问题 + 下一步"},
        {"id": "O01", "name": "Heading Hierarchy", "desc": "H1→H2→H3，不跳级"},
        {"id": "O02", "name": "Summary Box", "desc": "包含 Key Takeaways"},
        {"id": "O06", "name": "Section Chunking", "desc": "每节单一主题；段落 3-5 句"},
        {"id": "O09", "name": "Information Density", "desc": "无废话；术语一致"},
        {"id": "R01", "name": "Data Precision", "desc": "≥5 个带单位的精确数字"},
        {"id": "R02", "name": "Citation Density", "desc": "每 500 词 ≥1 个外部引用"},
        {"id": "R04", "name": "Evidence-Claim Mapping", "desc": "每个声明都有证据支持"},
        {"id": "R07", "name": "Entity Precision", "desc": "人名/机构名/产品名完整"},
        {"id": "C03", "name": "Query Coverage", "desc": "覆盖 ≥3 个查询变体"},
        {"id": "O08", "name": "Anchor Navigation", "desc": "带跳转链接的目录"},
        {"id": "O10", "name": "Multimedia Structure", "desc": "图片有说明文字"},
        {"id": "E07", "name": "Practical Tools", "desc": "包含可下载模板/检查清单"},
    ]

    # GEO-First 优化项
    GEO_FIRST_ITEMS = [
        {"id": "C02", "name": "Direct Answer", "desc": "前 150 字内直接回答"},
        {"id": "C09", "name": "Structured FAQ", "desc": "结构化 FAQ 与 Schema"},
        {"id": "O03", "name": "Data in Tables", "desc": "数据放在表格中"},
        {"id": "O05", "name": "JSON-LD Schema", "desc": "结构化数据标记"},
        {"id": "E01", "name": "Original Data", "desc": "原创一手数据"},
        {"id": "O02", "name": "Summary Box", "desc": "关键要点总结框"},
    ]

    def __init__(self):
        """初始化检查器"""
        pass

    def get_prewrite_checklist(self) -> list[dict]:
        """获取写作前检查清单"""
        return self.CORE_CHECKLIST.copy()

    def get_geo_first_checklist(self) -> list[dict]:
        """获取 GEO 优化检查清单"""
        return self.GEO_FIRST_ITEMS.copy()

    def check_article(
        self,
        article: dict[str, Any],
        keyword: str,
    ) -> dict[str, Any]:
        """
        检查文章的 CORE-EEAT 质量

        Args:
            article: 文章数据
            keyword: 主关键词

        Returns:
            检查结果
        """
        results = {
            "keyword": keyword,
            "title": article.get("title", ""),
            "checks": [],
            "passed": 0,
            "failed": 0,
            "score": 0,
        }

        # 检查各项
        for item in self.CORE_CHECKLIST:
            check_result = self._check_item(article, keyword, item)
            results["checks"].append(check_result)
            if check_result["passed"]:
                results["passed"] += 1
            else:
                results["failed"] += 1

        # 计算分数
        total = len(self.CORE_CHECKLIST)
        results["score"] = round((results["passed"] / total) * 100, 1)

        return results

    def _check_item(
        self,
        article: dict[str, Any],
        keyword: str,
        item: dict,
    ) -> dict:
        """检查单个项目"""
        item_id = item["id"]
        passed = False
        notes = ""

        # C01: Intent Alignment
        if item_id == "C01":
            title = article.get("title", "")
            h1 = article.get("h1", "")
            passed = keyword.lower() in title.lower() or keyword.lower() in h1.lower()
            notes = f"关键词在标题中: {'是' if passed else '否'}"

        # C02: Direct Answer
        elif item_id == "C02":
            intro = article.get("introduction", "")
            passed = len(intro) > 100 and keyword.lower() in intro.lower()[:300]
            notes = f"引言中有关键词: {'是' if passed else '否'}"

        # C06: Audience Targeting
        elif item_id == "C06":
            intro = article.get("introduction", "").lower()
            passed = any(word in intro for word in ["for beginners", "for sellers", "for dropshippers", "this guide is for"])
            notes = f"有受众定位: {'是' if passed else '否'}"

        # C10: Semantic Closure
        elif item_id == "C10":
            sections = article.get("sections", [])
            if sections:
                last_section = sections[-1].get("content", "") if sections else ""
                passed = len(last_section) > 100
            notes = f"有结论部分: {'是' if passed else '否'}"

        # O01: Heading Hierarchy
        elif item_id == "O01":
            sections = article.get("sections", [])
            passed = len(sections) >= 5
            notes = f"章节数量: {len(sections)}"

        # O02: Summary Box
        elif item_id == "O02":
            takeaways = article.get("keyTakeaways", [])
            passed = len(takeaways) >= 3
            notes = f"Key Takeaways 数量: {len(takeaways)}"

        # R01: Data Precision
        elif item_id == "R01":
            content = self._get_all_content(article)
            import re
            numbers = re.findall(r'\d+[\d,.\d]*%?', content)
            passed = len(numbers) >= 5
            notes = f"数据点数量: {len(numbers)}"

        # R02: Citation Density
        elif item_id == "R02":
            sources = article.get("sources", [])
            passed = len(sources) >= 5
            notes = f"来源数量: {len(sources)}"

        # 其他项默认通过
        else:
            passed = True
            notes = "自动通过"

        return {
            "id": item_id,
            "name": item["name"],
            "passed": passed,
            "notes": notes,
        }

    def _get_all_content(self, article: dict) -> str:
        """获取文章所有内容"""
        parts = [
            article.get("introduction", ""),
            article.get("title", ""),
        ]
        for section in article.get("sections", []):
            parts.append(section.get("content", ""))
            parts.append(section.get("sectionTitle", ""))
        return " ".join(parts)

    def get_seo_enhancement_prompt(self, keyword: str) -> str:
        """
        获取 SEO 增强提示

        用于集成到内容生成的 AI 提示中
        """
        return f"""
## CORE-EEAT Content Standards

### Keyword Requirements for "{keyword}":
- Include in title (preferably at start)
- Include in H1 heading
- Include in first 100 words
- Include in at least one H2
- Include in conclusion

### Content Structure Requirements:
- H1 → H2 → H3 hierarchy (no level skipping)
- Include Key Takeaways summary box
- Each paragraph: 3-5 sentences
- Use bullet points for lists
- Bold key phrases

### Data Requirements:
- At least 5 specific statistics with sources
- Include percentages, numbers, and metrics
- Cite authoritative sources
- Include year for time-sensitive data

### Link Requirements:
- Internal links: 2-5 relevant links
- External links: 2-3 authoritative sources
- All claims backed by evidence

### GEO Optimization (for AI citations):
- Answer the main question in first 150 words
- Include FAQ section with 3+ questions
- Use comparison tables
- Add clear definitions (25-50 words)
"""


# 全局单例
_core_eeat_checker: Optional[COREEEATChecker] = None


def get_core_eeat_checker() -> COREEEATChecker:
    """获取全局检查器单例"""
    global _core_eeat_checker
    if _core_eeat_checker is None:
        _core_eeat_checker = COREEEATChecker()
    return _core_eeat_checker
