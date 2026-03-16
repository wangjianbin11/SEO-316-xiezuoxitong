# SEO Content Generator 系统架构文档

## 概述

本系统是一个完整的 SEO 文章生成工具，从关键词输入到 WordPress 发布，实现全流程自动化。

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           GUI 界面 (gui.py)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 关键词输入   │  │ 策略问题选择 │  │ 文章类型确认 │  │ 进度显示    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    工作流编排器 (workflow.py)                         │
│                                                                      │
│  阶段0: 智能分类 → 阶段0.5: 知识库加载 → 阶段1: 标题生成              │
│                                    │                                 │
│  阶段2: 内容创作 ← ─ ─ ─ ─ ─ ─ ─ ─ ┘                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  知识库模块    │         │  SERP 分析    │         │  内容生成     │
│ (knowledge.py)│         │  (serp.py)    │         │ (content.py)  │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│ ASG 知识库    │         │ Google API    │         │  LLM 客户端   │
│(asg_knowledge)│         │ Custom Search │         │  (llm.py)     │
└───────────────┘         └───────────────┘         └───────────────┘
```

---

## 完整工作流程（11步）

### 阶段 0: 智能文章类型分类

**文件**: `content_classifier.py`

**流程**:
1. 接收用户输入的关键词
2. 使用 `ContentClassifier.classify()` 分析关键词
3. 返回文章类型推荐：
   - `pillar` (顶梁柱型): 4000-6000字，9个章节
   - `response` (回答型): 3000-4000字，7个章节
   - `share` (分享型): 3000-4000字，6个章节

**代码位置**: `workflow.py:107-138`

```python
classification_result = self.content_classifier.classify(keyword)
article_type = classification_result.article_type
```

---

### 阶段 0.5: 知识库加载

**文件**: `asg_knowledge.py`, `knowledge.py`

**知识库来源**:
```
/asg dropshipping 基础知识_副本/
├── janson介绍.txt          # Janson 个人介绍
├── 企业介绍.txt            # ASG 企业介绍
├── 业务流程.txt            # 业务流程说明
├── 客户画像-完整版.md      # 目标客户画像
└── GEO代发货专项指南.md    # GEO 写作规范

/asg-faq-matrix-geo_副本/
├── *-FAQ.md                # FAQ 矩阵文件
└── ASG成功案例库-*.md      # 成功案例库
```

**加载流程**:
1. `get_asg_knowledge_base()` 获取知识库单例
2. `get_context_for_keyword(keyword)` 根据关键词获取相关内容
3. 返回 `ASGKnowledgeContext` 包含:
   - `janson_intro`: Janson 个人介绍
   - `company_intro`: 企业介绍
   - `customer_persona`: 客户画像
   - `faq_snippets`: 相关 FAQ (最多5个)
   - `case_studies`: 相关案例 (最多3个)
   - `geo_guidelines`: GEO 写作规范

**关键词搜索逻辑** (`asg_knowledge.py:125-166`):
```python
def search_faq(self, keyword: str, limit: int = 5):
    # 遍历所有 FAQ 文件
    for faq_file in self.faq_matrix_dir.glob("*-FAQ.md"):
        content = self._read_file(faq_file)
        if keyword_lower in content.lower():
            sections = self._extract_relevant_sections(content, keyword_lower)
            results.append({"source": faq_file.name, "content": section})
