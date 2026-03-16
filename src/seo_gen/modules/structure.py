"""
文章结构分析模块 v2.0

分析竞品文章的结构模式
- 支持 6-9 个章节的动态调整
- 根据关键词复杂度智能推荐章节数量
- 更自然的文章结构，避免固定模板感
"""

from typing import Any, Optional

from loguru import logger

from seo_gen.modules.llm import LLMClient


class StructureAnalyzer:
    """分析竞品文章的结构模式 - 升级版"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """初始化结构分析器"""
        self.llm_client = llm_client

    def _estimate_section_count(self, keyword: str, search_results: list[dict]) -> int:
        """
        根据关键词复杂度和搜索结果估算合适的章节数量

        逻辑：
        - 简单/单一主题关键词 → 6 个章节
        - 中等复杂度关键词 → 7 个章节
        - 复杂/多维度关键词 → 8-9 个章节

        判断标准：
        - 关键词长度和复杂度
        - 竞争对手文章的平均章节数
        - 搜索意图的多样性
        """
        base_count = 7  # 默认 7 个章节

        # 分析关键词复杂度
        keyword_words = len(keyword.split())

        # 关键词越长越复杂，需要更多章节
        if keyword_words <= 2:
            complexity_adjustment = -1  # 简单关键词
        elif keyword_words <= 4:
            complexity_adjustment = 0   # 中等关键词
        else:
            complexity_adjustment = 1   # 复杂关键词

        # 分析竞争对手标题结构
        competitor_sections = 0
        for result in search_results[:5]:
            title = result.get("title", "")
            # 检查是否有数字列表型标题（如 "12 Best..."）
            if any(char.isdigit() for char in title.split()[0] if title.split()):
                try:
                    num = int(''.join(filter(str.isdigit, title.split()[0])))
                    if 5 <= num <= 15:
                        competitor_sections = max(competitor_sections, num // 2)
                except:
                    pass

        # 综合判断
        estimated = base_count + complexity_adjustment

        # 如果竞争对手有更多章节，适当增加
        if competitor_sections > estimated:
            estimated = min(competitor_sections, 9)

        # 确保在 6-9 范围内
        return max(6, min(9, estimated))

    async def analyze_article_structure(
        self,
        search_results: list[dict[str, Any]],
        keyword: str,
    ) -> dict[str, Any]:
        """
        分析竞品文章结构 - 支持动态章节数量

        Args:
            search_results: SERP 搜索结果
            keyword: 目标关键词

        Returns:
            结构分析结果（包含推荐的章节数量）
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")

        # 估算合适的章节数量
        recommended_section_count = self._estimate_section_count(keyword, search_results)
        logger.info(f"Estimated optimal section count: {recommended_section_count}")

        # 提取标题和片段
        content_samples = []
        for result in search_results[:10]:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("url", "")
            content_samples.append({
                "title": title,
                "snippet": snippet,
                "url": url,
            })

        messages = [
            {
                "role": "system",
                "content": f"""You are an expert content analyst specializing in SEO article structure analysis.

Your task is to analyze search results and create a NATURAL, HUMAN-LIKE article structure.

IMPORTANT - DYNAMIC SECTION COUNT:
- Analyze the keyword complexity and topic depth
- Recommend {recommended_section_count} main sections (H2 headings)
- The exact number should feel natural, not forced
- Some topics need 6 sections, others need 8 or 9 - let the content decide

SECTION COUNT GUIDELINES:
- 6 sections: Simple, focused topics (e.g., "what is X", "how to do X")
- 7 sections: Standard guides with multiple aspects
- 8 sections: Comprehensive guides with comparisons, case studies
- 9 sections: Deep dives covering all angles, including advanced topics

NATURAL STRUCTURE PRINCIPLES:
- Avoid rigid templates - vary section titles naturally
- Include sections that competitors miss (content gaps)
- Match the topic's natural information hierarchy
- Some sections can be longer, others shorter - follow the content's lead

OUTPUT FORMAT (JSON):
{{
  "commonSections": [
    {{"title": "Section Name", "frequency": 0.8, "description": "What this section covers"}}
  ],
  "sectionPatterns": {{
    "introduction": {{
      "frequency": 0.95,
      "typicalTitles": ["Introduction", "Overview", "What is..."],
      "keyPoints": ["Definition", "Importance", "Brief history"]
    }}
  }},
  "recommendedStructure": [
    {{
      "order": 1,
      "sectionTitle": "Natural H2 Title (not template-like)",
      "description": "What this section should cover",
      "keyPoints": ["Point 1", "Point 2"],
      "wordCount": 350,
      "importance": "high/medium/low"
    }}
  ],
  "contentGaps": [
    {{"topic": "Missing topic", "opportunity": "Why this is valuable"}}
  ],
  "toneAndStyle": {{
    "tone": "professional/casual",
    "perspective": "first-person/third-person",
    "complexity": "beginner/intermediate/advanced"
  }},
  "recommendedSectionCount": {recommended_section_count},
  "reasoning": "Brief explanation of why this structure works for this specific keyword"
}}

WORD COUNT DISTRIBUTION:
- Total target: 2500-3000 words
- Each section: 300-400 words (varies naturally)
- Introduction: 150-200 words
- Longer sections for core concepts, shorter for tips/summaries"""
            },
            {
                "role": "user",
                "content": f"""Analyze the content structure for articles about: "{keyword}"

Target Section Count: {recommended_section_count} sections (can adjust ±1 if needed)

Search Results:
{self._format_search_results(content_samples)}

Please provide:
1. Common section patterns from competitors
2. Content gap opportunities
3. A NATURAL {recommended_section_count}-section structure (avoid template-like titles)
4. Word count distribution that feels organic, not forced
5. Explain why this structure fits this specific keyword

IMPORTANT: The structure should feel like a real expert would organize it, not a formula."""
            }
        ]

        result = await self.llm_client.chat_json(messages, temperature=0.5)

        # 确保结果中包含推荐的章节数量
        if "recommendedSectionCount" not in result:
            result["recommendedSectionCount"] = recommended_section_count

        sections_count = len(result.get('recommendedStructure', []))
        logger.info(f"Structure analysis completed: {sections_count} sections recommended (target was {recommended_section_count})")
        return result

    def _format_search_results(self, results: list[dict]) -> str:
        """格式化搜索结果"""
        lines = []
        for i, r in enumerate(results[:10], 1):
            lines.append(f"{i}. {r.get('title', '')}")
            lines.append(f"   {r.get('snippet', '')[:200]}...")
            lines.append(f"   URL: {r.get('url', '')}")
            lines.append("")
        return "\n".join(lines)


# Global singleton
_structure_analyzer: Optional[StructureAnalyzer] = None


def get_structure_analyzer() -> StructureAnalyzer:
    """获取全局结构分析器单例"""
    global _structure_analyzer
    if _structure_analyzer is None:
        _structure_analyzer = StructureAnalyzer()
    return _structure_analyzer
