# SEO内容生成系统 v2.0 → v2.1 完整升级指令

> **发送对象：Claude Code（CC）**
> **发送人：Janson / ASG Dropshipping**
> **优先级：按编号顺序执行，不要跳步**
> **要求：每完成一个修复，告诉我改了哪些文件的哪些行，并给出修复前/后的代码对比**

---

## 指令总览

本文档包含 **7个关键Bug修复 + 3个质量提升 + 3个P1季度升级方向**。请按顺序逐一执行。每个修复我都给了：问题描述、根因定位、期望行为、具体修复方法。

---

## 第一部分：关键Bug修复（必须全部完成）

---

### BUG-1：SERP结果字段名全程用错（最高优先级）

**问题描述：**
`SERPAnalyzer.analyze()` 返回的数据结构中，搜索结果列表的字段名是 `"searchResults"`，但 `workflow.py` 中多处使用的是 `"results"`。这导致竞品爬取的 `top_urls` 永远是空列表，`CompetitorScraper` 从未真正爬取过任何对手文章。

**根因定位：**
- 文件：`workflow.py`
- 错误代码：`serp_data.get("results", [])` — 永远返回 `[]`
- 错误代码：`serp_data.get("primaryIntent")` — 永远返回 `None`

**期望行为：**
- `top_urls` 应该能正确提取出 SERP 前5条搜索结果的链接
- `primaryIntent` 应该能正确读取到搜索意图（如 "buy"、"compare"、"share" 等）
- `paaQuestions`（People Also Ask）应该能正确提取

**具体修复方法：**
在 `workflow.py` 中，找到所有读取 SERP 数据的地方，做以下替换：

```python
# ===== 修复1：搜索结果列表 =====
# 旧代码（错误）：
top_urls = [r.get("url") for r in serp_data.get("results", [])[:5]]

# 新代码（正确）：
top_urls = [
    r.get("link") or r.get("url")
    for r in serp_data.get("searchResults", [])[:5]
    if r.get("link") or r.get("url")
]

# ===== 修复2：搜索意图 =====
# 旧代码（错误）：
primary_intent = serp_data.get("primaryIntent", "share")

# 新代码（正确）：
primary_intent = serp_data.get("serpAnalysis", {}).get("primaryIntent", "share")

# ===== 修复3：People Also Ask =====
# 旧代码（错误，如果有的话）：
paa = serp_data.get("paaQuestions", [])

# 新代码（正确）：
paa = serp_data.get("serpAnalysis", {}).get("paaQuestions", [])
```

**注意：** Google Custom Search API 返回的链接字段名是 `"link"` 不是 `"url"`，所以用 `r.get("link") or r.get("url")` 做兼容。

**验证方式：** 修复后运行一个关键词，检查日志中 `top_urls` 是否有5条真实URL，`primary_intent` 是否不再是 `"share"`。

---

### BUG-2：serp_analysis 传错层级给 ContentGenerator

**问题描述：**
`workflow.py` 调用 `generate_article()` 时，把整个 `serp_data` 字典传给了 `serp_analysis` 参数，但 `content.py` 中读取的字段（如 `primaryIntent`、`searchIntent`）在 `serp_data["serpAnalysis"]` 子层下面，不在顶层。

**根因定位：**
- 文件：`workflow.py`
- 错误代码：`generate_article(serp_analysis=serp_data)`
- 文件：`content.py`
- 读取代码：`serp_analysis.get('primaryIntent', 'share')` — 在顶层找不到这个字段

**具体修复方法：**
在 `workflow.py` 中，找到调用 `generate_article()` 的地方：

```python
# 旧代码（错误）：
article = self.content_generator.generate_article(
    ...,
    serp_analysis=serp_data,
    ...
)

# 新代码（正确）：
article = self.content_generator.generate_article(
    ...,
    serp_analysis=serp_data.get("serpAnalysis", {}),
    ...
)
```

**验证方式：** 修复后，在 `content.py` 的 `generate_article()` 方法开头加一行临时日志 `logger.info(f"serp_analysis keys: {serp_analysis.keys()}")`，确认能看到 `primaryIntent`、`searchIntent`、`paaQuestions` 等字段。

---

### BUG-3：ASGKnowledgeBase 加载了但内容没进 ContentGenerator（最大的架构性浪费）

**问题描述：**
`workflow.py` 中加载了 `ASGKnowledgeBase`（包含Janson个人介绍、企业介绍、FAQ案例、GEO规范等宝贵内容），也调用了 `get_context_for_keyword(keyword)`，但返回的 context **只打了个log就扔掉了**，完全没有传给 `ContentGenerator`。

