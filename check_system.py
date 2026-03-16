#!/usr/bin/env python3
"""
SEO 内容生成器 — 全系统接通检查
检查所有模块导入、API连接、新模块初始化
"""

import sys
import os
import asyncio
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))
os.chdir(str(Path(__file__).parent))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
SKIP = "⏭️"

results = {}


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def record(name, ok, msg=""):
    status = PASS if ok else FAIL
    results[name] = ok
    print(f"  {status} {name}" + (f" — {msg}" if msg else ""))
    return ok


def record_warn(name, msg=""):
    results[name] = None
    print(f"  {WARN} {name}" + (f" — {msg}" if msg else ""))


# ============================================================
# 1. 基础环境
# ============================================================
section("1. 基础环境")

import platform
py_ver = platform.python_version()
record("Python 版本", True, py_ver)

try:
    from seo_gen.config import settings
    record("config.py 加载", True)
except Exception as e:
    record("config.py 加载", False, str(e))
    print("   ❌ 无法继续，config 是核心依赖")
    sys.exit(1)


# ============================================================
# 2. 所有模块 Import 检查
# ============================================================
section("2. 模块 Import 检查")

modules_to_check = [
    ("LLMClient", "seo_gen.modules.llm", "LLMClient"),
    ("SERPAnalyzer", "seo_gen.modules.serp", "SERPAnalyzer"),
    ("ContentGenerator", "seo_gen.modules.content", "ContentGenerator"),
    ("ImageGenerator", "seo_gen.modules.image", "ImageGenerator"),
    ("WordPressPublisher", "seo_gen.modules.wordpress", "WordPressPublisher"),
    ("QualityChecker(旧)", "seo_gen.modules.quality", "QualityChecker"),
    ("QualityChecker(新)", "seo_gen.modules.quality_checker", "QualityChecker"),
    ("FeishuClient", "seo_gen.modules.feishu", "FeishuClient"),
    ("KnowledgeBase", "seo_gen.modules.knowledge", "KnowledgeBase"),
    ("ContentClassifier", "seo_gen.modules.content_classifier", "ContentClassifier"),
    ("ASGKnowledgeBase", "seo_gen.modules.asg_knowledge", "ASGKnowledgeBase"),
    ("TitleGenerator", "seo_gen.modules.title", "TitleGenerator"),
    ("OutlineGenerator", "seo_gen.modules.outline", "OutlineGenerator"),
    ("StructureAnalyzer", "seo_gen.modules.structure", "StructureAnalyzer"),
    ("ContentDetector", "seo_gen.modules.detection", "ContentDetector"),
    ("InternalLinkManager", "seo_gen.modules.internal_links", "get_internal_link_manager"),
    # 新增模块
    ("CheckpointManager ⭐", "seo_gen.modules.checkpoint", "CheckpointManager"),
    ("CompetitorScraper ⭐", "seo_gen.modules.competitor_scraper", "CompetitorScraper"),
    ("GEOOptimizer ⭐", "seo_gen.modules.geo_optimizer", "GEOOptimizer"),
    ("SchemaGenerator ⭐", "seo_gen.modules.schema_generator", "SchemaGenerator"),
    ("ArticleTracker ⭐", "seo_gen.modules.article_tracker", "ArticleTracker"),
    ("KeywordDataClient ⭐", "seo_gen.modules.keyword_data", "KeywordDataClient"),
]

import importlib
for display_name, module_path, class_name in modules_to_check:
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        record(display_name, True)
    except Exception as e:
        record(display_name, False, str(e)[:80])

# __init__.py 聚合导入
try:
    from seo_gen.modules import (
        LLMClient, SERPAnalyzer, ContentGenerator, ImageGenerator,
        WordPressPublisher, QualityChecker, FeishuClient, KnowledgeBase,
        ContentClassifier, CheckpointManager, CompetitorScraper,
        GEOOptimizer, SchemaGenerator, ArticleTracker, KeywordDataClient,
    )
    record("modules/__init__.py 聚合导入", True)
