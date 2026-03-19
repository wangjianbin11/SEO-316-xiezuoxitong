"""
两阶段工作流编排器

编排高级内容生成工作流
"""

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from seo_gen.modules.content import ContentGenerator, get_content_generator
from seo_gen.modules.image import ImageGenerator
from seo_gen.modules.knowledge import KnowledgeBase, get_knowledge_base
from seo_gen.modules.llm import LLMClient
from seo_gen.modules.outline import OutlineGenerator, get_outline_generator
from seo_gen.modules.quality import QualityChecker as OldQualityChecker, get_quality_checker
from seo_gen.modules.quality_checker import QualityChecker  # 新版质量检查器
from seo_gen.modules.serp import SERPAnalyzer
from seo_gen.modules.structure import StructureAnalyzer, get_structure_analyzer
from seo_gen.modules.title import TitleGenerator, get_title_generator
from seo_gen.modules.wordpress import WordPressPublisher
from seo_gen.modules.content_classifier import ContentClassifier, ArticleType
from seo_gen.modules.asg_knowledge import ASGKnowledgeBase, get_asg_knowledge_base
from seo_gen.modules.checkpoint import CheckpointManager
from seo_gen.modules.competitor_scraper import CompetitorScraper
from seo_gen.modules.geo_optimizer import GEOOptimizer
from seo_gen.modules.schema_generator import SchemaGenerator
from seo_gen.modules.article_tracker import ArticleTracker
from seo_gen.modules.keyword_data import KeywordDataClient