同时，`ContentGenerator.__init__` 接收的是一个普通的 `KnowledgeBase`（读 `config/knowledge/` 目录下的txt文件），完全不是 `ASGKnowledgeBase`。

**结果：** 文章里的"Janson视角"纯粹靠System Prompt里硬写的一句描述，不是真正从知识库注入的。

**具体修复方法：**

**Step 1：** 在 `content.py` 的 `generate_article()` 方法中新增一个参数：

```python
# 旧签名：
def generate_article(self, keyword, serp_analysis=None, competitor_data=None, structure_analysis=None):

# 新签名：
def generate_article(self, keyword, serp_analysis=None, competitor_data=None, structure_analysis=None, asg_context: str = ""):
```

**Step 2：** 在 `content.py` 的 `generate_article()` 方法内部，找到构建 system_message 的地方，把 `asg_context` 注入到 System Prompt 的**最前面**（因为LLM对长Prompt的注意力会在末尾衰减）：

```python
# 在 system_message 的最前面添加：
if asg_context:
    system_message = (
        "=== ASG KNOWLEDGE BASE CONTEXT (USE THIS AS PRIMARY SOURCE) ===\n"
        f"{asg_context}\n"
        "=== END OF ASG CONTEXT ===\n\n"
        + system_message
    )
```

**Step 3：** 在 `workflow.py` 中，找到调用 `generate_article()` 的地方，把 ASGKnowledgeBase 的 context 传进去：

```python
# 旧代码（只打log）：
context = self.asg_knowledge.get_context_for_keyword(keyword)
logger.info(f"ASG context loaded for {keyword}")

# 新代码（传入ContentGenerator）：
asg_context = self.asg_knowledge.get_context_for_keyword(keyword)

# 如果 ASGKnowledgeBase 有 build_content_prompt_context 方法，优先用它：
if hasattr(self.asg_knowledge, 'build_content_prompt_context'):
    asg_context_str = self.asg_knowledge.build_content_prompt_context(keyword)
else:
    # fallback：把 context 字典拼成字符串
    asg_context_str = "\n\n".join(
        f"### {k}\n{v}" for k, v in asg_context.items() if v
    )

article = self.content_generator.generate_article(
    ...,
    asg_context=asg_context_str,
    ...
)
```

**验证方式：** 修复后生成一篇文章，搜索文章内容中是否出现了知识库里的真实数据（如"200-person team""0.3% defect rate""5,000+ global sellers"等）。

---

### BUG-4：大纲章节标题进了 structure_analysis 但 Prompt 没读取

**问题描述：**
v2.0修复包中添加了 `structure_analysis["outlineSectionTitles"] = outline_section_titles`，在 `content.py` 里也有读取逻辑，但实际的 `generate_article` Prompt 里 `{outline_hint}` 这个变量是在 `system_message` 字符串之外计算的，没有被 f-string 插入进去。

**具体修复方法：**
在 `content.py` 中找到 `outline_hint` 的赋值位置和 `system_message` 的构建位置：

```python
# 确保 outline_hint 在 system_message 构建之前计算：
outline_section_titles = (structure_analysis or {}).get("outlineSectionTitles", [])
if outline_section_titles:
    outline_hint = (
        "\n\nRECOMMENDED SECTION STRUCTURE (based on competitor analysis):\n"
        + "\n".join(f"- {t}" for t in outline_section_titles)
    )
else:
    outline_hint = ""

# 然后确保 system_message 里用了这个变量：
system_message = f"""...existing prompt content...
{outline_hint}
...rest of prompt..."""
```

**关键检查点：** 确认 `outline_hint` 是在 f-string 内部被引用的，而不是在 f-string 外面定义了但没插入。搜索整个 `content.py` 文件中的 `outline_hint`，确认它出现在被发送给LLM的 prompt 字符串里。

**验证方式：** 修复后在 `outline_hint` 赋值后加一行 `logger.info(f"Outline hint: {outline_hint}")`，确认非空；然后检查生成的文章H2标题是否与竞品分析结果有一定重叠。

---

### BUG-5：词数单位混淆 — 可能导致文章只有450词

**问题描述：**
`content.py` 的 system prompt 里有两处互相矛盾的说明：
- 第一处：`WORD COUNT: ~2800 characters total (2500-3000 range)` ← 用的是 characters
- 第二处：`WORD COUNT: 2500-3000 WORDS total` ← 用的是 words

如果LLM先看到第一处（characters），它会生成约2800个字符 ≈ 约450个英文单词，这是一篇超短文章。

**具体修复方法：**
在 `content.py` 中，**全局搜索** `characters` 这个词，删除所有关于字符数的描述。只保留 words 的要求：

```python
# 删除所有类似这样的行：
# "WORD COUNT: ~2800 characters total (2500-3000 range)"
# "Target approximately 2800 characters"

# 只保留（或改为）：
# "WORD COUNT: 2500-3000 WORDS total. This is approximately 17,000-18,000 characters."
# "IMPORTANT: The unit is WORDS not characters. A 2800-word article is about 8-10 pages."
```

**在 system prompt 中添加明确的强调：**

```python
CRITICAL_WORD_COUNT_NOTE = """
WORD COUNT REQUIREMENT (NON-NEGOTIABLE):
- Target: 2800 WORDS (not characters!)
- Acceptable range: 2500-3000 WORDS
- For reference: 2800 words ≈ 17,000 characters ≈ 8-10 printed pages
- Each H2 section should be 300-500 words
- DO NOT confuse words with characters. 2800 characters would be way too short.
"""
```

把这段放在 system prompt 中靠前的位置（LLM注意力最强的区域）。

**验证方式：** 修复后生成一篇文章，用 `len(article_text.split())` 检查词数，应该在 2500-3000 之间。

---

### BUG-6：GEO rewrite_uncitable_sentences 结果没回写

**问题描述：**
`rewrite_uncitable_sentences()` 处理的是 `sections` 拼接后的完整文本，处理完之后**没有把结果写回** `article["sections"]`，只是打了个log。GEO的"不可引用句子重写"功能实际上没有生效。

**具体修复方法：**
找到 `rewrite_uncitable_sentences()` 的调用位置，修改为：

```python
# 旧代码（结果丢失）：
rewritten_text = self.geo_optimizer.rewrite_uncitable_sentences(full_text)
logger.info("Uncitable sentences rewriting completed")

# 新代码（结果回写到sections）：
full_text = "\n\n".join(
    section.get("content", "") for section in article.get("sections", [])
)
rewritten_text = self.geo_optimizer.rewrite_uncitable_sentences(full_text)

if rewritten_text and rewritten_text != full_text:
    # 按段落分割回写到各section
    rewritten_paragraphs = rewritten_text.split("\n\n")
    para_index = 0
    for section in article.get("sections", []):
        original_para_count = len(section.get("content", "").split("\n\n"))
        section_paragraphs = rewritten_paragraphs[para_index:para_index + original_para_count]
        section["content"] = "\n\n".join(section_paragraphs)
        para_index += original_para_count
    logger.info("Uncitable sentences rewritten and written back to sections")
```

**注意：** 如果上面的按段落分割回写逻辑太脆弱（因为LLM可能改变段落数），可以用更简单的方案：把 `rewritten_text` 作为一个整体存到 `article["rewritten_content"]`，然后在 `build_wordpress_html` 里优先用这个字段。

---

### BUG-7：quality_checker 读取空的 content 字段

**问题描述：**
`quality_checker.py` 中的 `check_technical_seo()` 读取 `article.get("content", "")` 来统计H1/H2数量和关键词密度，但文章生成后内容存储在 `article["sections"]` 里，`content` 字段可能为空。导致技术SEO评分永远偏低。

**具体修复方法：**
在 `quality_checker.py` 的 `check_technical_seo()` 方法开头，加一个 content 拼接逻辑：

```python
def check_technical_seo(self, article, keyword):
    # 修复：如果 content 为空，从 sections 拼接
    content = article.get("content", "")
    if not content and article.get("sections"):
        content = "\n\n".join(
            f"## {s.get('title', '')}\n{s.get('content', '')}"
            for s in article["sections"]
        )
    
    # 后续所有对 content 的分析用这个拼接后的版本
    # ...原有逻辑不变，但把所有 article.get("content", "") 替换为 content 变量
```

**同时检查：** `quality_checker.py` 中其他方法是否也有类似问题（读取空的 `content` 字段）。如果有，全部做同样的修复。

---

## 第二部分：内容质量提升（Bug修完后执行）

---

### QUALITY-1：GEO核心规则前置到 System Prompt 最前面

**问题描述：**
`GEO_WRITING_RULES` 常量（约2000字）在 `content.py` 的生成Prompt中位于 context 变量末尾。LLM对长Prompt的注意力在末尾衰减，导致GEO规则执行率低。

