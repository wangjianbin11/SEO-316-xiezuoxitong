"""
结构化数据生成器

职责:生成所有 JSON-LD Schema 标记,注入 WordPress 文章
这是 GEO 优化最重要的技术层实现
"""

import json
import re
from datetime import datetime
from typing import Optional, List, Dict

from loguru import logger


class SchemaGenerator:
    """Schema 标记生成器"""

    SITE_INFO = {
        "name": "ASG Dropshipping",
        "url": "https://asgdropshipping.com",
        "logo_url": "https://asgdropshipping.com/wp-content/uploads/asg-logo.png",
        "author_name": "Janson",
        "author_title": "CEO & Founder",
        "author_bio_url": "https://asgdropshipping.com/about/",
        "author_same_as": [
            # "https://www.linkedin.com/in/janson-asg/",  # 如有请填写真实URL
        ]
    }

    def __init__(self, site_info: Optional[dict] = None):
        """
        初始化生成器

        Args:
            site_info: 站点信息覆盖(可选)
        """
        if site_info:
            self.SITE_INFO.update(site_info)

    def generate_article_schema(
        self,
        title: str,
        description: str,
        article_url: str,
        image_url: str,
        publish_date: str,
        keywords: List[str],
        word_count: int,
        article_type: str = "pillar"
    ) -> dict:
        """
        生成 Article / BlogPosting Schema

        article_type 映射:
        - pillar → @type: "Article"(权威性最高)
        - response → @type: "Article" with about.@type: "Question"
        - share → @type: "BlogPosting"

        必须包含字段:
        headline, description, author (Person), publisher (Organization + Logo),
        datePublished, dateModified, mainEntityOfPage (WebPage),
        image (ImageObject: url + width + height), keywords, wordCount,
        inLanguage, potentialAction (ReadAction)

        Args:
            title: 文章标题
            description: 描述
            article_url: 文章URL
            image_url: 封面图URL
            publish_date: 发布日期(ISO 8601格式)
            keywords: 关键词列表
            word_count: 字数
            article_type: 文章类型

        Returns:
            Article Schema字典
        """
        # 确定Schema类型
        schema_type = "Article" if article_type in ["pillar", "response"] else "BlogPosting"

        schema = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "headline": title[:110],  # Google截断上限
            "description": description[:160],
            "url": article_url,
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": article_url
            },
            "image": {
                "@type": "ImageObject",
                "url": image_url,
                "width": 1200,
                "height": 630
            },
            "author": {
                "@type": "Person",
                "name": self.SITE_INFO["author_name"],
                "jobTitle": self.SITE_INFO["author_title"],
                "url": self.SITE_INFO["author_bio_url"],
            },
            "publisher": {
                "@type": "Organization",
                "name": self.SITE_INFO["name"],
                "url": self.SITE_INFO["url"],
                "logo": {
                    "@type": "ImageObject",
                    "url": self.SITE_INFO["logo_url"],
                    "width": 600,
                    "height": 60
                }
            },
            "datePublished": publish_date,
            "dateModified": publish_date,
            "keywords": ", ".join(keywords[:10]),
            "wordCount": word_count,
            "inLanguage": "en-US",
            "potentialAction": {
                "@type": "ReadAction",
                "target": [article_url]
            }
        }

        # 添加 sameAs 如果有
        if self.SITE_INFO["author_same_as"]:
            schema["author"]["sameAs"] = self.SITE_INFO["author_same_as"]

        # 添加 worksFor
        schema["author"]["worksFor"] = {
            "@type": "Organization",
            "name": self.SITE_INFO["name"],
            "url": self.SITE_INFO["url"]
        }

        # 如果是 response 类型,添加 about
        if article_type == "response":
            schema["about"] = {
                "@type": "Question",
                "name": title
            }

        return schema

    def generate_faq_schema(self, faq_list: List[dict]) -> dict:
        """
        生成 FAQPage Schema

        faq_list 格式:[{"question": str, "answer": str}]

        答案字段规则:
        - 纯文本,不含任何HTML标签
        - 最大500字符(Google截断)
        - 必须以完整句子结尾(不能半途截断)

        验证:
        - 问题数量 6-8个
        - 每个答案 60-120词
        - 答案不含HTML实体

        Args:
            faq_list: FAQ列表

        Returns:
            FAQPage Schema字典
        """
        if not faq_list:
            logger.warning("Empty FAQ list provided")
            return {}

        # 验证FAQ数量
        if len(faq_list) < 6 or len(faq_list) > 8:
            logger.warning(f"FAQ count {len(faq_list)} not in recommended range 6-8")

        main_entity = []
        for item in faq_list:
            question = item.get("question", "")
            answer = item.get("answer", "")

            if not question or not answer:
                continue

            # 清理答案(移除HTML标签)
            clean_answer = self._strip_html(answer)

            # 截断到500字符
            if len(clean_answer) > 500:
                # 在句子边界截断
                clean_answer = clean_answer[:500]
                last_period = clean_answer.rfind('.')
                if last_period > 400:
                    clean_answer = clean_answer[:last_period + 1]

            main_entity.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": clean_answer
                }
            })

        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entity
        }

    def generate_breadcrumb_schema(
        self,
        article_title: str,
        article_url: str,
        category_name: str = "Blog",
        category_url: Optional[str] = None
    ) -> dict:
        """
        生成 BreadcrumbList Schema(3级:Home → Category → Article)

        Args:
            article_title: 文章标题
            article_url: 文章URL
            category_name: 分类名称
            category_url: 分类URL(可选)

        Returns:
            BreadcrumbList Schema字典
        """
        if not category_url:
            category_url = f"{self.SITE_INFO['url']}/blog/"

        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": self.SITE_INFO["url"]
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": category_name,
                    "item": category_url
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": article_title,
                    "item": article_url
                }
            ]
        }

    def generate_how_to_schema(
        self,
        steps: List[dict],
        title: str,
        total_time: str = "PT30M"
    ) -> dict:
        """
        为 How-To 类型文章生成 HowTo Schema(触发 SERP 步骤卡片)
        仅在文章类型为 "response" 且H2包含步骤编号时生成

        steps 格式:[{"name": str, "text": str, "url": str}]
        total_time 格式:ISO 8601 Duration,如 "PT30M"(30分钟)

        Args:
            steps: 步骤列表
            title: 标题
            total_time: 总时长

        Returns:
            HowTo Schema字典
        """
        if not steps:
            return {}

        step_list = []
        for i, step in enumerate(steps, 1):
            step_schema = {
                "@type": "HowToStep",
                "position": i,
                "name": step.get("name", f"Step {i}"),
                "text": step.get("text", ""),
            }

            # 添加URL如果有
            if step.get("url"):
                step_schema["url"] = step["url"]

            step_list.append(step_schema)

        return {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": title,
            "totalTime": total_time,
            "step": step_list
        }

    def generate_all_schemas(
        self,
        article: dict,
        article_url: str,
        faq_list: List[dict],
        category_name: str = "Blog",
        publish_date: Optional[str] = None
    ) -> str:
        """
        生成完整的 Schema 标记字符串,注入 <head>

        返回格式:
        <script type="application/ld+json">
        [
          {Article Schema},
          {FAQPage Schema},
          {BreadcrumbList Schema}
        ]
        </script>

        每个 Schema 生成后用 json.loads(json.dumps(schema)) 验证
        验证失败时 log warning,不抛出异常,跳过该Schema

        Args:
            article: 文章数据
            article_url: 文章URL
            faq_list: FAQ列表
            category_name: 分类名称
            publish_date: 发布日期(可选,默认当前时间)

        Returns:
            Schema标记HTML字符串
        """
        schemas = []

        # 默认发布日期
        if not publish_date:
            publish_date = datetime.now().isoformat()

        # 1. Article Schema
        try:
            article_schema = self.generate_article_schema(
                title=article.get("title", ""),
                description=article.get("metaDescription", ""),
                article_url=article_url,
                image_url=article.get("featuredImage", {}).get("url", ""),
                publish_date=publish_date,
                keywords=[article.get("keyword", "")],
                word_count=self._calculate_word_count(article),
                article_type=article.get("article_type", "pillar")
            )
            # 验证
            json.loads(json.dumps(article_schema))
            schemas.append(article_schema)
        except Exception as e:
            logger.warning(f"Failed to generate Article schema: {e}")

        # 2. FAQPage Schema
        if faq_list:
            try:
                faq_schema = self.generate_faq_schema(faq_list)
                if faq_schema:
                    # 验证
                    json.loads(json.dumps(faq_schema))
                    schemas.append(faq_schema)
            except Exception as e:
                logger.warning(f"Failed to generate FAQ schema: {e}")

        # 3. BreadcrumbList Schema
        try:
            breadcrumb_schema = self.generate_breadcrumb_schema(
                article_title=article.get("title", ""),
                article_url=article_url,
                category_name=category_name
            )
            # 验证
            json.loads(json.dumps(breadcrumb_schema))
            schemas.append(breadcrumb_schema)
        except Exception as e:
            logger.warning(f"Failed to generate Breadcrumb schema: {e}")

        # 4. HowTo Schema(条件生成)
        if self._is_howto_article(article):
            try:
                steps = self._extract_steps_from_article(article)
                if steps:
                    howto_schema = self.generate_how_to_schema(
                        steps=steps,
                        title=article.get("title", ""),
                        total_time="PT30M"  # 默认30分钟
                    )
                    if howto_schema:
                        # 验证
                        json.loads(json.dumps(howto_schema))
                        schemas.append(howto_schema)
            except Exception as e:
                logger.warning(f"Failed to generate HowTo schema: {e}")

        # 生成最终HTML
        if not schemas:
            logger.warning("No schemas generated")
            return ""

        schema_json = json.dumps(schemas, ensure_ascii=False, indent=2)
        return f'<script type="application/ld+json">\n{schema_json}\n</script>'

    def _strip_html(self, text: str) -> str:
        """移除HTML标签,保留纯文本"""
        # 简单的HTML标签移除
        clean = re.sub(r'<[^>]+>', '', text)
        # 移除HTML实体
        clean = re.sub(r'&[a-z]+;', ' ', clean)
        return clean.strip()

    def _is_howto_article(self, article: dict) -> bool:
        """判断是否为How-To格式:标题包含Step/How to,或H2包含编号"""
        title = article.get("title", "").lower()

        # 检查标题
        if any(keyword in title for keyword in ['how to', 'step', 'guide', 'tutorial']):
            return True

        # 检查sections中的H2
        sections = article.get("sections", [])
        for section in sections:
            section_title = section.get("sectionTitle", "").lower()
            # 检查是否有编号(Step 1, 1., etc.)
            if re.match(r'^(step\s+)?\d+[.:]?\s+', section_title):
                return True

        return False

    def _extract_steps_from_article(self, article: dict) -> List[dict]:
        """从文章中提取步骤"""
        steps = []
        sections = article.get("sections", [])

        for section in sections:
            section_title = section.get("sectionTitle", "")

            # 检查是否是步骤标题
            if re.match(r'^(step\s+)?\d+[.:]?\s+', section_title.lower()):
                step_text = section.get("content", "")

                # 提取纯文本(移除HTML)
                clean_text = self._strip_html(step_text)

                # 限制长度
                if len(clean_text) > 300:
                    clean_text = clean_text[:300] + "..."

                steps.append({
                    "name": section_title,
                    "text": clean_text,
                    "url": ""  # 可以添加锚点链接
                })

        return steps

    def _calculate_word_count(self, article: dict) -> int:
        """计算文章字数"""
        word_count = 0

        # 统计introduction
        intro = article.get("introduction", "")
        word_count += len(self._strip_html(intro).split())

        # 统计sections
        sections = article.get("sections", [])
        for section in sections:
            content = section.get("content", "")
            word_count += len(self._strip_html(content).split())

        # 统计FAQ
        faq_section = article.get("faqSection", {})
        faq_items = faq_section.get("items", [])
        for item in faq_items:
            answer = item.get("answer", "")
            word_count += len(self._strip_html(answer).split())

        return word_count

    def validate_schema(self, schema: dict) -> tuple[bool, Optional[str]]:
        """
        验证Schema是否有效

        Args:
            schema: Schema字典

        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 尝试序列化和反序列化
            json_str = json.dumps(schema)
            json.loads(json_str)

            # 检查必需字段
            if "@context" not in schema:
                return False, "Missing @context"

            if "@type" not in schema:
                return False, "Missing @type"

            return True, None

        except Exception as e:
            return False, str(e)
