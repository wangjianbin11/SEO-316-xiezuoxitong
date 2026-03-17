# SEO系统 — 全面修复与升级指令
# 发给 Claude Code 终端执行，请按顺序完成所有任务

你是这个项目的主力工程师。项目路径：`src/seo_gen/`
请按顺序执行以下 **15个任务**，每完成一个告诉我，再继续下一个。

---

## ══════════════════════════════════════
## 第一部分：必须修复的致命Bug（7个）
## ══════════════════════════════════════

---

### 任务1 — 重写 `src/seo_gen/skills/geo_content_optimizer.py`

该文件语法完全破损，用以下内容完整替换整个文件：

```python
"""
GEO Content Optimizer Skill
优化内容以提高 AI 引擎引用频率
"""

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class GEOOptimizationResult:
    geo_score: float = 0.0
    quotable_statements: list = field(default_factory=list)
    definitions_added: list = field(default_factory=list)
    authority_signals: list = field(default_factory=list)
    structural_improvements: list = field(default_factory=list)
    before_after_scores: dict = field(default_factory=dict)
    changes_made: list = field(default_factory=list)


class GEOContentOptimizer:
    GEO_FIRST_ITEMS = {
        "C02": {"name": "Direct Answer", "priority": 1, "description": "前150字内直接回答"},
        "C09": {"name": "Structured FAQ", "priority": 2, "description": "结构化FAQ与Schema"},
        "O03": {"name": "Data in Tables", "priority": 3, "description": "数据放在表格中"},
        "O05": {"name": "JSON-LD Schema", "priority": 4, "description": "结构化数据标记"},
        "E01": {"name": "Original Data", "priority": 5, "description": "原创一手数据"},
        "O02": {"name": "Summary Box", "priority": 6, "description": "关键要点总结框"},
    }

    def get_geo_first_checklist(self) -> list:
        return [
            {"id": k, "name": v["name"], "description": v["description"], "priority": v["priority"]}
            for k, v in self.GEO_FIRST_ITEMS.items()
        ]

    def optimize_content(self, content: str, keyword: str, target_queries: list = None) -> GEOOptimizationResult:
        result = GEOOptimizationResult()
        analysis = self._analyze_content(content)
        result.quotable_statements = self._create_quotable_statements(content, keyword)
        result.definitions_added = self._add_definitions(content, keyword)
        result.authority_signals = self._add_authority_signals(content)
        result.structural_improvements = self._improve_structure(content)
        result.geo_score = analysis.get("overall_score", 0)
        result.changes_made = self._summarize_changes(analysis)
        return result

    def _analyze_content(self, content: str) -> dict:
        metrics = {
            "clear_definitions": self._count_clear_definitions(content),
            "quotable_statements": self._count_quotable(content),
            "factual_density": self._calculate_factual_density(content),
            "source_citations": content.count("http"),
            "qa_format": int(self._has_qa_format(content)),
            "authority_signals": self._count_authority_signals(content),
        }
        values = list(metrics.values())
        metrics["overall_score"] = sum(values) / len(values) if values else 0
        return metrics

    def _count_clear_definitions(self, content: str) -> int:
        patterns = [" is a ", " refers to ", " means that "]
        return sum(1 for p in patterns if p in content)

    def _count_quotable(self, content: str) -> int:
        return len(re.findall(r'"([^"]{20,})"', content))

    def _calculate_factual_density(self, content: str) -> float:
        numbers = re.findall(r'\d+[\d,.]*%?', content)
        return min(len(numbers) / 10, 1.0)

    def _count_authority_signals(self, content: str) -> int:
        lower = content.lower()
        return sum(1 for phrase in ["according to", "research", "expert"] if phrase in lower)

    def _has_qa_format(self, content: str) -> bool:
        return "?" in content and any(line.strip().endswith("?") for line in content.split("\n"))

    def _improve_structure(self, content: str) -> list:
        improvements = []
        if "|" not in content and "<table" not in content:
            improvements.append("添加比较表格")
        if "Key Takeaways" not in content:
            improvements.append("添加Key Takeaways总结框")
        return improvements

    def _create_quotable_statements(self, content: str, keyword: str) -> list:
        statements = []
        for sentence in re.split(r'(?<=[.!?])\s+', content):
            if len(sentence) > 20 and keyword.lower() in sentence.lower():
                if re.search(r'\d+', sentence):
                    statements.append(f'"{sentence.strip()}"')
        return statements[:5]

    def _add_definitions(self, content: str, keyword: str) -> list:
        patterns = [f"{keyword} is", f"{keyword} refers to", f"What is {keyword}"]
        return [f"建议添加: '{p}'" for p in patterns if p.lower() not in content.lower()][:3]

    def _add_authority_signals(self, content: str) -> list:
        signals = []
        if "according to" not in content.lower():
            signals.append("添加引用来源 (According to...)")
        return signals[:2]

    def _summarize_changes(self, analysis: dict) -> list:
        changes = []
        if analysis.get("clear_definitions", 0) == 0:
            changes.append("建议添加清晰定义")
        if analysis.get("source_citations", 0) == 0:
            changes.append("建议添加来源引用")
        return changes


_geo_content_optimizer = None

def get_geo_content_optimizer() -> GEOContentOptimizer:
    global _geo_content_optimizer
    if _geo_content_optimizer is None:
        _geo_content_optimizer = GEOContentOptimizer()
    return _geo_content_optimizer
```