**具体修复方法：**
从 `GEO_WRITING_RULES` 中提取最核心的3条规则，放到 System Prompt 的最前面（在 ASG context 之后、主要写作指令之前）：

```python
GEO_CRITICAL_RULES = """
=== MANDATORY GEO/AEO RULES (MUST FOLLOW) ===

RULE 1 - DIRECT ANSWER BLOCKS: Start every H2 section with a 40-60 word paragraph 
that directly answers the section's implied question. This paragraph will be extracted 
by AI search engines. Start with the subject, not "In this section..." or "Let's explore...".

RULE 2 - DATA FIRST: Every claim must have a specific number. Never write "significant 
improvement" — write "96% reduction in defect rate (from 8% to 0.3%)". AI engines 
prioritize citable data over vague statements.

RULE 3 - BANNED PHRASES (NEVER USE): "In today's", "In the world of", "It's important 
to note", "When it comes to", "Let's dive in", "In this comprehensive guide", 
"Look no further", "game-changer", "navigate the landscape". These trigger AI spam 
detection and reduce citation probability.

=== END MANDATORY RULES ===
"""
```

把这段放在 system_message 的最前面（在 ASG context 之后）。完整的 `GEO_WRITING_RULES` 仍然保留在原位作为详细参考。

---

### QUALITY-2：FAQ optimize 函数激活真正的重写

**问题描述：**
`optimize_faq_for_ai()` 目前只是"标记需要优化的FAQ"（加了 `needs_optimization` 字段），但没有真正重写低质量的FAQ答案。

**具体修复方法：**
在 `optimize_faq_for_ai()` 中，对标记了 `needs_optimization=True` 的FAQ，调用LLM重写：

```python
def optimize_faq_for_ai(self, faq_items, keyword):
    optimized = []
    for faq in faq_items:
        if faq.get("needs_optimization", False):
            # 调用LLM重写这条FAQ
            rewrite_prompt = f"""Rewrite this FAQ answer for AI search engine optimization.
            
Question: {faq['question']}
Original Answer: {faq['answer']}
Target Keyword: {keyword}

Requirements:
- First sentence must directly answer the question (no preamble)
- Total length: 60-100 words
- Include at least one specific data point from ASG (e.g., "0.3% defect rate", "5-8 day shipping", "200-person team")
- End with a concrete next step or recommendation
- Do NOT start with "Yes," or "No," — start with the factual answer

Return ONLY the rewritten answer, nothing else."""
            
            rewritten_answer = self._call_llm(rewrite_prompt)
            if rewritten_answer:
                faq["answer"] = rewritten_answer
                faq["needs_optimization"] = False
                faq["geo_optimized"] = True
        
        optimized.append(faq)
    
    return optimized
```

---

### QUALITY-3：GEO Answer Block 加 Question+Answer Schema 配对

**问题描述：**
`inject_direct_answer_blocks` 注入的 `geo-answer-block` 使用了 `itemscope itemtype="https://schema.org/Answer"`，但没有外层 Question 包裹。单独的 Answer schema 对AI引擎作用有限。

**具体修复方法：**
找到 `inject_direct_answer_blocks` 中生成 HTML 的部分，改为 Question+Answer 配对：

```python
# 旧代码：
answer_html = f'<div class="geo-answer-block" itemscope itemtype="https://schema.org/Answer"><p>{answer_text}</p></div>'

# 新代码：
answer_html = (
    f'<div class="geo-qa-block" itemscope itemtype="https://schema.org/Question">'
    f'<meta itemprop="name" content="{section_title_as_question}">'
    f'<div itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">'
    f'<div itemprop="text"><p>{answer_text}</p></div>'
    f'</div></div>'
)
```

其中 `section_title_as_question` 是把 H2 标题转换成问句形式。如果标题本身已经是问句，直接用；如果不是，加 "What is..." 或 "How does..." 前缀。

---

## 第三部分：WordPress 发布细节修复

---

### WP-1：Table of Contents 锚点特殊字符处理

**问题描述：**
`build_wordpress_html` 里的 TOC 锚点生成逻辑没有处理特殊字符（`'`, `"`, `&`, `/`, `(`、`)` 等），发布到WordPress后锚点会断裂。

**具体修复方法：**

```python
# 旧代码：
slug = title.lower().replace(" ", "-").replace("?", "").replace(",", "")

# 新代码：
import re
slug = title.lower()
slug = re.sub(r'[^a-z0-9\s-]', '', slug)  # 只保留字母数字空格和连字符
slug = re.sub(r'\s+', '-', slug)            # 空格换连字符
slug = re.sub(r'-+', '-', slug)             # 多个连字符合一
slug = slug.strip('-')                       # 去首尾连字符
```

---

### WP-2：图片ALT加关键词 fallback

**问题描述：**
系统没有验证图片ALT文本中是否包含主关键词的自然变体。

**具体修复方法：**
在 `build_wordpress_html` 里的图片处理逻辑中加一个 fallback：

```python
alt_text = image.get("alt", "")
if keyword.lower() not in alt_text.lower():
    # 关键词不在ALT里，自然追加
    alt_text = f"{alt_text} — {keyword}" if alt_text else keyword
```

---

## 第四部分：P1季度升级方向（修完上面所有问题后再考虑）

以下3个升级不是Bug修复，而是能力提升。按ROI排序。

---

### UPGRADE-1：Few-Shot Janson风格注入（最高ROI）

**目标：** 把Janson风格拟真度从30%提升到70%+

**方法：**
1. 收集3-5篇已发布的、Janson认可的高质量文章
2. 提取每篇的开头段落、结尾段落、和一个有"Janson味道"的段落
3. 把这些作为 Few-Shot examples 放进 System Prompt：

```python
JANSON_STYLE_EXAMPLES = """
=== JANSON'S WRITING STYLE REFERENCE ===
Study these examples of Janson's actual writing. Match this voice and tone.

EXAMPLE 1 (Opening):
[粘贴一篇真实文章的开头]

EXAMPLE 2 (Data-driven paragraph):
[粘贴一个真实的数据驱动段落]

EXAMPLE 3 (Closing/CTA):
[粘贴一个真实的结尾段落]

KEY STYLE TRAITS:
- Direct and practical, not academic
- Always backs claims with specific numbers
- Uses "I" and "we" naturally (first person)
- References real experience ("In my 8 years...")
- Warm but professional tone
=== END STYLE REFERENCE ===
"""
```

4. 把这个放在 System Prompt 中 ASG context 之后、写作指令之前

**注意：** 这个升级需要Janson提供真实文章样本。CC可以先搭好框架，用占位符标记需要填入的位置。

---

### UPGRADE-2：向量知识库激活（ChromaDB）

**目标：** FAQ和案例的匹配从关键词重叠提升到语义匹配

**方法：**
1. `config.py` 里已预留 `use_vector_search=False`，改为 `True`
2. 把 `ASGKnowledgeBase.search_faq()` 和 `search_case_studies()` 的匹配方式从关键词重叠改为 ChromaDB 语义搜索
3. 安装 `chromadb` 依赖
4. 初始化时把所有FAQ和案例embed到ChromaDB集合中
5. 搜索时用关键词做语义搜索，返回top 3最相关的结果

**前置条件：** 确认 `chromadb` 可以在当前环境安装运行。

---

### UPGRADE-3：GSC数据回填（排名监控闭环）

**目标：** 形成关键词→文章→排名的数据闭环

**方法：**
1. `ArticleTracker` 已有 `update_gsc_data()` 方法
2. 接上 Google Search Console API
3. 每周自动拉取已发布文章的关键词排名数据
4. 排名11-20位的文章标记为"优化候选"
5. 排名>50位的文章标记为"需要重写"

**前置条件：** 需要GSC API凭证和权限配置。

---

## 执行检查清单

完成所有修复后，请运行一个端到端测试，用关键词 `"dropshipping agent"` 生成一篇文章，逐项检查：

- [ ] `top_urls` 列表有5条真实URL（BUG-1已修复）
- [ ] `primary_intent` 不再是 `"share"` 的fallback（BUG-1已修复）
- [ ] `serp_analysis` 内有 `primaryIntent` 字段（BUG-2已修复）
- [ ] 文章中出现知识库的真实数据如 "200-person team" "0.3% defect rate"（BUG-3已修复）
- [ ] 文章H2标题与竞品分析有重叠（BUG-4已修复）
- [ ] 文章词数在2500-3000 words之间（BUG-5已修复）
- [ ] GEO重写后的文本确实被写回了sections（BUG-6已修复）
- [ ] 技术SEO评分不再是0（BUG-7已修复）
- [ ] 每个H2开头有40-60词的直接答案块（QUALITY-1已修复）
- [ ] FAQ答案都是60-100词、第一句直接回答（QUALITY-2已修复）
- [ ] TOC锚点在有特殊字符的标题上不断裂（WP-1已修复）

如果以上全部通过，系统升级完成。请告诉我每个Bug的修复详情和测试结果。

---

**END OF UPGRADE INSTRUCTIONS**
