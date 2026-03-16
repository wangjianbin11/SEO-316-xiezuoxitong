"""
SEO Content Generator - CLI Main Program v2

Upgraded Features:
- 3000 characters, pure English output
- E-E-A-T quality assessment (Fair/Medium/High/Perfect)
- 1 cover image + 6 section collage images (3x3 grid)
- WordPress HTML format ready for publishing
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

from seo_gen.config import settings
from seo_gen.modules.content import ContentGenerator
from seo_gen.modules.feishu import FeishuClient
from seo_gen.modules.image import ImageGenerator
from seo_gen.modules.knowledge import KnowledgeBase
from seo_gen.modules.llm import LLMClient
from seo_gen.modules.quality import QualityChecker, get_quality_checker
from seo_gen.modules.serp import SERPAnalyzer
from seo_gen.modules.wordpress import WordPressPublisher

# 创建 CLI 应用
app = typer.Typer(
    name="seo-gen",
    help="SEO Content Generator - AI-powered content generation for WordPress",
    add_completion=False,
)

console = Console()


# ==================== 核心工作流 ====================


async def generate_content_workflow(
    keyword: str,
    slug: str,
    search_intent: str = "share",
    skip_images: bool = False,
    skip_wordpress: bool = False,
    output_dir: Optional[Path] = None,
) -> dict:
    """
    完整的内容生成工作流

    Args:
        keyword: 关键词
        slug: URL slug
        search_intent: 搜索意图 (share/qa/pillar)
        skip_images: 跳过图片生成
        skip_wordpress: 跳过 WordPress 发布
        output_dir: 输出目录

    Returns:
        生成结果
    """
    output_dir = output_dir or settings.output_path
    output_dir.mkdir(parents=True, exist_ok=True)

    # 初始化模块
    llm = LLMClient()
    knowledge = KnowledgeBase()
    serp_analyzer = SERPAnalyzer(llm)
    content_generator = ContentGenerator(llm, knowledge)
    quality_checker = QualityChecker(llm)

    result = {
        "keyword": keyword,
        "slug": slug,
        "success": False,
        "steps": {},
    }

    try:
        with console.status("[bold cyan]SEO 内容生成进行中...") as status:
            # Step 1: SERP 分析
            status.update("Step 1: 分析 Google SERP...")
            logger.info(f"开始 SERP 分析: {keyword}")
            serp_result = await serp_analyzer.analyze(keyword)
            result["steps"]["serp"] = {"status": "completed", "data": serp_result}
            console.print("[green][OK][/green] Step 1: SERP 分析完成")

            # Step 2: 生成文章内容
            status.update("Step 2: 生成文章内容...")
            logger.info(f"开始生成文章: {keyword}")

            # 设置搜索意图
            serp_analysis = serp_result.get("serpAnalysis", {})
            serp_analysis["primaryIntent"] = search_intent

            article = await content_generator.generate_article(
                keyword=keyword,
                slug=slug,
                serp_analysis=serp_analysis,
            )
            result["steps"]["content"] = {"status": "completed", "data": article}
            console.print("[green][OK][/green] Step 2: 文章内容生成完成")

            # Step 3: 质量检测循环
            status.update("Step 3: 质量检测...")
            logger.info("开始质量检测")

            for attempt in range(settings.max_regeneration_count):
                quality_result = await quality_checker.check_article_quality(article, keyword)

                # 显示详细的 E-E-A-T 报告
                display_eeat_report(quality_result)

                if quality_checker.should_regenerate(quality_result):
                    logger.warning(f"质量未通过，重新生成 (尝试 {attempt + 1}/{settings.max_regeneration_count})")

                    # 获取改进建议
                    suggestion = await quality_checker.get_improvement_suggestions(article, quality_result)
                    # 这里可以实现重新生成逻辑
                    # 简化版：跳过重新生成
                    break
                else:
                    console.print(f"[green][OK][/green] Step 3: 质量检测通过 (分数: {quality_result.get('overallScore', 0)})")
                    result["steps"]["quality"] = {"status": "passed", "data": quality_result}
                    break

            # Step 4: 生成配图
            images = {}  # type: dict[str, bytes]
            section_media_ids = {}  # type: dict[str, int]
            featured_media_id = None

            if not skip_images:
                status.update("Step 4: 生成配图...")
                logger.info("开始生成配图")

                image_gen = ImageGenerator()
                section_titles = [s["sectionTitle"] for s in article.get("sections", [])]
                images = await image_gen.generate_all_article_images(
                    keyword=keyword,
                    title=article.get("title", ""),
                    section_titles=section_titles,
                )
                await image_gen.close()

                result["steps"]["images"] = {"status": "completed", "count": len(images)}
                console.print(f"[green][OK][/green] Step 4: 配图生成完成 ({len(images)} 张)")

                # 保存图片到本地
                for key, data in images.items():
                    filename = f"{slug}_{key}.png"
                    img_path = output_dir / filename
                    img_path.write_bytes(data)

            # Step 5: 保存 Markdown 文件
            status.update("Step 5: 保存 Markdown...")
            md_content = build_markdown(article)
            md_path = output_dir / f"{slug}.md"
            md_path.write_text(md_content, encoding="utf-8")
            result["steps"]["markdown"] = {"status": "completed", "path": str(md_path)}
            console.print(f"[green][OK][/green] Step 5: Markdown 已保存")

            # Step 6: 发布到 WordPress
            if not skip_wordpress:
                status.update("Step 6: 发布到 WordPress...")
                logger.info("发布到 WordPress")

                wp_publisher = WordPressPublisher()

                # 上传封面图
                if not skip_images and "cover" in images:
                    cover_result = await wp_publisher.upload_image(
                        images["cover"],
                        filename=f"{slug}_cover.png",
                        alt_text=article.get("title", ""),
                    )
                    if cover_result:
                        featured_media_id = cover_result.get("id")
                        logger.info(f"Cover image uploaded: media_id={featured_media_id}")

                # 上传板块配图
                if not skip_images and images:
                    for key, data in images.items():
                        if key.startswith("section_"):
                            section_num = key.split("_")[1]
                            img_result = await wp_publisher.upload_image(
                                data,
                                filename=f"{slug}_{key}.png",
                                alt_text=f"{article.get('title', '')} - Section {section_num}",
                            )
                            if img_result:
                                # 存储图片 URL 而不是 media_id
                                section_media_ids[section_num] = img_result.get("url", "")
                                logger.info(f"Section {section_num} image uploaded: url={img_result.get('url', '')}")

                # 构建 WordPress HTML 内容（包含配图）
                html_content = content_generator.build_wordpress_html(
                    article,
                    section_images=section_media_ids,
                )

                # 发布文章
                post_id = await wp_publisher.publish_article(
                    title=article.get("title", ""),
                    content=html_content,
                    excerpt=article.get("metaDescription", "")[:150],
                    slug=article.get("slug", ""),
                    meta_description=article.get("metaDescription", ""),
                    featured_media_id=featured_media_id,
                    status="draft",  # 默认发布为草稿
                )
                await wp_publisher.close()

                if post_id:
                    result["steps"]["wordpress"] = {
                        "status": "completed",
                        "post_id": post_id,
                        "featured_media_id": featured_media_id if isinstance(featured_media_id, int) else None,
                        "section_media_count": len(section_media_ids),
                    }
                    console.print(f"[green][OK][/green] Step 6: WordPress 草稿已创建 (ID: {post_id})")
                    if featured_media_id and isinstance(featured_media_id, int):
                        console.print(f"  [dim]封面图已设置 (media_id: {featured_media_id})[/dim]")
                    if section_media_ids:
                        console.print(f"  [dim]板块配图已插入 ({len(section_media_ids)} 张)[/dim]")
                else:
                    result["steps"]["wordpress"] = {"status": "failed"}
                    console.print("[yellow][WARN][/yellow] Step 6: WordPress 发布失败")

        result["success"] = True
        console.print(Panel.fit(f"[bold green]内容生成完成![/bold green]\n关键词: {keyword}"))

    except Exception as e:
        logger.exception(f"工作流执行失败: {e}")
        console.print(f"[bold red]错误:[/bold red] {e}")
        result["success"] = False

    finally:
        await llm.close()
        await serp_analyzer.close()

    return result


def build_markdown(article: dict) -> str:
    """构建 Markdown 格式文章"""
    lines = [
        f"# {article.get('h1', article.get('title', ''))}",
        "",
    ]

    # Key Takeaways
    if article.get("keyTakeaways"):
        lines.append("## Key Takeaways")
        lines.append("")
        for point in article["keyTakeaways"]:
            lines.append(f"- {point}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Main sections
    for section in article.get("sections", []):
        lines.append(f"## {section['sectionTitle']}")
        lines.append("")
        lines.append(section["content"])
        lines.append("")
        lines.append("---")
        lines.append("")

    # Sources
    if article.get("sources"):
        lines.append("## Sources and Further Reading")
        lines.append("")
        for source in article["sources"]:
            name = source.get("source", "")
            url = source.get("url", "")
            desc = source.get("description", "")
            lines.append(f"- **{name}**: {desc} [Read more]({url})")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def display_eeat_report(quality_result: dict) -> None:
    """Display detailed E-E-A-T quality assessment report"""
    from rich.columns import Columns
    from rich.text import Text

    overall_score = quality_result.get("overallScore", 0)
    overall_grade = quality_result.get("overallGrade", "Unknown")
    eeat_scores = quality_result.get("eeatScores", {})
    content_quality = quality_result.get("contentQuality", {})
    word_count = quality_result.get("wordCount", 0)
    target_word_count = quality_result.get("targetWordCount", 3000)
    issues = quality_result.get("issues", [])
    suggestions = quality_result.get("suggestions", [])

    # Grade color mapping
    grade_colors = {
        "Fair": "bright_yellow",
        "Medium": "yellow",
        "High": "green",
        "Perfect": "bright_blue",
    }

    grade_color = grade_colors.get(overall_grade, "white")

    # E-E-A-T dimension name mapping
    eeat_names = {
        "experience": ("Experience", "cyan"),
        "expertise": ("Expertise", "blue"),
        "authoritativeness": ("Authoritativeness", "magenta"),
        "trustworthiness": ("Trustworthiness", "green"),
    }

    # Content quality name mapping
    quality_names = {
        "engagement": ("Engagement", "cyan"),
        "accuracy": ("Accuracy", "blue"),
        "talent": ("Talent/Skill", "magenta"),
        "originality": ("Originality", "green"),
    }

    console.print()
    console.print(Panel.fit(
        f"[bold]E-E-A-T Quality Assessment Report[/bold]",
        title="Quality Check",
        border_style=grade_color,
    ))

    # Overall score
    console.print(f"  [dim]Overall Score:[/dim] {overall_score}/100")
    console.print(f"  [dim]Overall Grade:[/dim] [{grade_color}]{overall_grade}[/{grade_color}]")
    console.print()

    # E-E-A-T dimensions
    console.print(Panel.fit(
        Text("E-E-A-T Dimensions", style="bold"),
        border_style="dim",
    ))

    for key, (name, color) in eeat_names.items():
        data = eeat_scores.get(key, {})
        score = data.get("score", 0)
        grade = data.get("grade", "MM")
        reasoning = data.get("reasoning", "")

        console.print()
        console.print(f"  [{color}]{name}[/{color}] - [{color}]{grade}[/{color}]")
        if reasoning:
            # Wrap reasoning text, max 80 chars per line
            for i in range(0, len(reasoning), 80):
                console.print(f"  [dim]{reasoning[i:i+80]}[/dim]")

    console.print()
    console.print()

    # Content quality
    console.print(Panel.fit(
        Text("Content Quality", style="bold"),
        border_style="dim",
    ))

    for key, (name, color) in quality_names.items():
        data = content_quality.get(key, {})
        grade = data.get("grade", "MM") if isinstance(data, dict) else data
        reasoning = data.get("reasoning", "") if isinstance(data, dict) else ""

        console.print()
        console.print(f"  [{color}]{name}[/{color}] - [{color}]{grade}[/{color}]")
        if reasoning:
            for i in range(0, len(reasoning), 80):
                console.print(f"  [dim]{reasoning[i:i+80]}[/dim]")

    console.print()
    console.print()

    # Word count
    word_status = word_count >= 2000 and word_count <= 4000
    status_text = "[green]OK[/green]" if word_status else "[yellow]![/yellow]"
    console.print(f"  [dim]Word Count:[/dim] {word_count} / {target_word_count} chars {status_text}")
    console.print()

    # Suggestions
    if suggestions or issues:
        console.print(Panel.fit(
            Text("Improvement Suggestions", style="bold"),
            border_style="yellow",
        ))
        console.print()

        if issues:
            for issue in issues:
                console.print(f"  [yellow]- {issue}[/yellow]")
            console.print()

        if suggestions:
            for suggestion in suggestions:
                console.print(f"  [dim]- {suggestion}[/dim]")
        console.print()

    console.print()


# ==================== CLI 命令 ====================


@app.command()
def generate(
    keyword: str = typer.Argument(..., help="目标关键词"),
    slug: str = typer.Option(..., "--slug", "-s", help="URL slug"),
    intent: str = typer.Option("share", "--intent", "-i", help="搜索意图: share/qa/pillar"),
    skip_images: bool = typer.Option(False, "--skip-images", help="跳过图片生成"),
    skip_wordpress: bool = typer.Option(False, "--skip-wordpress", help="跳过 WordPress 发布"),
    output: str = typer.Option("", "--output", "-o", help="输出目录"),
):
    """
    生成 SEO 优化文章

    Example:
        seo-gen generate "drop shipping fulfillment services" --slug how-to-drop-shipping-fulfillment-services
    """
    import asyncio

    output_dir = Path(output) if output else None

    console.print(Panel.fit(
        f"[bold cyan]SEO Content Generator[/bold cyan]\n"
        f"关键词: {keyword}\n"
        f"Slug: {slug}\n"
        f"意图: {intent}"
    ))

    result = asyncio.run(generate_content_workflow(
        keyword=keyword,
        slug=slug,
        search_intent=intent,
        skip_images=skip_images,
        skip_wordpress=skip_wordpress,
        output_dir=output_dir,
    ))

    # 输出结果摘要
    if result["success"]:
        console.print("\n[bold]生成结果:[/bold]")
        for step, data in result["steps"].items():
            status = data.get("status", "unknown")
            icon = "[green][OK][/green]" if status in ["completed", "passed"] else "[yellow][WARN][/yellow]"
            console.print(f"  {icon} {step}: {status}")

    raise typer.Exit(0 if result["success"] else 1)


@app.command("generate-advanced")
def generate_advanced(
    keyword: str = typer.Argument(..., help="目标关键词"),
    slug: str = typer.Option("", "--slug", "-s", help="URL slug (留空自动生成)"),
    skip_images: bool = typer.Option(False, "--skip-images", help="跳过图片生成"),
    skip_wordpress: bool = typer.Option(False, "--skip-wordpress", help="跳过 WordPress 发布"),
    output: str = typer.Option("", "--output", "-o", help="输出目录"),
):
    """
    高级工作流 - 两阶段智能内容生成

    阶段1: 标题生成
      - Google 搜索调研关键词
      - SERP 分析
      - AI 生成候选标题 (5个)
      - 选择最佳标题

    阶段2: 内容创作
      - Google 搜索调研标题
      - SERP 分析文章结构
      - AI 生成文章大纲
      - AI 撰写文章内容
      - E-E-A-T 质量检测
      - 发布 WordPress 草稿

    Example:
        seo-gen generate-advanced "dropshipping automation"
        seo-gen generate-advanced "dropshipping tips" --slug dropshipping-tips-2026
    """
    import asyncio

    from seo_gen.modules.workflow import get_workflow_orchestrator

    output_dir = Path(output) if output else None

    console.print(Panel.fit(
        f"[bold cyan]Advanced SEO Content Generator[/bold cyan]\n"
        f"Keyword: {keyword}\n"
        f"Two-Stage Workflow"
    ))

    orchestrator = get_workflow_orchestrator()

    async def run_workflow():
        result = await orchestrator.run_advanced_workflow(
            keyword=keyword,
            slug=slug or None,
            skip_images=skip_images,
            skip_wordpress=skip_wordpress,
            output_dir=output_dir,
        )
        return result

    result = asyncio.run(run_workflow())

    # 显示结果
    console.print("\n[bold]Workflow Result:[/bold]")
    for stage, data in result.get("stages", {}).items():
        status = data.get("status", "unknown")
        icon = "[green][OK][/green]" if status == "completed" else "[yellow][WARN][/yellow]"
        console.print(f"  {icon} {stage}: {status}")

    if result.get("quality"):
        from seo_gen.main import display_eeat_report
        display_eeat_report(result["quality"])

    if result.get("success"):
        console.print(Panel.fit(
            f"[bold green]Advanced Workflow Completed![/bold green]\n"
            f"Keyword: {keyword}"
        ))

    raise typer.Exit(0 if result["success"] else 1)


@app.command()
def batch(
    input_file: str = typer.Argument(..., help="输入文件 (Excel 或 CSV)"),
    skip_images: bool = typer.Option(False, "--skip-images", help="跳过图片生成"),
    skip_wordpress: bool = typer.Option(False, "--skip-wordpress", help="跳过 WordPress 发布"),
):
    """
    批量生成文章

    从 Excel 或 CSV 文件读取关键词列表，批量生成文章。

    Example:
        seo-gen batch keywords.xlsx
    """
    import asyncio
    import pandas as pd

    console.print(Panel.fit(f"[bold cyan]批量生成模式[/bold cyan]\n文件: {input_file}"))

    # 读取输入文件
    df = pd.read_excel(input_file) if input_file.endswith(".xlsx") else pd.read_csv(input_file)

    console.print(f"找到 {len(df)} 个关键词")

    results = []

    for _, row in df.iterrows():
        keyword = row.get("关键词", row.get("keyword", ""))
        slug = row.get("slug", "")
        intent = row.get("搜索意图", row.get("searchIntent", "share"))

        if not keyword or not slug:
            logger.warning(f"跳过无效行: {row}")
            continue

        console.print(f"\n[bold]处理:[/bold] {keyword}")

        result = asyncio.run(generate_content_workflow(
            keyword=keyword,
            slug=slug,
            search_intent=intent,
            skip_images=skip_images,
            skip_wordpress=skip_wordpress,
        ))
        results.append(result)

    # 输出摘要
    success_count = sum(1 for r in results if r["success"])
    console.print(f"\n[bold]批量完成:[/bold] {success_count}/{len(results)} 成功")


@app.command()
def config():
    """
    显示当前配置

    显示所有环境变量和配置选项。
    """
    from rich.table import Table

    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    config_items = [
        ("API 端点", settings.openai_api_base),
        ("模型", settings.openai_model),
        ("WordPress 站点", settings.wordpress_site_url),
        ("输出目录", str(settings.output_path)),
        ("质量阈值", str(settings.quality_score_threshold)),
    ]

    for key, value in config_items:
        display_value = value if value else "[dim]未配置[/dim]"
        table.add_row(key, display_value)

    console.print(table)


@app.command()
def init():
    """
    初始化配置文件

    创建 .env 文件和必要的目录结构。
    """
    import shutil

    project_root = settings.project_root

    # 复制示例配置
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"

    if env_file.exists():
        console.print("[yellow].env 文件已存在[/yellow]")
        if not typer.confirm("是否覆盖？"):
            return
    else:
        shutil.copy(env_example, env_file)
        console.print(f"[green][OK][/green] 创建 .env 文件: {env_file}")

    # 创建输出目录
    settings.output_path.mkdir(parents=True, exist_ok=True)
    console.print(f"[green][OK][/green] 创建输出目录: {settings.output_path}")

    console.print("\n[bold cyan]下一步:[/bold cyan]")
    console.print("1. 编辑 .env 文件，填写你的 API 密钥和配置")
    console.print("2. 运行: seo-gen generate <关键词> --slug <url-slug>")


@app.command()
def version():
    """显示版本信息"""
    from seo_gen import __version__
    console.print(f"SEO Content Generator v{__version__}")


if __name__ == "__main__":
    # 修复 Windows 控制台编码问题
    import sys
    import io

    if sys.platform == "win32":
        # 设置 UTF-8 编码
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # 配置日志
    logger.remove()
    logger.add(
        settings.output_path / "seo_gen.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.log_level,
    )
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    app()