---

### 任务2 — 修复 `src/seo_gen/skills/__init__.py`

用以下内容完整替换该文件：

```python
"""SEO & GEO Skills 模块"""

try:
    from .seo_content_writer import SEOContentWriter
except (SyntaxError, ImportError):
    SEOContentWriter = None

try:
    from .geo_content_optimizer import GEOContentOptimizer
except (SyntaxError, ImportError):
    GEOContentOptimizer = None

try:
    from .core_eeat import COREEEATChecker
except (SyntaxError, ImportError):
    COREEEATChecker = None

__all__ = ["SEOContentWriter", "GEOContentOptimizer", "COREEEATChecker"]
```

---

### 任务3 — 修复 `src/seo_gen/modules/workflow.py` 中的5处接口Bug

**请在workflow.py中找到并修改以下5处，其他代码保持不变：**

**修改3-A**：找到这行（约在竞品分析结果保存处）：
```python
"content_gaps": competitor_analysis.content_gaps[:3],
```
替换为：
```python
"uncovered_topics": competitor_analysis.uncovered_topics[:3],
```

**修改3-B**：找到这行（约在竞品分析调用处）：
```python
competitor_analysis = await self.competitor_scraper.analyze_competitors(top_urls)
```
替换为：
```python
_paa_questions = serp_data.get("serpAnalysis", {}).get("paaQuestions", [])
competitor_analysis = await self.competitor_scraper.analyze_competitors(
    keyword=keyword,
    urls=top_urls,
    paa_questions=_paa_questions,
    llm_client=self.llm_client
)
```

**修改3-C**：找到GEO优化部分的这段代码（约3行）：
```python
geo_score_before = self.geo_optimizer.analyze_geo_score(article.get("content", ""))
self._log(f"  GEO 优化前得分: {geo_score_before['total_score']}/100")

optimized_content = self.geo_optimizer.inject_direct_answer_blocks(
    article.get("content", ""),
    article.get("sections", [])
)
if "faq" in article:
    optimized_faq = self.geo_optimizer.optimize_faq_for_ai(article["faq"])
    article["faq"] = optimized_faq
article["content"] = optimized_content
geo_score_after = self.geo_optimizer.analyze_geo_score(optimized_content)
```
替换为：
```python
geo_score_before = self.geo_optimizer.analyze_geo_score(article)
self._log(f"  GEO 优化前得分: {geo_score_before.total_score}/100")

article = await self.geo_optimizer.inject_direct_answer_blocks(article, self.llm_client)

if "faqSection" in article:
    faq_items = article["faqSection"].get("items", [])
    if faq_items:
        optimized_faq = self.geo_optimizer.optimize_faq_for_ai(faq_items)
        article["faqSection"]["items"] = optimized_faq

geo_score_after = self.geo_optimizer.analyze_geo_score(article)
```

