"""GEO Content Optimizer Skill"""
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GEOOptimizationResult:
    geo_score: float = 0.0
    quotable_statements: list = field(default_factory=list)
    definitions_added: list = field(default_factory=list)
    authority_signals: list = field(default_factory=list)
    structural_improvements: list = field(default_factory=list)
    before_after_scores: dict = field(default_factory=dict)
    changes_made: list = field(default_factory=list)


class GEOContentOptimizer:
    GEO_FIRST_ITEMS = {
        "C02": {"name": "Direct Answer", "priority": 1, "description": "前150字内直接回答"},
        "C09": {"name": "Structured FAQ", "priority": 2, "description": "结构化FAQ与Schema"},
        "O03": {"name": "Data in Tables", "priority": 3, "description": "数据放在表格中"},
        "O05": {"name": "JSON-LD Schema", "priority": 4, "description": "结构化数据标记"},
        "E01": {"name": "Original Data", "priority": 5, "description": "原创一手数据"},
        "O02": {"name": "Summary Box", "priority": 6, "description": "关键要点总结框"},
    }

    def get_geo_first_checklist(self) -> list:
        return [
            {"id": k, "name": v["name"], "description": v["description"], "priority": v["priority"]}
            for k, v in self.GEO_FIRST_ITEMS.items()
        ]

    def optimize_content(self, content: str, keyword: str, target_queries: list = None) -> GEOOptimizationResult:
        result = GEOOptimizationResult()
        analysis = self._analyze_content(content)
        result.quotable_statements = self._create_quotable_statements(content, keyword)
        result.definitions_added = self._add_definitions(content, keyword)
        result.authority_signals = self._add_authority_signals(content)
        result.structural_improvements = self._improve_structure(content)
        result.geo_score = analysis.get("overall_score", 0)
        result.changes_made = self._summarize_changes(analysis)
        return result

    def _analyze_content(self, content: str) -> dict:
        raw = {
            "clear_definitions": float(self._count_clear_definitions(content)),
            "quotable_statements": float(self._count_quotable(content)),
            "factual_density": self._calculate_factual_density(content),
            "source_citations": float(content.count("http")),
            "qa_format": 1.0 if self._has_qa_format(content) else 0.0,
            "authority_signals": float(self._count_authority_signals(content)),
        }
        values = list(raw.values())
        raw["overall_score"] = sum(values) / len(values) if values else 0.0
        return raw

    def _count_clear_definitions(self, content: str) -> int:
        return sum(1 for p in [" is a ", " refers to ", " means that "] if p in content)

    def _count_quotable(self, content: str) -> int:
        return len(re.findall(r'"([^"]{20,})"', content))

    def _calculate_factual_density(self, content: str) -> float:
        return min(len(re.findall(r'\d+[\d,.]*%?', content)) / 10, 1.0)

    def _count_authority_signals(self, content: str) -> int:
        lower = content.lower()
        return sum(1 for p in ["according to", "research", "expert"] if p in lower)

    def _has_qa_format(self, content: str) -> bool:
        return "?" in content and any(line.strip().endswith("?") for line in content.split("\n"))

    def _improve_structure(self, content: str) -> list:
        improvements = []
        if "|" not in content and "<table" not in content:
            improvements.append("添加比较表格")
        if "Key Takeaways" not in content:
            improvements.append("添加Key Takeaways总结框")
        return improvements

    def _create_quotable_statements(self, content: str, keyword: str) -> list:
        results = []
        for sentence in re.split(r'(?<=[.!?])\s+', content):
            if len(sentence) > 20 and keyword.lower() in sentence.lower() and re.search(r'\d+', sentence):
                results.append(f'"{sentence.strip()}"')
        return results[:5]

    def _add_definitions(self, content: str, keyword: str) -> list:
        return [f"建议添加: '{p}'" for p in [f"{keyword} is", f"{keyword} refers to", f"What is {keyword}"]
                if p.lower() not in content.lower()][:3]

    def _add_authority_signals(self, content: str) -> list:
        return ["添加引用来源"] if "according to" not in content.lower() else []

    def _summarize_changes(self, analysis: dict) -> list:
        changes = []
        if analysis.get("clear_definitions", 0) == 0:
            changes.append("建议添加清晰定义")
        if analysis.get("source_citations", 0) == 0:
            changes.append("建议添加来源引用")
        return changes


_geo_optimizer_instance = None

def get_geo_content_optimizer() -> GEOContentOptimizer:
    global _geo_optimizer_instance
    if _geo_optimizer_instance is None:
        _geo_optimizer_instance = GEOContentOptimizer()
    return _geo_optimizer_instance
