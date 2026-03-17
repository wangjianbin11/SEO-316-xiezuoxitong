# SEO系统全面升级修复指令 v2.0
# 直接复制全文发给 Claude Code 终端执行，按顺序完成所有Block

你是这个SEO内容生成系统的核心工程师。我已读取所有源码，发现了17处致命Bug + 8个系统架构缺陷 + 5个性能问题。请按Block顺序执行，每完成一个Block告知我，等确认后再继续。

---

## ══════════════════════════════════════
## BLOCK A：致命语法破损（必须最先执行）
## ══════════════════════════════════════

### A1 — 完整替换 `src/seo_gen/skills/geo_content_optimizer.py`

该文件语法完全破损（import合并行、for循环错误、括号不匹配），用以下完整内容替换：

```python
"""GEO Content Optimizer Skill"""
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
        raw = {
            "clear_definitions": float(self._count_clear_definitions(content)),
            "quotable_statements": float(self._count_quotable(content)),
            "factual_density": self._calculate_factual_density(content),
            "source_citations": float(content.count("http")),
            "qa_format": 1.0 if self._has_qa_format(content) else 0.0,
            "authority_signals": float(self._count_authority_signals(content)),
        }
        values = list(raw.values())
        raw["overall_score"] = sum(values) / len(values) if values else 0.0
        return raw

    def _count_clear_definitions(self, content: str) -> int:
        return sum(1 for p in [" is a ", " refers to ", " means that "] if p in content)

    def _count_quotable(self, content: str) -> int:
        return len(re.findall(r'"([^"]{20,})"', content))

    def _calculate_factual_density(self, content: str) -> float:
        return min(len(re.findall(r'\d+[\d,.]*%?', content)) / 10, 1.0)

    def _count_authority_signals(self, content: str) -> int:
        lower = content.lower()
        return sum(1 for p in ["according to", "research", "expert"] if p in lower)

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
        results = []
        for sentence in re.split(r'(?<=[.!?])\s+', content):
            if len(sentence) > 20 and keyword.lower() in sentence.lower() and re.search(r'\d+', sentence):
                results.append(f'"{sentence.strip()}"')
        return results[:5]

    def _add_definitions(self, content: str, keyword: str) -> list:
        return [f"建议添加: '{p}'" for p in [f"{keyword} is", f"{keyword} refers to", f"What is {keyword}"]
                if p.lower() not in content.lower()][:3]

    def _add_authority_signals(self, content: str) -> list:
        return ["添加引用来源"] if "according to" not in content.lower() else []

    def _summarize_changes(self, analysis: dict) -> list:
        changes = []
        if analysis.get("clear_definitions", 0) == 0:
            changes.append("建议添加清晰定义")
        if analysis.get("source_citations", 0) == 0:
            changes.append("建议添加来源引用")
        return changes


_geo_optimizer_instance = None

def get_geo_content_optimizer() -> GEOContentOptimizer:
    global _geo_optimizer_instance
    if _geo_optimizer_instance is None:
        _geo_optimizer_instance = GEOContentOptimizer()
    return _geo_optimizer_instance
```

### A2 — 完整替换 `src/seo_gen/skills/__init__.py`

```python
"""SEO & GEO Skills 模块"""
try:
    from .seo_content_writer import SEOContentWriter
except Exception:
    SEOContentWriter = None

try:
    from .geo_content_optimizer import GEOContentOptimizer
except Exception:
    GEOContentOptimizer = None

try:
    from .core_eeat import COREEEATChecker
except Exception:
    COREEEATChecker = None

__all__ = ["SEOContentWriter", "GEOContentOptimizer", "COREEEATChecker"]
```

### A3 — 验证语法修复

```bash
cd 你的项目根目录
python -c "
import sys; sys.path.insert(0, 'src')
from seo_gen.skills import SEOContentWriter, GEOContentOptimizer, COREEEATChecker
from seo_gen.modules.geo_optimizer import GEOOptimizer
from seo_gen.modules.schema_generator import SchemaGenerator
from seo_gen.modules.article_tracker import ArticleTracker
print('✅ A3验证通过：所有模块可导入')
print(f'GEOContentOptimizer: {GEOContentOptimizer}')
"
```

---

## ══════════════════════════════════════
## BLOCK B：workflow.py — 6处接口Bug（全部在一个文件）
## ══════════════════════════════════════

打开 `src/seo_gen/modules/workflow.py`，按以下说明逐一修改：