except Exception as e:
    record("modules/__init__.py 聚合导入", False, str(e)[:80])

# workflow.py 导入
try:
    from seo_gen.modules.workflow import WorkflowOrchestrator
    record("WorkflowOrchestrator 导入", True)
except Exception as e:
    record("WorkflowOrchestrator 导入", False, str(e)[:80])


# ============================================================
# 3. 新模块实例化检查
# ============================================================
section("3. 新模块实例化检查")

# LLMClient
try:
    llm = LLMClient()
    record("LLMClient 实例化", True,
           f"model={settings.openai_model}")
except Exception as e:
    record("LLMClient 实例化", False, str(e)[:80])
    llm = None

# CheckpointManager
try:
    cp = CheckpointManager("outputs", "test-keyword")
    record("CheckpointManager 实例化", True)
except Exception as e:
    record("CheckpointManager 实例化", False, str(e)[:80])

# CompetitorScraper
try:
    cs = CompetitorScraper()
    record("CompetitorScraper 实例化", True)
except Exception as e:
    record("CompetitorScraper 实例化", False, str(e)[:80])

# GEOOptimizer
try:
    geo = GEOOptimizer(llm)
    record("GEOOptimizer 实例化", True)
except Exception as e:
    record("GEOOptimizer 实例化", False, str(e)[:80])

# SchemaGenerator
try:
    sg = SchemaGenerator()
    record("SchemaGenerator 实例化", True)
except Exception as e:
    record("SchemaGenerator 实例化", False, str(e)[:80])

# QualityChecker (新)
try:
    qc = QualityChecker(llm)
    record("QualityChecker(新) 实例化", True)
except Exception as e:
    record("QualityChecker(新) 实例化", False, str(e)[:80])

# ArticleTracker
try:
    at = ArticleTracker()
    # 测试基本操作
    published = at.is_published("__test_never_exist__")
    record("ArticleTracker 实例化+查询", True, f"SQLite 正常")
except Exception as e:
    record("ArticleTracker 实例化+查询", False, str(e)[:80])

# KeywordDataClient
try:
    kdc = KeywordDataClient()
    record("KeywordDataClient 实例化", True,
           f"user={settings.dataforseo_username[:20]}...")
except Exception as e:
    record("KeywordDataClient 实例化", False, str(e)[:80])

# WorkflowOrchestrator
try:
    wo = WorkflowOrchestrator()
    record("WorkflowOrchestrator 实例化", True, "所有子模块已初始化")
except Exception as e:
    record("WorkflowOrchestrator 实例化", False, str(e)[:120])


# ============================================================
# 4. API 连接检查
# ============================================================
section("4. API 连接检查")

import requests, base64

# 4.1 OpenAI / LLM API
try:
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    r = requests.post(
        f"{settings.openai_api_base}/chat/completions",
        headers=headers,
        json={
            "model": settings.openai_model,
            "messages": [{"role": "user", "content": "Say OK"}],
            "max_tokens": 5
        },
        timeout=15
    )
    if r.status_code == 200:
        reply = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        record("LLM API (OpenRouter)", True, f"回复: {reply.strip()[:30]}")
    else:
        record("LLM API (OpenRouter)", False, f"HTTP {r.status_code}: {r.text[:80]}")
except Exception as e:
    record("LLM API (OpenRouter)", False, str(e)[:80])

# 4.2 Google Search API
try:
    r = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={
            "key": settings.google_search_api_key,
            "cx": settings.google_search_engine_id,
            "q": "test", "num": 1
        },
        timeout=10
    )
    if r.status_code == 200:
        record("Google Search API", True, f"正常")
    elif r.status_code == 429:
        record_warn("Google Search API", "配额用完(429), 明天重置")
    else:
        record("Google Search API", False, f"HTTP {r.status_code}")
