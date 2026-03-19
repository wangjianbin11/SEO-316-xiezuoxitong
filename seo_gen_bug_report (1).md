# SEO Gen 代码审查报告 & 修复指南
> 生成时间: 2026-03-19 | 审查范围: src/seo_gen/ 全部模块
> 格式: 可直接在终端 `cat` 或 `less` 阅读，按严重程度排列

---

## 总览

| 等级 | 数量 | 说明 |
|------|------|------|
| 🔴 Critical | 3 | 运行时直接崩溃 |
| 🟠 High | 4 | 功能静默失效 |
| 🟡 Medium | 3 | 数据污染 / 逻辑混乱 |
| 🟢 Low | 4 | 代码质量 / 死代码 |

---

## 🔴 CRITICAL — 运行时崩溃

---

### BUG-C1: `internal_links.py` — `REQUEST_TIMEOUT` 未定义 + `httpx` 未导入

**文件:** `src/seo_gen/modules/internal_links.py`

**触发场景:** 调用 `validate_links_with_check()` 时

**报错:**
```
NameError: name 'REQUEST_TIMEOUT' is not defined
NameError: name 'httpx' is not defined
```

**问题代码 (约第580行):**
```python
async def _init_http_client(self):
    if self.http_client is None:
        self.http_client = httpx.AsyncClient(   # ← httpx 没有 import
            timeout=REQUEST_TIMEOUT,             # ← REQUEST_TIMEOUT 从未定义
            follow_redirects=True,
        )
```

**修复:**

在文件顶部添加:
```python
import httpx   # 文件顶部，与其他 import 放在一起

REQUEST_TIMEOUT = 15.0   # 在 SITEMAP_URLS 之前定义
```

同时在 `_close_http_client` 中添加 None 检查:
```python
async def _close_http_client(self):
    if self.http_client:          # ← 加这个检查
        await self.http_client.aclose()
```

---

### BUG-C2: `geo_optimizer.py` — 在 async 函数中调用 `run_until_complete()`

**文件:** `src/seo_gen/modules/geo_optimizer.py`
**方法:** `optimize_faq_for_ai()`

**触发场景:** 任何调用 GEO FAQ 优化的流程（workflow 第 7.5 步）

**报错:**
```
RuntimeError: This event loop is already running.
```

**问题代码 (约第260行):**
```python
async def optimize_faq_for_ai(self, faq_list, llm_client=None):
    ...
    if needs_optimization and client:
        try:
            rewritten_answer = asyncio.get_event_loop().run_until_complete(   # ← 错误！
                self._rewrite_faq_answer(question, answer, client)
            )
```

`optimize_faq_for_ai` 本身是 `async` 函数，内部已经在事件循环里运行，再调用 `run_until_complete` 必然崩溃。

**修复:** 直接 `await`，这个方法本来就是 async 的：
```python
async def optimize_faq_for_ai(self, faq_list, llm_client=None):
    ...
    if needs_optimization and client:
        try:
            rewritten_answer = await self._rewrite_faq_answer(   # ← 改为 await
                question, answer, client
            )
```

---

### BUG-C3: `workflow.py` — WordPress 失败时 `post_id=None` 传入 `mark_published()`

**文件:** `src/seo_gen/modules/workflow.py`
**方法:** `run_advanced_workflow()`

**触发场景:** WordPress API 发布失败，`post_id` 为 None

**报错:**
```
TypeError: 'NoneType' object cannot be interpreted as an integer
```
或 SQLite 写入异常，导致 article_tracker 数据污染。

**问题代码 (约第360行):**
```python
post_id = await wp_publisher.publish_article(...)

# ... 无任何 None 检查 ...

self.article_tracker.mark_published(
    ...
    wp_post_id=post_id,      # ← post_id 可能是 None
    wordpress_url=f"https://asgdropshipping.com/?p={post_id}",  # ← URL 会变成 ".../?p=None"
    ...
)
```

**修复:** 在记录前加 guard：
```python
if post_id:
    self._log(f"✓ WordPress 草稿创建成功")
    self._log(f"  文章链接: https://asgdropshipping.com/?p={post_id}")
    self._update_step(10, "completed", "发布 WordPress - 完成", 1.0)

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
    self._log("✓ 文章已记录到跟踪器")
else:
    self._log("⚠️ WordPress 发布失败，跳过追踪器记录")
```