```

---

### 阶段 1: SERP 分析与标题生成

#### 1.1 Google 搜索调研

**文件**: `serp.py`

**流程**:
1. 调用 Google Custom Search API
2. 获取 100 条搜索结果（10页）
3. AI 分析搜索意图

**API 调用** (`serp.py:36-73`):
```python
url = "https://www.googleapis.com/customsearch/v1"
params = {
    "key": self.api_key,
    "cx": self.engine_id,
    "q": query,
    "num": 10,
    "start": start,
}
response = await self.client.get(url, params=params)
```

**搜索意图分析** (`serp.py:120-196`):
- 使用 LLM 分析前 20 条结果
- 返回:
  - `searchIntent`: informational/navigational/transactional/commercial
  - `primaryIntent`: share/qa/pillar
  - `paaQuestions`: 用户常见问题
  - `keyTopics`: 关键主题

#### 1.2 标题生成

**文件**: `title.py`

**流程**:
1. `generate_titles()`: 生成 5 个候选标题
2. `select_best_title()`: AI 选择最佳标题

---

### 阶段 2: 内容创作

#### 2.1 结构分析

**文件**: `structure.py`

**流程**:
1. 分析竞争对手文章结构
2. 推荐章节数量和结构

#### 2.2 大纲生成

**文件**: `outline.py`

**流程**:
1. 基于结构分析生成文章大纲
2. 确定每个章节的主题和要点

#### 2.3 文章撰写

**文件**: `content.py`

**核心方法**: `generate_article()` (`content.py:276-673`)

**输入参数**:
- `keyword`: 关键词
- `slug`: URL slug
- `serp_analysis`: SERP 分析结果
- `structure_analysis`: 结构分析结果
- `article_type`: 文章类型 (pillar/response/share)

**案例库引用逻辑** (`content.py:100-194`):
```python
def _select_relevant_case(self, title: str, keyword: str) -> str:
    # 关键词与案例主题的映射
    topic_keywords = {
        "dropshipping": ["dropshipping", "一件代发", "代发", "fulfillment"],
        "supplier": ["supplier", "供应商", "sourcing", "采购", "工厂"],
        "quality": ["quality", "质量", "质检", "qc", "inspection"],
        "shipping": ["shipping", "物流", "发货", "配送", "delivery"],
        # ... 更多映射
    }

    # 遍历案例文件，计算相关性分数
    for case_file in case_files:
        content = case_file.read_text().lower()
        score = 0
        if keyword_lower in content:
            score += 10  # 直接匹配
        for topic in matched_topics:
            for kw in topic_keywords.get(topic, []):
                if kw in content:
                    score += 2
```

**LLM Prompt 构建** (`content.py:328-579`):
- 包含作者背景 (Janson)
- 目标受众
- 企业介绍
- GEO 策略
- 文章类型指令
- 图片要求 (1封面 + 3章节图)
- 链接要求 (5外链 + 3-5内链)
- E-E-A-T 要求

**输出 JSON 格式**:
```json
{
  "keyword": "关键词",
  "title": "SEO优化标题",
  "h1": "H1标题",
  "metaDescription": "Meta描述",
  "slug": "url-slug",
  "featuredImage": {"alt": "...", "caption": "..."},
  "introduction": "引言段落",
  "keyTakeaways": ["要点1", "要点2", ...],
  "sections": [
    {
      "sectionIndex": 1,
      "sectionTitle": "章节标题",
      "content": "章节内容",
      "image": {"alt": "...", "caption": "..."}
    }
  ],
  "authorBio": {...},
  "sources": [...],
  "externalLinks": [...]
}
```

#### 2.4 质量检测

**文件**: `quality.py`

**检测项目**:
- E-E-A-T 评分
- 内容原创性
- AI 检测概率

---

### 阶段 3: 图片生成

**文件**: `image.py`

**图片风格** (`image.py:19-29`):
```python
IMAGE_STYLES = {
    "modern": "Modern flat design, clean lines...",
    "minimalist": "Minimalist design, lots of white space...",
    "professional": "Corporate professional style...",
    "creative": "Creative and artistic, vibrant colors...",
    "tech": "Technology-focused, futuristic elements...",
    "nature": "Natural and organic, earth tones...",
    "elegant": "Elegant and sophisticated, luxury feel...",
    "playful": "Playful and friendly, bright colors...",
}
```

**生成流程**:
1. `generate_cover_image()`: 生成封面图
2. `generate_collage_image()`: 生成章节配图 (3张)

**API 调用** (`image.py:58-143`):
- 使用 OpenRouter `/chat/completions` 端点
- 支持 base64 和 URL 两种返回格式

---

### 阶段 4: WordPress 发布

**文件**: `wordpress.py`

**发布流程**:
1. `upload_image()`: 上传封面图和章节图到媒体库
2. `publish_article()`: 创建文章草稿

**API 端点**:
- 媒体上传: `{site_url}/wp-json/wp/v2/media`
- 文章发布: `{site_url}/wp-json/wp/v2/posts`

**HTML 构建** (`content.py:747-893`):
```python
def build_wordpress_html(self, article, cover_image_url, section_images,
                         keyword, internal_links, external_links):
    # 1. 封面图
    # 2. 引言
    # 3. Key Takeaways
    # 4. 目录
    # 5. 章节内容 + 图片
    # 6. 作者介绍
    # 7. 参考来源
