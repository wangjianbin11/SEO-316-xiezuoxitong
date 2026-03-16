"""
知识库管理模块

加载和管理 5 个前置条件的内容
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from seo_gen.config import settings


class KnowledgeBase:
    """知识库管理器"""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        """
        初始化知识库

        Args:
            knowledge_dir: 知识库目录，默认从 settings 读取
        """
        self.knowledge_dir = knowledge_dir or settings.knowledge_dir

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"知识库目录不存在: {self.knowledge_dir}")

        # 5个前置条件文件 + GEO策略
        self._files = {
            "janson_jieshao": "janson_jieshao.txt",
            "kehuhuaxiang": "kehuhuaxiang.txt",
            "qiyejieshao": "qiyejieshao.txt",
            "yewuliucheng": "yewuliucheng.txt",
            "xiezuojianyi": "xiezuojianyi.txt",
            "geo_strategy": "geo_strategy.md",  # GEO策略指南
        }

        self._cache: dict[str, str] = {}

    def _load_file(self, filename: str) -> str:
        """加载文件内容"""
        file_path = self.knowledge_dir / filename

        if not file_path.exists():
            logger.warning(f"知识库文件不存在: {file_path}")
            return ""

        try:
            content = file_path.read_text(encoding="utf-8")
            logger.debug(f"加载知识库文件: {filename}, {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"读取知识库文件失败 {filename}: {e}")
            return ""

    def get(self, key: str) -> str:
        """
        获取知识库内容

        Args:
            key: 知识库键名 (janson_jieshao, kehuhuaxiang, qiyejieshao, yewuliucheng, xiezuojianyi)

        Returns:
            文件内容
        """
        if key not in self._files:
            raise ValueError(f"无效的知识库键名: {key}")

        if key not in self._cache:
            filename = self._files[key]
            self._cache[key] = self._load_file(filename)

        return self._cache[key]

    def get_all(self) -> dict[str, str]:
        """
        获取所有知识库内容

        Returns:
            所有知识库内容的字典
        """
        return {key: self.get(key) for key in self._files}

    def reload(self):
        """重新加载所有知识库文件"""
        self._cache.clear()
        logger.info("知识库已重新加载")

    @property
    def janson_jieshao(self) -> str:
        """站长介绍"""
        return self.get("janson_jieshao")

    @property
    def kehuhuaxiang(self) -> str:
        """客户画像"""
        return self.get("kehuhuaxiang")

    @property
    def qiyejieshao(self) -> str:
        """企业介绍"""
        return self.get("qiyejieshao")

    @property
    def yewuliucheng(self) -> str:
        """业务流程"""
        return self.get("yewuliucheng")

    @property
    def xiezuojianyi(self) -> str:
        """协作建议"""
        return self.get("xiezuojianyi")

    @property
    def geo_strategy(self) -> str:
        """GEO策略指南"""
        return self.get("geo_strategy")


# 全局单例
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """获取全局知识库单例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