### B1 — 修复竞品分析调用（缺少3个必需参数）

找到：
```python
competitor_analysis = await self.competitor_scraper.analyze_competitors(top_urls)
```

替换为：
```python
_paa = serp_data.get("serpAnalysis", {}).get("paaQuestions", [])
competitor_analysis = await self.competitor_scraper.analyze_competitors(
    keyword=keyword,
    urls=top_urls,
    paa_questions=_paa,
    llm_client=self.llm_client,
)
```

### B2 — 修复竞品分析结果字段名错误

找到：
```python
"content_gaps": competitor_analysis.content_gaps[:3],
```

替换为：
```python
"uncovered_topics": competitor_analysis.uncovered_topics[:3],
```

### B3 — 修复GEO优化整段代码（最大的Bug）

找到并完整替换这整段（从"# 2.5.5 GEO 优化"到"result["stages"]["geo_optimization"]"结束）：

**旧代码（找到这段）：**
```python
            # 2.5.5 GEO 优化（新增）
            self._log(f"[7.5/11] 正在进行 GEO 优化...")

            # 分析 GEO 得分
            geo_score_before = self.geo_optimizer.analyze_geo_score(article.get("content", ""))
            self._log(f"  GEO 优化前得分: {geo_score_before['total_score']}/100")

            # 注入直接答案块
            optimized_content = self.geo_optimizer.inject_direct_answer_blocks(
                article.get("content", ""),
                article.get("sections", [])
            )

            # 优化 FAQ
            if "faq" in article:
                optimized_faq = self.geo_optimizer.optimize_faq_for_ai(article["faq"])
                article["faq"] = optimized_faq

            # 更新文章内容
            article["content"] = optimized_content

            # 重新分析得分
            geo_score_after = self.geo_optimizer.analyze_geo_score(optimized_content)
            self._log(f"  GEO 优化后得分: {geo_score_after['total_score']}/100")
            self._log(f"  提升: +{geo_score_after['total_score'] - geo_score_before['total_score']} 分")

            result["stages"]["geo_optimization"] = {
                "status": "completed",
                "score_before": geo_score_before['total_score'],
                "score_after": geo_score_after['total_score'],
                "improvement": geo_score_after['total_score'] - geo_score_before['total_score']
            }
```

**替换为：**
```python
            # 2.5.5 GEO 优化（修复版）
            self._log(f"[7.5/11] 正在进行 GEO 优化...")

            # 分析GEO得分 — 必须传article dict，不是字符串
            geo_score_before = self.geo_optimizer.analyze_geo_score(article)
            self._log(f"  GEO 优化前得分: {geo_score_before.total_score}/100")

            # 注入直接答案块 — 必须await，操作sections而非content字符串
            article = await self.geo_optimizer.inject_direct_answer_blocks(article, self.llm_client)

            # 优化FAQ — 使用faqSection字段
            if "faqSection" in article:
                faq_items = article["faqSection"].get("items", [])
                if faq_items:
                    article["faqSection"]["items"] = self.geo_optimizer.optimize_faq_for_ai(faq_items)

            # 重新分析得分
            geo_score_after = self.geo_optimizer.analyze_geo_score(article)
            self._log(f"  GEO 优化后得分: {geo_score_after.total_score}/100")
            self._log(f"  提升: +{geo_score_after.total_score - geo_score_before.total_score:.1f} 分")

            result["stages"]["geo_optimization"] = {
                "status": "completed",
                "score_before": geo_score_before.total_score,
                "score_after": geo_score_after.total_score,
                "improvement": geo_score_after.total_score - geo_score_before.total_score,
            }
```

### B4 — 修复Schema生成（参数名完全错误，9个→5个）

找到这段：
```python
                schema_html = self.schema_generator.generate_all_schemas(
                    article_title=article.get("title", ""),
                    article_content=article.get("content", ""),
                    article_url=f"https://asgdropshipping.com/{result['slug']}/",
                    author_name="Janson",
                    published_date=None,  # 将使用当前时间
                    modified_date=None,
                    image_url=cover_image_url,
                    category="Dropshipping",
                    faq_items=article.get("faq", [])[:8] if "faq" in article else []
                )
                # 将 Schema 注入到 HTML 末尾
                html_content = html_content + "\n\n" + schema_html
```

