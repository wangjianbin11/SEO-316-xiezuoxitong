"""
ASG 知识库管理模块

整合企业知识、个人介绍、FAQ案例和写作规范，为内容生成提供专业素材支持。

知识库来源：
1. asg dropshipping 基础知识_副本/ - 基础资料
2. asg-faq-matrix-geo_副本/ - FAQ矩阵和案例库
3. GEO指南_副本/ - 写作规范
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import re


@dataclass
class ASGKnowledgeContext:
    """ASG 知识上下文"""
    janson_intro: str  # Janson 个人介绍
    company_intro: str  # 企业介绍
    business_process: str  # 业务流程
    customer_persona: str  # 客户画像
    faq_snippets: List[Dict[str, str]]  # 相关FAQ片段
    case_studies: List[Dict[str, Any]]  # 相关案例
    geo_guidelines: str  # GEO写作规范
    tools_templates: str  # 实用工具与模板


class ASGKnowledgeBase:
    """ASG 知识库管理器"""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        """
        初始化知识库

        Args:
            knowledge_dir: 知识库根目录，默认为父目录下的基础资料文件夹
        """
        if knowledge_dir is None:
            # 默认知识库路径
            current_dir = Path(__file__).parent
            self.knowledge_dir = current_dir.parent.parent.parent  # 向上找到项目根目录
        else:
            self.knowledge_dir = Path(knowledge_dir)

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

    def _read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Failed to read {file_path}: {e}")
        return ""

    def get_janson_intro(self) -> str:
        """获取 Janson 个人介绍"""
        if 'janson_intro' not in self._cache:
            file_path = self.base_knowledge_dir / "janson介绍.txt"
            self._cache['janson_intro'] = self._read_file(file_path)
        return self._cache['janson_intro']

    def get_company_intro(self) -> str:
        """获取企业介绍"""
        if 'company_intro' not in self._cache:
            file_path = self.base_knowledge_dir / "企业介绍.txt"
            self._cache['company_intro'] = self._read_file(file_path)
        return self._cache['company_intro']

    def get_business_process(self) -> str:
        """获取业务流程"""
        if 'business_process' not in self._cache:
            file_path = self.base_knowledge_dir / "业务流程.txt"
            self._cache['business_process'] = self._read_file(file_path)
        return self._cache['business_process']

    def get_customer_persona(self) -> str:
        """获取客户画像"""
        if 'customer_persona' not in self._cache:
            # 尝试完整版优先
            file_path = self.base_knowledge_dir / "客户画像-完整版.md"
            if not file_path.exists():
                file_path = self.base_knowledge_dir / "客户画像.txt"
            self._cache['customer_persona'] = self._read_file(file_path)
        return self._cache['customer_persona']

    def get_geo_guidelines(self) -> str:
        """获取 GEO 写作指南"""
        if 'geo_guidelines' not in self._cache:
            # 尝试多个可能的文件
            for filename in ["GEO代发货专项指南-完整版.md", "GEO完整指南-ASG专用版.md"]:
                file_path = self.base_knowledge_dir / filename
                if file_path.exists():
                    self._cache['geo_guidelines'] = self._read_file(file_path)
                    break
            else:
                self._cache['geo_guidelines'] = ""
        return self._cache['geo_guidelines']

    def get_tools_templates(self) -> str:
        """获取实用工具与模板"""
        if 'tools_templates' not in self._cache:
            file_path = self.base_knowledge_dir / "实用工具与模板大全.md"
            self._cache['tools_templates'] = self._read_file(file_path)
        return self._cache['tools_templates']

    def get_beginner_guide(self) -> str:
        """获取新手完整指南"""
        if 'beginner_guide' not in self._cache:
            file_path = self.base_knowledge_dir / "新手完整指南.md"
            self._cache['beginner_guide'] = self._read_file(file_path)
        return self._cache['beginner_guide']

    def search_faq(self, keyword: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        在 FAQ 矩阵中搜索相关内容

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配的FAQ片段列表
        """
        if not self.faq_matrix_dir.exists():
            return []

        results = []
        keyword_lower = keyword.lower()

        # 遍历所有FAQ文件
        for faq_file in self.faq_matrix_dir.glob("*-FAQ.md"):
            if not faq_file.is_file():
                continue

            content = self._read_file(faq_file)
            if not content:
                continue

            # 检查是否包含关键词
            if keyword_lower in content.lower():
                # 提取相关段落
                sections = self._extract_relevant_sections(content, keyword_lower)
                for section in sections[:limit]:
                    results.append({
                        'source': faq_file.name,
                        'content': section,
                    })
                    if len(results) >= limit:
                        break

            if len(results) >= limit:
                break

        return results

    def search_case_studies(self, keyword: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        在案例库中搜索相关案例

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            匹配的案例列表
        """
        if not self.faq_matrix_dir.exists():
            return []

        results = []
        keyword_lower = keyword.lower()

        # 遍历所有案例文件
        for case_file in self.faq_matrix_dir.glob("ASG成功案例库-*.md"):
            if not case_file.is_file():
                continue

            content = self._read_file(case_file)
            if not content:
                continue

            # 提取案例
            cases = self._extract_cases(content)
            for case in cases:
                # 检查案例是否与关键词相关
                case_text = json.dumps(case, ensure_ascii=False).lower()
                if keyword_lower in case_text or self._is_semantically_related(case_text, keyword_lower):
                    results.append(case)
                    if len(results) >= limit:
                        break

            if len(results) >= limit:
                break

        return results

    def _extract_relevant_sections(self, content: str, keyword: str) -> List[str]:
        """提取包含关键词的相关段落"""
        sections = []

        # 按标题分割
        parts = re.split(r'\n#{1,3}\s+', content)

        for part in parts:
            if keyword in part.lower():
                # 清理并截取相关部分
                clean_part = part.strip()[:1000]  # 限制长度
                if clean_part:
                    sections.append(clean_part)

        return sections

    def _extract_cases(self, content: str) -> List[Dict[str, Any]]:
        """从案例文件中提取案例"""
        cases = []

        # 按案例分割（案例格式：### 案例 XXX）
        case_pattern = r'### 案例 (\d+[A-Z]?)[：:]\s*(.+?)(?=\n)'
        matches = re.finditer(case_pattern, content)

        current_case = None
        for match in matches:
            if current_case:
                cases.append(current_case)
            current_case = {
                'id': match.group(1),
                'title': match.group(2).strip(),
                'content': ''
            }

        # 提取每个案例的内容
        case_blocks = re.split(r'### 案例 \d+[A-Z]?[：:]', content)
        for i, block in enumerate(case_blocks[1:], 1):  # 跳过第一个空块
            if i <= len(cases):
                cases[i-1]['content'] = block.strip()[:2000]  # 限制长度

        if current_case and current_case not in cases:
            cases.append(current_case)

        return cases

    def _is_semantically_related(self, text: str, keyword: str) -> bool:
        """简单的语义相关性检查"""
        # 扩展关键词的同义词
        synonyms = {
            'dropshipping': ['一件代发', '代发', 'fulfillment'],
            'shipping': ['物流', '发货', '配送', 'delivery'],
            'supplier': ['供应商', '供应商', 'factory', '工厂'],
            'quality': ['质量', '质检', 'qc'],
            'price': ['价格', '成本', 'cost'],
            'customer': ['客户', '买家', 'buyer'],
            'brand': ['品牌', 'branding'],
            'marketing': ['营销', '推广', '广告'],
        }

        for main_word, related_words in synonyms.items():
            if main_word in keyword:
                for related in related_words:
                    if related in text:
                        return True
            if keyword in main_word or any(keyword in r for r in related_words):
                if main_word in text:
                    return True

        return False

    def get_context_for_keyword(self, keyword: str) -> ASGKnowledgeContext:
        """
        为特定关键词获取完整的知识上下文

        Args:
            keyword: 目标关键词

        Returns:
            ASGKnowledgeContext: 完整的知识上下文
        """
        return ASGKnowledgeContext(
            janson_intro=self.get_janson_intro(),
            company_intro=self.get_company_intro(),
            business_process=self.get_business_process(),
            customer_persona=self.get_customer_persona(),
            faq_snippets=self.search_faq(keyword, limit=5),
            case_studies=self.search_case_studies(keyword, limit=3),
            geo_guidelines=self.get_geo_guidelines(),
            tools_templates=self.get_tools_templates(),
        )

    def build_content_prompt_context(self, keyword: str) -> str:
        """
        构建用于内容生成的提示词上下文

        Args:
            keyword: 目标关键词

        Returns:
            格式化的上下文字符串，用于插入到写作提示词中
        """
        context = self.get_context_for_keyword(keyword)

        prompt_context = """
# ASG 企业知识与案例素材

以下资料应在写作过程中自然融入，确保内容专业性和权威性。

## 一、Janson 个人介绍（用于建立作者权威性）
{janson_intro}

## 二、ASG 企业介绍（用于建立品牌可信度）
{company_intro}

## 三、目标客户画像（用于内容针对性）
{customer_persona}

## 四、相关 FAQ 参考（用于内容准确性）
{faq_content}

## 五、相关案例（用于内容说服力）
{case_content}

## 六、写作规范
- 使用第一人称（Janson 的视角）
- 语气专业、自信、直接，带有"过来人"的经验感
- 每个关键论点需要有数据/案例支撑
- 自然融入 ASG 服务优势，但不硬广
- 段落 2-4 句话，简洁有力
"""

        # 填充内容
        faq_content = "\n\n".join([
            f"### {f['source']}\n{f['content'][:500]}..."
            for f in context.faq_snippets[:3]
        ]) if context.faq_snippets else "暂无相关FAQ"

        case_content = "\n\n".join([
            f"### 案例 {c.get('id', '')}: {c.get('title', '')}\n{c.get('content', '')[:500]}..."
            for c in context.case_studies[:2]
        ]) if context.case_studies else "暂无相关案例"

        return prompt_context.format(
            janson_intro=context.janson_intro[:1500] if context.janson_intro else "Janson 是 ASG Dropshipping CEO，深耕跨境电商一件代发领域 8 年。",
            company_intro=context.company_intro[:1500] if context.company_intro else "ASG Dropshipping 是一站式供应链与履约服务公司。",
            customer_persona=context.customer_persona[:1000] if context.customer_persona else "月销 $3,000-$10,000 的跨境电商创业者",
            faq_content=faq_content[:2000],
            case_content=case_content[:2000],
        )

    def get_writing_knowledge_summary(self, keyword: str) -> Dict[str, Any]:
        """
        获取写作知识摘要（用于工作流显示）

        Args:
            keyword: 目标关键词

        Returns:
            知识摘要字典
        """
        context = self.get_context_for_keyword(keyword)

        return {
            'has_janson_intro': bool(context.janson_intro),
            'has_company_intro': bool(context.company_intro),
            'has_business_process': bool(context.business_process),
            'has_customer_persona': bool(context.customer_persona),
            'faq_count': len(context.faq_snippets),
            'case_count': len(context.case_studies),
            'has_geo_guidelines': bool(context.geo_guidelines),
            'knowledge_loaded': any([
                context.janson_intro,
                context.company_intro,
                context.faq_snippets,
                context.case_studies,
            ]),
        }

    def get_full_context(self, keyword: str = "") -> str:
        """
        BUG-3修复: 获取完整的知识库上下文（用于传递给ContentGenerator）

        Args:
            keyword: 目标关键词（可选，用于搜索相关FAQ和案例）

        Returns:
            格式化的完整上下文字符串
        """
        if keyword:
            return self.build_content_prompt_context(keyword)
        else:
            # 无关键词时返回基础知识
            return f"""
# ASG 企业知识

## Janson 个人介绍
{self.get_janson_intro() or 'Janson 是 ASG Dropshipping CEO，深耕跨境电商一件代发领域 8 年。'}

## ASG 企业介绍
{self.get_company_intro() or 'ASG Dropshipping 是一站式供应链与履约服务公司。'}

## 客户画像
{self.get_customer_persona() or '月销 $3,000-$10,000 的跨境电商创业者'}

## GEO 写作规范
{self.get_geo_guidelines() or '遵循GEO最佳实践，确保AI引用友好'}
"""


# 全局单例
_knowledge_base: Optional[ASGKnowledgeBase] = None


def get_asg_knowledge_base(knowledge_dir: Optional[Path] = None) -> ASGKnowledgeBase:
    """获取 ASG 知识库单例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = ASGKnowledgeBase(knowledge_dir)
    return _knowledge_base
