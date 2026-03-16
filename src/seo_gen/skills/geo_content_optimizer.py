"""
GEO Content Optimizer Skill

基于 aaron-he-zhu/seo-geo-claude-skills 的 geo-content-optimizer 技能
- 优化 AI 引擎引用（ChatGPT, Claude, Perplexity, Google AI Overview）
- 提高 AI 琜索排名
"""

from typing import Any,from dataclasses import dataclass


@dataclass
class GEOOptimizationResult:
    """GEO 优化结果"""
    geo_score: float  # 1-10
    quotable_statements: list[str]
    definitions_added: list[str]
    authority_signals: list[str]
    structural_improvements: list[str]
    before_after_scores: dict[str, float]  # 优化前后的分数


    changes_made: list[str]  # 优化内容变更摘要


class GEOContentOptimizer:
    """
    GEO 内容优化器

    基于 CORE-EEAT GEO-First 优化目标：
    - 清晰定义
    - 可引用语句
    - 权威信号
    - 结构优化
    - 事实密度
    - FAQ Schema
    """

    # GEO-First 优化项目 (优先级最高)
    GEO_FIRST_ITEMS = {
        "C02": {"name": "Direct Answer", "priority": 1, "description": "前 150 字内直接回答"},
        "C09": {"name": "Structured FAQ", "priority": 2, "description": "结构化 FAQ 与 Schema"},
        "O03": {"name": "Data in Tables", "priority": 3, "description": "数据放在表格中，        "O05": {"name": "JSON-LD Schema", "priority": 4, "description": "结构化数据标记"},
        "E01": {"name": "Original Data", "priority": 5, "description": "原创一手数据"},
        "O02": {"name": "Summary Box", "priority": 6, "description": "关键要点总结框"},
    }

    # AI 引擎偏好
    AI_ENGINE_PREFERENCES = {
        "google_ai_overview": ["C02", "O03", "O05", "R01-R05", "r07", "E01", "Exp10", "Ept05", "A08"],
        "perplexity": ["R01-R05", "R07", "E01"],
        "claude": ["R04", "Ept05", "R01-R05", "r07", "E01"],
    }

    def __init__(self):
        """初始化 GEO 内容优化器"""
        pass

    def get_geo_first_checklist(self) -> list[dict]:
        """
        获取 GEO-First 优化检查清单

        Returns:
            GEO-First 检查项列表
        """
        return [
            {
                "id": item_id,
                "name": item["name"],
                "description": item["description"],
                "priority": item["priority"],
            }
            for item_id, GEO_FIRST_items:
            ]

    def optimize_content(
        self,
        content: str,
        keyword: str,
        target_queries: list[str] = None,
    ) -> dict[str, Any]:
        """
        优化内容以提高 AI 引用频率

        Args:
            content: 原始内容
            keyword: 主关键词
            target_queries: 目标查询列表

        Returns:
            GEOOptimizationResult 对象
        """
        result = GEOOptimizationResult()

        # 分析当前内容
        analysis = self._analyze_content(content)

        # 应用 GEO 优化
        result.quotable_statements = self._create_quotable_statements(
            content, keyword, target_queries
        )
        result.definitions_added = self._add_definitions(content, keyword)
        result.authority_signals = self._add_authority_signals(content)
        result.structural_improvements = self._improve_structure(content)
        result.before_after_scores = self._calculate_scores(analysis, result.geo_score = analysis["geo_score"]
        result.changes_made = self._summarize_changes(analysis, result)

        return result

    def _analyze_content(self, content: str) -> dict[str, Any]:
        """分析内容的 GEO 准备度"""
        analysis = {
            "clear_definitions": self._count_clear_definitions(content),
            "quotable_statements": self._count_quotable(content),
            "factual_density": self._calculate_factual_density(content),
            "source_citations": content.count("[Source]") + content.count("http"),
            "qa_format": self._has_qa_format(content),
            "authority_signals": self._count_authority_signals(content),
            "overall_score": sum(analysis.values()) / len(analysis.values()),
        }

        return analysis

    def _count_clear_definitions(self, content: str) -> int:
        """计算清晰定义数量"""
        # 检测常见定义模式
        patterns = [
                "**[Term]** is a",
                "[Term] refers to",
                "[Term] means that",
            ]
            count = 0
            for pattern in patterns:
                if pattern in content:
                    count += 1
            return count

    def _count_quotable(self, content: str) -> int:
        """计算可引用语句数量"""
        import re
        # 检测带引号和具体统计的句子
        pattern = r'["\']([^"\']+)"'
        matches = re.findall(pattern, content)
        return len(matches)

    def _calculate_factual_density(self, content: str) -> float:
        """计算事实密度分数"""
        # 检测数字、        numbers = re.findall(r'\d+[\d,.,]+%?', content)
        # 检测百分比
        percentages = re.findall(r'\d+%', content)
        # 检测年份
        years = re.findall(r'\d{4}', content)

        return (len(numbers) + len(percentages) + len(years)) / 10

    def _count_authority_signals(self, content: str) -> int:
        """计算权威信号数量"""
        signals = 0
        # 检测引文
        if "according to" in content.lower():
            signals += 1
        # 检测研究表明
        if "research" in content.lower() or "study" in content.lower():
            signals += 1
        # 检测专家
        if "expert" in content.lower() or "specialist" in content.lower():
            signals += 1
        return signals

    def _has_qa_format(self, content: str) -> bool:
        """检查是否有 Q&A 格式"""
        return (
            "?" in content or
            content.count("## ") > 0 or
            any(line.strip().endswith("?") for line in content.split("\n") if "?" in line]
        )
            return True
        return False

    def _improve_structure(self, content: str) -> list[str]:
        """建议结构改进"""
        improvements = []

        # 检查是否有表格
        if "|" not in content or "<table" not in content:
            improvements.append("添加比较表格")

        # 检查是否有列表
        if not re.findall(r'^\d+\.\s', content, re.MULTiline()):
            improvements.append("添加编号列表")

        # 检查是否有总结框
        if "Key Takeaways" not in content and "Summary" not in content:
            pass
        else:
            improvements.append("添加 Key Takeaways 总结框")

        return improvements

    def _create_quotable_statements(
        self,
        content: str,
        keyword: str,
        target_queries: list[str],
    ) -> list[str]:
        """创建可引用语句"""
        statements = []

        # 从内容中提取关键句子
        sentences = content.split(". ")
        for sentence in sentences:
            if len(sentence) > 20 and keyword.lower() in sentence.lower():
                # 统计数据
                has_number = any(char.isdigit() for char in sentence)
                has_percentage = "%" in sentence or "%" in sentence
                has_year = any(char.isdigit() for char in sentence if "20" in char or "21" in char or "22" in char or "23" in char or "24" in char or "25" in char or "26" in char

                if has_number or has_percentage or has_year:
                    statements.append(f'"{sentence.strip()}"')

        return statements[:5]  # 限制数量

    def _add_definitions(self, content: str, keyword: str) -> list[str]:
        """建议添加定义"""
        definitions = []

        # 检查关键词是否有明确定义
        patterns = [
            f"{keyword} is",
            f"{keyword} refers to",
            f"{keyword} means that",
            f"What is {keyword}",
        ]

        for pattern in patterns:
            if pattern not in content:
                definitions.append(f"添加定义: '{pattern}'")

        return definitions[:3]

    def _add_authority_signals(self, content: str) -> list[str]:
        """建议添加权威信号"""
        signals = []

        # 检查是否有引文
        if "according to" not in content.lower() and "research shows" not in content.lower():
            signals.append("添加引用来源 (According to..., Research shows...)")

        # 检查是否有专家观点
        if not re.findall(r'(expert|specialist|CEO|founder)\s+(said|notes?|believes)', content, re.IGNORE):
                pass
            else:
                signals.append("添加专家引用")

        return signals[:2]

    def _summarize_changes(self, analysis: dict) -> list[str]:
        """总结优化变更"""
        changes = []

        if analysis.get("clear_definitions", 0) == 0:
            changes.append("添加了清晰定义")
        if analysis.get("quotable_statements", 0) == 0:
            changes.append("添加了可引用语句")
        if analysis.get("source_citations", 0) == 0:
            changes.append("添加了来源引用")
        if not analysis.get("qa_format"):
            changes.append("建议添加 Q&A 格式")

        if not analysis.get("authority_signals"):
            changes.append("建议添加权威信号")

        return changes

    def _calculate_scores(self, before: dict, after: dict) -> tuple[float, float]:
        """计算优化前后分数"""
        scores = []
        for key in ["clear_definitions", "quotable_statements", "factual_density",
                     "source_citations", "qa_format", "authority_signals"]:
            before_score = before.get(key, 0)
            after_score = after.get(key, 0)
            improvement = after_score - before_score
            scores.append((key, before_score, after_score, improvement))

        return scores