---

## 🟠 HIGH — 功能静默失效

---

### BUG-H1: `title.py` — 竞品标题永远为空，使用错误字段名

**文件:** `src/seo_gen/modules/title.py`
**方法:** `generate_titles()`

**影响:** 生成标题时拿不到任何竞品数据，标题质量下降，评分不准确。

**问题代码:**
```python
async def generate_titles(self, keyword, serp_data, count=5):
    competing_titles = []
    for result in serp_data.get("results", []):   # ← 字段名错误！
        title = result.get("title", "")
```

`serp_analyzer.analyze()` 返回的字段名是 `"searchResults"`，不是 `"results"`：
```python
# serp.py 的返回值:
return {
    "keyword": keyword,
    "searchResults": search_results,   # ← 正确字段名
    "serpAnalysis": analysis,
    "totalResults": len(search_results),
}
```

**修复:**
```python
for result in serp_data.get("searchResults", []):   # ← 改为 searchResults
    title = result.get("title", "")
    if title:
        competing_titles.append(title)
```

---

### BUG-H2: `workflow.py` — `word_count` 从空字段计算，记录为 0

**文件:** `src/seo_gen/modules/workflow.py`

**影响:** `article_tracker` 和日志中的字数记录始终为 0，无法追踪实际字数。

**问题代码:**
```python
actual_sections = len(article.get('sections', []))
word_count = len(article.get('content', ''))          # ← 顶层 content 通常为空字符串
total_word_count = article.get('totalWordCount', word_count)  # ← 备用值也是 0
```

文章内容存在 `sections[i]['content']` 里，顶层 `content` 字段通常是空的。

**修复:**
```python
actual_sections = len(article.get('sections', []))

# 从 sections 聚合计算真实字数
_all_content = " ".join(
    s.get("content", "") for s in article.get("sections", [])
)
word_count = len(_all_content.split())
total_word_count = article.get('totalWordCount', word_count)

self._log(f"✓ 文章撰写完成: {actual_sections} 章节, {total_word_count} 词")
```

---

### BUG-H3: `workflow.py` — `get_workflow_orchestrator` 单例模式失效

**文件:** `src/seo_gen/modules/workflow.py`
**函数:** `get_workflow_orchestrator()`

**影响:** 每次 GUI 点击"开始生成"都会重建整个 Orchestrator，丢失检查点状态，浪费初始化资源。

**问题代码:**
```python
def get_workflow_orchestrator(progress_callback=None):
    global _workflow_orchestrator
    if _workflow_orchestrator is None or progress_callback is not None:  # ← 每次有 callback 都重建
        _workflow_orchestrator = WorkflowOrchestrator(progress_callback=progress_callback)
        if progress_callback is None:
            pass
    if progress_callback and _workflow_orchestrator:
        _workflow_orchestrator.progress_callback = progress_callback  # ← 重建后又多余更新
    return _workflow_orchestrator
```

**修复:**
```python
def get_workflow_orchestrator(progress_callback=None):
    global _workflow_orchestrator
    if _workflow_orchestrator is None:
        _workflow_orchestrator = WorkflowOrchestrator(progress_callback=progress_callback)
    elif progress_callback is not None:
        # 只更新 callback，不重建实例
        _workflow_orchestrator.progress_callback = progress_callback
    return _workflow_orchestrator
```

---

### BUG-H4: `content.py` — `_markdown_to_html` 有序列表未转换

**文件:** `src/seo_gen/modules/content.py`
**方法:** `_markdown_to_html()`

**影响:** 文章内容中所有有序列表（如步骤说明 `1. 2. 3.`）在 WordPress 中显示为纯文字，没有 `<ol><li>` 格式。

**问题代码:**
```python
# 现有代码只处理无序列表:
html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
html = re.sub(r'(<li>.+</li>\n?)+', r'<ul>\n\0</ul>', html)
# 有序列表 1. 2. 3. 没有对应处理
```