except Exception as e:
    record("Google Search API", False, str(e)[:80])

# 4.3 WordPress API
try:
    wp_pass = settings.wordpress_app_password.replace(" ", "")
    auth_b64 = base64.b64encode(
        f"{settings.wordpress_username}:{wp_pass}".encode()
    ).decode()
    r = requests.get(
        f"{settings.wordpress_site_url.rstrip('/')}/wp-json/wp/v2/users/me",
        headers={"Authorization": f"Basic {auth_b64}"},
        timeout=10
    )
    if r.status_code == 200:
        name = r.json().get("name", "?")
        record("WordPress API", True, f"用户: {name}")
    else:
        record("WordPress API", False, f"HTTP {r.status_code}")
except Exception as e:
    record("WordPress API", False, str(e)[:80])

# 4.4 DataForSEO API
try:
    auth_b64 = base64.b64encode(
        f"{settings.dataforseo_username}:{settings.dataforseo_password}".encode()
    ).decode()
    dfs_headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    r = requests.get(
        "https://api.dataforseo.com/v3/appendix/user_data",
        headers=dfs_headers, timeout=10
    )
    if r.status_code == 200 and r.json().get("status_code") == 20000:
        record("DataForSEO API", True, f"认证成功")
    else:
        record("DataForSEO API", False, f"HTTP {r.status_code}")
except Exception as e:
    record("DataForSEO API", False, str(e)[:80])

# 4.5 飞书 API
try:
    if settings.feishu_app_id and settings.feishu_app_secret:
        r = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={
                "app_id": settings.feishu_app_id,
                "app_secret": settings.feishu_app_secret
            },
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                record("飞书 API", True, f"Token 获取成功")
            else:
                record("飞书 API", False, f"code={data.get('code')}: {data.get('msg','')[:50]}")
        else:
            record("飞书 API", False, f"HTTP {r.status_code}")
    else:
        record_warn("飞书 API", "未配置 (可选)")
except Exception as e:
    record("飞书 API", False, str(e)[:80])

# 4.6 图片生成 API
try:
    img_base = settings.image_api_base or settings.openai_api_base
    img_key = settings.image_api_key or settings.openai_api_key
    img_model = settings.image_model

    record("图片生成 API 配置", True,
           f"model={img_model}, base={img_base[:30]}...")
except Exception as e:
    record("图片生成 API 配置", False, str(e)[:80])


# ============================================================
# 5. GEO 写作规则注入检查
# ============================================================
section("5. GEO/FAQ 写作规则注入检查")

try:
    from seo_gen.modules.content import GEO_WRITING_RULES, FAQ_WRITING_RULES
    geo_ok = "直接答案块" in GEO_WRITING_RULES and "G1" in GEO_WRITING_RULES
    faq_ok = "FAQ写作规则" in FAQ_WRITING_RULES and "65-100" in FAQ_WRITING_RULES
    record("GEO_WRITING_RULES 常量", geo_ok, f"{len(GEO_WRITING_RULES)} 字符")
    record("FAQ_WRITING_RULES 常量", faq_ok, f"{len(FAQ_WRITING_RULES)} 字符")
except Exception as e:
    record("GEO/FAQ 写作规则", False, str(e)[:80])

# 检查是否注入到 _build_context
try:
    import inspect
    from seo_gen.modules.content import ContentGenerator
    source = inspect.getsource(ContentGenerator._build_context)
    has_geo = "GEO_WRITING_RULES" in source
    has_faq = "FAQ_WRITING_RULES" in source
    record("_build_context 注入 GEO 规则", has_geo)
    record("_build_context 注入 FAQ 规则", has_faq)
except Exception as e:
    record("_build_context 规则注入", False, str(e)[:80])


# ============================================================
# 6. Workflow 集成检查
# ============================================================
section("6. Workflow 集成检查")

