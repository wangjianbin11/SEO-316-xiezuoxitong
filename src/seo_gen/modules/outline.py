"""
大纲生成模块 v2.0

基于结构分析生成文章大纲
- 支持 6-9 个章节的动态生成
- 根据关键词复杂度智能调整
- 更自然的大纲结构，避免固定模板
"""

from typing import Any, Optional

from loguru import logger

from seo_gen.modules.llm import LLMClient


class OutlineGenerator:
    """基于结构分析生成文章大纲 - 升级版"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """初始化大纲生成器"""
        self.llm_client = llm_client

    async def generate_outline(
        self,
        keyword: str,
        title: str,
        structure_analysis: dict[str, Any],
        serp_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        生成文章大纲（支持动态章节数量）

        Args:
            keyword: 关键词
            title: 文章标题
            structure_analysis: 结构分析结果
            serp_data: SERP 数据

        Returns:
            文章大纲
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")

        recommended_structure = structure_analysis.get("recommendedStructure", [])
        content_gaps = structure_analysis.get("contentGaps", [])

        # 获取推荐的章节数量（从结构分析中获取）
        target_section_count = structure_analysis.get("recommendedSectionCount", len(recommended_structure))
        if target_section_count < 6:
            target_section_count = 6
        elif target_section_count > 9:
            target_section_count = 9

        # 计算每个章节的目标字数（总字数 2500-3000 分配到各章节）
        total_words = 2800  # 目标总字数
        intro_words = 200    # 引言字数
        section_words = (total_words - intro_words) // target_section_count

        messages = [
            {
                "role": "system",
                "content": f"""You are Janson, CEO of ASG dropshipping, an expert content strategist.

Create a detailed article outline based on:
- Target keyword and title
- SERP structure analysis
- Content gap opportunities
- Dynamic section count (NOT fixed at 6)

IMPORTANT - DYNAMIC SECTION COUNT:
- Target: {target_section_count} main sections (H2 headings)
- Can be 6-9 sections depending on topic complexity
- Let the content naturally determine the structure
- Avoid forcing a template

SECTION COUNT GUIDELINES:
- 6 sections: Focused topics with clear scope
- 7 sections: Standard comprehensive guides
- 8 sections: Topics with multiple aspects or comparisons
- 9 sections: Deep dives covering all angles

OUTLINE STRUCTURE:
Each section should include:
- Section title (H2) - Natural, not template-like
- Subsections (H3) - 2-3 per section
- Key points to cover
- Target word count (varies by section importance)
- Data/statistics to include

WORD COUNT TARGETS:
- Total article: 2500-3000 words
- Introduction: 150-200 words
- Each section: 300-400 words (varies naturally)
- Core sections can be longer, tips/summaries can be shorter

OUTPUT FORMAT (JSON):
{{
  "title": "Article Title",
  "estimatedWordCount": {total_words},
  "actualSectionCount": {target_section_count},
  "sections": [
    {{
      "sectionIndex": 1,
      "sectionTitle": "Natural H2 Title (not template-like)",
      "subsections": [
        "H3 Subsection 1",
        "H3 Subsection 2"
      ],
      "keyPoints": [
        "Main point 1",
        "Main point 2"
      ],
      "dataToInclude": ["Stat or data point 1", "Stat or data point 2"],
      "targetWordCount": 350,
      "importance": "high/medium/low"
    }}
  ],
  "uniqueAngle": "What makes this article different",
  "targetAudience": "Who this article is for",
  "structureReasoning": "Why this specific structure works for this keyword"
}}

SECTION TITLE GUIDELINES - AVOID TEMPLATES:
❌ Don't use: "Understanding X", "Why X Matters", "Implementation Strategies"
✅ Do use: Natural titles that fit the specific topic
✅ Examples for "dropshipping quality control":
   - "The Real Cost of Bad Quality (It's Higher Than You Think)"
   - "3 Pre-shipment Checks That Save Thousands in Returns"
   - "How Top Sellers Handle QC Without Visiting Factories"

NATURAL STRUCTURE PRINCIPLES:
- Section order should follow reader's learning journey
- More important topics get more words
- Some topics naturally combine, others need separation
- Follow the topic's inherent logic, not a formula

GUIDELINES:
- {target_section_count} main sections total
- Each section: 300-400 words (varies by importance)
- Include specific data points and statistics
- Address content gaps identified
- Maintain E-E-A-T principles
- Vary section titles naturally - avoid template phrases"""
            },
            {
                "role": "user",
                "content": f"""Generate a detailed article outline for:

Keyword: {keyword}
Title: {title}
Target Section Count: {target_section_count} sections (adjust ±1 if topic requires)
Total Word Target: {total_words} words
Search Intent: {serp_data.get('searchIntent', 'informational')}

Structure Analysis Insights:
- Recommended Sections: {len(recommended_structure)}
- Target Section Count: {target_section_count}
- Content Gaps: {len(content_gaps)}

Recommended Structure from Analysis:
{self._format_recommended_structure(recommended_structure)}

Content Gap Opportunities:
{self._format_content_gaps(content_gaps)}

Create a comprehensive {target_section_count}-section outline that:
1. Covers the recommended topics naturally
2. Addresses the content gaps
3. Includes specific data points to reference
4. Uses NATURAL section titles (not template phrases)
5. Varies word count by section importance
6. Maintains Janson's expert, first-person perspective

IMPORTANT: The outline should feel like a real expert organized it, not a template."""
            }
        ]

        result = await self.llm_client.chat_json(messages, temperature=0.7)
        sections = result.get('sections', [])
        actual_count = len(sections)
        logger.info(f"Outline generated: {actual_count} sections (target was {target_section_count})")
        return result

    def _format_recommended_structure(self, structure: list) -> str:
        """格式化推荐结构"""
        lines = []
        for s in structure[:12]:  # 增加到 12 个，支持更多章节
            title = s.get("sectionTitle", "")
            desc = s.get("description", "")
            lines.append(f"- {title}: {desc}")
        return "\n".join(lines) if lines else "No specific structure recommended"

    def _format_content_gaps(self, gaps: list) -> str:
        """格式化内容缺口"""
        lines = []
        for g in gaps[:10]:
            topic = g.get("topic", "")
            opp = g.get("opportunity", "")
            lines.append(f"- {topic}: {opp}")
        return "\n".join(lines) if lines else "No specific gaps identified"


# Global singleton
_outline_generator: Optional[OutlineGenerator] = None


def get_outline_generator() -> OutlineGenerator:
    """获取全局大纲生成器单例"""
    global _outline_generator
    if _outline_generator is None:
        _outline_generator = OutlineGenerator()
    return _outline_generator