**修复 (在无序列表处理之后添加):**
```python
# 有序列表
html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
# 将连续的 <li> 包裹在 <ol> 中（区分已有的 <ul> 避免重复包裹）
# 注意: 需要在 <ul> 包裹逻辑之前先标记来源
# 更健壮的方式: 先替换有序列表标记为特殊占位符
html = re.sub(r'^\d+\. (.+)$', r'<oli>\1</oli>', html, flags=re.MULTILINE)
html = re.sub(r'(<oli>.+</oli>\n?)+', lambda m: '<ol>\n' + m.group(0).replace('<oli>', '<li>').replace('</oli>', '</li>') + '</ol>', html)
```

---

## 🟡 MEDIUM — 数据污染 / 逻辑混乱

---

### BUG-M1: `geo_optimizer.py` — `inject_direct_answer_blocks` 错误覆盖顶层 `content`

**文件:** `src/seo_gen/modules/geo_optimizer.py`
**方法:** `inject_direct_answer_blocks()`

**影响:** 执行 GEO 注入后，`article["content"]` 变成所有 sections 拼接的巨型字符串，与 `build_wordpress_html` 期望的数据结构不一致，可能导致 HTML 构建重复输出内容。

**问题代码:**
```python
article["sections"] = sections

# 同时更新顶层 content 字段（如果存在）
if "content" in article:
    combined = "\n\n".join(
        s.get("content", "") for s in sections
    )
    article["content"] = combined  # ← 用合并字符串覆盖原有结构
```

**修复:** 删除这段顶层 content 更新逻辑：
```python
article["sections"] = sections
# 不要同步更新顶层 content，build_wordpress_html 从 sections 读取
return article
```

---

### BUG-M2: `detection.py` — `detect_all_sync` 功能与 `detect_all` 不等同

**文件:** `src/seo_gen/modules/detection.py`
**方法:** `detect_all_sync()`

**影响:** 注释说"向后兼容"，实际上缺少在线 Google Search 抄袭检测，只做本地检测，结果差异大。

**问题代码:**
```python
def detect_all_sync(self, text: str) -> Dict:
    """
    Synchronous version of detect_all for backward compatibility
    Returns: Same as detect_all but runs synchronously
    """
    ai_result = self.ai_detector.detect(text)
    plagiarism_result = self.plagiarism_detector.detect(text)   # ← 只有本地检测
    # 没有 online_detector 调用
```

**修复选项一 (推荐):** 用 `asyncio.run()` 真正调用 async 版本：
```python
def detect_all_sync(self, text: str) -> Dict:
    """同步包装，调用完整的异步检测流程"""
    import asyncio
    try:
        return asyncio.run(self.detect_all(text))
    except RuntimeError:
        # 如果已有事件循环（如在 Jupyter），fallback 到本地
        ai_result = self.ai_detector.detect(text)
        plagiarism_result = self.plagiarism_detector.detect(text)
        human_score = ai_result['human_probability']
        originality_score = plagiarism_result['originality_score']
        overall_score = (human_score * 0.6 + originality_score * 0.4) * 100
        return {
            "ai_detection": ai_result,
            "plagiarism_detection": plagiarism_result,
            "overall_score": round(overall_score, 1),
            "recommendation": self._generate_recommendation(ai_result, plagiarism_result, overall_score),
            "note": "Local detection only (event loop conflict)"
        }
```

---

### BUG-M3: 两个 `QualityChecker` 类共存导致命名混淆

**文件:** `src/seo_gen/modules/quality.py` 和 `src/seo_gen/modules/quality_checker.py`

**影响:** `modules/__init__.py` 中：
```python
from seo_gen.modules.quality import QualityChecker as OldQualityChecker   # 旧版（LLM评估）
from seo_gen.modules.quality_checker import QualityChecker                 # 新版（规则评估）
```

`workflow.py` 导入了新版但实例化时方法签名略有不同；`check_article_quality` 在两个类中都存在，容易在 IDE 中混淆跳转，且新旧版本返回格式不完全一致（新版多了 `publishReady`、`technicalSEO` 等字段）。