**修改3-D**：找到这段schema生成代码：
```python
schema_html = self.schema_generator.generate_all_schemas(
    article_title=article.get("title", ""),
    article_content=article.get("content", ""),
    article_url=f"https://asgdropshipping.com/{result['slug']}/",
    author_name="Janson",
    published_date=None,
    modified_date=None,
    image_url=cover_image_url,
    category="Dropshipping",
    faq_items=article.get("faq", [])[:8] if "faq" in article else []
)
```
替换为：
```python
_faq_list_for_schema = []
if "faqSection" in article:
    _faq_list_for_schema = article["faqSection"].get("items", [])[:8]

schema_html = self.schema_generator.generate_all_schemas(
    article=article,
    article_url=f"https://asgdropshipping.com/{result['slug']}/",
    faq_list=_faq_list_for_schema,
    category_name="Dropshipping",
    publish_date=None
)
```

**修改3-E**：找到article_tracker调用代码：
```python
self.article_tracker.mark_published(
    keyword=keyword,
    title=article.get("title", ""),
    article_type=article_type.value,
    word_count=total_word_count,
    url=f"https://asgdropshipping.com/?p={post_id}",
    post_id=post_id,
    quality_score=score,
    geo_score=geo_score_after['total_score']
)
```
替换为：
```python
self.article_tracker.mark_published(
    keyword=keyword,
    article_title=article.get("title", ""),
    article_type=article_type.value,
    word_count=total_word_count,
    wordpress_url=f"https://asgdropshipping.com/?p={post_id}",
    wp_post_id=post_id,
    quality_score=score,
    geo_score=geo_score_after.total_score
)
```

---

### 任务4 — 修复 `src/seo_gen/modules/serp.py` 默认抓取页数

找到analyze方法签名：
```python
async def analyze(self, keyword: str, total_results: int = 100) -> dict[str, Any]:
```
替换为：
```python
async def analyze(self, keyword: str, total_results: int = 30) -> dict[str, Any]:
```

---

### 任务5 — 验证前4个任务

执行以下命令，确认无报错：
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from seo_gen.modules.workflow import WorkflowOrchestrator
from seo_gen.modules.geo_optimizer import GEOOptimizer
from seo_gen.modules.schema_generator import SchemaGenerator
from seo_gen.modules.article_tracker import ArticleTracker
from seo_gen.skills import SEOContentWriter, GEOContentOptimizer, COREEEATChecker
print('✅ 所有模块导入成功')
print(f'GEOContentOptimizer: {GEOContentOptimizer}')
"
```

---

## ══════════════════════════════════════
## 第二部分：内容质量关键修复（5个）
## ══════════════════════════════════════

---

### 任务6 — 修复知识库路径硬编码问题

打开 `src/seo_gen/modules/content.py`，找到：
```python
ASG_CASE_LIBRARY_PATH = Path("/Users/apple/Documents/新的网站内容生成/asg-faq-matrix-geo_副本")
ASG_CASE_LIBRARY_ALT_PATH = Path("/Users/apple/Documents/cc-工作流/asg-faq-matrix-geo")
```
替换为：
```python
# 使用相对路径，从项目根目录开始查找
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ASG_CASE_LIBRARY_PATH = _PROJECT_ROOT / "asg-faq-matrix-geo_副本"
ASG_CASE_LIBRARY_ALT_PATH = _PROJECT_ROOT / "asg-faq-matrix-geo"
```

同时打开 `src/seo_gen/modules/asg_knowledge.py`，找到：
```python
self.base_knowledge_dir = self.knowledge_dir.parent / "asg dropshipping 基础知识_副本"
self.faq_matrix_dir = self.knowledge_dir.parent / "asg-faq-matrix-geo_副本"
self.geo_guide_dir = self.knowledge_dir.parent / "GEO指南_副本"
```
在这三行**之后**加入路径存在性检查和日志：
```python
# 检查路径是否存在，提前告警
if not self.base_knowledge_dir.exists():
    import logging
    logging.warning(f"[ASG知识库] 基础知识目录不存在: {self.base_knowledge_dir}")
if not self.faq_matrix_dir.exists():
    import logging
    logging.warning(f"[ASG知识库] FAQ矩阵目录不存在: {self.faq_matrix_dir}")
