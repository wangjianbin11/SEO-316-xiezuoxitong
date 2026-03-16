"""
工作流检查点管理器

职责:为工作流提供检查点,允许从失败处恢复
防止API费用浪费,支持断点续跑
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

from loguru import logger


@dataclass
class CheckpointMeta:
    """检查点元数据"""
    stage: int
    stage_name: str
    keyword: str
    timestamp: str
    duration_seconds: float
    success: bool
    error_message: Optional[str]


class CheckpointManager:
    """检查点管理器"""

    STAGE_NAMES = {
        0: "keyword_classification",
        1: "knowledge_base_loading",
        2: "serp_analysis",
        3: "competitor_scraping",
        4: "keyword_data",
        5: "title_generation",
        6: "outline_generation",
        7: "content_generation",
        8: "geo_optimization",
        9: "quality_check",
        10: "image_generation",
        11: "schema_generation",
        12: "wordpress_publish"
    }

    def __init__(self, base_output_dir: str, keyword: str):
        """
        初始化检查点管理器

        Args:
            base_output_dir: 输出基础目录
            keyword: 关键词
        """
        self.keyword = keyword
        self.keyword_slug = re.sub(r'[^\w-]', '-', keyword.lower()).strip('-')
        self.checkpoint_dir = Path(base_output_dir) / self.keyword_slug / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Checkpoint manager initialized for '{keyword}' at {self.checkpoint_dir}")

    def save(self, stage: int, data: Any, duration_seconds: float = 0) -> None:
        """
        保存阶段结果

        Args:
            stage: 阶段编号
            data: 阶段数据
            duration_seconds: 执行时长(秒)
        """
        stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")
        filepath = self.checkpoint_dir / f"stage_{stage:02d}_{stage_name}.json"

        checkpoint = {
            "meta": {
                "stage": stage,
                "stage_name": stage_name,
                "keyword": self.keyword,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration_seconds, 2),
                "success": True,
                "error_message": None
            },
            "data": data
        }

        try:
            filepath.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
            logger.info(f"✓ Checkpoint saved: stage {stage} ({stage_name})")
        except Exception as e:
            logger.error(f"Failed to save checkpoint for stage {stage}: {e}")
            raise

    def save_error(self, stage: int, error_message: str, duration_seconds: float = 0) -> None:
        """
        保存错误状态

        Args:
            stage: 阶段编号
            error_message: 错误信息
            duration_seconds: 执行时长(秒)
        """
        stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")
        filepath = self.checkpoint_dir / f"stage_{stage:02d}_{stage_name}_error.json"

        checkpoint = {
            "meta": {
                "stage": stage,
                "stage_name": stage_name,
                "keyword": self.keyword,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration_seconds, 2),
                "success": False,
                "error_message": error_message
            },
            "data": None
        }

        try:
            filepath.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
            logger.warning(f"✗ Error checkpoint saved: stage {stage} ({stage_name})")
        except Exception as e:
            logger.error(f"Failed to save error checkpoint for stage {stage}: {e}")

    def load(self, stage: int) -> Optional[Any]:
        """
        读取阶段结果

        Args:
            stage: 阶段编号

        Returns:
            阶段数据,不存在返回 None
        """
        stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")
        filepath = self.checkpoint_dir / f"stage_{stage:02d}_{stage_name}.json"

        if not filepath.exists():
            return None

        try:
            data = json.loads(filepath.read_text())
            return data.get("data")
        except Exception as e:
            logger.warning(f"Failed to load checkpoint for stage {stage}: {e}")
            return None

    def get_resume_stage(self) -> int:
        """
        返回最后成功完成的阶段+1

        Returns:
            下一个要执行的阶段编号,0=从头开始
        """
        for stage in range(max(self.STAGE_NAMES.keys()), -1, -1):
            if self.load(stage) is not None:
                logger.info(f"Found checkpoint at stage {stage}, will resume from stage {stage + 1}")
                return stage + 1
        return 0

    def clear(self) -> None:
        """清除所有检查点(强制重新运行)"""
        try:
            count = 0
            for f in self.checkpoint_dir.glob("*.json"):
                f.unlink()
                count += 1
            if count > 0:
                logger.info(f"Cleared {count} checkpoint files")
        except Exception as e:
            logger.error(f"Failed to clear checkpoints: {e}")

    def is_complete(self) -> bool:
        """
        检查是否所有阶段都已完成

        Returns:
            True 如果所有阶段完成
        """
        return self.get_resume_stage() > max(self.STAGE_NAMES.keys())

    def get_summary(self) -> dict:
        """
        返回当前进度摘要

        Returns:
            包含进度信息的字典
        """
        completed = []
        for stage in sorted(self.STAGE_NAMES.keys()):
            if self.load(stage) is not None:
                completed.append(self.STAGE_NAMES[stage])

        return {
            "keyword": self.keyword,
            "keyword_slug": self.keyword_slug,
            "completed_stages": completed,
            "completed_count": len(completed),
            "total_stages": len(self.STAGE_NAMES),
            "resume_from": self.get_resume_stage(),
            "is_complete": self.is_complete(),
            "checkpoint_dir": str(self.checkpoint_dir)
        }

    def get_stage_duration(self, stage: int) -> Optional[float]:
        """
        获取某个阶段的执行时长

        Args:
            stage: 阶段编号

        Returns:
            执行时长(秒),如果不存在返回 None
        """
        stage_name = self.STAGE_NAMES.get(stage, f"stage_{stage}")
        filepath = self.checkpoint_dir / f"stage_{stage:02d}_{stage_name}.json"

        if not filepath.exists():
            return None

        try:
            data = json.loads(filepath.read_text())
            return data.get("meta", {}).get("duration_seconds")
        except Exception:
            return None

    def get_total_duration(self) -> float:
        """
        获取所有已完成阶段的总时长

        Returns:
            总时长(秒)
        """
        total = 0.0
        for stage in self.STAGE_NAMES.keys():
            duration = self.get_stage_duration(stage)
            if duration is not None:
                total += duration
        return total
