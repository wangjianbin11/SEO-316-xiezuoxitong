# 快速开始指南 - SEO Content Generator v3.0

## 🚀 5分钟快速上手

### 1. 安装依赖 (1分钟)

```bash
# 进入项目目录
cd seo-content-generator-315-新版本调试

# 安装依赖
pip install -e .
```

### 2. 配置环境变量 (2分钟)

```bash
# 复制模板
cp .env.example .env

# 编辑 .env,填写以下必填项:
# - OPENAI_API_KEY (必填)
# - GOOGLE_SEARCH_API_KEY (必填)
# - GOOGLE_SEARCH_ENGINE_ID (必填)
# - WORDPRESS_SITE_URL (必填)
# - WORDPRESS_USERNAME (必填)
# - WORDPRESS_APP_PASSWORD (必填)
```

### 3. 运行第一篇文章 (2分钟)

```bash
# 使用GUI
python -m seo_gen.gui

# 或使用CLI
python -m seo_gen.main generate "dropshipping agent"
```

---

## 📋 核心功能使用

### 功能1: 检查点恢复

如果生成过程中断,再次运行会自动从断点恢复:

```python
# 自动恢复(默认)
result = await orchestrator.run_advanced_workflow(
    keyword="your keyword",
    resume=True  # 默认True
)

# 强制重新开始
result = await orchestrator.run_advanced_workflow(
    keyword="your keyword",
    resume=False  # 清除检查点,从头开始
)
```

### 功能2: 质量检查

生成后自动进行质量检查:

```python
from seo_gen.modules.quality_checker import QualityChecker

checker = QualityChecker()
report = checker.check(
    article=article_data,
    target_word_count=2500,
    primary_keyword="dropshipping agent"
)

# 查看结果
print(f"总分: {report.total_score}/100")
print(f"可发布: {report.publish_ready}")

if not report.publish_ready:
    print("问题:")
    for issue in report.critical_issues:
        print(f"  - {issue}")
```

### 功能3: 竞品分析

自动爬取并分析竞品:

```python
from seo_gen.modules.competitor_scraper import CompetitorScraper

scraper = CompetitorScraper()

# 爬取竞品
analysis = await scraper.analyze_competitors(
    keyword="dropshipping agent",
    urls=["url1", "url2", "url3"],
    paa_questions=["question1", "question2"],
    llm_client=llm_client
)

# 查看结果
print(f"目标字数: {analysis.target_word_count}")
print(f"主导格式: {analysis.dominant_format}")
print(f"内容缺口: {analysis.uncovered_topics}")
```

### 功能4: GEO优化

优化文章使其更易被AI引用:

```python
from seo_gen.modules.geo_optimizer import GEOOptimizer

optimizer = GEOOptimizer(llm_client)

# 评分
score = optimizer.analyze_geo_score(article)
print(f"GEO总分: {score.total_score}/100")

# 注入直接答案块
article = await optimizer.inject_direct_answer_blocks(article, llm_client)

# 优化FAQ
faq_list = optimizer.optimize_faq_for_ai(article['faqSection']['items'])
```

### 功能5: Schema生成

生成完整的Schema标记:

```python
from seo_gen.modules.schema_generator import SchemaGenerator

generator = SchemaGenerator()

# 生成所有Schema
schema_html = generator.generate_all_schemas(
    article=article_data,
    article_url="https://example.com/article",
    faq_list=faq_items,
    category_name="Blog",
    publish_date="2026-03-15T10:00:00+08:00"
)

# schema_html 可直接注入到 <head> 标签
```

### 功能6: 文章追踪

追踪已发布文章,防止重复:

```python
from seo_gen.modules.article_tracker import get_article_tracker

tracker = get_article_tracker()

# 检查是否已发布
if tracker.is_published("dropshipping agent"):
    print("该关键词已发布")
    url = tracker.get_url("dropshipping agent")
    print(f"URL: {url}")
else:
    # 生成并发布...
    
    # 标记为已发布
    tracker.mark_published(
        keyword="dropshipping agent",
        article_title="Complete Guide to Dropshipping Agents",
        article_type="pillar",
        word_count=2500,
        wordpress_url="https://example.com/article",
        wp_post_id=123,
        quality_score=85.5,
        geo_score=90.0
    )

# 查看统计
stats = tracker.get_statistics()
print(f"总文章数: {stats['total_articles']}")
print(f"平均质量分: {stats['avg_quality_score']}")
```

### 功能7: 关键词数据

获取真实关键词数据(需配置DataForSEO):