```

---

### 任务7 — 修复图片ALT被覆盖问题

打开 `src/seo_gen/modules/content.py`，在 `build_wordpress_html` 方法中，找到：
```python
# 使用具体的描述性 alt text，不使用通用描述
alt_text = f"{title} - Professional Guide"
html_parts.append(f'<img src="{section_images[str(idx)]}" alt="{alt_text}"
```
替换为（使用LLM生成的具体alt text）：
```python
# 优先使用LLM生成的具体alt text，回退到section标题
section_image_meta = section.get("image", {})
alt_text = section_image_meta.get("alt", "") or f"{title} - {keyword} guide"
# 清理alt text中的特殊字符
alt_text = alt_text.replace('"', "'").replace('<', '').replace('>', '')
html_parts.append(f'<img src="{section_images[str(idx)]}" alt="{alt_text}"
```

---

### 任务8 — 在generate_article中加入FAQ生成

打开 `src/seo_gen/modules/content.py`，找到 `generate_article` 方法的 `messages` 中，
在 `"sections"` JSON格式说明之后（找到 `"externalLinkCount": 5` 那一行后面），加入FAQ字段说明。

具体操作：在OUTPUT FORMAT (JSON)的json示例中，找到：
```
  "actualSectionCount": {target_sections},
  "totalWordCount": 2800,
  "imageCount": 4,
  "externalLinkCount": 5
}}
```
替换为：
```
  "actualSectionCount": {target_sections},
  "totalWordCount": 2800,
  "imageCount": 4,
  "externalLinkCount": 5,
  "faqSection": {{
    "items": [
      {{
        "question": "完整的问题（来自Google PAA或用户常见问题）",
        "answer": "直接回答（65-100词，自成一体，包含具体数字，以事实开头）"
      }}
    ]
  }}
}}
```

同时在user message的Requirements列表末尾加入：
```
18. FAQ SECTION - 必须生成6-8个FAQ，来源优先级：Google PAA问题 > 竞品FAQ > 用户常见疑问
    - 每个答案65-100词（英文）
    - 第一句直接回答（Yes/No/数字/核心事实）
    - 包含至少1个具体数字
    - 自成一体，不引用"上文"
```

---

### 任务9 — 修复字数目标混淆（字符vs词）

打开 `src/seo_gen/modules/content.py`，找到：
```python
total_words = 2800  # 总字数目标
intro_words = 200    # 引言字数
words_per_section = (total_words - intro_words) // target_sections
```
替换为（添加注释说明并修正prompt中的措辞）：
```python
# 注意：这里的单位是"words（词）"，英文约等于15,000-18,000字符
# 2500-3000 words 是标准博客文章长度
target_word_count = 2800  # 目标词数（words，不是characters）
intro_words = 200    # 引言词数
words_per_section = (target_word_count - intro_words) // target_sections
```

同时在system message中找到：
```
WORD COUNT: ~2800 characters total (2500-3000 range)
```
替换为：
```
WORD COUNT: 2500-3000 WORDS total (NOT characters - this means approximately 15,000-18,000 characters)
Each section: 300-400 words. Introduction: 150-200 words.
```

---

### 任务10 — 将竞品分析数据传入文章生成

打开 `src/seo_gen/modules/workflow.py`，找到调用 `generate_article` 的代码：
```python
article = await self.content_generator.generate_article(
    keyword=keyword,
    slug=result["slug"],
    serp_analysis=serp_data,
    structure_analysis=structure_analysis,
    article_type=article_type.value,
)
```
替换为：
```python
# 构建竞品上下文，传入文章生成
competitor_context = ""
if competitor_analysis and competitor_analysis.total_scraped > 0:
    competitor_context = f"""
COMPETITOR ANALYSIS INSIGHTS (从真实竞品文章提取，必须参考):
- 建议目标字数: {competitor_analysis.target_word_count} words (基于前3名平均 × 1.15)
- 竞品主流格式: {competitor_analysis.dominant_format}
- 竞品覆盖的H2话题 (你必须覆盖这些): {', '.join(competitor_analysis.all_h2_topics[:10])}
- 竞品未覆盖的话题 (这是你的差异化机会): {', '.join(competitor_analysis.uncovered_topics[:5])}
- 竞品弱点: {competitor_analysis.weakness_summary}
"""

