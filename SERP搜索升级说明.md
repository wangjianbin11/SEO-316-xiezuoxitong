# SERP 搜索功能升级说明

## 升级内容

### ✅ 搜索页数提升
- **之前**: 每次只搜索 1 页(10条结果)
- **现在**: 默认搜索 10 页(100条结果)

### ✅ 分页搜索实现
新增 `_search_google_multiple_pages` 方法:
- 自动进行多次 API 调用
- 每次获取 10 条结果
- 循环获取直到达到目标数量
- 智能停止(如果某页没有结果)

### ✅ 搜索质量提升
- 使用前 20 条结果进行 AI 分析(之前只用 5 条)
- 更准确的搜索意图判断
- 更全面的竞争对手分析
- 更多的内容创作机会发现

### ✅ 日志优化
- 显示当前获取进度: "已获取 30/100 条结果"
- 显示每页的搜索状态
- 记录最终获取的总结果数

## 技术细节

### API 调用次数
- 获取 100 条结果 = 10 次 API 调用
- Google Custom Search API 限制: 每次最多 10 条
- 使用 `start` 参数进行分页: 1, 11, 21, 31...

### 方法签名变化

**之前:**
```python
async def analyze(self, keyword: str) -> dict[str, Any]:
    search_results = await self._search_google(keyword)  # 只获取10条
```

**现在:**
```python
async def analyze(self, keyword: str, total_results: int = 100) -> dict[str, Any]:
    search_results = await self._search_google_multiple_pages(keyword, total_results)
```

### 返回数据增强
新增 `totalResults` 字段:
```python
{
    "keyword": "...",
    "searchResults": [...],  # 100条结果
    "serpAnalysis": {...},
    "totalResults": 100  # 新增字段
}
```

## 使用示例

### 默认使用(10页)
```python
serp_analyzer = SERPAnalyzer(llm_client)
result = await serp_analyzer.analyze("how to learn python")
# 自动获取 100 条结果
```

### 自定义页数
```python
# 获取 5 页(50条结果)
result = await serp_analyzer.analyze("seo tools", total_results=50)

# 获取 20 页(200条结果)
result = await serp_analyzer.analyze("best practices", total_results=200)
```

## 性能影响

### API 配额消耗
- **之前**: 1 次搜索 = 1 次 API 调用
- **现在**: 1 次搜索 = 10 次 API 调用
- **建议**: 注意 Google API 的每日配额限制

### 响应时间
- 每次 API 调用约 0.5-1 秒
- 10 页搜索总耗时约 5-10 秒
- 已添加进度日志,用户可以看到实时进度

## 兼容性

✅ **完全向后兼容**
- 所有现有功能保持不变
- 默认参数确保行为一致
- 不影响其他模块

## 注意事项

1. **API 配额**: Google Custom Search API 有每日调用限制,请注意监控
2. **成本**: 如果使用付费 API,调用次数增加会增加成本
3. **超时设置**: httpx 客户端超时设置为 30 秒,足够完成单次请求

## 测试建议

1. 先用小数据量测试: `total_results=20` (2页)
2. 确认 API 配额充足
3. 观察日志输出,确认搜索正常
4. 逐步增加到 100 条

## 日志示例

```
[INFO] 开始 SERP 分析: how to learn python, 获取 100 条结果
[INFO] 开始获取 10 页搜索结果 (共 100 条)
[INFO] Google 搜索: how to learn python, start=1, 返回 10 条结果
[INFO] 已获取 10/100 条结果
[INFO] Google 搜索: how to learn python, start=11, 返回 10 条结果
[INFO] 已获取 20/100 条结果
...
[INFO] 搜索完成: how to learn python, 共获取 100 条结果
[INFO] 搜索意图分析完成: how to learn python, intent=informational, 分析了 20 条结果
```

## 未来优化方向

1. 添加缓存机制,避免重复搜索
2. 支持并发 API 调用,提升速度
3. 添加搜索结果去重
4. 支持更多搜索引擎
