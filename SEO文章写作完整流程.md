# SEO文章写作完整流程 - ASG Dropshipping

## 🎯 整体流程概览

```
关键词输入 → SERP分析(10页) → 文章类型分类 → 标题生成 →
类型确认 → GEO优化 → 内容生成 → 图片插入 → 作者介绍 →
内外链优化 → 关键词加粗 → 质量检查 → 输出发布
```

---

## 第一阶段: 关键词研究与SERP分析

### 1.1 关键词输入
- **输入**: 用户提供目标关键词
- **示例**: "how to find dropshipping suppliers"

### 1.2 深度SERP分析 (10页搜索)
```
📊 搜索范围: 100条Google搜索结果(10页)
🔍 分析维度:
  - 搜索意图识别 (informational/transactional/navigational)
  - 竞争对手内容策略
  - 用户关心的问题(PAA)
  - 关键主题提取
  - 内容机会点
```

**技术实现**:
- Google Custom Search API
- 10次API调用,每次10条结果
- 使用前20条结果进行AI深度分析
- 提取: 标题模式、内容结构、关键词密度

### 1.3 搜索意图分析
AI分析100条结果,判断:
- **Informational**: 用户寻求知识(how to, what is, guide)
- **Commercial**: 用户比较选项(best, top, vs, review)
- **Transactional**: 用户准备购买(buy, price, discount)
- **Navigational**: 用户寻找特定网站

---

## 第二阶段: 文章类型智能分类

### 2.1 ASG内容分类系统
基于关键词和SERP分析,自动分类为三种类型:

#### 📚 顶梁柱型 (Pillar Post)
- **识别特征**: complete guide, ultimate guide, comprehensive
- **字数**: 4000-6000字
- **结构**: H1 → 引言 → 摘要 → 目录 → 9个深度章节 → 结论 → FAQ
- **适用**: 核心主题,建立权威性

#### ❓ 回答型 (Response Post)
- **识别特征**: how to, what is, why, when
- **字数**: 3000-4000字
- **结构**: H1 → 引言 → 核心答案 → 7个章节 → 结论 → FAQ
- **适用**: 具体问题,直接解答

#### 📊 分享型 (Share Post)
- **识别特征**: best, top 10, X ways, comparison, vs
- **字数**: 3000-4000字
- **结构**: H1 → 引言 → 快速回答 → 6个列表项 → 结论 → FAQ
- **适用**: 列表、排名、对比内容

### 2.2 分类算法
```python
置信度计算:
- 关键词模式匹配: 40%
- SERP结果分析: 30%
- 搜索意图判断: 20%
- 竞争对手结构: 10%
```

### 2.3 用户确认
- 系统推荐类型(带置信度)
- 用户可确认或修改
- 显示每种类型的特点和字数

---

## 第三阶段: 标题生成与优化

### 3.1 标题生成策略
基于SERP分析生成5个候选标题:

**标题公式**:
```
[数字/形容词] + [核心关键词] + [价值主张] + [年份]

示例:
- "Complete Guide to Dropshipping Suppliers in 2026"
- "How to Find Reliable Dropshipping Suppliers (2026 Edition)"
- "10 Best Dropshipping Suppliers for Your Business in 2026"
```

### 3.2 标题评分系统
每个标题评分标准(100分制):
- **关键词包含** (25分): 目标关键词完整出现
- **长度优化** (20分): 50-60字符
- **情感吸引** (20分): 使用power words
- **年份时效** (15分): 包含2026
- **点击诱因** (20分): 数字、问题、承诺

### 3.3 最佳标题选择
AI自动选择得分最高的标题,考虑:
- SERP竞争度
- 用户搜索意图匹配度
- CTR预测

---

## 第四阶段: GEO优化策略

### 4.1 什么是GEO (Generative Engine Optimization)
**定义**: 针对AI搜索引擎(ChatGPT, Claude, Perplexity, Google AI)的内容优化

### 4.2 GEO核心原则
```
1. 引用友好性 (Citation-Worthy)
   - 提供独特数据和见解
   - 使用具体数字和案例
   - 结构化信息便于AI提取

2. 权威性信号 (Authority Signals)
   - 作者专业背景
   - 公司资质(ASG 1000+客户)
   - 行业经验展示

3. 上下文丰富性 (Contextual Richness)
   - 完整回答用户问题
   - 提供相关背景信息
   - 多角度覆盖主题

4. 结构化数据 (Structured Data)
   - 清晰的标题层级
   - 列表和表格
   - FAQ格式
```

### 4.3 GEO关键词布局策略

#### 主关键词布局 (5-8次加粗)
```
位置分布:
- H1标题: 1次
- 引言段落: 1次 **加粗**
- 第2章节: 1次 **加粗**
- 第4章节: 1次 **加粗**
- 第6章节: 1次 **加粗**
- 结论: 1次 **加粗**
- Meta描述: 1次
```

#### 相关关键词布局
```
LSI关键词(语义相关):
- 自然分布在各章节
- 使用 **加粗** 强调(2-3次)
- 不过度优化,保持自然
```

#### 长尾关键词
```
- 用于H2/H3标题
- 回答具体问题
- 提高长尾流量
```

### 4.4 ASG GEO案例引用
在文章中自然引用ASG的成功案例:

**引用位置**:
- 第3或第4章节
- 作为实际案例说明
- 包含具体数据

**引用格式**:
```markdown
### Real-World Success: ASG's GEO Implementation

At ASG dropshipping, we implemented **GEO optimization strategies**
for our content, resulting in:

- 300% increase in AI search engine citations
- Featured in ChatGPT responses for "dropshipping suppliers"
- 45% boost in organic traffic from AI-powered searches

Our approach focused on **structured content**, **authoritative data**,
and **citation-worthy insights** - exactly what AI engines prioritize.

[Learn more about our GEO services](https://asg-dropshipping.com/geo)
```

---

## 第五阶段: 内容生成

### 5.1 内容结构
```
1. 特色图片 (封面)
2. H1 标题
3. 引言段落 (150-200字)
4. Key Takeaways (4-6点)
5. 目录 (可点击锚链接)
6. 主体内容 (6-9章节)
   - 第2章节: 插入图片1
   - 第4章节: 插入图片2
   - 第6章节: 插入图片3
7. 作者介绍 (100x100头像 + 简介)
8. 结论
9. FAQ (5-8个问题)
10. 来源和延伸阅读 (10+来源)
```

### 5.2 E-E-A-T优化
```
Experience (经验):
- 真实案例研究
- 具体数字和结果
- Before/After对比

Expertise (专业性):
- 行业术语使用
- 深度技术分析
- 引用权威来源

Authoritativeness (权威性):
- ASG品牌背书
- 1000+客户服务记录
- 行业认可

Trustworthiness (可信度):
- 准确数据
- 诚实建议
- 来源引用
```

### 5.3 内容写作风格
```
第一人称视角 (Janson, CEO of ASG):
- "In my 10 years of dropshipping experience..."
- "We've helped over 1,000 clients..."
- "Here's what I've learned..."

数据驱动:
- 具体百分比
- 真实案例数字
- 行业统计数据

可操作建议:
- Step-by-step指导
- 实用工具推荐
- 避免空洞理论
```

---

## 第六阶段: 图片优化

### 6.1 图片配置 (共4张)

#### 特色图片 (封面)
```json
{
  "position": "文章最顶部(H1之前)",
  "size": "1200x630px (推荐)",
  "alt": "包含主关键词的描述",
  "caption": "简短说明",
  "format": "![alt](url \"caption\")"
}
```

#### 文中图片 (3张)
```
图片1: 第2章节
- 位置: 章节内容中间
- 相关性: 与章节主题匹配
- Alt: 描述性文本 + 关键词

图片2: 第4章节
- 位置: 章节内容中间
- 类型: 流程图/对比图/案例图
- Alt: 优化的描述文本

图片3: 第6章节
- 位置: 章节内容中间
- 类型: 数据图表/截图/示例
- Alt: SEO优化描述
```

### 6.2 作者头像 (100x100)
```
位置: 文章末尾,结论之后
尺寸: 100x100px
格式: 圆形头像
内容: Janson照片
配文:
  - 姓名: Janson
  - 职位: CEO, ASG Dropshipping
  - 简介: 50-100字
  - 社交链接: LinkedIn, Twitter
```

---

## 第七阶段: 链接优化

### 7.1 内部链接策略
```
数量: 3-5个
位置: 自然分布在内容中
锚文本: 描述性,非通用
格式: [描述性锚文本](内部URL)

示例:
- "Learn more about [dropshipping product research](link)"
- "Check our guide on [supplier negotiation](link)"
- "See our [pricing calculator](link)"

注意:
- 链接文本不加粗
- 字体大小与正文相同
- 颜色使用默认链接色
```

### 7.2 外部链接策略
```
数量: 最少5个
类型: 权威来源
- 行业报告 (Statista, eMarketer)
- 研究论文 (学术期刊)
- 权威博客 (Shopify, BigCommerce)
- 工具网站 (官方工具)
- 新闻媒体 (Forbes, Entrepreneur)

锚文本示例:
✅ "According to [Shopify's 2026 report](url)"
✅ "Research from [Harvard Business Review](url) shows"
✅ "As noted by [Oberlo's data](url)"

❌ "Click here"
❌ "Read more"
❌ "This link"

注意:
- 外链文本不加粗
- 字体大小正常
- 自然融入句子
```

---

## 第八阶段: 关键词加粗优化