article = await self.content_generator.generate_article(
    keyword=keyword,
    slug=result["slug"],
    serp_analysis=serp_data,
    structure_analysis=structure_analysis,
    article_type=article_type.value,
    competitor_context=competitor_context,
)
```

然后打开 `src/seo_gen/modules/content.py`，在 `generate_article` 方法签名中加入参数：
```python
async def generate_article(
    self,
    keyword: str,
    slug: str,
    serp_analysis: dict[str, Any],
    structure_analysis: Optional[dict[str, Any]] = None,
    article_type: Optional[str] = None,
    competitor_context: str = "",  # 新增参数
) -> dict[str, Any]:
```

同时在该方法的user message末尾（找到"Remember: The goal is to write like a real expert"那行之前），加入：
```python
# 在user message的content字符串末尾拼接竞品信息
if competitor_context:
    # 找到user message并在末尾加入竞品上下文
```

具体实现：找到messages列表中user role的content字符串，在最后的 `Remember: The goal is to write like a real expert (Janson), not follow a template."""` 之前插入：

```
{competitor_context if competitor_context else ""}
```

---

## ══════════════════════════════════════
## 第三部分：GEO/SEO技术修复（3个）
## ══════════════════════════════════════

---

### 任务11 — 修复geo_optimizer.inject_direct_answer_blocks操作sections

打开 `src/seo_gen/modules/geo_optimizer.py`，找到 `inject_direct_answer_blocks` 方法，
用以下完整代码替换整个方法体：

```python
async def inject_direct_answer_blocks(self, article: dict, llm_client: Any = None) -> dict:
    """
    为每个section注入直接答案块（操作sections列表，不是顶层content字段）
    """
    client = llm_client or self.llm_client
    if not client:
        logger.warning("No LLM client available, skipping direct answer block injection")
        return article

    sections = article.get("sections", [])
    if not sections:
        logger.warning("No sections found, skipping direct answer block injection")
        return article

    for i, section in enumerate(sections):
        section_title = section.get("sectionTitle", "")
        section_content = section.get("content", "")

        if not section_title or not section_content:
            continue

        # 检查是否已有答案块
        if 'class="geo-answer-block"' in section_content or "geo-answer-block" in section_content:
            logger.debug(f"Section {i+1} already has answer block, skipping")
            continue

        try:
            answer_text = await self._generate_direct_answer(section_title, client)

            answer_block = (
                f'<div class="geo-answer-block" itemscope itemtype="https://schema.org/Answer">'
                f'<p itemprop="text">{answer_text}</p>'
                f'</div>\n\n'
            )

            sections[i]["content"] = answer_block + section_content
            logger.debug(f"✓ Injected answer block for: {section_title[:50]}")

        except Exception as e:
            logger.error(f"Failed to generate answer block for '{section_title}': {e}")
            continue

    article["sections"] = sections

    # 同步更新顶层content字段（如果存在）
    if "content" in article:
        article["content"] = "\n\n".join(s.get("content", "") for s in sections)

    return article
```

---

### 任务12 — 修复analyze_geo_score接收dict而非string

打开 `src/seo_gen/modules/geo_optimizer.py`，找到 `analyze_geo_score` 方法签名：
```python
def analyze_geo_score(self, article: dict) -> GEOScore:
    content_html = article.get("content", "")
```
在 `content_html = article.get("content", "")` 这行**之后**加入：

```python
# 如果顶层content为空，从sections中拼接
if not content_html:
    sections = article.get("sections", [])
    content_html = "\n\n".join(s.get("content", "") for s in sections)
```

---

### 任务13 — 修复Schema注入位置（body→head）

打开 `src/seo_gen/modules/workflow.py`，找到：
```python
# 将 Schema 注入到 HTML 末尾
html_content = html_content + "\n\n" + schema_html
```
替换为：
```python
# Schema应注入<head>，通过WordPress wp_head钩子
# 这里先注入到HTML开头（WordPress会识别script标签位置）
# 更好的方案：通过Yoast SEO或Custom Header plugin注入
# 当前方案：注入到文章最开头，WordPress通常能正确处理
html_content = schema_html + "\n\n" + html_content
```

---

## ══════════════════════════════════════
## 第四部分：激活未使用的功能（2个）
## ══════════════════════════════════════

---

### 任务14 — 激活DataForSEO关键词数据采集

打开 `src/seo_gen/modules/workflow.py`，找到以下代码段（约在SERP分析完成后、标题生成前）：
```python
result["stages"]["serp_analysis"] = {"status": "completed", "data": serp_data}
self._log(f"✓ 搜索意图: {serp_data.get('primaryIntent', 'N/A')}")
self._update_step(1, "completed", "分析 SERP - 完成", 0.12)

# 1.1.5 竞争对手内容分析（新增）
```
在 `self._update_step(1, "completed", "分析 SERP - 完成", 0.12)` 和 `# 1.1.5` 之间插入：

```python
# 1.1.3 获取关键词真实数据（DataForSEO）
if self.keyword_data_client.enabled:
    self._log(f"[1.2/11] 正在获取关键词真实数据...")
    try:
        kw_metrics_list = await self.keyword_data_client.get_keyword_metrics([keyword])
        if kw_metrics_list:
            kw_metrics = kw_metrics_list[0]
            result["keyword_metrics"] = {
                "monthly_volume": kw_metrics.monthly_volume,
                "kd_score": kw_metrics.kd_score,
                "cpc": kw_metrics.cpc,
                "competition_level": kw_metrics.competition_level,
                "data_source": kw_metrics.data_source,
            }
            self._log(f"✓ 关键词数据: 月搜索量={kw_metrics.monthly_volume}, KD={kw_metrics.kd_score:.0f}, CPC=${kw_metrics.cpc:.2f}")
    except Exception as e:
        self._log(f"⚠️  关键词数据获取失败（不影响流程）: {e}")
else:
    self._log(f"  ℹ️  DataForSEO未配置，跳过关键词数据采集")
```

---

### 任务15 — 全面验证 + 生成测试报告

执行以下验证命令，把所有输出告诉我：

```bash
# 验证1：包导入
python -c "
import sys
sys.path.insert(0, 'src')
print('=== 包导入测试 ===')
from seo_gen.modules.workflow import WorkflowOrchestrator
from seo_gen.modules.geo_optimizer import GEOOptimizer
from seo_gen.modules.schema_generator import SchemaGenerator
from seo_gen.modules.article_tracker import ArticleTracker
from seo_gen.modules.content import ContentGenerator
from seo_gen.modules.competitor_scraper import CompetitorScraper
from seo_gen.skills import SEOContentWriter, GEOContentOptimizer, COREEEATChecker
print('✅ 所有模块导入成功')
print(f'GEOContentOptimizer: {GEOContentOptimizer}')
"

# 验证2：article_tracker方法签名
python -c "
import sys
sys.path.insert(0, 'src')
import inspect
from seo_gen.modules.article_tracker import ArticleTracker
sig = inspect.signature(ArticleTracker.mark_published)
print('=== ArticleTracker.mark_published 签名 ===')
print(sig)
"

# 验证3：geo_optimizer方法签名
python -c "
import sys
sys.path.insert(0, 'src')
import inspect
from seo_gen.modules.geo_optimizer import GEOOptimizer
sig = inspect.signature(GEOOptimizer.inject_direct_answer_blocks)
print('=== GEOOptimizer.inject_direct_answer_blocks 签名 ===')
print(sig)
"

# 验证4：schema_generator方法签名
python -c "
import sys
sys.path.insert(0, 'src')
import inspect
from seo_gen.modules.schema_generator import SchemaGenerator
sig = inspect.signature(SchemaGenerator.generate_all_schemas)
print('=== SchemaGenerator.generate_all_schemas 签名 ===')
print(sig)
"
```

---

## ══════════════════════════════════════
## 完成后请输出完整报告
## ══════════════════════════════════════

所有任务完成后，请输出：

1. **每个任务的状态**（✅完成 / ❌失败 + 原因）
2. **4个验证命令的实际输出**
3. **如果在任何文件中发现了额外的bug，一并列出**

**严格要求**：
- 不修改任何未在本指令中提到的代码
- 每个任务完成后告知我，等我确认再继续
- 如果某个"找到XX代码"找不到，告诉我，不要自己猜测修改其他位置

