"""
SEO Content Generator v2.0

AI-powered SEO content generation system with:
- ASG Knowledge Base integration (Janson intro, company info, FAQ, case studies)
- Intelligent article type classification (Pillar/Response/Share)
- WordPress integration
"""

__version__ = "2.0.0"
__author__ = "ASG"
__license__ = "MIT"

from seo_gen.config import Settings
from seo_gen.modules.llm import LLMClient
from seo_gen.modules.serp import SERPAnalyzer
from seo_gen.modules.content import ContentGenerator
from seo_gen.modules.image import ImageGenerator
from seo_gen.modules.wordpress import WordPressPublisher
from seo_gen.modules.quality import QualityChecker
from seo_gen.modules.content_classifier import ContentClassifier, ArticleType
from seo_gen.modules.asg_knowledge import ASGKnowledgeBase

__all__ = [
    "Settings",
    "LLMClient",
    "SERPAnalyzer",
    "ContentGenerator",
    "ImageGenerator",
    "WordPressPublisher",
    "QualityChecker",
    "ContentClassifier",
    "ArticleType",
    "ASGKnowledgeBase",
]
