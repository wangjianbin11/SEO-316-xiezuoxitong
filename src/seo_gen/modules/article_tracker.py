"""
发布追踪数据库

职责:追踪已发布文章,防止重复生成,支持排名回填
"""

import sqlite3
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class ArticleTracker:
    """文章追踪器"""

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS published_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        keyword_slug TEXT NOT NULL UNIQUE,
        article_title TEXT,
        article_type TEXT,
        word_count INTEGER,
        wordpress_url TEXT,
        wp_post_id INTEGER,
        wp_post_status TEXT DEFAULT 'draft',
        published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_updated DATETIME,
        quality_score REAL,
        geo_score REAL,
        gsc_clicks INTEGER DEFAULT 0,
        gsc_impressions INTEGER DEFAULT 0,
        gsc_avg_position REAL DEFAULT 0,
        gsc_last_synced DATETIME,
        generation_cost_usd REAL,
        notes TEXT
    )
    """

    def __init__(self, db_path: str = "./seo_tracker.db"):
        """
        初始化追踪器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
        logger.debug(f"Article tracker initialized with database: {db_path}")

    def _init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(self.CREATE_TABLE_SQL)
                conn.commit()
            logger.info("Article tracker database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def is_published(self, keyword: str) -> bool:
        """
        检查是否已发布(使用slug防止大小写/空格差异)

        Args:
            keyword: 关键词

        Returns:
            True 如果已发布
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT id FROM published_articles WHERE keyword_slug = ?",
                    (slug,)
                ).fetchone()
            return row is not None
        except Exception as e:
            logger.error(f"Failed to check if published: {e}")
            return False

    def mark_published(
        self,
        keyword: str,
        article_title: str,
        article_type: str,
        word_count: int,
        wordpress_url: str,
        wp_post_id: int,
        quality_score: float = 0,
        geo_score: float = 0,
        generation_cost_usd: float = 0,
        wp_post_status: str = "draft"
    ) -> None:
        """
        标记为已发布

        Args:
            keyword: 关键词
            article_title: 文章标题
            article_type: 文章类型
            word_count: 字数
            wordpress_url: WordPress URL
            wp_post_id: WordPress文章ID
            quality_score: 质量分数
            geo_score: GEO分数
            generation_cost_usd: 生成成本(美元)
            wp_post_status: WordPress状态
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO published_articles
                    (keyword, keyword_slug, article_title, article_type, word_count,
                     wordpress_url, wp_post_id, wp_post_status, quality_score, geo_score,
                     generation_cost_usd, published_at, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    keyword, slug, article_title, article_type, word_count,
                    wordpress_url, wp_post_id, wp_post_status, quality_score, geo_score,
                    generation_cost_usd, datetime.now().isoformat(), datetime.now().isoformat()
                ))
                conn.commit()
            logger.info(f"Marked as published: {keyword} (ID: {wp_post_id})")
        except Exception as e:
            logger.error(f"Failed to mark as published: {e}")
            raise

    def get_article(self, keyword: str) -> Optional[dict]:
        """
        获取文章信息

        Args:
            keyword: 关键词

        Returns:
            文章信息字典,不存在返回None
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM published_articles WHERE keyword_slug = ?",
                    (slug,)
                ).fetchone()

            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Failed to get article: {e}")
            return None

    def get_all(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """
        获取所有已发布文章,按发布时间倒序

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            文章列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT * FROM published_articles
                    ORDER BY published_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset)
                ).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get all articles: {e}")
            return []

    def get_url(self, keyword: str) -> Optional[str]:
        """
        获取文章URL

        Args:
            keyword: 关键词

        Returns:
            WordPress URL,不存在返回None
        """
        article = self.get_article(keyword)
        if article:
            return article.get("wordpress_url")
        return None

    def update_gsc_data(
        self,
        keyword: str,
        clicks: int,
        impressions: int,
        avg_position: float
    ) -> None:
        """
        更新 Google Search Console 数据

        Args:
            keyword: 关键词
            clicks: 点击数
            impressions: 展示数
            avg_position: 平均排名
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE published_articles
                    SET gsc_clicks = ?,
                        gsc_impressions = ?,
                        gsc_avg_position = ?,
                        gsc_last_synced = ?,
                        last_updated = ?
                    WHERE keyword_slug = ?
                """, (
                    clicks, impressions, avg_position,
                    datetime.now().isoformat(), datetime.now().isoformat(),
                    slug
                ))
                conn.commit()
            logger.info(f"Updated GSC data for: {keyword}")
        except Exception as e:
            logger.error(f"Failed to update GSC data: {e}")

    def update_post_status(self, keyword: str, status: str) -> None:
        """
        更新文章状态

        Args:
            keyword: 关键词
            status: 状态(draft/publish/private)
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE published_articles
                    SET wp_post_status = ?,
                        last_updated = ?
                    WHERE keyword_slug = ?
                """, (status, datetime.now().isoformat(), slug))
                conn.commit()
            logger.info(f"Updated post status for {keyword}: {status}")
        except Exception as e:
            logger.error(f"Failed to update post status: {e}")

    def add_note(self, keyword: str, note: str) -> None:
        """
        添加备注

        Args:
            keyword: 关键词
            note: 备注内容
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取现有备注
                existing = conn.execute(
                    "SELECT notes FROM published_articles WHERE keyword_slug = ?",
                    (slug,)
                ).fetchone()

                if existing and existing[0]:
                    new_note = f"{existing[0]}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}"
                else:
                    new_note = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {note}"

                conn.execute("""
                    UPDATE published_articles
                    SET notes = ?,
                        last_updated = ?
                    WHERE keyword_slug = ?
                """, (new_note, datetime.now().isoformat(), slug))
                conn.commit()
            logger.info(f"Added note for {keyword}")
        except Exception as e:
            logger.error(f"Failed to add note: {e}")

    def get_statistics(self) -> dict:
        """
        获取统计信息

        Returns:
            统计数据字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 总文章数
                total = conn.execute(
                    "SELECT COUNT(*) FROM published_articles"
                ).fetchone()[0]

                # 按状态统计
                status_counts = {}
                rows = conn.execute("""
                    SELECT wp_post_status, COUNT(*) as count
                    FROM published_articles
                    GROUP BY wp_post_status
                """).fetchall()
                for row in rows:
                    status_counts[row[0]] = row[1]

                # 按类型统计
                type_counts = {}
                rows = conn.execute("""
                    SELECT article_type, COUNT(*) as count
                    FROM published_articles
                    GROUP BY article_type
                """).fetchall()
                for row in rows:
                    type_counts[row[0]] = row[1]

                # 平均分数
                avg_scores = conn.execute("""
                    SELECT AVG(quality_score) as avg_quality,
                           AVG(geo_score) as avg_geo
                    FROM published_articles
                    WHERE quality_score > 0
                """).fetchone()

                # 总成本
                total_cost = conn.execute("""
                    SELECT SUM(generation_cost_usd)
                    FROM published_articles
                """).fetchone()[0] or 0

                # GSC数据
                gsc_stats = conn.execute("""
                    SELECT SUM(gsc_clicks) as total_clicks,
                           SUM(gsc_impressions) as total_impressions,
                           AVG(gsc_avg_position) as avg_position
                    FROM published_articles
                    WHERE gsc_clicks > 0
                """).fetchone()

                return {
                    "total_articles": total,
                    "status_counts": status_counts,
                    "type_counts": type_counts,
                    "avg_quality_score": round(avg_scores[0] or 0, 2),
                    "avg_geo_score": round(avg_scores[1] or 0, 2),
                    "total_cost_usd": round(total_cost, 2),
                    "gsc_total_clicks": gsc_stats[0] or 0,
                    "gsc_total_impressions": gsc_stats[1] or 0,
                    "gsc_avg_position": round(gsc_stats[2] or 0, 2) if gsc_stats[2] else 0
                }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def delete_article(self, keyword: str) -> bool:
        """
        删除文章记录

        Args:
            keyword: 关键词

        Returns:
            True 如果删除成功
        """
        slug = self._to_slug(keyword)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM published_articles WHERE keyword_slug = ?",
                    (slug,)
                )
                conn.commit()
            logger.info(f"Deleted article record: {keyword}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete article: {e}")
            return False

    def _to_slug(self, keyword: str) -> str:
        """
        转换为slug

        Args:
            keyword: 关键词

        Returns:
            slug字符串
        """
        # 转小写
        slug = keyword.lower().strip()
        # 替换非字母数字字符为连字符
        slug = re.sub(r'[^\w-]', '-', slug)
        # 合并多个连字符
        slug = re.sub(r'-+', '-', slug)
        # 去除首尾连字符
        slug = slug.strip('-')
        return slug


# 全局单例
_article_tracker: Optional[ArticleTracker] = None


def get_article_tracker(db_path: str = "./seo_tracker.db") -> ArticleTracker:
    """
    获取全局文章追踪器单例

    Args:
        db_path: 数据库路径

    Returns:
        ArticleTracker实例
    """
    global _article_tracker
    if _article_tracker is None:
        _article_tracker = ArticleTracker(db_path)
    return _article_tracker
