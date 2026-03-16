"""
图片生成模块 - 升级版

- 1张封面图
- 每个板块一张六宫格配图（9张图组合）
- 支持多种图片风格
"""

import base64
from pathlib import Path
from typing import Optional, Literal

import httpx
from loguru import logger

from seo_gen.config import settings


# Image style definitions
IMAGE_STYLES = {
    "modern": "Modern flat design, clean lines, minimalist, professional blue/white color scheme",
    "minimalist": "Minimalist design, lots of white space, simple shapes, monochromatic with accent colors",
    "professional": "Corporate professional style, business-oriented, clean and trustworthy",
    "creative": "Creative and artistic, vibrant colors, dynamic composition, eye-catching",
    "tech": "Technology-focused, futuristic elements, digital aesthetic, gradient backgrounds",
    "nature": "Natural and organic, earth tones, soft shapes, environmental feel",
    "elegant": "Elegant and sophisticated, luxury feel, refined colors, premium quality",
    "playful": "Playful and friendly, bright colors, fun illustrations, approachable",
}


class ImageGenerator:
    """AI 图片生成器 - 支持六宫格和多种风格"""

    def __init__(self, default_style: str = "modern"):
        """
        初始化图片生成器

        Args:
            default_style: 默认图片风格 (modern, minimalist, professional, creative, tech, nature, elegant, playful)
        """
        self.api_base = settings.image_api_base
        self.api_key = settings.image_api_key
        self.model = settings.image_model
        self.default_style = default_style

        self.client = httpx.AsyncClient(timeout=120.0)

    def get_style_description(self, style: str = None) -> str:
        """获取风格描述"""
        style = style or self.default_style
        return IMAGE_STYLES.get(style, IMAGE_STYLES["modern"])

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        model: Optional[str] = None,
    ) -> bytes:
        """
        生成单张图片

        使用 OpenRouter /chat/completions 端点

        Args:
            prompt: 图片描述 Prompt
            aspect_ratio: 图片比例 (16:9, 4:3, 1:1)
            model: 模型名称

        Returns:
            图片二进制数据
        """
        if not self.api_base or not self.api_key:
            logger.warning("Image generation API not configured, using placeholder")
            return self._generate_placeholder()

        model = model or self.model
        # 使用 /chat/completions 端点
        url = self.api_base.rstrip("/") + "/chat/completions"

        # 构建请求格式
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            # 添加图片生成参数
            "max_tokens": 1000,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://asgdropshipping.com",
            "X-Title": "ASG Dropshipping",
        }

        try:
            logger.info(f"Generating image with {model}: {prompt[:50]}...")
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Image API response: {data}")

            # OpenRouter 图片生成响应格式
            # choices[0].message.images[0].image_url.url
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "images" in choice["message"]:
                    images = choice["message"]["images"]
                    if len(images) > 0:
                        image_url = images[0].get("image_url", {}).get("url")
                        if image_url:
                            logger.info(f"Image URL received: {image_url[:100]}...")
                            # 处理 base64 data URL
                            if image_url.startswith("data:image/png;base64,"):
                                import base64
                                base64_data = image_url.split(",", 1)[1]
                                return base64.b64decode(base64_data)
                            elif image_url.startswith("data:image/jpeg;base64,"):
                                import base64
                                base64_data = image_url.split(",", 1)[1]
                                return base64.b64decode(base64_data)
                            else:
                                # 下载图片
                                img_response = await self.client.get(image_url, timeout=60.0)
                                return img_response.content

            logger.warning("Image API response format not recognized, using placeholder")
            logger.debug(f"Response data: {data}")
            return self._generate_placeholder()

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return self._generate_placeholder()

    async def generate_cover_image(
        self,
        keyword: str,
        title: str,
        style: str = None,
    ) -> bytes:
        """
        生成封面图

        Args:
            keyword: 关键词
            title: 文章标题
            style: 图片风格 (modern, minimalist, professional, creative, tech, nature, elegant, playful)

        Returns:
            图片二进制数据
        """
        style_desc = self.get_style_description(style)
        prompt = f"""Professional blog header image for: "{title}"

Context: About {keyword}, dropshipping, e-commerce, business

Style Requirements:
- {style_desc}
- No text overlay
- High quality, 16:9 aspect ratio
- Business/professional theme
- Eye-catching and engaging"""

        return await self.generate(prompt, aspect_ratio="16:9")

    async def generate_collage_image(
        self,
        keyword: str,
        section_title: str,
        section_index: int,
        image_descriptions: list[str] = None,
        style: str = None,
    ) -> bytes:
        """
        生成六宫格配图（9张图组合成一张）

        Args:
            keyword: 关键词
            section_title: 板块标题
            section_index: 板块序号
            image_descriptions: 9张图片的描述列表
            style: 图片风格 (modern, minimalist, professional, creative, tech, nature, elegant, playful)

        Returns:
            图片二进制数据（六宫格组合图）
        """
        if not self.api_base or not self.api_key:
            logger.warning("Image generation API not configured, using placeholder")
            return self._generate_placeholder()

        # 如果没有提供图片描述，生成默认的9张图
        if not image_descriptions:
            image_descriptions = self._get_default_collage_prompts(
                keyword, section_title, section_index
            )

        style_desc = self.get_style_description(style)
        # 为六宫格生成一个综合的 prompt
        collage_prompt = f"""A professional 3x3 grid infographic collage (9 images arranged in a square grid) about: "{section_title}"

Each of the 9 grid cells should contain:
{self._format_collage_descriptions(image_descriptions)}

Style: {style_desc}, no text, high quality, square aspect ratio"""

        try:
            logger.info(f"Generating collage for section {section_index}: {section_title} (style: {style or self.default_style})")
            return await self.generate(collage_prompt, aspect_ratio="1:1")

        except Exception as e:
            logger.error(f"Collage generation failed: {e}")
            return self._generate_placeholder()

    def _get_default_collage_prompts(
        self,
        keyword: str,
        section_title: str,
        section_index: int,
    ) -> list[str]:
        """获取默认的六宫格图片描述"""
        base_prompts = [
            f"Concept diagram illustrating {section_title}",
            f"Data visualization showing trends for {keyword}",
            f"Process flowchart for {section_title}",
            f"Comparison table related to {keyword}",
            f"Strategy framework for {section_title}",
            f"Best practices checklist for {section_title}",
            f"Case study visualization for {keyword}",
            f"Tools and resources for {section_title}",
            f"Action plan summary for {section_title}",
        ]
        return base_prompts

    def _format_collage_descriptions(self, descriptions: list[str]) -> str:
        """格式化六宫格描述"""
        lines = []
        for i, desc in enumerate(descriptions[:9], 1):
            lines.append(f"Grid {i}: {desc}")
        return "\n".join(lines)

    async def generate_all_article_images(
        self,
        keyword: str,
        title: str,
        section_titles: list[str],
        style: str = None,
    ) -> dict[str, bytes]:
        """
        为文章生成所有图片

        Args:
            keyword: 关键词
            title: 文章标题
            section_titles: 板块标题列表
            style: 图片风格 (modern, minimalist, professional, creative, tech, nature, elegant, playful)

        Returns:
            图片数据字典 {"cover": bytes, "section_1": bytes, ...}
        """
        logger.info(f"Generating all images for: {keyword} (style: {style or self.default_style})")

        images = {}

        # 1. 生成封面图
        try:
            cover = await self.generate_cover_image(keyword, title, style=style)
            images["cover"] = cover
            logger.info("Cover image generated")
        except Exception as e:
            logger.error(f"Cover image generation failed: {e}")
            images["cover"] = self._generate_placeholder()

        # 2. 为前3个板块生成配图（修复：原来是2张，现在是3张）
        for i, section_title in enumerate(section_titles[:3], 1):
            try:
                collage = await self.generate_collage_image(
                    keyword=keyword,
                    section_title=section_title,
                    section_index=i,
                    style=style,
                )
                images[f"section_{i}"] = collage
                logger.info(f"Section {i} collage generated")
            except Exception as e:
                logger.error(f"Section {i} collage generation failed: {e}")
                images[f"section_{i}"] = self._generate_placeholder()

        logger.info(f"All images generated: {len(images)} total")
        return images

    def _generate_placeholder(self) -> bytes:
        """生成占位图 (1x1 灰色 PNG)"""
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )

    def save_images(
        self,
        images: dict[str, bytes],
        output_dir: Path,
        slug: str,
    ) -> dict[str, str]:
        """
        保存图片到目录

        Args:
            images: 图片数据字典
            output_dir: 输出目录
            slug: 文章 slug

        Returns:
            保存的文件路径字典
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = {}

        for key, data in images.items():
            filename = f"{slug}_{key}.png"
            filepath = output_dir / filename
            filepath.write_bytes(data)
            saved_paths[key] = str(filepath)
            logger.debug(f"Saved image: {filename}")

        return saved_paths

    def sync_generate_all_article_images(
        self,
        keyword: str,
        title: str,
        section_titles: list[str],
    ) -> dict[str, bytes]:
        """同步版本的图片生成"""
        import asyncio
        return asyncio.run(self.generate_all_article_images(keyword, title, section_titles))


# Global singleton
_image_generator: Optional[ImageGenerator] = None


def get_image_generator() -> ImageGenerator:
    """Get global image generator singleton"""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator
