# SEO生成系统终极升级指令
# 发给Claude Code直接执行
# 版本：v3.0 | 日期：2026-03

---

## 升级总览

本次升级目标：让系统生成的文章达到"专家人工写作"标准，并确保被AI搜索引擎（ChatGPT/Perplexity/Google AI Overview）高频引用。

核心问题（按优先级）：
P0-1: geo_optimizer.py存在未解决的Git合并冲突 → 系统无法启动
P0-2: 内容格式不统一（Markdown/HTML混合）→ 渲染崩溃
P1-1: 三种文章类型的写作提示词未真正注入生成流程
P1-2: 关键词密度无控制 → 可能触发Google惩罚
P1-3: FAQ字段不稳定 → AEO失效
P1-4: quality_checker从Markdown解析HTML → 评分全部失真
P2-1: 竞品分析字段名Bug → 竞品数据永远空

---

## 第一步：修复P0紧急Bug

### Fix 1: 修复 geo_optimizer.py 合并冲突

文件：src/seo_gen/modules/geo_optimizer.py
找到以下冲突标记并修复：

```
# 删除这些行（Git冲突标记）：
<<<<<<< HEAD
    async def optimize_faq_for_ai(...):
=======
    def optimize_faq_for_ai(...):
>>>>>>> parent of 98c10574
```

保留版本：async版本（保留await）
修复后的方法签名：
```python
async def optimize_faq_for_ai(self, faq_list: List[Dict], llm_client: Any = None) -> List[Dict]:
```

同时检查workflow.py中调用此方法的地方，确保有await：
```python
# workflow.py 约第480行
article["faqSection"]["items"] = await self.geo_optimizer.optimize_faq_for_ai(
    faq_items, self.llm_client
)
```

### Fix 2: 统一内容格式为Markdown

决策：全系统统一使用Markdown格式，在WordPress发布时才转换为HTML。

修改 geo_optimizer.py 的 inject_direct_answer_blocks() 方法：

```python
# 原来注入HTML块（错误）：
answer_block = f'<div class="geo-answer-block">...'

# 改为注入Markdown标记（正确）：
answer_block = f'> **[GEO Answer]** {answer_text}\n\n'
```

同时在 quality_checker.py 中：
```python
# 修复check_technical_seo()和check_geo_optimization()
# 原来：soup = BeautifulSoup(content_html, 'html.parser')
# 改为：先将Markdown转为HTML再解析

import markdown as md

def _markdown_to_soup(self, markdown_text: str):
    """将Markdown转为BeautifulSoup对象"""
    html = md.markdown(markdown_text, extensions=['tables', 'extra'])
    return BeautifulSoup(html, 'html.parser')
```

---

## 第二步：新增三份提示词文件

在项目 prompts/ 目录下创建以下三个文件，内容从升级版提示词文件复制：

```
prompts/
├── pillar_post_v3.md      ← 来自 ASG-顶梁柱-UPGRADED.md
├── response_post_v3.md    ← 来自 ASG-回答型-UPGRADED.md  
└── share_post_v3.md       ← 来自 ASG-分享型-UPGRADED.md
```

---

## 第三步：修改 content.py（核心升级）

### 3.1 加载文章类型提示词

在 content.py 中修改 `_load_type_template()` 方法：

```python
# 更新模板文件名映射
ARTICLE_TYPE_TEMPLATES = {
    "pillar": "pillar_post_v3.md",
    "response": "response_post_v3.md",
    "share": "share_post_v3.md",
}

def _load_type_template(self, article_type: str) -> str:
    """加载文章类型提示词"""
    template_name = ARTICLE_TYPE_TEMPLATES.get(article_type)
    if not template_name:
        logger.warning(f"Unknown article type: {article_type}")
        return ""
    
    # 搜索路径（按优先级）
    possible_paths = [
        Path(__file__).parent.parent.parent / "prompts" / template_name,  # 项目根/prompts/
        Path(__file__).parent.parent / "prompts" / template_name,          # src/prompts/
        Path("prompts") / template_name,                                    # 工作目录/prompts/
    ]
    
    for path in possible_paths:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            logger.info(f"✓ 加载文章类型提示词: {template_name} ({len(content)}字符)")
            return content
    
    logger.error(f"✗ 找不到文章类型提示词: {template_name}")
    logger.error(f"  搜索路径: {[str(p) for p in possible_paths]}")
    return ""
```

### 3.2 重写 generate_article() 的系统提示词构建

在 generate_article() 方法中，将 [SYSTEM_INJECT_*] 占位符替换为实际内容：

```python
async def generate_article(
    self,
    keyword: str,
    slug: str,
    serp_analysis: dict,
    structure_analysis: dict = None,
    article_type: str = None,
    competitor_context: str = "",
    asg_context: str = "",
) -> dict:
    
    # 1. 加载对应类型的写作提示词
    type_template = self._load_type_template(article_type or "share")
    
    # 2. 加载大纲章节
    outline_sections = []
    if structure_analysis:
        outline_sections = structure_analysis.get("outlineSectionTitles", [])
    
    # 3. 提取竞品话题
    competitor_topics = []
    uncovered_topics = []
    if competitor_context:
        # 从competitor_context字符串中提取（简单解析）
        lines = competitor_context.split('\n')
        for line in lines:
            if '竞品已覆盖' in line or 'all_h2_topics' in line.lower():
                topics_str = line.split(':', 1)[-1].strip()
                competitor_topics = [t.strip() for t in topics_str.split(',')][:10]
            if '竞品未覆盖' in line or 'uncovered' in line.lower():
                topics_str = line.split(':', 1)[-1].strip()
                uncovered_topics = [t.strip() for t in topics_str.split(',')][:5]
    
    # 4. 提取PAA问题
    paa_questions = serp_analysis.get("paaQuestions", [])
    
    # 5. 替换提示词中的系统注入标记
    filled_template = type_template.replace(
        "[SYSTEM_INJECT_KEYWORD]", keyword
    ).replace(
        "[SYSTEM_INJECT_TITLE]", slug.replace("-", " ").title()  # 临时，workflow会传入真实title
    ).replace(
        "[SYSTEM_INJECT_OUTLINE_SECTIONS]", 
        "\n".join(f"- {s}" for s in outline_sections) if outline_sections else "根据关键词自动规划"
    ).replace(
        "[SYSTEM_INJECT_COMPETITOR_TOPICS]",
        ", ".join(competitor_topics) if competitor_topics else "暂无竞品数据"
    ).replace(
        "[SYSTEM_INJECT_UNCOVERED_TOPICS]",
        ", ".join(uncovered_topics) if uncovered_topics else "暂无"
    ).replace(
        "[SYSTEM_INJECT_PAA_QUESTIONS]",
        "\n".join(f"- {q}" for q in paa_questions[:8]) if paa_questions else "暂无PAA数据"
    ).replace(
        "[SYSTEM_INJECT_CASE_STUDY]",
        self._select_relevant_case(slug, keyword)[:1500] if self._select_relevant_case(slug, keyword) else "暂无相关案例"
    ).replace(
        "[SYSTEM_INJECT_LONGTAIL]", 
        ", ".join(serp_analysis.get("relatedSearches", [])[:5])
    ).replace(
        "[SYSTEM_INJECT_LSI]",
        keyword  # 简化处理，实际可扩展
    )
    
    # 6. 构建最终messages
    # ASG知识库上下文放在system prompt最前面（最高优先级）
    system_content = f"""
{GEO_CRITICAL_RULES}

# === ASG KNOWLEDGE BASE (PRIMARY SOURCE - USE THIS FIRST) ===
{asg_context}
# === END ASG KNOWLEDGE BASE ===

# === ARTICLE TYPE WRITING GUIDE ===
{filled_template}
# === END WRITING GUIDE ===
"""
    
    user_content = f"""
Now write the complete article in JSON format.

Keyword: {keyword}
Article Type: {article_type or 'share'}
Slug: {slug}

CRITICAL REQUIREMENTS:
1. Follow the writing guide above EXACTLY
2. Every H2 section MUST have a geoAnswerBlock (50-80 words, self-contained)
3. FAQ section MUST have 6-8 items, each answer 65-100 words
4. Keyword density MUST be 0.8%-1.5% (count carefully)
5. NO banned phrases (check the list in the writing guide)
6. At least ONE real case study with specific numbers
7. Introduction MUST be the specified word count for this article type
8. Conclusion MUST be the specified word count for this article type

Output ONLY valid JSON matching the output format in the writing guide.
"""
    
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    
    result = await self.llm_client.chat_json(messages, temperature=0.7)
    return result
```

### 3.3 增加关键词密度控制

在 content.py 中新增 `_validate_keyword_density()` 方法：

```python
def _validate_keyword_density(self, article: dict, keyword: str) -> dict:
    """
    验证并修正关键词密度
    目标：0.8%-1.5%
    如果超出，返回警告（不自动修改内容，由LLM重新生成）
    """
    # 提取全文
    full_text = ""
    full_text += article.get("introduction", "") + " "
    for section in article.get("sections", []):
        full_text += section.get("content", "") + " "
        full_text += section.get("geoAnswerBlock", "") + " "
    for faq in article.get("faqSection", {}).get("items", []):
        full_text += faq.get("answer", "") + " "
    full_text += article.get("conclusion", "")
    
    # 计算密度
    words = full_text.lower().split()
    total_words = len(words)
    keyword_count = full_text.lower().count(keyword.lower())
    density = keyword_count / total_words if total_words > 0 else 0
    
    article["_meta"] = {
        "keyword_density": round(density, 4),
        "keyword_count": keyword_count,
        "total_words": total_words,
        "density_ok": 0.008 <= density <= 0.015,
        "density_warning": density > 0.015 or density < 0.008,
    }
    
    if density > 0.015:
        logger.warning(f"⚠️ 关键词密度过高: {density:.2%} > 1.5% (出现{keyword_count}次/{total_words}词)")
    elif density < 0.008:
        logger.warning(f"⚠️ 关键词密度过低: {density:.2%} < 0.8% (出现{keyword_count}次/{total_words}词)")
    else:
        logger.info(f"✓ 关键词密度正常: {density:.2%} (出现{keyword_count}次/{total_words}词)")
    
    return article
```

在 generate_article() 返回前调用：
```python
result = await self.llm_client.chat_json(messages, temperature=0.7)
result = self._validate_keyword_density(result, keyword)
return result
```

---

## 第四步：修改 quality_checker.py

### 4.1 修复Markdown解析问题

在文件顶部添加依赖：
```python
try:
    import markdown as md_parser
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown包未安装，将使用正则fallback解析")
```

修改 `_get_soup_from_article()` 工具方法：
```python
def _get_soup_from_article(self, article: dict) -> BeautifulSoup:
    """
    从文章数据获取BeautifulSoup对象
    处理Markdown/HTML混合格式
    """
    # 优先从sections拼接content（Markdown格式）
    sections = article.get("sections", [])
    markdown_parts = []
    
    for section in sections:
        title = section.get("sectionTitle", "")
        if title:
            markdown_parts.append(f"## {title}")
        
        # GEO答案块（已是Markdown引用格式）
        geo_block = section.get("geoAnswerBlock", "")
        if geo_block:
            markdown_parts.append(f"> {geo_block}")
        
        content = section.get("content", "")
        if content:
            markdown_parts.append(content)
    
    full_markdown = "\n\n".join(markdown_parts)
    
    # 转换为HTML再解析
    if MARKDOWN_AVAILABLE and full_markdown:
        html = md_parser.markdown(full_markdown, extensions=['tables', 'extra', 'toc'])
    else:
        # Regex fallback
        html = full_markdown
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    return BeautifulSoup(html, 'html.parser')
```

修改 check_technical_seo() 使用新方法：
```python
def check_technical_seo(self, article: dict, primary_keyword: str) -> dict:
    # 删除原来的content读取逻辑
    # content_html = article.get("content", "")
    # if not content_html.strip(): ...
    
    # 改为使用新方法
    soup = self._get_soup_from_article(article)
    # 后续代码不变...
```

同样修改 check_geo_optimization()：
```python
def check_geo_optimization(self, article: dict) -> dict:
    soup = self._get_soup_from_article(article)
    
    # 检查GEO答案块（从sections字段而非HTML中查找）
    sections = article.get("sections", [])
    geo_blocks_count = sum(
        1 for s in sections 
        if s.get("geoAnswerBlock") and len(s["geoAnswerBlock"].split()) >= 40
    )
    h2_count = len(sections)
    # 后续评分逻辑不变...
```

### 4.2 新增关键词密度检查项

在 check_content_quality() 中添加：
```python
# 关键词密度检查（从_meta字段读取，content.py已计算）
meta = article.get("_meta", {})
if meta.get("density_ok"):
    scores["keyword_density"] = 10
    scores["passed"].append(f"关键词密度正常 ({meta.get('keyword_density', 0):.2%})")
elif meta.get("density_warning"):
    density = meta.get("keyword_density", 0)
    if density > 0.015:
        scores["critical"].append(f"关键词密度过高 ({density:.2%})，可能触发堆砌惩罚")
        scores["keyword_density"] = 0
    else:
        scores["warnings"].append(f"关键词密度偏低 ({density:.2%})")
        scores["keyword_density"] = 5
else:
    # 没有_meta数据，自行计算
    density = self.calculate_keyword_density(
        self._extract_full_text(article), primary_keyword
    )
    if 0.008 <= density <= 0.015:
        scores["keyword_density"] = 10
    elif density > 0.015:
        scores["keyword_density"] = 0
        scores["critical"].append(f"关键词密度过高 ({density:.2%})")
    else:
        scores["keyword_density"] = 5
        scores["warnings"].append(f"关键词密度偏低 ({density:.2%})")
```

---

## 第五步：修改 workflow.py

### 5.1 修复title传递给generate_article（确保标题注入）

在 run_advanced_workflow() 中，generate_article调用时传入最终标题：

```python
# 原来调用（缺少title参数）：
article = await self.content_generator.generate_article(
    keyword=keyword,
    slug=result["slug"],
    serp_analysis=serp_analysis_for_content,
    structure_analysis=structure_analysis,
    article_type=article_type.value,
    competitor_context=competitor_context,
    asg_context=asg_context,
)

# 修改为（传入title）：
article = await self.content_generator.generate_article(
    keyword=keyword,
    slug=result["slug"],
    title=final_title,  # 新增：传入TitleGenerator选出的最佳标题
    serp_analysis=serp_analysis_for_content,
    structure_analysis=structure_analysis,
    article_type=article_type.value,
    competitor_context=competitor_context,
    asg_context=asg_context,
)
```

同时在 generate_article() 方法签名中添加 title 参数，并在filled_template中使用：
```python
async def generate_article(
    self,
    keyword: str,
    slug: str,
    title: str = "",  # 新增
    serp_analysis: dict = None,
    ...
):
    # 在替换标记时使用实际title
    filled_template = type_template.replace(
        "[SYSTEM_INJECT_TITLE]", title or slug.replace("-", " ").title()
    )
```

### 5.2 修复Schema注入位置

Schema不应该注入到post content正文，应该通过WordPress自定义字段：

```python
# 原来（错误）：
html_content = schema_html + "\n\n" + html_content

# 改为（正确）：
# Schema通过WordPress自定义字段传递
schema_meta = {
    "_asg_schema_markup": schema_html,  # 主题或插件读取此字段注入<head>
}

# 在publish_article调用时传入meta：
post_id = await wp_publisher.publish_article(
    title=article.get("title", ""),
    content=html_content,  # 不含schema
    excerpt=...,
    slug=result["slug"],
    meta_description=...,
    featured_media_id=featured_media_id,
    status="draft",
    extra_meta=schema_meta,  # 新增参数
)
```

同时修改 wordpress.py 的 publish_article() 支持 extra_meta：
```python
async def publish_article(
    self,
    ...,
    extra_meta: dict = None,  # 新增
) -> Optional[int]:
    payload = {
        "title": title,
        "content": content,
        ...
        "meta": {
            "_yoast_wpseo_metadesc": meta_description,
            **(extra_meta or {}),  # 合并额外meta
        },
    }
```

### 5.3 修复竞品分析字段名Bug（确认已修复）

检查 workflow.py 中以下两行：
```python
# 正确写法（link字段，不是url）：
top_urls = [
    r.get("link") or r.get("url")  # 双重fallback保险
    for r in serp_data.get("searchResults", [])[:5]
    if r.get("link") or r.get("url")
]
```
这个在原代码中已经有了双重fallback，确认即可。

---

## 第六步：安装缺失依赖

在项目根目录执行：
```bash
pip install markdown --break-system-packages
```

或在 pyproject.toml / requirements.txt 中添加：
```
markdown>=3.5.0
```

---

## 第七步：验证升级效果

升级完成后，运行以下验证流程：

### 7.1 验证提示词加载
```python
from seo_gen.modules.content import ContentGenerator
gen = ContentGenerator()
for t in ["pillar", "response", "share"]:
    template = gen._load_type_template(t)
    print(f"{t}: {len(template)} chars, {'✓' if template else '✗'}")
```
期望输出：每种类型>3000字符

### 7.2 验证geo_optimizer导入
```python
from seo_gen.modules.geo_optimizer import GEOOptimizer
print("geo_optimizer import: ✓")
```
期望：不报SyntaxError

### 7.3 验证quality_checker解析
```python
from seo_gen.modules.quality_checker import QualityChecker
qc = QualityChecker()
test_article = {
    "title": "Test Article About Dropshipping",
    "sections": [
        {
            "sectionTitle": "What is Dropshipping",
            "geoAnswerBlock": "Dropshipping is a fulfillment method where sellers...",
            "content": "## What is Dropshipping\n\nDropshipping is...",
        }
    ],
    "faqSection": {"items": [{"question": "Q?", "answer": "A answer here."}]},
    "metaDescription": "Test description 150 chars long enough for SEO check.",
}
soup = qc._get_soup_from_article(test_article)
h2s = soup.find_all('h2')
print(f"H2 count: {len(h2s)}")  # 期望: 1
```

### 7.4 快速端到端测试
```bash
python -c "
import asyncio
from seo_gen.modules.workflow import WorkflowOrchestrator

async def test():
    orch = WorkflowOrchestrator()
    result = await orch.run_advanced_workflow(
        keyword='dropshipping agent china',
        skip_images=True,
        skip_wordpress=True,
        confirmed_article_type='response',
    )
    print('Success:', result.get('success'))
    article = result.get('article', {})
    sections = article.get('sections', [])
    faq = article.get('faqSection', {}).get('items', [])
    print(f'Sections: {len(sections)}')
    print(f'FAQ items: {len(faq)}')
    meta = article.get('_meta', {})
    print(f'Keyword density: {meta.get(\"keyword_density\", \"N/A\")}')
    for s in sections[:2]:
        geo = s.get('geoAnswerBlock', '')
        print(f'GEO block words: {len(geo.split())}')

asyncio.run(test())
"
```

期望输出：
- Success: True
- Sections: 3-6
- FAQ items: 6-8
- Keyword density: 0.008-0.015
- GEO block words: 50-80 (每个)

---

## 文件修改清单（发给CC的执行清单）

| 文件 | 操作 | 优先级 |
|------|------|--------|
| src/seo_gen/modules/geo_optimizer.py | 删除Git冲突标记，保留async版本 | P0 |
| src/seo_gen/modules/geo_optimizer.py | 将HTML答案块改为Markdown引用格式 | P0 |
| src/seo_gen/modules/content.py | 更新ARTICLE_TYPE_TEMPLATES路径 | P1 |
| src/seo_gen/modules/content.py | 重写_load_type_template()方法 | P1 |
| src/seo_gen/modules/content.py | 重写generate_article()系统提示词构建 | P1 |
| src/seo_gen/modules/content.py | 新增_validate_keyword_density()方法 | P1 |
| src/seo_gen/modules/quality_checker.py | 新增_get_soup_from_article()方法 | P1 |
| src/seo_gen/modules/quality_checker.py | 修改check_technical_seo()使用新方法 | P1 |
| src/seo_gen/modules/quality_checker.py | 修改check_geo_optimization()使用新方法 | P1 |
| src/seo_gen/modules/quality_checker.py | 新增关键词密度检查 | P1 |
| src/seo_gen/modules/workflow.py | generate_article调用新增title参数 | P2 |
| src/seo_gen/modules/workflow.py | Schema改用WordPress自定义字段 | P2 |
| src/seo_gen/modules/wordpress.py | publish_article支持extra_meta参数 | P2 |
| prompts/pillar_post_v3.md | 新建文件 | P1 |
| prompts/response_post_v3.md | 新建文件 | P1 |
| prompts/share_post_v3.md | 新建文件 | P1 |
| requirements.txt / pyproject.toml | 添加markdown>=3.5.0 | P1 |

---

## 升级后的写作流程验证标准

以下是判断升级成功的最终验收标准：

生成一篇文章后，检查以下10项：

1. ✅ 每个H2章节都有geoAnswerBlock字段（50-80词）
2. ✅ FAQ有6-8个条目，每个answer 65-100词
3. ✅ 关键词密度0.8%-1.5%（_meta字段中有density_ok: true）
4. ✅ 文章类型提示词被真正加载和使用（日志显示"✓ 加载文章类型提示词"）
5. ✅ 引言在规定字数内（顶梁柱100-150词，回答型50-75词，分享型≤50词）
6. ✅ 结论在规定字数内（顶梁柱50-75词，回答型50-75词，分享型≤300字符）
7. ✅ 至少1个真实案例（含具体数字）
8. ✅ quality_checker评分中H2计数>0（说明Markdown解析正常）
9. ✅ 没有合并冲突标记（geo_optimizer正常导入）
10. ✅ Schema通过WordPress meta传递（不在正文HTML中）

---

*本指令由Janson/ASG系统升级工作组生成 | 基于32个源文件深度审计 | 2026-03*