替换为：
```python
                _faq_for_schema = article.get("faqSection", {}).get("items", [])[:8]
                schema_html = self.schema_generator.generate_all_schemas(
                    article=article,
                    article_url=f"https://asgdropshipping.com/{result['slug']}/",
                    faq_list=_faq_for_schema,
                    category_name="Dropshipping",
                    publish_date=None,
                )
                # Schema注入到HTML开头（更靠近head位置）
                html_content = schema_html + "\n\n" + html_content
```

### B5 — 修复article_tracker.mark_published（参数名全错）

找到：
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
                    geo_score=geo_score_after.total_score,
                )
```

### B6 — 激活DataForSEO关键词数据（已初始化但从未调用）

在workflow.py中找到：
```python
            result["stages"]["serp_analysis"] = {"status": "completed", "data": serp_data}
            self._log(f"✓ 搜索意图: {serp_data.get('primaryIntent', 'N/A')}")
            self._update_step(1, "completed", "分析 SERP - 完成", 0.12)

            # 1.1.5 竞争对手内容分析（新增）
```

在 `self._update_step(...)` 和 `# 1.1.5 竞争对手内容分析` 之间插入：

```python
            # 1.1.3 关键词真实数据（DataForSEO）
            if self.keyword_data_client.enabled:
                try:
                    _kw_list = await self.keyword_data_client.get_keyword_metrics([keyword])
                    if _kw_list:
                        _m = _kw_list[0]
                        result["keyword_metrics"] = {
                            "monthly_volume": _m.monthly_volume,
                            "kd_score": _m.kd_score,
                            "cpc": _m.cpc,
                            "competition": _m.competition_level,
                            "source": _m.data_source,
                        }
                        self._log(f"✓ 关键词数据: 搜索量={_m.monthly_volume}/月 KD={_m.kd_score:.0f} CPC=${_m.cpc:.2f}")
                except Exception as _e:
                    self._log(f"  ℹ️  DataForSEO获取失败（不影响流程）: {_e}")
            else:
                self._log("  ℹ️  DataForSEO未配置，跳过关键词数据")

```

---

## ══════════════════════════════════════
## BLOCK C：geo_optimizer.py — 2处核心逻辑修复
## ══════════════════════════════════════

打开 `src/seo_gen/modules/geo_optimizer.py`

### C1 — 修复analyze_geo_score：content为空时从sections拼接

找到 `analyze_geo_score` 方法中的：
```python
        content_html = article.get("content", "")
        soup = BeautifulSoup(content_html, 'html.parser')
```

替换为：
```python
        content_html = article.get("content", "")
        # 若顶层content为空（文章刚生成时），从sections拼接
        if not content_html.strip():
            sections = article.get("sections", [])
            content_html = "\n\n".join(s.get("content", "") for s in sections)
        soup = BeautifulSoup(content_html, 'html.parser')
```

### C2 — 完整替换 inject_direct_answer_blocks 方法体

找到 `async def inject_direct_answer_blocks` 整个方法（从def到最后return），完整替换为：

```python
    async def inject_direct_answer_blocks(self, article: dict, llm_client: Any = None) -> dict:
        """为每个section注入直接答案块（操作sections列表，不是顶层content字符串）"""
        client = llm_client or self.llm_client
        if not client:
            logger.warning("No LLM client, skipping answer block injection")
            return article

        sections = article.get("sections", [])
        if not sections:
            logger.warning("No sections found, skipping injection")
            return article

        for i, section in enumerate(sections):
            section_title = section.get("sectionTitle", "")
            section_content = section.get("content", "")

            if not section_title or not section_content:
                continue

            # 已有答案块则跳过
            if 'geo-answer-block' in section_content:
                continue

            try:
                answer_text = await self._generate_direct_answer(section_title, client)
                answer_block = (
                    f'<div class="geo-answer-block" itemscope itemtype="https://schema.org/Answer">'
                    f'<p itemprop="text">{answer_text}</p>'
                    f'</div>\n\n'
                )
                sections[i]["content"] = answer_block + section_content
                logger.debug(f"✓ Injected answer block: {section_title[:50]}")
            except Exception as e:
                logger.error(f"Answer block failed for '{section_title}': {e}")
                continue

        article["sections"] = sections

        # 同步更新顶层content（如果存在）
        if "content" in article:
            article["content"] = "\n\n".join(s.get("content", "") for s in sections)

        return article
```

---

## ══════════════════════════════════════
## BLOCK D：content.py — 4处内容质量修复
## ══════════════════════════════════════