class WorkflowOrchestrator:
    """两阶段工作流编排器"""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        progress_callback: Optional[Callable] = None,
    ):
        """初始化编排器"""
        self.llm_client = llm_client or LLMClient()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.progress_callback = progress_callback

        # 初始化各模块（传递 LLM 客户端）
        self.serp_analyzer = SERPAnalyzer(self.llm_client)
        self.title_generator = TitleGenerator(self.llm_client)
        self.structure_analyzer = StructureAnalyzer(self.llm_client)
        self.outline_generator = OutlineGenerator(self.llm_client)
        self.content_generator = ContentGenerator(self.llm_client, self.knowledge_base)
        self.quality_checker = QualityChecker(self.llm_client)  # 使用新版质量检查器
        self.content_classifier = ContentClassifier()
        self.asg_knowledge = get_asg_knowledge_base()

        # 初始化新模块
        self.competitor_scraper = CompetitorScraper()
        self.geo_optimizer = GEOOptimizer(self.llm_client)
        self.schema_generator = SchemaGenerator()
        self.article_tracker = ArticleTracker()
        self.keyword_data_client = KeywordDataClient()

    def _log(self, message: str, level: str = "info"):
        """通过回调函数输出日志"""
        if self.progress_callback:
            self.progress_callback("log", message)
        else:
            print(message)

    def _update_step(self, step_index: int, status: str, message: str, progress: float):
        """更新步骤进度"""
        if self.progress_callback:
            self.progress_callback("step", (step_index, status, message, progress))

    async def run_advanced_workflow(
        self,
        keyword: str,
        slug: Optional[str] = None,
        skip_images: bool = False,
        skip_wordpress: bool = False,
        output_dir: Optional[Path] = None,
        image_style: str = "modern",
        user_answers: Optional[Dict[str, str]] = None,
        custom_inputs: Optional[Dict[str, str]] = None,
        questions_data: Optional[Dict[str, Any]] = None,
        enhanced_keywords: Optional[List[str]] = None,
        confirmed_article_type: Optional[str] = None,  # 新增:用户确认的文章类型
        pre_confirmed_title: Optional[str] = None,  # Bug Fix 1: GUI预确认的标题
        resume: bool = True,  # 新增:是否从断点恢复
        use_checkpoint: bool = True,  # 新增:是否使用检查点
    ) -> Dict[str, Any]:
        """
        执行完整的高级工作流

        Args:
            keyword: 关键词
            slug: URL slug(可选,自动生成)
            skip_images: 跳过图片生成
            skip_wordpress: 跳过 WordPress 发布
            output_dir: 输出目录
            image_style: 图片风格 (modern, minimalist, professional, creative, tech, nature, elegant, playful)
            user_answers: 用户选择的答案 {"1": "A", "2": "B", "3": "A"}
            custom_inputs: 用户自定义输入内容 {"1": "custom value", "2": "..."}
            questions_data: 问题数据
            enhanced_keywords: 基于答案增强的搜索关键词列表
            confirmed_article_type: 用户确认的文章类型 (pillar/response/share),如果不提供则自动分类
            resume: 是否从断点恢复(默认True)
            use_checkpoint: 是否使用检查点功能(默认True)

        Returns:
            工作流结果
        """
        # 初始化检查点管理器
        checkpoint = None
        if use_checkpoint:
            base_dir = output_dir or Path("outputs")
            checkpoint = CheckpointManager(str(base_dir), keyword)

            if resume:
                summary = checkpoint.get_summary()
                if summary["completed_count"] > 0:
                    self._log(f"📌 发现检查点: 已完成 {summary['completed_count']}/{summary['total_stages']} 个阶段")
                    self._log(f"   将从阶段 {summary['resume_from']} 继续执行")
            else:
                # 不恢复,清除所有检查点
                checkpoint.clear()
                self._log("🔄 已清除所有检查点,将从头开始")

        result = {
            "keyword": keyword,
            "slug": slug or self._generate_slug(keyword),
            "success": False,
            "stages": {},
            "user_answers": user_answers or {},
            "custom_inputs": custom_inputs or {},
            "questions_data": questions_data or {},
        }

        # 使用增强的搜索关键词（如果有）
        search_keywords = enhanced_keywords or [keyword]

        try:
            # ==================== 阶段 -1: 检查是否已发布 ====================
            if self.article_tracker.is_published(keyword):
                self._log(f"⚠️  关键词 '{keyword}' 已发布过,跳过生成")
                existing = self.article_tracker.get_article(keyword)
                result["already_published"] = True
                result["existing_article"] = existing
                return result

            # ==================== 阶段0: 智能分类（新增）====================
            self._log("=" * 50)
            self._log("阶段0: 智能文章类型分类")
            self._log("=" * 50)

            # 先进行自动分类，获取推荐结果
            classification_result = self.content_classifier.classify(keyword)

            # 如果用户已确认类型，则使用用户选择的类型，否则使用自动分类结果
            if confirmed_article_type:
                # 将用户确认的类型字符串转换为枚举
                type_mapping = {
                    "pillar": ArticleType.PILLAR,
                    "response": ArticleType.RESPONSE,
                    "share": ArticleType.SHARE,
                }
                article_type = type_mapping.get(confirmed_article_type, classification_result.article_type)
                self._log(f"✓ 使用用户确认的类型: {article_type.value}")
                result["article_type_source"] = "user_confirmed"
            else:
                article_type = classification_result.article_type
                result["article_type_source"] = "auto_detected"

            result["article_type"] = article_type.value
            result["classification"] = {
                "type": article_type.value,
                "confidence": classification_result.confidence,
                "reasons": classification_result.reasons,
                "search_intent": classification_result.search_intent,
                "recommended_word_count": classification_result.recommended_word_count,
                "template_name": self.content_classifier.get_template_name(article_type),
            }

            # ==================== 新增：知识库加载 ====================
            self._log("=" * 50)
            self._log("阶段0.5: 智能分类 - 加载知识库")
            self._log("=" * 50)

            # 加载知识库
            context = self.asg_knowledge.get_context_for_keyword(keyword)
            result["knowledge_context"] = {
                "janson_intro": bool(context.janson_intro),
                "company_intro": bool(context.company_intro),
                "customer_persona": bool(context.customer_persona),
                "faq_count": len(context.faq_snippets),
                "case_count": len(context.case_studies),
                "geo_guidelines": bool(context.geo_guidelines),
            }
            self._log(f"✓ 知识库加载完成")
            self._log(f"    - Janson 介绍: {'已加载' if context.janson_intro else '暂无'}")
            self._log(f"    - 企业介绍: {'已加载' if context.company_intro else '暂无'}")
            self._log(f"    - 客户画像: {'已加载' if context.customer_persona else '暂无'}")
            self._log(f"    - 相关FAQ: {len(context.faq_snippets)} 个")
            self._log(f"    - 相关案例: {len(context.case_studies)} 个")
            self._log(f"    - GEO写作规范: {'已加载' if context.geo_guidelines else '暂无'}")

            # ==================== 阶段1: 标题生成 ====================
            self._log("")
            self._log("=" * 50)
            self._log("阶段1: 标题生成")
            self._log("=" * 50)

            # 1.1 Google 搜索调研关键词（使用增强关键词）
            self._update_step(1, "running", "分析 SERP - 搜索竞争对手", 0.08)

            # 如果有用户答案，记录到日志
            if user_answers:
                self._log(f"📋 用户策略:")
                for q_id, answer in user_answers.items():
                    questions = questions_data.get("questions", [])
                    q = next((qu for qu in questions if qu.get("id") == int(q_id)), None)
                    if q:
                        opt = next((o for o in q.get("options", []) if o.get("key") == answer), None)
                        if opt:
                            self._log(f"   Q{q_id}: {opt.get('label', '')}")

            # 搜索所有增强关键词
            all_serp_data = []
            for i, kw in enumerate(search_keywords[:3]):  # 最多搜索3个关键词
                self._log(f"[1/11] 正在搜索 ({i+1}/{min(len(search_keywords), 3)}): {kw[:50]}...")
                serp_data = await self.serp_analyzer.analyze(kw)
                all_serp_data.append(serp_data)

            # 合并SERP数据（使用主关键词的数据作为主数据源）
            serp_data = all_serp_data[0] if all_serp_data else {}
            serp_data["additional_searches"] = all_serp_data[1:] if len(all_serp_data) > 1 else []

            result["stages"]["serp_analysis"] = {"status": "completed", "data": serp_data}
            # BUG-1修复: primaryIntent 在 serpAnalysis 子层
            primary_intent = serp_data.get("serpAnalysis", {}).get("primaryIntent", "N/A")
            self._log(f"✓ 搜索意图: {primary_intent}")
            self._update_step(1, "completed", "分析 SERP - 完成", 0.12)

            # 1.1.3 关键词真实数据（DataForSEO）
            if self.keyword_data_client.enabled:
                try:
                    _kw_list = await self.keyword_data_client.get_keyword_metrics([keyword])
                    if _kw_list:
                        _m = _kw_list[0]
                        result["keyword_metrics"] = {
                            "monthly_volume": _m.monthly_volume,
                            "kd_score": _m.kd_score,
                            "cpc": _m.cpc,
                            "competition": _m.competition_level,
                            "source": _m.data_source,
                        }
                        self._log(f"✓ 关键词数据: 搜索量={_m.monthly_volume}/月 KD={_m.kd_score:.0f} CPC=${_m.cpc:.2f}")
                except Exception as _e:
                    self._log(f"  ℹ️  DataForSEO获取失败（不影响流程）: {_e}")
            else:
                self._log("  ℹ️  DataForSEO未配置，跳过关键词数据")

            # 1.1.5 竞争对手内容分析（新增）
            self._log(f"[1.5/11] 正在分析竞争对手内容...")
            # BUG-1修复: Google Custom Search API 返回的字段是 "searchResults" 不是 "results"，链接字段是 "link" 不是 "url"
            top_urls = [
                r.get("link") or r.get("url")
                for r in serp_data.get("searchResults", [])[:5]
                if r.get("link") or r.get("url")
            ]
            _paa_questions = serp_data.get("serpAnalysis", {}).get("paaQuestions", [])
            try:
                competitor_analysis = await self.competitor_scraper.analyze_competitors(
                    keyword=keyword,
                    urls=top_urls,
                    paa_questions=_paa_questions,
                    llm_client=self.llm_client
                )
                result["stages"]["competitor_analysis"] = {
                    "status": "completed",
                    "data": {
                        "target_word_count": competitor_analysis.target_word_count,
                        "dominant_format": competitor_analysis.dominant_format,
                        "uncovered_topics": competitor_analysis.uncovered_topics[:3],
                    }
                }
                self._log(f"✓ 竞争对手分析完成")
                self._log(f"  目标字数: {competitor_analysis.target_word_count}")
                self._log(f"  主流格式: {competitor_analysis.dominant_format}")
                self._log(f"  内容缺口: {len(competitor_analysis.uncovered_topics)} 个")
            except Exception as e:
                self._log(f"⚠️ 竞争对手分析失败: {e}")
                competitor_analysis = None
                result["stages"]["competitor_analysis"] = {
                    "status": "failed",
                    "error": str(e)
                }


            # 1.2 AI 生成候选标题 (Bug Fix 1: 如果GUI已预确认标题则跳过)
            if pre_confirmed_title:
                self._log(f"✓ 使用GUI预确认标题: {pre_confirmed_title}")
                final_title = pre_confirmed_title
                result["stages"]["title_generation"] = {
                    "status": "skipped_pre_confirmed",
                    "title": final_title
                }
                result["stages"]["title_selection"] = {
                    "status": "skipped_pre_confirmed",
                    "selected": {"title": final_title, "score": 100, "reasoning": "User confirmed in GUI"}
                }
                self._update_step(2, "completed", f"标题已确认: {final_title[:30]}...", 0.24)
            else:
                # 原有的标题生成逻辑
                self._update_step(2, "running", "生成候选标题", 0.16)
                self._log(f"[2/11] 正在生成标题...")
                title_candidates = await self.title_generator.generate_titles(
                    keyword=keyword,
                    serp_data=serp_data,
                    count=5,
                )
                result["stages"]["title_generation"] = {
                    "status": "completed",
                    "candidates": title_candidates
                }
                self._log(f"✓ 生成了 {len(title_candidates)} 个候选标题")
                self._update_step(2, "completed", "生成标题 - 完成", 0.20)

                # 1.3 选择最佳标题
                self._log(f"[3/11] 正在选择最佳标题...")
                best_title = await self.title_generator.select_best_title(
                    titles=title_candidates,
                    serp_data=serp_data,
                )
                result["stages"]["title_selection"] = {
                    "status": "completed",
                    "selected": best_title
                }
                final_title = best_title.get("title", keyword)
                self._log(f"✓ 选择标题: {final_title}")
                self._update_step(2, "completed", f"选择标题 - {final_title[:30]}...", 0.24)

            # ==================== 阶段2: 内容创作 ====================
            self._log("=" * 50)
            self._log("阶段2: 内容创作")
            self._log("=" * 50)

            # 2.1 Google 搜索调研标题
            self._log(f"[4/11] 正在搜索标题: {final_title[:30]}...")
            title_serp_data = await self.serp_analyzer.analyze(final_title)
            result["stages"]["title_serp_analysis"] = {"status": "completed"}
            self._log("✓ 标题搜索完成")
            self._update_step(3, "completed", "分析文章结构", 0.32)

            # 2.2 SERP 分析文章结构
            self._log(f"[5/9] 正在分析文章结构...")
            # BUG-1修复: 同样需要 searchResults 字段
            structure_analysis = await self.structure_analyzer.analyze_article_structure(
                search_results=title_serp_data.get("searchResults", []),
                keyword=keyword,
            )
            result["stages"]["structure_analysis"] = {
                "status": "completed",
                "data": structure_analysis
            }
            sections_count = len(structure_analysis.get('recommendedStructure', []))
            self._log(f"✓ 推荐结构: {sections_count} 个章节")
            self._update_step(3, "completed", "分析文章结构 - 完成", 0.40)

            # 2.3 AI 生成文章大纲
            self._update_step(4, "running", "生成文章大纲", 0.46)
            self._log(f"[5/11] 正在生成大纲...")
            outline = await self.outline_generator.generate_outline(
                keyword=keyword,
                title=final_title,
                structure_analysis=structure_analysis,
                serp_data=serp_data,
            )
            result["stages"]["outline_generation"] = {
                "status": "completed",
                "data": outline
            }
            outline_sections = len(outline.get('sections', []))
            self._log(f"✓ 大纲生成: {outline_sections} 个章节")
            self._update_step(4, "completed", "生成大纲 - 完成", 0.52)

            # 从大纲提取章节标题（传入文章生成，避免双重LLM工作）
            outline_section_titles = [
                s.get("sectionTitle", "") for s in outline.get("sections", [])
                if s.get("sectionTitle")
            ]
            if outline_section_titles:
                # 将大纲章节标题注入structure_analysis，供generate_article使用
                structure_analysis["outlineSectionTitles"] = outline_section_titles
                self._log(f"  大纲章节: {', '.join(outline_section_titles[:3])}...")

            # 2.4 AI 撰写文章内容（传递结构分析结果以支持动态章节数量）
            self._update_step(5, "running", "撰写文章内容", 0.58)
            self._log(f"[6/11] 正在撰写文章...")

            # 获取推荐的章节数量
            target_sections = structure_analysis.get("recommendedSectionCount", 7)
            self._log(f"  目标章节数: {target_sections} 个")

            # 记录使用的文章类型
            self._log(f"  文章类型: {article_type.value}")

            # 构建竞品上下文（之前爬了但没用，现在真正传入）
            competitor_context = ""
            if competitor_analysis and competitor_analysis.total_scraped > 0:
                competitor_context = f"""
COMPETITOR ANALYSIS INSIGHTS (从真实竞品文章提取，必须参考):
- 建议目标字数: {competitor_analysis.target_word_count} words (基于前3名平均×1.15)
- 竞品主流格式: {competitor_analysis.dominant_format}
- 竞品已覆盖的H2话题 (你必须覆盖这些，且做得更好): {', '.join(competitor_analysis.all_h2_topics[:10])}
- 竞品未覆盖的话题 (差异化机会，必须包含): {', '.join(competitor_analysis.uncovered_topics[:5])}
- 竞品弱点: {competitor_analysis.weakness_summary}
"""

            # BUG-3修复: 获取 ASG Knowledge Base 上下文
            asg_context = ""
            if self.asg_knowledge:
                try:
                    asg_context = self.asg_knowledge.get_full_context(keyword)
                    self._log(f"  ✓ ASG知识库上下文已加载 ({len(asg_context)} 字符)")
                except Exception as _e:
                    self._log(f"  ⚠ ASG知识库加载失败: {_e}")

            # BUG-2修复: serp_analysis 参数应该传递 serpAnalysis 子层而不是完整的 serp_data
            serp_analysis_for_content = serp_data.get("serpAnalysis", {})
            article = await self.content_generator.generate_article(
                keyword=keyword,
                slug=result["slug"],
                serp_analysis=serp_analysis_for_content,  # 修复: 只传递 serpAnalysis 子层
                structure_analysis=structure_analysis,  # 传递结构分析结果
                article_type=article_type.value,  # 传递文章类型
                competitor_context=competitor_context,
                asg_context=asg_context,  # BUG-3修复: 传递ASG知识库上下文
            )
            result["stages"]["content_generation"] = {
                "status": "completed",
                "data": article
            }

            # 统计实际生成的章节数和字数
            actual_sections = len(article.get('sections', []))
            word_count = len(article.get('content', ''))
            total_word_count = article.get('totalWordCount', word_count)

            self._log(f"✓ 文章撰写完成: {actual_sections} 章节, {total_word_count} 字")
            self._update_step(5, "completed", f"撰写内容 - {actual_sections}章节", 0.68)

            # 2.5 E-E-A-T 质量检测
            self._update_step(6, "running", "E-E-A-T 质量检测", 0.74)
            self._log(f"[7/11] 正在检测质量...")
            quality_result = await self.quality_checker.check_article_quality(
                article=article,
                keyword=keyword,
            )
            result["stages"]["quality_check"] = {
                "status": "completed",
                "data": quality_result
            }
            score = quality_result.get('overallScore', 0)
            grade = quality_result.get('overallGrade', 'N/A')
            self._log(f"✓ 质量检测: {score}/100 ({grade})")
            self._update_step(6, "completed", f"质量检测 - {score}/100", 0.85)

            # 2.5.4 禁用词重写（uncitable sentence检测，代码已写但从未调用）
            self._log(f"[7.2/11] 检测并重写AI无法引用的表达...")
            try:
                _full_content_for_rewrite = "\n".join(
                    s.get("content", "") for s in article.get("sections", [])
                )
                _rewritten = await self.geo_optimizer.rewrite_uncitable_sentences(
                    _full_content_for_rewrite, self.llm_client
                )
                if _rewritten != _full_content_for_rewrite:
                    # BUG-6修复: 将重写后的内容分配回sections
                    _rewritten_parts = _rewritten.split("\n\n")
                    for _i, _section in enumerate(article.get("sections", [])):
                        if _i < len(_rewritten_parts):
                            article["sections"][_i]["content"] = _rewritten_parts[_i]
                    self._log("  ✓ 检测到并重写了AI不可引用的表达")
                else:
                    self._log("  ✓ 未发现AI不可引用的表达")
            except Exception as _rewrite_err:
                self._log(f"  ⚠️ 禁用词检测跳过: {_rewrite_err}")

            # 2.5.5 GEO 优化（新增）
            self._log(f"[7.5/11] 正在进行 GEO 优化...")

            # 分析 GEO 得分
            geo_score_before = self.geo_optimizer.analyze_geo_score(article)
            self._log(f"  GEO 优化前得分: {geo_score_before.total_score}/100")

            # 注入直接答案块
            article = await self.geo_optimizer.inject_direct_answer_blocks(
                article, self.llm_client
            )

            # 优化 FAQ — 使用faqSection字段
            # QUALITY-2修复: 传入 llm_client 以激活真正的重写
            # Bug Fix 2: 添加 await 调用 async 方法
            if "faqSection" in article:
                faq_items = article["faqSection"].get("items", [])
                if faq_items:
                    article["faqSection"]["items"] = await self.geo_optimizer.optimize_faq_for_ai(
                        faq_items, self.llm_client
                    )

            # 重新分析得分
            geo_score_after = self.geo_optimizer.analyze_geo_score(article)
            self._log(f"  GEO 优化后得分: {geo_score_after.total_score}/100")
            self._log(f"  提升: +{geo_score_after.total_score - geo_score_before.total_score} 分")

            result["stages"]["geo_optimization"] = {
                "status": "completed",
                "score_before": geo_score_before.total_score,
                "score_after": geo_score_after.total_score,
                "improvement": geo_score_after.total_score - geo_score_before.total_score
            }


            # 2.6 AI内容检测和原创性检测 (联网检测)
            self._update_step(7, "running", "AI/原创检测 (联网)", 0.88)
            self._log(f"[9/11] 正在检测内容原创性 (使用 Google 搜索)...")

            from seo_gen.modules.detection import ContentDetector

            detector = ContentDetector(reference_dir=Path("outputs"), use_online_detection=True)
            content = article.get('content', '')
            detection_result = await detector.detect_all(content)

            result["stages"]["content_detection"] = {
                "status": "completed",
                "data": detection_result
            }

            ai_prob = detection_result['ai_detection']['ai_probability']
            orig_score = detection_result['plagiarism_detection']['originality_score']
            overall_det_score = detection_result['overall_score']
            method = detection_result['plagiarism_detection'].get('method', 'unknown')

            self._log(f"✓ AI检测: {ai_prob*100:.0f}% AI概率")
            self._log(f"✓ 原创度: {orig_score*100:.0f}% (检测方法: {method})")
            self._log(f"✓ 综合评分: {overall_det_score}/100")
            self._update_step(7, "completed", f"AI/原创检测 - {overall_det_score}/100", 0.92)

            # ==================== 生成配图 ====================
            images = {}
            section_media_ids = {}
            featured_media_id = None

            if not skip_images:
                self._update_step(8, "running", "生成配图", 0.94)
                self._log("=" * 50)
                self._log("正在生成配图...")
                self._log("=" * 50)
                image_gen = ImageGenerator(default_style=image_style)

                # 生成封面图
                self._log("  [1/3] 正在生成封面图...")
                cover = await image_gen.generate_cover_image(
                    keyword=keyword,
                    title=article.get("title", ""),
                    style=image_style,
                )
                images["cover"] = cover
                self._log("  ✓ 封面图生成完成")

                # 生成2张板块配图（共3张图：1封面 + 2配图）
                sections = article.get("sections", [])[:2]  # 取前2个section
                for i, section in enumerate(sections, 1):
                    self._log(f"  [{i+1}/3] 正在生成板块配图 {i}...")
                    collage = await image_gen.generate_collage_image(
                        keyword=keyword,
                        section_title=section.get("sectionTitle", ""),
                        section_index=i,
                        style=image_style,
                    )
                    images[f"section_{i}"] = collage
                    self._log(f"  ✓ 板块配图 {i} 生成完成")

                await image_gen.close()
                result["stages"]["image_generation"] = {
                    "status": "completed",
                    "count": len(images)
                }
                self._log(f"✓ 图片生成完成: 共 {len(images)} 张")
                self._update_step(8, "completed", "生成配图 - 完成", 0.96)

            # ==================== 保存 Markdown ====================
            # 默认输出到 outputs 文件夹
            output_dir = output_dir or Path("outputs")
            output_dir.mkdir(parents=True, exist_ok=True)

            self._update_step(9, "running", "保存文件", 0.97)
            self._log(f"[10/11] 正在保存文件...")

            # 保存图片
            if not skip_images and images:
                for key, data in images.items():
                    filename = f"{result['slug']}_{key}.png"
                    (output_dir / filename).write_bytes(data)

            # 保存 Markdown
            from seo_gen.main import build_markdown
            md_content = build_markdown(article)
            md_path = output_dir / f"{result['slug']}.md"
            md_path.write_text(md_content, encoding="utf-8")
            result["stages"]["markdown_saved"] = {"status": "completed", "path": str(md_path)}
            self._log(f"✓ Markdown 已保存: {md_path.name}")
            self._update_step(9, "completed", "保存文件 - 完成", 0.98)

            # ==================== 发布 WordPress ====================
            if not skip_wordpress:
                self._update_step(10, "running", "发布到 WordPress", 0.99)
                self._log("=" * 50)
                self._log("正在发布到 WordPress...")
                self._log("=" * 50)
                wp_publisher = WordPressPublisher()

                # 初始化封面图 URL
                cover_image_url = ""

                # 上传封面图
                if not skip_images and "cover" in images:
                    self._log("  [1/3] 正在上传封面图...")
                    cover_result = await wp_publisher.upload_image(
                        images["cover"],
                        filename=f"{result['slug']}_cover.png",
                        alt_text=article.get("title", ""),
                    )
                    if cover_result:
                        featured_media_id = cover_result.get("id")
                        cover_image_url = cover_result.get("url", "")  # 获取封面图 URL
                        self._log(f"  ✓ 封面图上传完成 (ID: {featured_media_id})")
                        self._log(f"  ✓ 封面图 URL: {cover_image_url[:80]}...")

                # 上传板块配图
                if not skip_images and images:
                    for key, data in images.items():
                        if key.startswith("section_"):
                            section_num = key.split("_")[1]
                            self._log(f"  [2/3] 正在上传板块配图 {section_num}...")
                            img_result = await wp_publisher.upload_image(
                                data,
                                filename=f"{result['slug']}_{key}.png",
                                alt_text=f"{article.get('title', '')} - Section {section_num}",
                            )
                            if img_result:
                                section_media_ids[section_num] = img_result.get("url", "")
                                self._log(f"  ✓ 板块配图 {section_num} 上传完成")

                # 构建 HTML（包含内部链接、外部链接、关键词标记）
                self._log("  [3/3] 正在构建 HTML...")

                # 获取内部链接
                from seo_gen.modules.internal_links import get_internal_link_manager
                link_manager = get_internal_link_manager()

                # 获取相关内部链接
                article_content = " ".join([s.get("content", "") for s in article.get("sections", [])])
                internal_links = link_manager.get_relevant_internal_links(
                    keyword=keyword,
                    article_title=article.get("title", ""),
                    article_content=article_content,
                    count=3,
                    exclude_urls=[f"https://asgdropshipping.com/{result['slug']}/"],
                )
                self._log(f"  找到 {len(internal_links)} 个相关内部链接")

                # 从文章 sources 中提取外部链接
                external_links = []
                for source in article.get("sources", [])[:5]:
                    external_links.append({
                        "keyword": source.get("source", ""),
                        "url": source.get("url", ""),
                    })

                html_content = self.content_generator.build_wordpress_html(
                    article,
                    cover_image_url=cover_image_url,
                    section_images=section_media_ids,
                    keyword=keyword,
                    internal_links=internal_links,
                    external_links=external_links,
                )
                self._log("  ✓ HTML 构建完成（含内部链接和关键词标记）")

                # 生成 Schema 标记（新增）
                self._log("  [3.5/4] 正在生成 Schema 标记...")
                _faq_list_for_schema = []
                if "faqSection" in article:
                    _faq_list_for_schema = article["faqSection"].get("items", [])[:8]
                elif "faq" in article:
                    _faq_list_for_schema = article["faq"][:8]

                schema_html = self.schema_generator.generate_all_schemas(
                    article=article,
                    article_url=f"https://asgdropshipping.com/{result['slug']}/",
                    faq_list=_faq_list_for_schema,
                    category_name="Dropshipping",
                    publish_date=None
                )
                # Schema注入到HTML开头（更靠近head位置）
                html_content = schema_html + "\n\n" + html_content
                self._log("  ✓ Schema 标记生成完成")


                # 发布
                self._log("  [4/4] 正在创建草稿...")
                post_id = await wp_publisher.publish_article(
                    title=article.get("title", ""),
                    content=html_content,
                    excerpt=article.get("metaDescription", "")[:150],
                    slug=result["slug"],
                    meta_description=article.get("metaDescription", ""),
                    featured_media_id=featured_media_id,
                    status="draft",
                )
                await wp_publisher.close()

                result["stages"]["wordpress_published"] = {
                    "status": "completed",
                    "post_id": post_id
                }
                self._log(f"✓ WordPress 草稿创建成功")
                self._log(f"  文章链接: https://asgdropshipping.com/?p={post_id}")
                self._update_step(10, "completed", "发布 WordPress - 完成", 1.0)

                # 记录到文章跟踪器（新增）
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


            result["success"] = True
            result["article"] = article
            result["quality"] = quality_result

            self._log("=" * 50)
            self._log("✓ 所有步骤完成!")
            self._log("=" * 50)

        except Exception as e:
            import traceback
            error_msg = f"错误: {str(e)}\n\n{traceback.format_exc()}"
            self._log(error_msg)
            result["error"] = str(e)

        return result

    def _generate_slug(self, keyword: str) -> str:
        """自动生成 slug"""
        import re
        # 转小写，替换空格和特殊字符
        slug = keyword.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:100]  # 限制长度


# Global singleton
_workflow_orchestrator: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator(progress_callback: Optional[Callable] = None) -> WorkflowOrchestrator:
    """获取全局工作流编排器单例"""
    global _workflow_orchestrator
    if _workflow_orchestrator is None or progress_callback is not None:
        _workflow_orchestrator = WorkflowOrchestrator(progress_callback=progress_callback)
        # 重置全局引用以便下次可以创建新的
        if progress_callback is None:
            pass
    # 如果有新的回调，更新现有的编排器
    if progress_callback and _workflow_orchestrator:
        _workflow_orchestrator.progress_callback = progress_callback
    return _workflow_orchestrator
