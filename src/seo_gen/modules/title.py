"""
标题生成模块

基于 SERP 分析生成 SEO 优化标题
"""

from typing import Any, Optional

from loguru import logger

from seo_gen.modules.llm import LLMClient


class TitleGenerator:
    """基于 SERP 分析生成 SEO 优化标题"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """初始化标题生成器"""
        self.llm_client = llm_client

    async def generate_titles(
        self,
        keyword: str,
        serp_data: dict[str, Any],
        count: int = 5,
    ) -> list[dict[str, Any]]:
        """
        生成多个候选标题

        Args:
            keyword: 关键词
            serp_data: SERP 分析数据
            count: 生成数量

        Returns:
            候选标题列表 [{"title": "...", "score": 85, "reason": "..."}, ...]
        """
        if not self.llm_client:
            raise ValueError("LLM client not configured")

        # 提取 SERP 中的现有标题
        competing_titles = []
        for result in serp_data.get("searchResults", []):
            title = result.get("title", "")
            if title:
                competing_titles.append(title)

        messages = [
            {
                "role": "system",
                "content": """You are an SEO expert specializing in title optimization.

Your task is to generate compelling, SEO-optimized titles based on:
- Target keyword
- Search intent
- Competing titles from SERP

TITLE OPTIMIZATION PRINCIPLES:
- Include the target keyword naturally
- Match search intent (informational/commercial/transactional)
- Be unique compared to competitors
- Use power words: Ultimate, Complete, Guide, Tips, Strategies
- **FLEXIBLE year usage**: Include year (2026) ONLY when it adds value (e.g., trends, statistics, updates)
- **DO NOT force year into every title** - use it naturally based on keyword type:
  - ✅ Use year for: trends, statistics, updates, "best of", comparisons, reviews
  - ❌ Skip year for: evergreen guides, how-to, definitions, concepts, processes
- Examples WITH year: "Best Dropshipping Suppliers 2026", "E-commerce Trends in 2026"
- Examples WITHOUT year: "Complete Guide to Dropshipping", "How to Start an Online Store"
- Optimal length: 50-60 characters
- Create curiosity while remaining accurate

OUTPUT FORMAT (JSON):
{
  "titles": [
    {
      "title": "Proposed title here",
      "score": 85,
      "reasoning": "Brief explanation of why this title works"
    }
  ]
}

Scoring criteria (0-100):
- Keyword inclusion (20 points)
- Intent match (20 points)
- Uniqueness (20 points)
- Click appeal (20 points)
- Length optimization (20 points)"""
            },
            {
                "role": "user",
                "content": f"""Generate {count} SEO-optimized titles for:

Keyword: {keyword}
Search Intent: {serp_data.get('searchIntent', 'informational')}
Primary Intent: {serp_data.get('primaryIntent', 'share')}

Competing Titles from SERP:
{chr(10).join(f"- {t}" for t in competing_titles[:10])}

Requirements:
1. Each title must include the keyword naturally
2. Match the search intent
3. Be different from competing titles
4. Target 50-60 characters
5. Use compelling, click-worthy language
6. **IMPORTANT: Include year 2026 ONLY when appropriate** (trends, stats, "best of" lists - NOT for evergreen guides)"""
            }
        ]

        result = await self.llm_client.chat_json(messages, temperature=0.7)
        titles = result.get("titles", [])
        logger.info(f"Generated {len(titles)} title candidates")
        return titles

    async def select_best_title(
        self,
        titles: list[dict[str, Any]],
        serp_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        从候选标题中选择最佳标题

        Args:
            titles: 候选标题列表
            serp_data: SERP 分析数据

        Returns:
            最佳标题数据
        """
        if not titles:
            return {"title": "", "score": 0, "reasoning": "No titles available"}

        # 简单选择：返回得分最高的
        best = max(titles, key=lambda x: x.get("score", 0))
        logger.info(f"Selected best title: {best.get('title')} (score: {best.get('score')})")
        return best


# Global singleton
_title_generator: Optional[TitleGenerator] = None


def get_title_generator() -> TitleGenerator:
    """获取全局标题生成器单例"""
    global _title_generator
    if _title_generator is None:
        _title_generator = TitleGenerator()
    return _title_generator