try:
    import inspect
    from seo_gen.modules.workflow import WorkflowOrchestrator
    wf_source = inspect.getsource(WorkflowOrchestrator.run_advanced_workflow)

    checks = {
        "article_tracker.is_published": "article_tracker.is_published" in wf_source,
        "competitor_scraper.analyze": "competitor_scraper.analyze" in wf_source,
        "geo_optimizer.analyze_geo_score": "geo_optimizer.analyze_geo_score" in wf_source,
        "geo_optimizer.inject_direct_answer": "inject_direct_answer" in wf_source,
        "schema_generator.generate_all": "schema_generator.generate_all" in wf_source,
        "article_tracker.mark_published": "article_tracker.mark_published" in wf_source,
        "CheckpointManager 初始化": "CheckpointManager" in wf_source,
    }
    for name, ok in checks.items():
        record(f"workflow 集成: {name}", ok)
except Exception as e:
    record("workflow 集成检查", False, str(e)[:80])


# ============================================================
# 7. 知识库文件检查
# ============================================================
section("7. 知识库文件检查")

knowledge_dir = Path("config/knowledge")
if knowledge_dir.exists():
    files = list(knowledge_dir.glob("*.md")) + list(knowledge_dir.glob("*.txt"))
    record("知识库目录", True, f"{len(files)} 个文件")
    for f in files[:8]:
        size = f.stat().st_size
        print(f"     📄 {f.name} ({size:,} bytes)")
else:
    record_warn("知识库目录", f"不存在: {knowledge_dir}")

# ASG 知识库
try:
    from seo_gen.modules.asg_knowledge import get_asg_knowledge_base
    asg_kb = get_asg_knowledge_base()
    ctx = asg_kb.get_context_for_keyword("dropshipping")
    record("ASG 知识库加载", True,
           f"FAQ: {len(ctx.faq_snippets)}, Cases: {len(ctx.case_studies)}")
except Exception as e:
    record("ASG 知识库加载", False, str(e)[:80])


# ============================================================
# 8. 输出目录和数据库检查
# ============================================================
section("8. 文件系统检查")

output_dir = Path(settings.output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
record("输出目录", output_dir.exists(), str(output_dir.resolve()))

tracker_path = Path(settings.tracker_db_path)
record("跟踪数据库路径", True, str(tracker_path))

# 错误日志目录
errors_dir = Path("outputs/errors")
errors_dir.mkdir(parents=True, exist_ok=True)
record("错误日志目录", True, str(errors_dir))


# ============================================================
# 9. 依赖包检查
# ============================================================
section("9. 关键依赖包检查")

deps = [
    "httpx", "loguru", "pydantic", "pydantic_settings",
    "bs4", "lxml", "requests", "openai",
]
for dep in deps:
    try:
        mod = importlib.import_module(dep)
        ver = getattr(mod, "__version__", "?")
        record(f"  {dep}", True, f"v{ver}")
    except ImportError:
        record(f"  {dep}", False, "未安装")


# ============================================================
# 总结
# ============================================================
section("📊 全系统检查总结")

passed = sum(1 for v in results.values() if v is True)
failed = sum(1 for v in results.values() if v is False)
warned = sum(1 for v in results.values() if v is None)
total = len(results)

print(f"\n  通过: {passed}/{total}")
print(f"  失败: {failed}/{total}")
print(f"  警告: {warned}/{total}")

if failed > 0:
    print(f"\n  ❌ 失败项目:")
    for name, ok in results.items():
        if ok is False:
            print(f"     • {name}")

if warned > 0:
    print(f"\n  ⚠️  警告项目:")
    for name, ok in results.items():
        if ok is None:
            print(f"     • {name}")

print()
if failed == 0:
    print("  🎉🎉🎉 全系统接通！可以开始使用！")
elif failed <= 2:
    print("  ✨ 系统基本可用，少量非关键项需关注")
else:
    print("  ⛔ 系统存在较多问题，请先修复上述失败项")

print()
sys.exit(0 if failed == 0 else 1)