**修复建议:** 将旧版重命名为 `LLMQualityChecker`，在 `__init__.py` 中统一：
```python
# modules/__init__.py
from seo_gen.modules.quality import QualityChecker as LLMQualityChecker     # 明确命名
from seo_gen.modules.quality_checker import QualityChecker                   # 规则版，保持主用
```
同时在 `workflow.py` 中确认只使用规则版：
```python
from seo_gen.modules.quality_checker import QualityChecker   # 只 import 一个
```

---

## 🟢 LOW — 代码质量 / 死代码

---

### BUG-L1: `src/seo_gen/modules/nul` — 空文件应删除

**影响:** 无功能影响，但会污染 `__init__.py` 的导入扫描，可能在某些工具中报错。

**修复:**
```bash
rm src/seo_gen/modules/nul
```

---

### BUG-L2: `workflow.py` — `pre_confirmed_title` 参数从未被 GUI 传递

**文件:** `src/seo_gen/modules/workflow.py`

`run_advanced_workflow()` 签名中有 `pre_confirmed_title: Optional[str] = None`，但 `gui.py` 的所有调用路径（`run_single_generation`, `_batch_run_single_generation`）均不传这个参数，相关逻辑永远不会触发。

**修复选项:**
- 如果 GUI 生成的标题需要传入：在 `_on_type_confirmed()` 的调用中添加 `pre_confirmed_title=generated_title`
- 如果此功能暂不需要：删除参数和相关 if 分支以减少混淆

---

### BUG-L3: `content.py` — 函数内重复 `import`

**文件:** `src/seo_gen/modules/content.py`
**方法:** `build_wordpress_html()`

```python
def build_wordpress_html(self, ...):
    from seo_gen.modules.internal_links import get_internal_link_manager   # ← 每次调用都执行
    ...
    import re as _re    # ← 出现 2 次，且文件顶部已有 import re
    import re as _re    # ← 重复
```

**修复:** 将 `from seo_gen.modules.internal_links import get_internal_link_manager` 移到文件顶部；删除函数内的 `import re as _re`（文件顶部已有 `import re`，直接用 `re` 即可）。

---

### BUG-L4: `serp.py` — `results` vs `searchResults` 字段名在多处不一致

**影响范围:**
- `title.py`: `serp_data.get("results", [])` ← 已在 BUG-H1 中修复
- `content.py` 的 `generate_article` 中接收的是 `serp_analysis`（serpAnalysis 子层），正确
- `structure.py`: 使用 `searchResults`，正确

**建议:** 全局搜索 `serp_data.get("results"` 确认没有其他遗漏：
```bash
grep -rn 'serp_data.get("results"' src/
```

---

## 修复优先级执行顺序

```
1. BUG-C2  geo_optimizer.py  await 替换 run_until_complete       ← 最快修，影响最大
2. BUG-C1  internal_links.py  添加 import httpx + REQUEST_TIMEOUT
3. BUG-H1  title.py           "results" → "searchResults"
4. BUG-C3  workflow.py        post_id None guard
5. BUG-H3  workflow.py        get_workflow_orchestrator 单例修复
6. BUG-H2  workflow.py        word_count 从 sections 聚合
7. BUG-M1  geo_optimizer.py   删除顶层 content 覆盖逻辑
8. BUG-H4  content.py         有序列表 HTML 转换
9. BUG-M2  detection.py       detect_all_sync 完整实现
10. BUG-M3 命名混淆重命名
11. BUG-L1 删除 nul 文件
12. BUG-L2~L4 代码质量清理
```

---

## 快速验证命令

修复完成后，建议运行以下命令验证：

```bash
# 1. 检查没有遗漏的 REQUEST_TIMEOUT 引用
grep -rn "REQUEST_TIMEOUT" src/

# 2. 检查所有 async 函数中的 run_until_complete（不应存在）
grep -rn "run_until_complete" src/

# 3. 检查 serp_data 字段名一致性
grep -rn 'serp_data.get("results"' src/
grep -rn 'get("searchResults"' src/

# 4. 单元测试（如果有）
python -m pytest tests/ -v

# 5. 快速冒烟测试（跳过 WordPress 和图片）
python -m seo_gen.main generate-advanced "dropshipping agent" \
  --skip-images --skip-wordpress
```

---

*报告生成: Claude Sonnet 4.6 | 基于全量源码静态分析*
