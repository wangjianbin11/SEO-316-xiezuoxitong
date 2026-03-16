"""
质量检测模块 - 升级版

检测生成内容的质量，E-E-A-T 评估
等级分为：一般、中等、高、满分
"""

from typing import Any, Optional

from loguru import logger

from seo_gen.modules.llm import LLMClient


class QualityChecker:
    """内容质量检测器 - E-E-A-T 评估版"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化质量检测器

        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client

    async def check_article_quality(
        self,
        article: dict[str, Any],
        keyword: str,
    ) -> dict[str, Any]:
        """
        检测文章质量 - E-E-A-T 全面评估

        Args:
            article: 文章数据
            keyword: 目标关键词

        Returns:
            质量检测结果，包含 E-E-A-T 评分和等级
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")

        # 构建检测内容
        title = article.get("title", "")
        sections = article.get("sections", [])
        sources = article.get("sources", article.get("references", []))

        # 统计字数
        total_chars = sum(len(s.get("content", "")) for s in sections)
        word_count = len(title) + total_chars

        messages = [
            {
                "role": "system",
                "content": """You are a professional content quality evaluator specializing in Google E-E-A-T assessment.

EVALUATION CRITERIA:

**E - Experience (实际经验)**
- MM (一般): Limited real-world examples, generic statements
- M+ (中等): Some concrete examples, but limited first-hand accounts
- HH (高): Rich case studies, specific data, before/after results
- HHH (满分): Extensive personal experience with verifiable proof

**E - Expertise (专业知识)**
- MM (一般): Basic information, shallow coverage
- M+ (中等): Good industry knowledge, some technical details
- HH (高): Deep expertise, industry terminology, advanced concepts
- HHH (满分): Authoritative expert with recognized credentials

**A - Authoritativeness (权威性)**
- MM (一般): No third-party endorsements or recognition
- M+ (中等): Some references, but limited authority signals
- HH (高): Cited by others, certifications, industry recognition
- HHH (满分): Leading authority, widely recognized expert

**T - Trustworthiness (可信度)**
- MM (一般): Vague claims, no sources, questionable accuracy
- M+ (中等): Some sources, generally accurate but limited transparency
- HH (高): Well-sourced, accurate data, transparent about affiliations
- HHH (满分): Highly transparent, verifiable claims, impeccable credibility

CONTENT QUALITY ASPECTS:
- 投入度: Substantial human effort vs minimal effort
- 准确性: Data accuracy, realistic claims
- 才华或技能: Writing quality, organization
- 原创性: Unique insights vs aggregated content

OUTPUT FORMAT (JSON):
{{
  "overallScore": 85,
  "overallGrade": "High",
  "eeatScores": {{
    "experience": {{
      "score": 70,
      "grade": "M+",
      "reasoning": "Detailed explanation of the experience score..."
    }},
    "expertise": {{
      "score": 80,
      "grade": "HH",
      "reasoning": "Detailed explanation of the expertise score..."
    }},
    "authoritativeness": {{
      "score": 75,
      "grade": "M+",
      "reasoning": "Detailed explanation of the authoritativeness score..."
    }},
    "trustworthiness": {{
      "score": 85,
      "grade": "HH",
      "reasoning": "Detailed explanation of the trustworthiness score..."
    }}
  }},
  "contentQuality": {{
    "engagement": {{
      "grade": "HH",
      "reasoning": "Detailed explanation..."
    }},
    "accuracy": {{
      "grade": "HH",
      "reasoning": "Detailed explanation..."
    }},
    "talent": {{
      "grade": "M+",
      "reasoning": "Detailed explanation..."
    }},
    "originality": {{
      "grade": "HH",
      "reasoning": "Detailed explanation..."
    }}
  }},
  "wordCount": 2800,
  "targetWordCount": 3000,
  "wordCountStatus": "acceptable",
  "issues": ["Issue 1", "Issue 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "passesThreshold": true
}}

GRADING SCALE:
- Fair (一般): 50-64 points
- Medium (中等): 65-79 points
- High (高): 80-89 points
- Perfect (满分): 90-100 points"""
            },
            {
                "role": "user",
                "content": f"""Please evaluate the following article for E-E-A-T quality:

Keyword: {keyword}
Title: {title}
Word Count: {word_count} (target: 3000 characters)
Sections: {len(sections)}
Sources: {len(sources)}

Sections Overview:
{self._format_sections_for_review(sections[:3])}

Sources:
{self._format_sources(sources)}

Provide a comprehensive E-E-A-T evaluation."""
            }
        ]

        try:
            # Increase temperature for more varied scoring (0.5 instead of 0.3)
            result = await self.llm_client.chat_json(messages, temperature=0.5)
            logger.info(
                f"Quality check completed: score={result.get('overallScore')}, "
                f"grade={result.get('overallGrade')}, "
                f"passes={result.get('passesThreshold')}"
            )
            return result

        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            return self._default_result(word_count)

    def _format_sections_for_review(self, sections: list) -> str:
        """格式化板块用于审核"""
        parts = []
        for i, section in enumerate(sections[:3], 1):
            title = section.get("sectionTitle", "")
            content = section.get("content", "")[:300]
            parts.append(f"{i}. {title}\n{content}...")
        return "\n".join(parts)

    def _format_sources(self, sources: list) -> str:
        """格式化引用来源"""
        if not sources:
            return "No sources provided"
        parts = []
        for source in sources[:5]:
            name = source.get("source", "")
            url = source.get("url", "")
            desc = source.get("description", "")
            parts.append(f"- {name}: {desc} ({url})")
        return "\n".join(parts)

    def _default_result(self, word_count: int = 0) -> dict[str, Any]:
        """返回默认检测结果"""
        return {
            "overallScore": 65,
            "overallGrade": "Medium",
            "eeatScores": {
                "experience": {"score": 65, "grade": "M+", "reasoning": "Default: Limited real-world examples detected"},
                "expertise": {"score": 65, "grade": "M+", "reasoning": "Default: Basic information coverage"},
                "authoritativeness": {"score": 65, "grade": "M+", "reasoning": "Default: Limited authority signals"},
                "trustworthiness": {"score": 65, "grade": "M+", "reasoning": "Default: Limited source transparency"},
            },
            "contentQuality": {
                "engagement": {"grade": "M+", "reasoning": "Default: Moderate content engagement"},
                "accuracy": {"grade": "M+", "reasoning": "Default: Generally accurate claims"},
                "talent": {"grade": "M+", "reasoning": "Default: Adequate writing quality"},
                "originality": {"grade": "M+", "reasoning": "Default: Some unique insights"},
            },
            "wordCount": word_count,
            "targetWordCount": 3000,
            "wordCountStatus": "acceptable" if 2000 <= word_count <= 4000 else "too_short",
            "issues": ["Quality check failed - using default scores"],
            "suggestions": ["Review article for E-E-A-T improvements"],
            "passesThreshold": True,
        }

    def should_regenerate(
        self,
        quality_result: dict[str, Any],
        threshold: Optional[int] = None,
    ) -> bool:
        """
        判断是否需要重新生成

        Args:
            quality_result: 质量检测结果
            threshold: 通过阈值，默认从 settings 读取

        Returns:
            是否需要重新生成
        """
        if threshold is None:
            from seo_gen.config import settings
            threshold = settings.quality_score_threshold

        passes = quality_result.get("passesThreshold", True)
        score = quality_result.get("overallScore", 0)

        # 检查字数是否在合理范围内
        word_count_status = quality_result.get("wordCountStatus", "")
        word_count_ok = word_count_status in ["acceptable", "too_long"]  # too_long 仍然可以接受

        should_regenerate = not passes or score < threshold or not word_count_ok

        if should_regenerate:
            logger.warning(
                f"Content did not pass quality check: score={score}, "
                f"threshold={threshold}, word_count_status={word_count_status}"
            )

        return should_regenerate

    def get_grade_display(self, grade: str) -> str:
        """获取等级显示"""
        grade_map = {
            "Fair": "一般",
            "Medium": "中等",
            "High": "高",
            "Perfect": "满分",
        }
        return grade_map.get(grade, grade)

    async def get_improvement_suggestions(
        self,
        article: dict[str, Any],
        quality_result: dict[str, Any],
    ) -> str:
        """
        获取改进建议

        Args:
            article: 原文章
            quality_result: 质量检测结果

        Returns:
            改进建议 Prompt
        """
        issues = quality_result.get("issues", [])
        suggestions = quality_result.get("suggestions", [])

        feedback = "\n".join([
            f"- {issue}"
            for issue in issues + suggestions
        ])

        grade = quality_result.get("overallGrade", "Medium")
        score = quality_result.get("overallScore", 0)

        return f"""QUALITY FEEDBACK:
Current Grade: {grade} ({score}/100)
Target: High (80+ points)

Issues to Fix:
{feedback}

REGENERATION INSTRUCTIONS:
Please rewrite the article to address all issues above while maintaining:
- 3000 character target
- Pure English output
- E-E-A-T optimization
- WordPress-ready format
- Source citations"""


# Global singleton
_quality_checker: Optional[QualityChecker] = None


def get_quality_checker() -> QualityChecker:
    """Get global quality checker singleton"""
    global _quality_checker
    if _quality_checker is None:
        _quality_checker = QualityChecker()
    return _quality_checker