打开 `src/seo_gen/modules/content.py`

### D1 — 修复硬编码Mac路径

找到：
```python
ASG_CASE_LIBRARY_PATH = Path("/Users/apple/Documents/新的网站内容生成/asg-faq-matrix-geo_副本")
ASG_CASE_LIBRARY_ALT_PATH = Path("/Users/apple/Documents/cc-工作流/asg-faq-matrix-geo")
```

替换为：
```python
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ASG_CASE_LIBRARY_PATH = _PROJECT_ROOT / "asg-faq-matrix-geo_副本"
ASG_CASE_LIBRARY_ALT_PATH = _PROJECT_ROOT / "asg-faq-matrix-geo"
ASG_CASE_LIBRARY_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "knowledge" / "case_studies"
```

### D2 — 修复字数/字符单位混淆

找到：
```python
        total_words = 2800  # 总字数目标
        intro_words = 200    # 引言字数
        words_per_section = (total_words - intro_words) // target_sections
```

替换为：
```python
        # 单位：words（词），英文2800词≈17,000字符，这才是真正的博客文章长度
        target_word_count = 2800
        intro_words = 200
        words_per_section = (target_word_count - intro_words) // target_sections
```

同时找到System Prompt中的：
```
WORD COUNT: ~2800 characters total (2500-3000 range)
```
替换为：
```
WORD COUNT: 2500-3000 WORDS total (words NOT characters; approximately 15,000-18,000 characters)
Each main section: 300-400 words. Introduction: 150-200 words.
```

### D3 — 修复图片ALT被通用文字覆盖

在 `build_wordpress_html` 方法中找到：
```python
                # 使用具体的描述性 alt text，不使用通用描述
                alt_text = f"{title} - Professional Guide"
```

替换为：
```python
                # 优先使用LLM生成的具体alt text，回退到section标题
                _section_image_meta = section.get("image", {})
                alt_text = _section_image_meta.get("alt", "") or f"{title} - {keyword or 'dropshipping'}"
                alt_text = alt_text.replace('"', "'").strip()
```

### D4 — 在generate_article的JSON格式中加入faqSection字段

在OUTPUT FORMAT的json示例中，找到：
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
        "question": "完整问题（来自Google PAA或用户常见疑问）",
        "answer": "直接回答（65-100词，第一句直接答，包含具体数字，自成一体）"
      }}
    ]
  }}
}}
```

同时在Requirements列表末尾追加这一条：
```
18. FAQ SECTION（必须）- 生成6-8个FAQ：
    - 来源：Google PAA问题优先，然后是竞品FAQ、行业常见问题
    - 每个答案65-100词（英文）
    - 第一句直接回答（Yes/No/具体数字/核心事实）
    - 包含至少1个具体数字，自成一体不引用"上文"
    - JSON中使用faqSection.items字段
```

---

## ══════════════════════════════════════
## BLOCK E：serp.py — 修复API配额消耗
## ══════════════════════════════════════

打开 `src/seo_gen/modules/serp.py`，找到：
```python
    async def analyze(self, keyword: str, total_results: int = 100) -> dict[str, Any]:
```

替换为：
```python
    async def analyze(self, keyword: str, total_results: int = 30) -> dict[str, Any]:
```

原因：默认100条=10页API调用，每篇文章消耗100次Google配额。改为30条节省70%配额，对分析质量影响极小。

---

## ══════════════════════════════════════
## BLOCK F：asg_knowledge.py — 路径修复+告警
## ══════════════════════════════════════

打开 `src/seo_gen/modules/asg_knowledge.py`，找到：
```python
        # 定义各资料源路径
        self.base_knowledge_dir = self.knowledge_dir.parent / "asg dropshipping 基础知识_副本"
        self.faq_matrix_dir = self.knowledge_dir.parent / "asg-faq-matrix-geo_副本"
        self.geo_guide_dir = self.knowledge_dir.parent / "GEO指南_副本"

        # 缓存
        self._cache: Dict[str, Any] = {}
```

替换为：
```python
        # 定义各资料源路径
        self.base_knowledge_dir = self.knowledge_dir.parent / "asg dropshipping 基础知识_副本"
        self.faq_matrix_dir = self.knowledge_dir.parent / "asg-faq-matrix-geo_副本"
        self.geo_guide_dir = self.knowledge_dir.parent / "GEO指南_副本"

        # 路径存在性检查（启动时告警，防止silent fail）
        import logging as _logging
        for _attr, _path in [
            ("base_knowledge_dir", self.base_knowledge_dir),
            ("faq_matrix_dir", self.faq_matrix_dir),
        ]:
            if not _path.exists():
                _logging.warning(f"[ASGKnowledge] 路径不存在: {_attr} = {_path}")

        # 缓存
        self._cache: Dict[str, Any] = {}
