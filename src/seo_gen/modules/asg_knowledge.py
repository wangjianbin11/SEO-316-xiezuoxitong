"""
ASG 知识库管理模块

整合企业知识、个人介绍、FAQ案例和写作规范，为内容生成提供专业素材支持。

知识库来源（ASG-KB-FULL）：
  00-企业DNA/          → 企业介绍、创始人、使命愿景、核心竞争力
  01-销售获客/          → 客户画像、获客系统、话术库
  01-GEO市场分析/       → 区域市场深度分析
  02-供应链与服务/      → 物流、QC、订单处理、付款
  03-品牌与营销/        → SEO、内容策略、社交媒体
  09-客户案例库/        → 成功案例
  ip知识库/             → 行业知识、案例库、实战工具包
  10-竞品情报库/        → 竞品分析
  11-行业洞察/          → 行业趋势
  07-模板库/            → 各类模板
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
    competitor_intel: str  # 竞品情报
    industry_insights: str  # 行业洞察
    supply_chain_knowledge: str  # 供应链知识
    marketing_knowledge: str  # 品牌与营销知识


class ASGKnowledgeBase:
    """ASG 知识库管理器"""

    def __init__(self, knowledge_dir: Optional[Path] = None):
        """
        初始化知识库

        Args:
            knowledge_dir: 知识库根目录，优先从环境变量 ASG_KNOWLEDGE_BASE_PATH 读取
        """
        if knowledge_dir is not None:
            self.knowledge_dir = Path(knowledge_dir)
        else:
            # 优先从环境变量读取（在.env里配置）
            env_path = os.getenv("ASG_KNOWLEDGE_BASE_PATH", "")

            if env_path and Path(env_path).exists():
                self.knowledge_dir = Path(env_path)
            else:
                # 尝试相对路径候选
                current_dir = Path(__file__).parent
                candidates = [
                    Path.home() / "Documents" / "ASG-知识库" / "ASG-KB-FULL",
                    current_dir.parent.parent.parent.parent / "ASG-KB-FULL",
                    current_dir.parent.parent.parent.parent / "ASG知识库" / "ASG-KB-FULL",
                ]
                found = next(
                    (p for p in candidates if p.exists() and (p / "00-企业DNA").exists()),
                    None
                )
                if found:
                    self.knowledge_dir = found
                else:
                    # 找不到时明确报错，不要用占位符！
                    raise FileNotFoundError(
                        f"[ASGKnowledge] 知识库未找到！\n"
                        f"请在 .env 文件里设置：\n"
                        f"ASG_KNOWLEDGE_BASE_PATH=/你的实际路径/ASG-KB-FULL\n"
                        f"已尝试的路径：{candidates}"
                    )

        from loguru import logger as _logger
        _logger.info(f"[ASGKnowledge] 知识库路径确认: {self.knowledge_dir}")

        # 验证核心目录存在
        if not (self.knowledge_dir / "00-企业DNA").exists():
            _logger.warning(f"[ASGKnowledge] 警告：00-企业DNA目录不存在，可能影响文章质量")

        # ==================== 新版路径映射（ASG-KB-FULL） ====================
        self.dir_enterprise_dna = self.knowledge_dir / "00-企业DNA"
        self.dir_sales = self.knowledge_dir / "01-销售获客"
        self.dir_geo_market = self.knowledge_dir / "01-GEO市场分析"
        self.dir_supply_chain = self.knowledge_dir / "02-供应链与服务"
        self.dir_marketing = self.knowledge_dir / "03-品牌与营销"
        self.dir_team = self.knowledge_dir / "04-团队管理"
        self.dir_strategy = self.knowledge_dir / "05-战略复盘"
        self.dir_ai_agent = self.knowledge_dir / "06-AI-Agent"
        self.dir_templates = self.knowledge_dir / "07-模板库"
        self.dir_case_studies = self.knowledge_dir / "09-客户案例库"
        self.dir_case_faq = self.knowledge_dir / "09-客户案例库-F&Q"
        self.dir_competitor = self.knowledge_dir / "10-竞品情报库"
        self.dir_industry = self.knowledge_dir / "11-行业洞察"
        self.dir_ip_kb = self.knowledge_dir / "ip知识库"

        # 向后兼容：旧代码引用的属性
        self.base_knowledge_dir = self.dir_enterprise_dna
        self.faq_matrix_dir = self.dir_case_faq if self.dir_case_faq.exists() else self.dir_case_studies
        self.geo_guide_dir = self.dir_geo_market

        # 路径存在性检查
        from loguru import logger as _logger
        for _attr, _path in [
            ("00-企业DNA", self.dir_enterprise_dna),
            ("01-销售获客", self.dir_sales),
            ("01-GEO市场分析", self.dir_geo_market),
            ("02-供应链与服务", self.dir_supply_chain),
            ("09-客户案例库", self.dir_case_studies),
            ("ip知识库", self.dir_ip_kb),
        ]:
            if not _path.exists():
                _logger.warning(f"[ASGKnowledge] 路径不存在: {_attr} = {_path}")

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
        """获取 Janson 个人介绍 - 不返回占位符，缺失时报错"""
        if 'janson_intro' not in self._cache:
            # 按优先级尝试多个文件名
            possible_files = [
                "Janson创始人介绍.md",
                "janson_intro.md",
                "janson介绍.txt",
                "创始人介绍.md",
            ]
            content = ""
            loaded_file = None
            for filename in possible_files:
                file_path = self.dir_enterprise_dna / filename
                if file_path.exists():
                    content = self._read_file(file_path)
                    if content:
                        loaded_file = filename
                        break

            from loguru import logger as _l
            if content:
                _l.info(f"[ASGKnowledge] ✓ Janson介绍已加载: {loaded_file} ({len(content)}字符)")
            else:
                _l.error(
                    f"[ASGKnowledge] ✗ Janson介绍文件未找到！"
                    f"请在 {self.dir_enterprise_dna} 目录下创建以下任一文件：{possible_files}"
                )
                # 不返回占位符，返回空字符串，让调用方知道数据缺失
                content = ""

            self._cache['janson_intro'] = content
        return self._cache['janson_intro']

    def get_company_intro(self) -> str:
        """获取企业介绍 - 不返回占位符"""
        if 'company_intro' not in self._cache:
            file_path = self.dir_enterprise_dna / "公司基本信息.md"
            if not file_path.exists():
                file_path = self.dir_enterprise_dna / "company_intro.md"
            if not file_path.exists():
                file_path = self.dir_enterprise_dna / "企业介绍.txt"
            content = self._read_file(file_path)

            from loguru import logger as _l
            if not content:
                _l.error(f"[ASGKnowledge] ✗ 企业介绍文件未找到！路径: {self.dir_enterprise_dna}")
                content = ""  # 不返回占位符
            else:
                _l.info(f"[ASGKnowledge] ✓ 企业介绍已加载 ({len(content)}字符)")

            self._cache['company_intro'] = content
        return self._cache['company_intro']

    def get_business_process(self) -> str:
        """获取业务流程"""
        if 'business_process' not in self._cache:
            # 从供应链目录获取
            file_path = self.dir_supply_chain / "订单处理" / "订单处理SOP.md"
            if not file_path.exists():
                file_path = self.dir_enterprise_dna / "核心服务菜单.md"
            self._cache['business_process'] = self._read_file(file_path)
        return self._cache['business_process']

    def get_customer_persona(self) -> str:
        """获取客户画像"""
        if 'customer_persona' not in self._cache:
            # 从销售获客/客户画像目录聚合
            persona_dir = self.dir_sales / "客户画像"
            if persona_dir.exists():
                parts = []
                for f in sorted(persona_dir.glob("画像*.md")):
                    parts.append(self._read_file(f))
                self._cache['customer_persona'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['customer_persona'] = ""
        return self._cache['customer_persona']

    def get_core_competency(self) -> str:
        """获取核心竞争力"""
        if 'core_competency' not in self._cache:
            file_path = self.dir_enterprise_dna / "核心竞争力-Why-ASG.md"
            self._cache['core_competency'] = self._read_file(file_path)
        return self._cache['core_competency']

    def get_geo_guidelines(self) -> str:
        """获取 GEO 写作指南（从 01-GEO市场分析 聚合）"""
        if 'geo_guidelines' not in self._cache:
            if self.dir_geo_market.exists():
                parts = []
                for f in sorted(self.dir_geo_market.glob("*.md")):
                    parts.append(self._read_file(f))
                self._cache['geo_guidelines'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['geo_guidelines'] = ""
        return self._cache['geo_guidelines']

    def get_tools_templates(self) -> str:
        """获取实用工具与模板（从 07-模板库 聚合）"""
        if 'tools_templates' not in self._cache:
            if self.dir_templates.exists():
                parts = []
                for f in sorted(self.dir_templates.glob("*.md")):
                    parts.append(self._read_file(f))
                self._cache['tools_templates'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['tools_templates'] = ""
        return self._cache['tools_templates']

    def get_competitor_intel(self) -> str:
        """获取竞品情报"""
        if 'competitor_intel' not in self._cache:
            if self.dir_competitor.exists():
                parts = []
                for f in sorted(self.dir_competitor.glob("*.md")):
                    if "MOC" not in f.name:
                        parts.append(self._read_file(f))
                self._cache['competitor_intel'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['competitor_intel'] = ""
        return self._cache['competitor_intel']

    def get_supply_chain_knowledge(self) -> str:
        """获取供应链知识"""
        if 'supply_chain' not in self._cache:
            if self.dir_supply_chain.exists():
                parts = []
                for f in sorted(self.dir_supply_chain.rglob("*.md")):
                    if "MOC" not in f.name:
                        parts.append(self._read_file(f))
                self._cache['supply_chain'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['supply_chain'] = ""
        return self._cache['supply_chain']

    def get_marketing_knowledge(self) -> str:
        """获取品牌与营销知识"""
        if 'marketing' not in self._cache:
            if self.dir_marketing.exists():
                parts = []
                for f in sorted(self.dir_marketing.rglob("*.md")):
                    if "MOC" not in f.name:
                        parts.append(self._read_file(f))
                self._cache['marketing'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['marketing'] = ""
        return self._cache['marketing']

    def get_industry_insights(self) -> str:
        """获取行业洞察"""
        if 'industry' not in self._cache:
            if self.dir_industry.exists():
                parts = []
                for f in sorted(self.dir_industry.rglob("*.md")):
                    if "MOC" not in f.name:
                        parts.append(self._read_file(f))
                self._cache['industry'] = "\n\n---\n\n".join(parts) if parts else ""
            else:
                self._cache['industry'] = ""
        return self._cache['industry']

    def search_faq(self, keyword: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        在知识库中搜索与关键词相关的内容片段

        搜索范围：09-客户案例库-FQ、01-销售获客/话术库、ip知识库
        """
        results = []
        keyword_lower = keyword.lower()

        # 搜索目录列表（按优先级）
        search_dirs = [
            self.faq_matrix_dir,
            self.dir_sales / "话术库",
            self.dir_ip_kb,
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for faq_file in search_dir.rglob("*.md"):
                if not faq_file.is_file():
                    continue
                content = self._read_file(faq_file)
                if not content:
                    continue
                if keyword_lower in content.lower():
                    sections = self._extract_relevant_sections(content, keyword_lower)
                    for section in sections[:limit]:
                        results.append({
                            'source': faq_file.name,
                            'content': section,
                        })
                        if len(results) >= limit:
                            return results
        return results

    def search_case_studies(self, keyword: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        在案例库中搜索相关案例

        搜索范围：09-客户案例库、ip知识库/案例库
        """
        results = []
        keyword_lower = keyword.lower()

        # 搜索目录列表
        search_dirs = [
            self.dir_case_studies,
            self.dir_ip_kb / "02-行业知识库（专业垂类层）" / "06-案例库",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for case_file in search_dir.rglob("*.md"):
                if not case_file.is_file() or "README" in case_file.name:
                    continue
                content = self._read_file(case_file)
                if not content:
                    continue

                # 先尝试结构化提取
                cases = self._extract_cases(content)
                if cases:
                    for case in cases:
                        case_text = json.dumps(case, ensure_ascii=False).lower()
                        if keyword_lower in case_text or self._is_semantically_related(case_text, keyword_lower):
                            results.append(case)
                            if len(results) >= limit:
                                return results
                else:
                    # 非结构化：整个文件作为一个案例
                    if keyword_lower in content.lower() or self._is_semantically_related(content.lower(), keyword_lower):
                        results.append({
                            'id': case_file.stem,
                            'title': case_file.stem,
                            'content': content[:2000],
                        })
                        if len(results) >= limit:
                            return results

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
            competitor_intel=self.get_competitor_intel(),
            industry_insights=self.get_industry_insights(),
            supply_chain_knowledge=self.get_supply_chain_knowledge(),
            marketing_knowledge=self.get_marketing_knowledge(),
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

## 三、核心竞争力（用于差异化论述）
{core_competency}

## 四、目标客户画像（用于内容针对性）
{customer_persona}

## 五、供应链与服务知识（用于专业论述）
{supply_chain}

## 六、相关 FAQ 参考（用于内容准确性）
{faq_content}

## 七、相关案例（用于内容说服力）
{case_content}

## 八、竞品情报（用于对比分析）
{competitor_intel}

## 九、写作规范
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
            core_competency=self.get_core_competency()[:1000] if self.get_core_competency() else "ASG 提供一站式代发货解决方案",
            customer_persona=context.customer_persona[:1000] if context.customer_persona else "月销 $3,000-$10,000 的跨境电商创业者",
            supply_chain=context.supply_chain_knowledge[:1500] if context.supply_chain_knowledge else "专业供应链管理与质检服务",
            faq_content=faq_content[:2000],
            case_content=case_content[:2000],
            competitor_intel=context.competitor_intel[:1000] if context.competitor_intel else "暂无竞品情报",
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
            'has_competitor_intel': bool(context.competitor_intel),
            'has_supply_chain': bool(context.supply_chain_knowledge),
            'has_marketing': bool(context.marketing_knowledge),
            'has_industry_insights': bool(context.industry_insights),
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