```

---

## 内部链接系统

**文件**: `internal_links.py`

### 链接匹配逻辑

**关键词映射** (`internal_links.py:79-144`):
```python
KEYWORD_URL_MAPPING = {
    "dropshipping": "https://asgdropshipping.com/how-to-start-dropshipping/",
    "shopify dropshipping": "https://asgdropshipping.com/how-to-shopify-dropshipping-store/",
    "dropshipping suppliers": "https://asgdropshipping.com/best-dropshipping-suppliers/",
    # ... 更多映射
}
```

**匹配算法** (`internal_links.py:165-246`):
```python
def get_relevant_internal_links(self, keyword, article_title, article_content, count=3):
    full_text = f"{article_title} {article_content}".lower()

    for kw, url in self.keyword_mapping.items():
        is_related = (
            kw_lower in keyword_lower or
            keyword_lower in kw_lower or
            kw_lower in full_text or
            any(word in full_text for word in kw_lower.split() if len(word) > 3)
        )
        if is_related:
            relevant_links.append({"keyword": kw, "url": url})
```

### 链接样式

- **内部链接**: 橘色加粗 `#FF8C00`
- **外部链接**: 蓝色加粗 `#0066CC`
- **关键词高亮**: 蓝色加粗 `#0066CC`

---

## 关键词分析系统

**文件**: `keyword_analyzer.py`

### 分析流程

1. **类型检测** (`_detect_keyword_type`):
   - service: 服务类
   - course: 课程类
   - software: 软件类
   - media: 媒体类
   - product: 产品类
   - other: 其他

2. **策略问题生成** (`_generate_questions`):
   - Q1: 搜索量最高的方面
   - Q2: 目标客户类型
   - Q3: 搜索意图分析

3. **增强搜索查询** (`build_enhanced_search_queries`):
   - 基于用户答案生成更精准的搜索词

---

## LLM 客户端

**文件**: `llm.py`

### 重试机制

```python
self.max_retries = 3

for attempt in range(self.max_retries):
    try:
        response = await self.client.post("/chat/completions", json=payload)
        # 成功处理
    except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
        wait_time = (attempt + 1) * 2  # 2, 4, 6 秒
        if attempt < self.max_retries - 1:
            await asyncio.sleep(wait_time)
```

---

## 配置文件

**文件**: `config.py`

**环境变量**:
```
# LLM API
LLM_API_BASE=https://openrouter.ai/api/v1
LLM_API_KEY=your_key
LLM_MODEL=anthropic/claude-3.5-sonnet

# Google Search API
GOOGLE_SEARCH_API_KEY=your_key
GOOGLE_SEARCH_ENGINE_ID=your_id

# WordPress
WORDPRESS_SITE_URL=https://asgdropshipping.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_password

# Image Generation
IMAGE_API_BASE=https://openrouter.ai/api/v1
IMAGE_API_KEY=your_key
IMAGE_MODEL=openai/dall-e-3
```

---

## 文件结构

```
seo-content-generator/
├── src/seo_gen/
│   ├── modules/
│   │   ├── asg_knowledge.py    # ASG 知识库
│   │   ├── content.py          # 内容生成
│   │   ├── content_classifier.py # 文章分类
│   │   ├── detection.py        # AI/原创检测
│   │   ├── image.py            # 图片生成
│   │   ├── internal_links.py   # 内部链接
│   │   ├── keyword_analyzer.py # 关键词分析
│   │   ├── knowledge.py        # 基础知识库
│   │   ├── llm.py              # LLM 客户端
│   │   ├── outline.py          # 大纲生成
│   │   ├── quality.py          # 质量检测
│   │   ├── serp.py             # SERP 分析
│   │   ├── structure.py        # 结构分析
│   │   ├── title.py            # 标题生成
│   │   ├── wordpress.py        # WordPress 发布
│   │   └── workflow.py         # 工作流编排
│   ├── gui.py                  # GUI 界面
│   ├── config.py               # 配置管理
│   └── main.py                 # 主入口
├── knowledge/                  # 知识库文件
├── outputs/                    # 输出目录
└── docs/                       # 文档
```

---

## 批量生成流程

**文件**: `gui.py`

批量生成使用与单篇生成相同的工作流，逐个处理关键词：

1. `start_batch_generation()`: 初始化批量队列
2. `_process_next_batch_keyword()`: 处理下一个关键词
3. `_batch_analyze_keyword()`: 分析关键词
4. `_batch_analyze_and_confirm_type()`: 确认文章类型
5. `_batch_run_single_generation()`: 执行单篇生成
6. 循环直到所有关键词处理完成

---

## 版本信息

- 版本: 2.0
- 最后更新: 2026-03-14
- 主要特性:
  - 三种文章类型支持
  - ASG 知识库集成
  - GEO 优化策略
  - 智能内部链接
  - 多风格图片生成
  - WordPress 自动发布
