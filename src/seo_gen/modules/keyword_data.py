"""
真实关键词数据客户端

职责:调用 DataForSEO API 获取真实关键词数据
替代:keyword_analyzer.py 中的 LLM 猜测逻辑
"""

import base64
from dataclasses import dataclass
from typing import Optional, Any

import httpx
from loguru import logger

from seo_gen.config import settings


@dataclass
class KeywordMetrics:
    """关键词指标数据"""
    keyword: str
    monthly_volume: int  # 月均搜索量
    kd_score: float  # 关键词难度 0-100
    cpc: float  # 每次点击成本(美元)
    competition_level: str  # low/medium/high
    serp_features: list[str]  # 存在的SERP特征
    data_source: str  # "dataforseo" 或 "llm_estimate"
    confidence: float  # 数据可信度 0-1


class KeywordDataClient:
    """DataForSEO API 客户端"""

    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self, username: str = None, password: str = None, timeout: float = 30.0):
        """
        初始化客户端

        Args:
            username: DataForSEO 用户名(邮箱), 不传则从config读取
            password: DataForSEO 密码, 不传则从config读取
            timeout: 请求超时时间(秒)
        """
        # 优先使用传入参数,否则从 config 读取
        username = username or getattr(settings, 'dataforseo_username', '')
        password = password or getattr(settings, 'dataforseo_password', '')

        if not username or not password:
            logger.warning("DataForSEO credentials not provided, will use LLM estimates")
            self.enabled = False
            return

        self.enabled = True
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        self.timeout = timeout
        logger.info("DataForSEO client initialized")

    async def get_keyword_metrics(
        self,
        keywords: list[str],
        location_code: int = 2840,  # 2840=US, 2826=UK, 2156=CN
        language_code: str = "en"
    ) -> list[KeywordMetrics]:
        """
        批量获取关键词数据

        DataForSEO 端点:POST /keywords_data/google_ads/search_volume/live
        单次最多1000个关键词

        Args:
            keywords: 关键词列表
            location_code: 地区代码
            language_code: 语言代码

        Returns:
            KeywordMetrics 列表
        """
        if not self.enabled:
            logger.warning("DataForSEO not enabled, using LLM estimates")
            return [self._estimate_from_llm(kw) for kw in keywords]

        # 分批处理(每批最多1000个)
        batch_size = 1000
        all_results = []

        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            try:
                results = await self._fetch_batch(batch, location_code, language_code)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Failed to fetch batch {i//batch_size + 1}: {e}")
                # 失败时使用LLM估算
                all_results.extend([self._estimate_from_llm(kw) for kw in batch])

        return all_results

    async def _fetch_batch(
        self,
        keywords: list[str],
        location_code: int,
        language_code: str
    ) -> list[KeywordMetrics]:
        """获取单批关键词数据"""
        endpoint = f"{self.BASE_URL}/keywords_data/google_ads/search_volume/live"

        payload = [{
            "location_code": location_code,
            "language_code": language_code,
            "keywords": keywords
        }]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        # 解析响应
        results = []
        if data.get("status_code") == 20000:
            tasks = data.get("tasks", [])
            if tasks and tasks[0].get("result"):
                for item in tasks[0]["result"]:
                    keyword = item.get("keyword", "")
                    search_volume = item.get("search_volume", 0)
                    competition = item.get("competition", "UNKNOWN")
                    cpc = item.get("cpc", 0.0)

                    # 计算KD分数(基于竞争度和搜索量)
                    kd_score = self._calculate_kd_score(
                        competition,
                        search_volume,
                        cpc
                    )

                    results.append(KeywordMetrics(
                        keyword=keyword,
                        monthly_volume=search_volume or 0,
                        kd_score=kd_score,
                        cpc=cpc or 0.0,
                        competition_level=self._map_competition(competition),
                        serp_features=[],  # 需要单独API调用
                        data_source="dataforseo",
                        confidence=1.0
                    ))
        else:
            logger.error(f"DataForSEO API error: {data.get('status_message')}")
            raise Exception(f"API error: {data.get('status_message')}")

        return results

    async def get_serp_features(
        self,
        keyword: str,
        location_code: int = 2840
    ) -> dict:
        """
        获取关键词的 SERP 特征

        端点:POST /serp/google/organic/live/advanced
        返回:featured_snippet(bool), paa_box(bool), video_carousel(bool),
              local_pack(bool), image_pack(bool), shopping(bool)

        Args:
            keyword: 关键词
            location_code: 地区代码

        Returns:
            SERP特征字典
        """
        if not self.enabled:
            return {}

        endpoint = f"{self.BASE_URL}/serp/google/organic/live/advanced"

        payload = [{
            "location_code": location_code,
            "language_code": "en",
            "keyword": keyword,
            "depth": 10  # 只获取前10个结果
        }]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            features = {
                "featured_snippet": False,
                "paa_box": False,
                "video_carousel": False,
                "local_pack": False,
                "image_pack": False,
                "shopping": False
            }

            if data.get("status_code") == 20000:
                tasks = data.get("tasks", [])
                if tasks and tasks[0].get("result"):
                    items = tasks[0]["result"][0].get("items", [])
                    for item in items:
                        item_type = item.get("type", "")
                        if item_type == "featured_snippet":
                            features["featured_snippet"] = True
                        elif item_type == "people_also_ask":
                            features["paa_box"] = True
                        elif item_type == "video":
                            features["video_carousel"] = True
                        elif item_type == "local_pack":
                            features["local_pack"] = True
                        elif item_type == "images":
                            features["image_pack"] = True
                        elif item_type == "shopping":
                            features["shopping"] = True

            return features

        except Exception as e:
            logger.error(f"Failed to get SERP features: {e}")
            return {}

    def _calculate_kd_score(
        self,
        competition: str,
        search_volume: int,
        cpc: float
    ) -> float:
        """
        计算关键词难度分数(0-100)

        算法:
        - 竞争度基础分:LOW=20, MEDIUM=50, HIGH=80
        - 搜索量调整:>10000 +10, >50000 +15
        - CPC调整:>$2 +5, >$5 +10

        Args:
            competition: 竞争度
            search_volume: 搜索量
            cpc: 每次点击成本

        Returns:
            KD分数(0-100)
        """
        # 基础分
        base_scores = {
            "LOW": 20,
            "MEDIUM": 50,
            "HIGH": 80,
            "UNKNOWN": 40
        }
        score = base_scores.get(competition, 40)

        # 搜索量调整
        if search_volume > 50000:
            score += 15
        elif search_volume > 10000:
            score += 10
        elif search_volume > 5000:
            score += 5

        # CPC调整
        if cpc > 5.0:
            score += 10
        elif cpc > 2.0:
            score += 5

        return min(100, max(0, score))

    def _map_competition(self, competition: str) -> str:
        """映射竞争度"""
        mapping = {
            "LOW": "low",
            "MEDIUM": "medium",
            "HIGH": "high",
            "UNKNOWN": "medium"
        }
        return mapping.get(competition, "medium")

    def _estimate_from_llm(self, keyword: str) -> KeywordMetrics:
        """
        DataForSEO 不可用时的 LLM 回退估算

        Args:
            keyword: 关键词

        Returns:
            估算的KeywordMetrics
        """
        # 简单的启发式估算
        word_count = len(keyword.split())

        # 长尾词通常搜索量低、难度低
        if word_count >= 4:
            monthly_volume = 500
            kd_score = 25
            cpc = 0.5
            competition = "low"
        elif word_count == 3:
            monthly_volume = 2000
            kd_score = 40
            cpc = 1.0
            competition = "medium"
        else:
            monthly_volume = 5000
            kd_score = 60
            cpc = 2.0
            competition = "high"

        logger.debug(f"Using LLM estimate for: {keyword}")

        return KeywordMetrics(
            keyword=keyword,
            monthly_volume=monthly_volume,
            kd_score=kd_score,
            cpc=cpc,
            competition_level=competition,
            serp_features=[],
            data_source="llm_estimate",
            confidence=0.3
        )


# 全局单例
_keyword_data_client: Optional[KeywordDataClient] = None


def get_keyword_data_client(
    username: Optional[str] = None,
    password: Optional[str] = None
) -> KeywordDataClient:
    """
    获取全局关键词数据客户端单例

    Args:
        username: DataForSEO用户名
        password: DataForSEO密码

    Returns:
        KeywordDataClient实例
    """
    global _keyword_data_client

    if _keyword_data_client is None:
        # 尝试从环境变量获取
        import os
        username = username or os.getenv("DATAFORSEO_USERNAME", "")
        password = password or os.getenv("DATAFORSEO_PASSWORD", "")

        _keyword_data_client = KeywordDataClient(username, password)

    return _keyword_data_client
