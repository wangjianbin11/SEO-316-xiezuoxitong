"""
SERP 分析模块

分析 Google 搜索结果、PAA、搜索意图等
"""

from typing import List, Dict, Any, Optional

import httpx
from loguru import logger

from seo_gen.config import settings
from seo_gen.modules.llm import LLMClient


class SERPAnalyzer:
    """Google SERP 分析器"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化 SERP 分析器

        Args:
            llm_client: LLM 客户端，默认使用全局单例
        """
        self.llm_client = llm_client
        self.api_key = settings.google_search_api_key
        self.engine_id = settings.google_search_engine_id

        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def _search_google(self, query: str, num: int = 10, start: int = 1) -> List[Dict[str, Any]]:
        """
        调用 Google Custom Search API

        Args:
            query: 搜索关键词
            num: 每次返回结果数量(最大10)
            start: 起始位置(用于分页)

        Returns:
            搜索结果列表
        """
        if not self.api_key or not self.engine_id:
            logger.warning("Google Search API 未配置，使用模拟数据")
            return self._mock_search_results(query)

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": query,
            "num": min(num, 10),  # Google API 限制每次最多10条
            "start": start,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            logger.info(f"Google 搜索: {query}, start={start}, 返回 {len(items)} 条结果")
            return items

        except Exception as e:
            logger.error(f"Google 搜索失败 (start={start}): {e}")
            return []

    async def _search_google_multiple_pages(self, query: str, total_results: int = 100) -> List[Dict[str, Any]]:
        """
        获取多页 Google 搜索结果

        Args:
            query: 搜索关键词
            total_results: 总共需要的结果数量(默认100条,即10页)

        Returns:
            所有页面的搜索结果列表
        """
        all_results = []
        pages = (total_results + 9) // 10  # 向上取整,计算需要的页数

        logger.info(f"开始获取 {pages} 页搜索结果 (共 {total_results} 条)")

        for page in range(pages):
            start = page * 10 + 1
            results = await self._search_google(query, num=10, start=start)

            if not results:
                logger.warning(f"第 {page + 1} 页没有返回结果,停止搜索")
                break

            all_results.extend(results)
            logger.info(f"已获取 {len(all_results)}/{total_results} 条结果")

            # 如果已经获取足够的结果,提前退出
            if len(all_results) >= total_results:
                break

        logger.info(f"搜索完成: {query}, 共获取 {len(all_results)} 条结果")
        return all_results[:total_results]  # 确保不超过请求的数量

    def _mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """返回模拟搜索结果（API 未配置时）"""
        return [
            {
                "title": f"Search result for {query}",
                "link": f"https://example.com/{query.replace(' ', '-')}",
                "snippet": f"Example snippet for {query}...",
            }
            for _ in range(3)
        ]

    async def analyze_search_intent(
        self,
        keyword: str,
        search_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        使用 AI 分析搜索意图

        Args:
            keyword: 关键词
            search_results: 搜索结果列表

        Returns:
            包含搜索意图、PAA 问题等信息的字典
        """
        if not self.llm_client:
            raise ValueError("LLM 客户端未配置")

        # 构建搜索结果摘要 - 使用更多结果进行分析
        results_summary = "\n".join([
            f"{i+1}. {r.get('title', '')}: {r.get('snippet', '')}"
            for i, r in enumerate(search_results[:20])  # 使用前20条结果
        ])

        messages = [
            {
                "role": "system",
                "content": """你是一个专业的 SEO 分析师。分析给定的关键词和搜索结果，返回 JSON 格式的分析报告。

返回格式:
{
  "searchIntent": "informational|navigational|transactional|commercial",
  "primaryIntent": "share|qa|pillar",
  "targetAudience": "目标受众描述",
  "paaQuestions": ["问题1", "问题2", "..."],
  "keyTopics": ["主题1", "主题2", "..."],
  "competitorAnalysis": "竞争对手分析摘要",
  "contentOpportunities": "内容机会建议"
}"""
            },
            {
                "role": "user",
                "content": f"""请分析以下关键词和搜索结果:

关键词: {keyword}

搜索结果 (共 {len(search_results)} 条):
{results_summary}

请基于这些搜索结果提供详细的 SEO 分析,重点关注:
1. 搜索意图的准确判断
2. 竞争对手的内容策略
3. 用户最关心的问题
4. 内容创作的机会点"""
            }
        ]

        try:
            result = await self.llm_client.chat_json(messages, temperature=0.3)
            logger.info(f"搜索意图分析完成: {keyword}, intent={result.get('searchIntent')}, 分析了 {len(search_results)} 条结果")
            return result

        except Exception as e:
            logger.error(f"搜索意图分析失败: {e}")
            return self._default_analysis(keyword)

    def _default_analysis(self, keyword: str) -> Dict[str, Any]:
        """返回默认分析结果"""
        return {
            "searchIntent": "informational",
            "primaryIntent": "share",
            "targetAudience": "跨境电商从业者",
            "paaQuestions": [],
            "keyTopics": [keyword],
            "competitorAnalysis": "未获取到数据",
            "contentOpportunities": "基于关键词创建有价值的内容",
        }

    async def analyze(self, keyword: str, total_results: int = 30) -> Dict[str, Any]:
        """
        完整的 SERP 分析流程

        Args:
            keyword: 要分析的关键词
            total_results: 需要获取的搜索结果总数(默认30条,即3页)

        Returns:
            完整的分析结果
        """
        logger.info(f"开始 SERP 分析: {keyword}, 获取 {total_results} 条结果")

        # 1. 获取多页搜索结果
        search_results = await self._search_google_multiple_pages(keyword, total_results)

        # 2. AI 分析搜索意图 (使用前20条结果进行分析,提高质量)
        analysis = await self.analyze_search_intent(keyword, search_results[:20])

        # 组合结果
        return {
            "keyword": keyword,
            "searchResults": search_results,
            "serpAnalysis": analysis,
            "totalResults": len(search_results),
        }

    def sync_analyze(self, keyword: str) -> Dict[str, Any]:
        """
        同步版本的分析方法
        """
        import asyncio

        return asyncio.run(self.analyze(keyword))


# 全局单例
_serp_analyzer: Optional[SERPAnalyzer] = None


def get_serp_analyzer() -> SERPAnalyzer:
    """获取全局 SERP 分析器单例"""
    global _serp_analyzer
    if _serp_analyzer is None:
        _serp_analyzer = SERPAnalyzer()
    return _serp_analyzer