```python
from seo_gen.modules.keyword_data import get_keyword_data_client

client = get_keyword_data_client()

# 批量获取关键词数据
metrics = await client.get_keyword_metrics(
    keywords=["dropshipping agent", "china sourcing agent"],
    location_code=2840  # US
)

for metric in metrics:
    print(f"{metric.keyword}:")
    print(f"  搜索量: {metric.monthly_volume}")
    print(f"  难度: {metric.kd_score}")
    print(f"  CPC: ${metric.cpc}")
    print(f"  数据源: {metric.data_source}")
```

---

## 🔧 常见问题

### Q1: 生成失败怎么办?

**A**: 检查以下内容:
1. 查看 `outputs/errors/` 目录下的错误日志
2. 检查 `.env` 配置是否正确
3. 确认API密钥有效且有余额
4. 查看检查点目录 `outputs/{keyword}/checkpoints/`

### Q2: 如何强制重新生成?

**A**: 两种方法:
```python
# 方法1: 代码中设置
result = await orchestrator.run_advanced_workflow(
    keyword="your keyword",
    resume=False  # 强制重新开始
)

# 方法2: 手动删除检查点
rm -rf outputs/your-keyword-slug/checkpoints/
```

### Q3: 质量分数太低怎么办?

**A**: 查看质量报告的建议:
```python
report = checker.check(article, target_word_count, primary_keyword)

print("改进建议:")
for rec in report.recommendations:
    print(f"  - {rec}")

print("\n严重问题:")
for issue in report.critical_issues:
    print(f"  - {issue}")
```

### Q4: DataForSEO是必须的吗?

**A**: 不是必须的
- 不配置: 使用LLM估算(confidence=0.3)
- 配置后: 获取真实数据(confidence=1.0)
- 推荐配置以获得更准确的关键词难度

### Q5: 如何查看生成进度?

**A**: 检查点系统会保存进度:
```python
from seo_gen.modules.checkpoint import CheckpointManager

checkpoint = CheckpointManager("outputs", "your keyword")
summary = checkpoint.get_summary()

print(f"已完成: {summary['completed_count']}/{summary['total_stages']}")
print(f"完成阶段: {summary['completed_stages']}")
print(f"下次从阶段 {summary['resume_from']} 继续")
```

---

## 📊 性能优化建议

### 1. 并发控制

在 `.env` 中调整速率限制:

```bash
# LLM请求速率
LLM_MAX_RPM=5

# Google API速率
GOOGLE_API_MAX_QPS=2.0

# 图片生成并发
IMAGE_MAX_CONCURRENT=1

# 竞品爬取延迟
COMPETITOR_SCRAPE_DELAY_MIN=1.5
COMPETITOR_SCRAPE_DELAY_MAX=3.0
```

### 2. 批量处理

使用检查点系统批量处理多个关键词:

```python
keywords = ["keyword1", "keyword2", "keyword3"]

for keyword in keywords:
    try:
        result = await orchestrator.run_advanced_workflow(
            keyword=keyword,
            resume=True  # 支持断点恢复
        )
        print(f"✓ {keyword} 完成")
    except Exception as e:
        print(f"✗ {keyword} 失败: {e}")
        continue  # 继续下一个
```

### 3. 成本控制

追踪生成成本:

```python
tracker = get_article_tracker()
stats = tracker.get_statistics()

print(f"总成本: ${stats['total_cost_usd']:.2f}")
print(f"平均成本: ${stats['total_cost_usd'] / stats['total_articles']:.2f}/篇")
```

---

## 🎯 最佳实践

### 1. 关键词选择
- 优先选择KD<45的关键词(如果有DataForSEO数据)
- 长尾词(3-4个单词)通常更容易排名
- 使用 `keyword_data.py` 获取真实搜索量

### 2. 质量控制
- 设置合理的 `MIN_PUBLISH_SCORE` (推荐75-80)
- 定期检查质量报告,优化Prompt
- 使用 `quality_checker.py` 在发布前验证

### 3. 内容优化
- 确保每个H2都有直接答案块
- FAQ数量保持在6-8个
- 每500词至少2个具体数字
- 包含作者bio和经验陈述

### 4. Schema标记
- 始终生成完整Schema(Article + FAQ + Breadcrumb)
- 使用 https://validator.schema.org/ 验证
- 确保FAQ Schema与正文FAQ匹配

### 5. 追踪管理
- 定期备份 `seo_tracker.db`
- 使用 `article_tracker.py` 防止重复生成
- 回填GSC数据以追踪效果

---

## 📚 更多资源

- **完整文档**: `UPGRADE_COMPLETE.md`
- **升级规范**: `SEO_SYSTEM_UPGRADE_SPEC_v3.md`
- **系统架构**: `docs/SYSTEM_ARCHITECTURE.md`
- **配置模板**: `.env.example`

---

**版本**: v3.0  
**更新日期**: 2026-03-15  
**状态**: ✅ 生产就绪
