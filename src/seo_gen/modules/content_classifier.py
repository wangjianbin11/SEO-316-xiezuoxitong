"""
ASG 内容类型分类器

根据关键词/标题智能判断适合的文章类型:
- Pillar Post (顶梁柱型)
- Response Post (回答型)
- Share Post (分享型)
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ArticleType(Enum):
    """文章类型枚举"""
    PILLAR = "pillar"      # 顶梁柱型
    RESPONSE = "response"  # 回答型
    SHARE = "share"        # 分享型


@dataclass
class ClassificationResult:
    """分类结果"""
    article_type: ArticleType
    confidence: float
    reasons: List[str]
    search_intent: str
    suggested_structure: str
    recommended_word_count: str
    related_keywords: List[str]


# ==================== 关键词模式定义 ====================

# 顶梁柱型关键词模式
PILLAR_PATTERNS = [
    r'\b(complete|comprehensive|ultimate|full|all-in-one|everything\s+about)\b',
    r'\bguide\b(?!\s+to\s+\d+)',  # guide 但不是 "guide to 10..."
    r'\b(handbook|bible|encyclopedia|roadmap)\b',
    r'\b(mastery|mastering)\b',
    r'\bfrom\s+a\s+to\s+z\b',
    r'\b101\b|\bintroductory\b',
    r'\bdeep\s+dive\b',
    r'\b(definitive|exhaustive)\b',
]

# 回答型关键词模式
RESPONSE_PATTERNS = [
    r'^how\s+to\b',
    r'^what\s+(is|are)\b',
    r'^why\s+(do|does|is|are|should)\b',
    r'^can\s+(i|you|we)\b',
    r'^does\s+\w+\b',
    r'^is\s+\w+\b',
    r'^when\s+(should|do|to)\b',
    r'^where\s+(to|can|should)\b',
    r'^which\s+\w+\s+(is|are)\b',
    r'\bhow\s+do\s+(i|you)\b',
    r'\bwhy\s+\w+\s+(matters|important|works)\b',
    r'\?\s*$',  # 以问号结尾
    r'\b(fix|solve|resolve|troubleshoot)\b',
    r'\b(problem|issue|error|solution)\b',
]

# 分享型关键词模式
SHARE_PATTERNS = [
    r'^\d+\s+',  # 以数字开头 (如 "10 best...", "7 ways...")
    r'\b(top\s+\d+|best\s+\d+|\d+\s+best)\b',
    r'\b(top\s+\d+\s+\w+)\b',
    r'\b(best|top|greatest|leading)\s+\w+\s+(in|of|for)\b',
    r'\bvs\b|\bversus\b',
    r'\bcomparison\b|\bcompared\b',
    r'\b(list|lists|ranking|rankings)\b',
    r'\b(steps|strategies|tactics|tips|tricks|hacks)\b',
    r'\b(checklist|cheat\s+sheet)\b',
    r'\balternatives?\b',
    r'\b(types|kinds|varieties)\s+of\b',
    r'\bexamples?\s+of\b',
]

# 优先级权重 (某些模式更重要)
PRIORITY_WEIGHTS = {
    # 回答型高优先级模式
    'response_high': [
        r'^how\s+to\s+\w+\s+\w+',  # "how to [verb] [noun]"
        r'^what\s+is\s+\w+',
        r'^why\s+should\s+i',
    ],
    # 分享型高优先级模式
    'share_high': [
        r'^\d+\s+(best|top|ways|tips|strategies)',
        r'\bvs\b.*\bwhich\s+is\s+better\b',
    ],
    # 顶梁柱型高优先级模式
    'pillar_high': [
        r'\b(complete|ultimate|comprehensive)\s+guide\b',
        r'\beverything\s+about\b',
    ],
}


class ContentClassifier:
    """内容类型分类器"""

    def __init__(self):
        """初始化分类器"""
        # 编译正则表达式以提高性能
        self.pillar_patterns = [re.compile(p, re.IGNORECASE) for p in PILLAR_PATTERNS]
        self.response_patterns = [re.compile(p, re.IGNORECASE) for p in RESPONSE_PATTERNS]
        self.share_patterns = [re.compile(p, re.IGNORECASE) for p in SHARE_PATTERNS]
        self.priority_patterns = {
            'response_high': [re.compile(p, re.IGNORECASE) for p in PRIORITY_WEIGHTS['response_high']],
            'share_high': [re.compile(p, re.IGNORECASE) for p in PRIORITY_WEIGHTS['share_high']],
            'pillar_high': [re.compile(p, re.IGNORECASE) for p in PRIORITY_WEIGHTS['pillar_high']],
        }

    def classify(self, keyword: str, title: Optional[str] = None) -> ClassificationResult:
        """
        分类关键词/标题

        Args:
            keyword: 关键词
            title: 可选的标题（用于更准确的分类）

        Returns:
            ClassificationResult: 分类结果
        """
        # 合并关键词和标题进行分析
        text = f"{keyword} {title or ''}".strip().lower()

        # 计算各类型得分
        scores = {
            ArticleType.PILLAR: self._calculate_pillar_score(text),
            ArticleType.RESPONSE: self._calculate_response_score(text),
            ArticleType.SHARE: self._calculate_share_score(text),
        }

        # 检查优先级模式
        priority_bonus = self._check_priority_patterns(text)
        for article_type, bonus in priority_bonus.items():
            scores[article_type] += bonus

        # 选择最高得分的类型
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type] / (sum(scores.values()) + 0.001)

        # 获取判断依据
        reasons = self._get_reasons(text, best_type)

        # 分析搜索意图
        search_intent = self._analyze_search_intent(text, best_type)

        # 获取建议结构
        structure = self._get_suggested_structure(best_type)

        # 获取推荐字数
        word_count = self._get_recommended_word_count(best_type)

        # 生成相关关键词
        related_keywords = self._generate_related_keywords(keyword, best_type)

        return ClassificationResult(
            article_type=best_type,
            confidence=min(confidence, 1.0),
            reasons=reasons,
            search_intent=search_intent,
            suggested_structure=structure,
            recommended_word_count=word_count,
            related_keywords=related_keywords,
        )

    def _calculate_pillar_score(self, text: str) -> float:
        """计算顶梁柱型得分"""
        score = 0.0
        for pattern in self.pillar_patterns:
            if pattern.search(text):
                score += 1.0
        return score

    def _calculate_response_score(self, text: str) -> float:
        """计算回答型得分"""
        score = 0.0
        for pattern in self.response_patterns:
            if pattern.search(text):
                score += 1.0
        return score

    def _calculate_share_score(self, text: str) -> float:
        """计算分享型得分"""
        score = 0.0
        for pattern in self.share_patterns:
            if pattern.search(text):
                score += 1.0
        return score

    def _check_priority_patterns(self, text: str) -> Dict[ArticleType, float]:
        """检查优先级模式并返回加分"""
        bonus = {ArticleType.PILLAR: 0.0, ArticleType.RESPONSE: 0.0, ArticleType.SHARE: 0.0}

        for pattern in self.priority_patterns['response_high']:
            if pattern.search(text):
                bonus[ArticleType.RESPONSE] += 2.0

        for pattern in self.priority_patterns['share_high']:
            if pattern.search(text):
                bonus[ArticleType.SHARE] += 2.0

        for pattern in self.priority_patterns['pillar_high']:
            if pattern.search(text):
                bonus[ArticleType.PILLAR] += 2.0

        return bonus

    def _get_reasons(self, text: str, article_type: ArticleType) -> List[str]:
        """获取判断依据"""
        reasons = []

        if article_type == ArticleType.PILLAR:
            if re.search(r'\b(complete|comprehensive|ultimate)\b', text, re.I):
                reasons.append("包含综合性关键词 (complete/comprehensive/ultimate)")
            if re.search(r'\bguide\b', text, re.I):
                reasons.append("包含 'guide' 关键词")
            if re.search(r'\beverything\s+about\b', text, re.I):
                reasons.append("包含 'everything about' 短语")
            if not reasons:
                reasons.append("主题广泛，适合深度全面覆盖")

        elif article_type == ArticleType.RESPONSE:
            if re.search(r'^how\s+to\b', text, re.I):
                reasons.append("以 'how to' 开头的具体问题")
            if re.search(r'^(what|why|when|where|which|can|does|is)\b', text, re.I):
                reasons.append("以疑问词开头的问题")
            if re.search(r'\?\s*$', text):
                reasons.append("以问号结尾")
            if re.search(r'\b(fix|solve|problem|solution)\b', text, re.I):
                reasons.append("包含问题解决相关词汇")
            if not reasons:
                reasons.append("搜索意图为获取具体答案")

        elif article_type == ArticleType.SHARE:
            if re.search(r'^\d+\s+', text):
                reasons.append("以数字开头，适合列表格式")
            if re.search(r'\b(best|top)\b', text, re.I):
                reasons.append("包含排名/最佳相关词汇")
            if re.search(r'\bvs\b', text, re.I):
                reasons.append("包含对比关键词 'vs'")
            if re.search(r'\b(list|strategies|tips|steps)\b', text, re.I):
                reasons.append("包含列表/策略相关词汇")
            if not reasons:
                reasons.append("适合用列表/编号形式展示")

        return reasons if reasons else ["根据关键词模式匹配"]

    def _analyze_search_intent(self, text: str, article_type: ArticleType) -> str:
        """分析搜索意图"""
        if article_type == ArticleType.PILLAR:
            return "学习型意图 - 用户希望全面了解一个主题的各个方面"
        elif article_type == ArticleType.RESPONSE:
            return "信息型意图 - 用户有具体问题需要直接答案"
        elif article_type == ArticleType.SHARE:
            return "探索型意图 - 用户希望浏览选项、比较或学习多个技巧"
        return "通用信息搜索意图"

    def _get_suggested_structure(self, article_type: ArticleType) -> str:
        """获取建议的文章结构"""
        structures = {
            ArticleType.PILLAR: "H1 → 引言(50-70字) → 摘要答案(300字符) → 过渡 → 目录 → 3个H2深潜(各含3-5个H3) → 结论(50-70字) → FAQ",
            ArticleType.RESPONSE: "H1 → 引言(50-75字) → 核心答案(300字符) → 引导阅读 → H2深潜 → H3×2-3组 → 结论(50-75字) → FAQ",
            ArticleType.SHARE: "H1 → 引言(50字) → 快速回答(300字符) → H2编号列表(4-8个) → 结论(300字符) → FAQ",
        }
        return structures[article_type]

    def _get_recommended_word_count(self, article_type: ArticleType) -> str:
        """获取推荐字数"""
        word_counts = {
            ArticleType.PILLAR: "4000-6000 字",
            ArticleType.RESPONSE: "3000-4000 字",
            ArticleType.SHARE: "3000-4000 字",
        }
        return word_counts[article_type]

    def _generate_related_keywords(self, keyword: str, article_type: ArticleType) -> List[str]:
        """生成相关长尾关键词建议"""
        related = []

        if article_type == ArticleType.PILLAR:
            related = [
                f"{keyword} guide 2026",
                f"complete {keyword} tutorial",
                f"{keyword} for beginners",
                f"how to master {keyword}",
                f"{keyword} best practices",
            ]
        elif article_type == ArticleType.RESPONSE:
            related = [
                f"how to {keyword}",
                f"{keyword} step by step",
                f"{keyword} explained",
                f"{keyword} tips and tricks",
                f"common {keyword} mistakes",
            ]
        elif article_type == ArticleType.SHARE:
            related = [
                f"best {keyword} 2026",
                f"top 10 {keyword}",
                f"{keyword} vs alternatives",
                f"{keyword} comparison",
                f"{keyword} checklist",
            ]

        return related[:5]

    def get_template_name(self, article_type: ArticleType) -> str:
        """获取对应的模板文件名"""
        templates = {
            ArticleType.PILLAR: "ASG-顶梁柱SEO文章写作提示词-终极单体版.md",
            ArticleType.RESPONSE: "ASG-回答型SEO文章写作提示词-终极单体版.md",
            ArticleType.SHARE: "ASG-SEO文章写作提示词-分享型.md",
        }
        return templates[article_type]

    def get_prompt_type(self, article_type: ArticleType) -> str:
        """获取用于工作流的类型标识"""
        types = {
            ArticleType.PILLAR: "pillar",
            ArticleType.RESPONSE: "qa",
            ArticleType.SHARE: "share",
        }
        return types[article_type]


# 全局单例
_classifier: Optional[ContentClassifier] = None


def get_content_classifier() -> ContentClassifier:
    """获取内容分类器单例"""
    global _classifier
    if _classifier is None:
        _classifier = ContentClassifier()
    return _classifier


def classify_keyword(keyword: str, title: Optional[str] = None) -> ClassificationResult:
    """
    快捷函数：分类关键词

    Args:
        keyword: 关键词
        title: 可选的标题

    Returns:
        ClassificationResult: 分类结果
    """
    return get_content_classifier().classify(keyword, title)


# ==================== CLI 测试 ====================

if __name__ == "__main__":
    import sys

    classifier = ContentClassifier()

    # 测试关键词
    test_keywords = [
        "how to find a reliable dropshipping agent",
        "10 best dropshipping suppliers 2026",
        "US dropshipping supplier selection guide",
        "what is dropshipping fulfillment",
        "AliExpress vs CJ Dropshipping which is better",
        "complete guide to dropshipping automation",
        "why use a dropshipping agent",
        "dropshipping tips for beginners",
    ]

    if len(sys.argv) > 1:
        test_keywords = [" ".join(sys.argv[1:])]

    print("=" * 60)
    print("ASG Content Type Classifier")
    print("=" * 60)

    for kw in test_keywords:
        result = classifier.classify(kw)

        print(f"\n关键词: {kw}")
        print(f"推荐类型: {result.article_type.value.upper()}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"判断依据:")
        for reason in result.reasons:
            print(f"  - {reason}")
        print(f"搜索意图: {result.search_intent}")
        print(f"推荐字数: {result.recommended_word_count}")
        print(f"对应模板: {classifier.get_template_name(result.article_type)}")
        print("-" * 40)
