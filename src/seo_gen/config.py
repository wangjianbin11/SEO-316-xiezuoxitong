"""
配置管理模块

使用 pydantic-settings 管理环境变量和配置
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== API 配置 ====================
    openai_api_base: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI 兼容 API 端点"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API 密钥"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="默认使用的模型"
    )

    # 图片生成 API
    image_api_base: Optional[str] = Field(
        default=None,
        description="图片生成 API 端点"
    )
    image_api_key: Optional[str] = Field(
        default=None,
        description="图片生成 API 密钥"
    )
    image_model: str = Field(
        default="flux-pro",
        description="图片生成模型"
    )

    # ==================== Google SERP API ====================
    google_search_api_key: Optional[str] = Field(
        default=None,
        description="Google Search API 密钥"
    )
    google_search_engine_id: Optional[str] = Field(
        default=None,
        description="Google 自定义搜索引擎 ID"
    )

    # ==================== WordPress 配置 ====================
    wordpress_site_url: str = Field(
        default="",
        description="WordPress 站点 URL"
    )
    wordpress_username: str = Field(
        default="",
        description="WordPress 用户名"
    )
    wordpress_app_password: str = Field(
        default="",
        description="WordPress 应用密码"
    )

    # ==================== 飞书配置 ====================
    feishu_app_id: Optional[str] = Field(
        default=None,
        description="飞书应用 ID"
    )
    feishu_app_secret: Optional[str] = Field(
        default=None,
        description="飞书应用密钥"
    )
    feishu_bitable_app_token: Optional[str] = Field(
        default=None,
        description="飞书多维表格 App Token"
    )
    feishu_bitable_table_id: Optional[str] = Field(
        default=None,
        description="飞书多维表格 ID"
    )

    # ==================== Google Drive 配置 ====================
    google_drive_credentials_path: str = Field(
        default="config/google-drive-credentials.json",
        description="Google Drive 凭证文件路径"
    )
    google_drive_folder_id: Optional[str] = Field(
        default=None,
        description="Google Drive 文件夹 ID"
    )

    # ==================== 应用配置 ====================
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    output_dir: str = Field(
        default="outputs",
        description="输出目录"
    )
    quality_score_threshold: int = Field(
        default=70,
        description="质量检测阈值 (0-100)"
    )
    max_regeneration_count: int = Field(
        default=3,
        description="最大重新生成次数"
    )

    # ==================== DataForSEO 配置 ====================
    dataforseo_username: str = Field(
        default="",
        description="DataForSEO 用户名(邮箱)"
    )
    dataforseo_password: str = Field(
        default="",
        description="DataForSEO 密码"
    )
    dataforseo_location_code: int = Field(
        default=2840,
        description="DataForSEO 地区代码(2840=US, 2826=UK, 2156=CN)"
    )

    # ==================== 向量知识库配置 ====================
    use_vector_search: bool = Field(
        default=False,
        description="是否使用向量搜索知识库"
    )
    vector_db_path: str = Field(
        default="./chroma_db",
        description="向量数据库路径"
    )
    embedding_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="Embedding模型名称"
    )

    # ==================== 质量控制配置 ====================
    min_publish_score: float = Field(
        default=75.0,
        description="最低发布分数(0-100)"
    )
    allow_force_publish: bool = Field(
        default=False,
        description="是否允许强制发布低分文章"
    )

    # ==================== 追踪数据库配置 ====================
    tracker_db_path: str = Field(
        default="./seo_tracker.db",
        description="文章追踪数据库路径"
    )

    # ==================== 站点信息配置 ====================
    author_name: str = Field(
        default="Janson",
        description="作者名称"
    )
    author_title: str = Field(
        default="CEO & Founder",
        description="作者职位"
    )
    site_name: str = Field(
        default="ASG Dropshipping",
        description="站点名称"
    )
    site_url: str = Field(
        default="https://asgdropshipping.com",
        description="站点URL"
    )
    site_logo_url: str = Field(
        default="https://asgdropshipping.com/wp-content/uploads/asg-logo.png",
        description="站点Logo URL"
    )

    # ==================== 图片配置 ====================
    cover_image_width: int = Field(
        default=1200,
        description="封面图宽度"
    )
    cover_image_height: int = Field(
        default=630,
        description="封面图高度"
    )
    section_image_width: int = Field(
        default=800,
        description="章节图宽度"
    )
    section_image_height: int = Field(
        default=450,
        description="章节图高度"
    )

    # ==================== 速率控制配置 ====================
    google_api_max_qps: float = Field(
        default=2.0,
        description="Google API 最大QPS"
    )
    llm_max_rpm: int = Field(
        default=5,
        description="LLM 最大RPM"
    )

    # ==================== DataForSEO 配置 (关键词真实数据) ====================
    dataforseo_username: Optional[str] = Field(
        default=None,
        description="DataForSEO 用户名(邮箱)"
    )
    dataforseo_password: Optional[str] = Field(
        default=None,
        description="DataForSEO API 密码"
    )
    dataforseo_location_code: int = Field(
        default=2840,
        description="DataForSEO 地区代码 (2840=US, 2826=UK)"
    )
    image_max_concurrent: int = Field(
        default=1,
        description="图片生成最大并发数"
    )
    competitor_scrape_delay_min: float = Field(
        default=1.5,
        description="竞品爬取最小延迟(秒)"
    )
    competitor_scrape_delay_max: float = Field(
        default=3.0,
        description="竞品爬取最大延迟(秒)"
    )

    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return get_project_root()

    @property
    def knowledge_dir(self) -> Path:
        """知识库目录"""
        return self.project_root / "config" / "knowledge"

    @property
    def prompts_dir(self) -> Path:
        """Prompt 模板目录"""
        return self.project_root / "prompts"

    @property
    def output_path(self) -> Path:
        """输出目录绝对路径"""
        path = self.output_dir
        if not Path(path).is_absolute():
            path = self.project_root / path
        return Path(path)

    def model_post_init(self, __context: object) -> None:
        """初始化后创建输出目录"""
        self.output_path.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()