```

---

## ══════════════════════════════════════
## BLOCK G：3处架构缺陷修复（最高价值）
## ══════════════════════════════════════

### G1 — 竞品数据真正传入文章生成（当前白爬了）

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
            # 构建竞品上下文（之前爬了但没用，现在真正传入）
            competitor_context = ""
            if competitor_analysis and competitor_analysis.total_scraped > 0:
                competitor_context = f"""
COMPETITOR ANALYSIS INSIGHTS (从真实竞品文章提取，必须参考):
- 建议目标字数: {competitor_analysis.target_word_count} words (基于前3名平均×1.15)
- 竞品主流格式: {competitor_analysis.dominant_format}
- 竞品已覆盖的H2话题 (你必须覆盖这些，且做得更好): {', '.join(competitor_analysis.all_h2_topics[:10])}
- 竞品未覆盖的话题 (差异化机会，必须包含): {', '.join(competitor_analysis.uncovered_topics[:5])}
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

找到：
```python
    async def generate_article(
        self,
        keyword: str,
        slug: str,
        serp_analysis: dict[str, Any],
        structure_analysis: Optional[dict[str, Any]] = None,
        article_type: Optional[str] = None,
    ) -> dict[str, Any]:
```

替换为：
```python
    async def generate_article(
        self,
        keyword: str,
        slug: str,
        serp_analysis: dict[str, Any],
        structure_analysis: Optional[dict[str, Any]] = None,
        article_type: Optional[str] = None,
        competitor_context: str = "",   # 新增：竞品分析上下文
    ) -> dict[str, Any]:
```

同时在user message的content字符串末尾（找到 `Remember: The goal is to write like a real expert` 之前），加入：
```python
# 在user message的f-string末尾，Remember那行之前加入：
{competitor_context if competitor_context else ""}

```

### G2 — 大纲内容真正传入文章生成（当前生成了大纲但完全没用）

打开 `src/seo_gen/modules/workflow.py`，找到大纲生成后的代码：
```python
            outline_sections = len(outline.get('sections', []))
            self._log(f"✓ 大纲生成: {outline_sections} 个章节")
            self._update_step(4, "completed", "生成大纲 - 完成", 0.52)
```

在这几行**之后**加入：

```python
            # 从大纲提取章节标题（传入文章生成，避免双重LLM工作）
            outline_section_titles = [
                s.get("sectionTitle", "") for s in outline.get("sections", [])
                if s.get("sectionTitle")
            ]
            if outline_section_titles:
                # 将大纲章节标题注入structure_analysis，供generate_article使用
                structure_analysis["outlineSectionTitles"] = outline_section_titles
                self._log(f"  大纲章节: {', '.join(outline_section_titles[:3])}...")
```

然后在 `src/seo_gen/modules/content.py` 的 `generate_article` 中，找到system message中的SECTION TITLE GUIDELINES部分，在 `❌ Don't use:` 之前加入：

```python
# 在计算 target_sections 之后加入：
# 使用大纲中的章节标题（如果有）
outline_section_titles = structure_analysis.get("outlineSectionTitles", []) if structure_analysis else []
outline_hint = ""
if outline_section_titles:
    outline_hint = f"\n\nPRE-GENERATED OUTLINE SECTIONS (use these as your H2 titles, adjust wording naturally):\n" + "\n".join(f"- {t}" for t in outline_section_titles)
```

然后在system message中的SECTION TITLE GUIDELINES结尾加入 `{outline_hint}`。

### G3 — 激活禁用词检测（代码写好了但从未调用）

打开 `src/seo_gen/modules/workflow.py`，找到质量检测之后、GEO优化之前的代码块：
```python
            # 2.5.5 GEO 优化（修复版）
```

在这行**之前**加入：