### 8.1 加粗策略
```
总次数: 5-8次
对象:
- 目标主关键词: 3-4次
- 相关LSI关键词: 2-4次

位置分布:
1. 引言段落: 1次主关键词
2. 第2章节: 1次主关键词
3. 第3章节: 1次相关关键词
4. 第4章节: 1次主关键词
5. 第5章节: 1次相关关键词
6. 第6章节: 1次主关键词
7. 结论: 1次主关键词
```

### 8.2 加粗格式规范
```markdown
✅ 正确:
When choosing **dropshipping suppliers**, focus on **product quality**
and **shipping times**.

❌ 错误:
When choosing **DROPSHIPPING SUPPLIERS**, focus on **PRODUCT QUALITY**.

规则:
1. 使用 **text** 格式,不用 <strong>
2. 字体大小与正文相同
3. 不加粗整句话
4. 不加粗链接文本
5. 不过度使用
```

### 8.3 加粗与链接的关系
```markdown
✅ 正确:
**Dropshipping suppliers** are crucial. Check [Oberlo's directory](url).

❌ 错误:
[**Dropshipping suppliers**](url) are crucial.

规则: 加粗和链接分开使用,不叠加
```

---

## 第九阶段: 质量检查

### 9.1 内容检查清单
```
□ 字数达标 (2500-3000字)
□ 章节数量正确 (6-9个)
□ 段落间有空行
□ 标题层级正确 (H1→H2→H3)
□ 无语法错误
□ 数据准确
□ 案例真实
```

### 9.2 SEO检查清单
```
□ 主关键词在H1
□ 主关键词加粗5-8次
□ Meta描述150-160字符
□ URL slug优化
□ Alt文本包含关键词
□ 内链3-5个
□ 外链5+个
```

### 9.3 GEO检查清单
```
□ 结构化内容(列表、表格)
□ 具体数据和案例
□ 作者权威性展示
□ FAQ部分完整
□ 引用来源标注
□ 易于AI提取信息
```

### 9.4 图片检查清单
```
□ 特色图片在顶部
□ 3张文中图片均匀分布
□ 作者头像100x100
□ 所有图片有alt文本
□ 所有图片有caption
```

---

## 第十阶段: 输出与发布

### 10.1 输出格式
```json
{
  "keyword": "目标关键词",
  "title": "优化的标题",
  "h1": "H1标题",
  "metaDescription": "Meta描述",
  "slug": "url-slug",
  "featuredImage": {
    "alt": "特色图片alt",
    "url": "图片URL",
    "caption": "图片说明"
  },
  "introduction": "引言段落",
  "keyTakeaways": ["要点1", "要点2", ...],
  "sections": [
    {
      "sectionIndex": 1,
      "sectionTitle": "章节标题",
      "content": "章节内容(markdown)",
      "image": {
        "alt": "图片alt",
        "url": "图片URL",
        "caption": "图片说明"
      }
    }
  ],
  "authorBio": {
    "name": "Janson",
    "title": "CEO, ASG Dropshipping",
    "image": "100x100头像URL",
    "bio": "作者简介",
    "links": ["LinkedIn", "Twitter"]
  },
  "sources": [来源列表],
  "externalLinks": [外链列表],
  "internalLinks": [内链列表],
  "imageCount": 4,
  "externalLinkCount": 5,
  "boldKeywordCount": 7
}
```

### 10.2 WordPress发布准备
```
1. 复制markdown内容
2. 上传图片到媒体库
3. 替换图片URL
4. 设置特色图片
5. 添加分类和标签
6. 设置SEO插件(Yoast/Rank Math)
7. 预览检查
8. 发布
```

---

## 🎯 关键成功因素

### 1. SERP深度分析
- 10页搜索确保全面了解竞争
- AI分析提取关键洞察
- 数据驱动决策

### 2. GEO优化
- 结构化内容便于AI引用
- 权威性信号建立
- 引用友好的格式

### 3. 用户体验
- 清晰的结构
- 丰富的视觉元素
- 可操作的建议

### 4. 技术SEO
- 关键词自然分布
- 内外链平衡
- 图片优化

### 5. 品牌建设
- ASG案例展示
- 作者权威性
- 专业形象

---

## 📊 效果预期

### SEO效果
- 目标关键词排名: Top 10 (3-6个月)
- 长尾关键词排名: Top 5 (1-3个月)
- 有机流量增长: 50-100% (6个月)

### GEO效果
- AI搜索引擎引用率: 30-50%
- ChatGPT/Claude引用: 高概率
- 品牌曝光度: 显著提升

### 用户参与
- 平均停留时间: 4-6分钟
- 跳出率: <40%
- 社交分享: 提升20-30%

---

## 🔄 持续优化

### 监控指标
- Google Search Console数据
- 排名变化追踪
- 用户行为分析
- AI引用监控

### 优化策略
- 定期更新数据
- 添加新案例
- 优化表现不佳的章节
- A/B测试不同元素

---

**流程版本**: v2.0
**最后更新**: 2026-03-08
**适用平台**: ASG Dropshipping 文章生成系统