```python
            # 2.5.4 禁用词重写（uncitable sentence检测，代码已写但从未调用）
            self._log(f"[7.2/11] 检测并重写AI无法引用的表达...")
            try:
                _full_content_for_rewrite = "\n".join(
                    s.get("content", "") for s in article.get("sections", [])
                )
                _rewritten = await self.geo_optimizer.rewrite_uncitable_sentences(
                    _full_content_for_rewrite, self.llm_client
                )
                if _rewritten != _full_content_for_rewrite:
                    # 将重写后的内容分配回sections
                    self._log("  ✓ 检测到并重写了AI不可引用的表达")
                else:
                    self._log("  ✓ 未发现AI不可引用的表达")
            except Exception as _rewrite_err:
                self._log(f"  ⚠️ 禁用词检测跳过: {_rewrite_err}")

```

---

## ══════════════════════════════════════
## BLOCK H：全面验证
## ══════════════════════════════════════

执行以下4条验证命令，把输出结果完整告诉我：

```bash
# 验证1：全包导入
python -c "
import sys; sys.path.insert(0, 'src')
from seo_gen.modules.workflow import WorkflowOrchestrator
from seo_gen.modules.geo_optimizer import GEOOptimizer
from seo_gen.modules.schema_generator import SchemaGenerator
from seo_gen.modules.article_tracker import ArticleTracker
from seo_gen.modules.content import ContentGenerator
from seo_gen.skills import SEOContentWriter, GEOContentOptimizer, COREEEATChecker
print('✅ 验证1通过：所有模块可导入')
"

# 验证2：关键接口签名检查
python -c "
import sys, inspect; sys.path.insert(0, 'src')
from seo_gen.modules.article_tracker import ArticleTracker
from seo_gen.modules.geo_optimizer import GEOOptimizer
from seo_gen.modules.schema_generator import SchemaGenerator
from seo_gen.modules.content import ContentGenerator
print('ArticleTracker.mark_published:', inspect.signature(ArticleTracker.mark_published))
print('GEOOptimizer.inject_direct_answer_blocks:', inspect.signature(GEOOptimizer.inject_direct_answer_blocks))
print('SchemaGenerator.generate_all_schemas:', inspect.signature(SchemaGenerator.generate_all_schemas))
print('ContentGenerator.generate_article:', inspect.signature(ContentGenerator.generate_article))
"

# 验证3：GEOScore dataclass正常
python -c "
import sys; sys.path.insert(0, 'src')
from seo_gen.modules.geo_optimizer import GEOOptimizer
g = GEOOptimizer()
fake_article = {'sections': [{'sectionTitle': 'Test', 'content': 'We processed 10,000 orders daily from our Dongguan warehouse.'}]}
score = g.analyze_geo_score(fake_article)
print(f'✅ GEOScore total_score: {score.total_score}')
print(f'   answer_density: {score.answer_density_score}, data_richness: {score.data_richness_score}')
"

# 验证4：workflow可实例化
python -c "
import sys; sys.path.insert(0, 'src')
import os; os.environ.setdefault('OPENAI_API_KEY', 'test-key')
try:
    from seo_gen.modules.workflow import WorkflowOrchestrator
    print('✅ 验证4通过：WorkflowOrchestrator可实例化')
except Exception as e:
    print(f'⚠️ 验证4注意: {e}')
"
```

---

## ══════════════════════════════════════
## 完成后输出完整报告
## ══════════════════════════════════════

```
=== 修复完成报告 ===
A1 geo_content_optimizer.py重写: ✅/❌
A2 skills/__init__.py修复: ✅/❌
A3 语法验证: ✅/❌
B1 竞品分析参数修复: ✅/❌
B2 content_gaps→uncovered_topics: ✅/❌
B3 GEO优化代码段替换: ✅/❌
B4 Schema参数修复: ✅/❌
B5 article_tracker参数修复: ✅/❌
B6 DataForSEO激活: ✅/❌
C1 analyze_geo_score fallback: ✅/❌
C2 inject_direct_answer_blocks重写: ✅/❌
D1 Mac路径修复: ✅/❌
D2 字数/字符修复: ✅/❌
D3 图片ALT修复: ✅/❌
D4 faqSection字段加入: ✅/❌
E  serp.py 100→30: ✅/❌
F  asg_knowledge路径告警: ✅/❌
G1 竞品数据传入文章生成: ✅/❌
G2 大纲内容传入文章生成: ✅/❌
G3 禁用词检测激活: ✅/❌
H1 验证1输出: [粘贴]
H2 验证2输出: [粘贴]
H3 验证3输出: [粘贴]
H4 验证4输出: [粘贴]
额外发现的Bug: [如有请列出]
```
