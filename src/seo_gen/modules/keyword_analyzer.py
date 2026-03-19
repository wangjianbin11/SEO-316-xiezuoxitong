# -*- coding: utf-8 -*-
"""
Keyword Analysis Module

Analyze keyword type and generate targeted research questions
"""

from typing import Any, Dict, List, Optional
from loguru import logger
from seo_gen.modules.llm import LLMClient


class KeywordAnalyzer:
    """Keyword Analyzer - Identify type and generate research questions (Chinese interface)"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize keyword analyzer

        Args:
            llm_client: LLM client
        """
        self.llm_client = llm_client

    async def analyze(
        self,
        keyword: str,
        serp_data: Optional[Dict[str, Any]] = None,
        platform: str = "article"
    ) -> Dict[str, Any]:
        """
        Analyze keyword and generate research questions

        Args:
            keyword: Keyword
            serp_data: Optional SERP data for dynamic question generation
            platform: Target platform (article, tiktok, youtube, facebook, linkedin, x, reddit, instagram, pinterest)

        Returns:
            {
                "keyword": str,
                "type": str,  # service, course, software, media, product, other
                "category": str,
                "confidence": float,
                "platform": str,
                "questions": [
                    {
                        "id": 1,
                        "question": str,
                        "options": [
                            {"key": "A", "label": str, "description": str},
                            {"key": "B", "label": str, "description": str},
                            {"key": "X", "label": "其他", "description": "手动输入自定义内容", "allow_custom": true},
                            ...
                        ]
                    },
                    ...
                ]
            }
        """
        if not self.llm_client:
            return self._fallback_analysis(keyword, serp_data, platform)

        try:
            # Step 1: Analyze keyword type
            keyword_type = await self._detect_keyword_type(keyword)

            # Step 2: Generate questions based on type, platform, and SERP data
            questions = await self._generate_questions(
                keyword,
                keyword_type,
                serp_data,
                platform
            )

            return {
                "keyword": keyword,
                "type": keyword_type.get("type", "other"),
                "category": keyword_type.get("category", ""),
                "confidence": keyword_type.get("confidence", 0.5),
                "platform": platform,
                "questions": questions
            }

        except Exception as e:
            logger.error(f"Keyword analysis failed: {e}")
            return self._fallback_analysis(keyword, serp_data, platform)

    async def _detect_keyword_type(self, keyword: str) -> Dict[str, Any]:
        """Detect keyword type"""
        messages = [
            {
                "role": "system",
                "content": """You are a keyword classification expert for SEO content.

Classify the keyword into one of these types:
- service: Business services, agencies, consulting, outsourcing
- course: Online courses, training, coaching, education
- software: SaaS tools, apps, platforms, software
- media: YouTube channels, blogs, influencers, publications
- product: Physical products, e-commerce items
- other: Everything else

Return JSON format:
{
  "type": "service|course|software|media|product|other",
  "category": "Specific category (e.g., 'e-commerce automation')",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}

Examples:
- "ASG Dropshipping" → {"type": "service", "category": "dropshipping automation"}
- "Shopify Course" → {"type": "course", "category": "e-commerce training"}
- "Dropshipping Tool" → {"type": "software", "category": "automation software"}
- "AliExpress Reviews" → {"type": "product", "category": "marketplace"}"""
            },
            {
                "role": "user",
                "content": f"Classify this keyword: {keyword}"
            }
        ]

        result = await self.llm_client.chat_json(messages, temperature=0.3)
        return result

    async def _generate_questions(
        self,
        keyword: str,
        keyword_type: Dict[str, Any],
        serp_data: Optional[Dict[str, Any]] = None,
        platform: str = "article"
    ) -> List[Dict[str, Any]]:
        """
        Generate research questions based on keyword type, platform, and SERP data (Chinese interface)

        Args:
            keyword: The keyword being analyzed
            keyword_type: Type classification result
            serp_data: Optional SERP data for dynamic question generation
            platform: Target platform for content generation

        Returns:
            List of questions with options (including "Other" option for custom input)
        """
        # 根据平台选择问题集
        if platform == "article":
            return await self._generate_article_questions(keyword, keyword_type, serp_data)
        else:
            return await self._generate_social_questions(keyword, platform, serp_data)

    async def _generate_article_questions(
        self,
        keyword: str,
        keyword_type: Dict[str, Any],
        serp_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成文章类型的策略问题"""
        keyword_type_str = keyword_type.get("type", "other")

        # Question 1 & 2: Fixed templates based on type
        questions = self._get_type_based_questions(keyword, keyword_type_str)

        # Question 3: Dynamic search intent question
        search_intent_question = await self._generate_search_intent_question(
            keyword,
            keyword_type_str,
            serp_data
        )
        if search_intent_question:
            questions.append(search_intent_question)

        # Add "Other" option to all questions
        return self._add_custom_option_to_questions(questions)

    async def _generate_social_questions(
        self,
        keyword: str,
        platform: str,
        serp_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成社交媒体平台的策略问题"""
        # 获取平台特定问题
        questions = self._get_platform_specific_questions(keyword, platform, serp_data)

        # Add "Other" option to all questions
        return self._add_custom_option_to_questions(questions)

    def _get_platform_specific_questions(
        self,
        keyword: str,
        platform: str,
        serp_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取平台特定的策略问题"""

        # 平台特定问题模板
        platform_questions = {
            "tiktok": [
                {
                    "id": 1,
                    "question": f"根据 TikTok 热门趋势，'{keyword}' 的内容应该采用什么形式？",
                    "options": [
                        {"key": "A", "label": "教程分享", "description": "step-by-step 教学内容"},
                        {"key": "B", "label": "剧情/故事", "description": "有开头、发展、结尾的故事线"},
                        {"key": "C", "label": "热点回应", "description": "参与热门话题/挑战"},
                        {"key": "D", "label": "日常生活", "description": "Vlog、日常片段"}
                    ]
                },
                {
                    "id": 2,
                    "question": "TikTok 内容的目标受众是谁？",
                    "options": [
                        {"key": "A", "label": "Z世代 (18-24岁)", "description": "年轻用户群体"},
                        {"key": "B", "label": "千禧一代 (25-40岁)", "description": "职场人群"},
                        {"key": "C", "label": "银发族 (50岁+)", "description": "中老年用户"},
                        {"key": "D", "label": "全年龄段", "description": "大众向内容"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望内容达成什么效果？",
                    "options": [
                        {"key": "A", "label": "快速传播", "description": "追求高播放、高分享"},
                        {"key": "B", "label": "互动参与", "description": "评论、点赞、收藏"},
                        {"key": "C", "label": "涨粉关注", "description": "吸引长期粉丝"},
                        {"key": "D", "label": "带货转化", "description": "产品推广/销售"}
                    ]
                }
            ],
            "youtube": [
                {
                    "id": 1,
                    "question": f"YouTube 视频 '{keyword}' 应该采用什么内容形式？",
                    "options": [
                        {"key": "A", "label": "教程/How-to", "description": "step-by-step 教学视频"},
                        {"key": "B", "label": "评测/Review", "description": "产品或服务评测"},
                        {"key": "C", "label": "列表/Top 10", "description": "盘点推荐类"},
                        {"key": "D", "label": "Vlog/日常", "description": "生活记录"}
                    ]
                },
                {
                    "id": 2,
                    "question": "YouTube 视频的目标时长？",
                    "options": [
                        {"key": "A", "label": "短视频 (1-5分钟)", "description": "Shorts 或快速内容"},
                        {"key": "B", "label": "中等 (8-15分钟)", "description": "标准YouTube视频"},
                        {"key": "C", "label": "长视频 (20分钟+)", "description": "深度内容"},
                        {"key": "D", "label": "系列视频", "description": "分集连载"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望在 YouTube 达成什么目标？",
                    "options": [
                        {"key": "A", "label": "搜索流量", "description": "SEO 优化，被动流量"},
                        {"key": "B", "label": "推荐算法", "description": "高点击率、高完播率"},
                        {"key": "C", "label": "订阅增长", "description": "长期粉丝积累"},
                        {"key": "D", "label": "变现收入", "description": "广告、赞助、联盟营销"}
                    ]
                }
            ],
            "facebook": [
                {
                    "id": 1,
                    "question": f"Facebook 帖子 '{keyword}' 的内容类型？",
                    "options": [
                        {"key": "A", "label": "图文帖", "description": "文字+图片"},
                        {"key": "B", "label": "链接分享", "description": "外部链接预览"},
                        {"key": "C", "label": "视频内容", "description": "本地或外链视频"},
                        {"key": "D", "label": "轮播图", "description": "多图展示"}
                    ]
                },
                {
                    "id": 2,
                    "question": "Facebook 帖子的目标受众？",
                    "options": [
                        {"key": "A", "label": "专业/商业", "description": "B2B、行业相关"},
                        {"key": "B", "label": "个人/生活", "description": "朋友、家人互动"},
                        {"key": "C", "label": "兴趣社群", "description": "爱好、兴趣小组"},
                        {"key": "D", "label": "本地社区", "description": "同城、本地服务"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望 Facebook 帖子达成什么效果？",
                    "options": [
                        {"key": "A", "label": "互动参与", "description": "评论、分享、反应"},
                        {"key": "B", "label": "点击链接", "description": "流量引导到网站"},
                        {"key": "C", "label": "品牌曝光", "description": "提高品牌认知"},
                        {"key": "D", "label": "活动转化", "description": "报名、购买等"}
                    ]
                }
            ],
            "linkedin": [
                {
                    "id": 1,
                    "question": f"LinkedIn 内容 '{keyword}' 的专业定位？",
                    "options": [
                        {"key": "A", "label": "行业洞察", "description": "趋势分析、市场观察"},
                        {"key": "B", "label": "个人成长", "description": "职业发展、技能提升"},
                        {"key": "C", "label": "管理心得", "description": "领导力、团队管理"},
                        {"key": "D", "label": "案例分享", "description": "成功/失败经验"}
                    ]
                },
                {
                    "id": 2,
                    "question": "LinkedIn 内容的目标受众？",
                    "options": [
                        {"key": "A", "label": "高管/决策者", "description": "企业高层"},
                        {"key": "B", "label": "同行/专家", "description": "行业专业人士"},
                        {"key": "C", "label": "求职者/学生", "description": "职业新人"},
                        {"key": "D", "label": "创业者", "description": "中小企业主"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望 LinkedIn 内容达成什么效果？",
                    "options": [
                        {"key": "A", "label": "专业形象", "description": "建立个人品牌"},
                        {"key": "B", "label": "商务合作", "description": "获得合作机会"},
                        {"key": "C", "label": "招聘/求职", "description": "人才吸引"},
                        {"key": "D", "label": "思想领袖", "description": "行业影响力"}
                    ]
                }
            ],
            "x": [
                {
                    "id": 1,
                    "question": f"X/Twitter 推文 '{keyword}' 的内容类型？",
                    "options": [
                        {"key": "A", "label": "观点分享", "description": "个人见解、评论"},
                        {"key": "B", "label": "信息转发", "description": "新闻、资源分享"},
                        {"key": "C", "label": "互动提问", "description": "引发讨论"},
                        {"key": "D", "label": "幽默娱乐", "description": "段子、梗图"}
                    ]
                },
                {
                    "id": 2,
                    "question": "推文的发布策略？",
                    "options": [
                        {"key": "A", "label": "热点跟风", "description": "结合热门话题"},
                        {"key": "B", "label": "定时发布", "description": "固定时间推送"},
                        {"key": "C", "label": "线索联动", "description": "Thread 系列"},
                        {"key": "D", "label": "互动回复", "description": "参与讨论"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望推文达成什么效果？",
                    "options": [
                        {"key": "A", "label": "病毒传播", "description": "大量转推、点赞"},
                        {"key": "B", "label": "粉丝增长", "description": "吸引关注者"},
                        {"key": "C", "label": "话题参与", "description": "上热搜、引发讨论"},
                        {"key": "D", "label": "流量引导", "description": "点击链接"}
                    ]
                }
            ],
            "reddit": [
                {
                    "id": 1,
                    "question": f"Reddit 帖子 '{keyword}' 应该发布到哪个子版块类型？",
                    "options": [
                        {"key": "A", "label": "专业社区", "description": "r/Entrepreneur, r/SideHustle 等"},
                        {"key": "B", "label": "兴趣小组", "description": "特定爱好、兴趣"},
                        {"key": "C", "label": "求助/咨询", "description": "r/help, r/ask 等"},
                        {"key": "D", "label": "娱乐/轻松", "description": "r/funny, r/memes 等"}
                    ]
                },
                {
                    "id": 2,
                    "question": "Reddit 帖子的互动策略？",
                    "options": [
                        {"key": "A", "label": "引发讨论", "description": "开放式话题"},
                        {"key": "B", "label": "提供价值", "description": "教程、指南、资源"},
                        {"key": "C", "label": "求助建议", "description": "问问题、求经验"},
                        {"key": "D", "label": "分享成果", "description": "展示成果/作品"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望 Reddit 帖子达成什么效果？",
                    "options": [
                        {"key": "A", "label": "高赞置顶", "description": "获得大量 upvote"},
                        {"key": "B", "label": "活跃讨论", "description": "评论互动"},
                        {"key": "C", "label": "社区认可", "description": "获得 awards"},
                        {"key": "D", "label": "引流外站", "description": "引导到个人网站"}
                    ]
                }
            ],
            "instagram": [
                {
                    "id": 1,
                    "question": f"Instagram 内容 '{keyword}' 的形式？",
                    "options": [
                        {"key": "A", "label": "Posts 帖子", "description": "方图、横图内容"},
                        {"key": "B", "label": "Stories 故事", "description": "24小时消失"},
                        {"key": "C", "label": "Reels 短视频", "description": "竖屏短视频"},
                        {"key": "D", "label": "Carousel 轮播", "description": "多图滑动"}
                    ]
                },
                {
                    "id": 2,
                    "question": "Instagram 内容的风格调性？",
                    "options": [
                        {"key": "A", "label": "精致生活", "description": "aesthetic、生活方式"},
                        {"key": "B", "label": "专业干货", "description": "知识分享、教程"},
                        {"key": "C", "label": "幽默搞笑", "description": "meme、娱乐"},
                        {"key": "D", "label": "励志成长", "description": "motivation、正能量"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望 Instagram 内容达成什么效果？",
                    "options": [
                        {"key": "A", "label": "视觉吸引", "description": "likes、saved"},
                        {"key": "B", "label": "粉丝增长", "description": "followers 增加"},
                        {"key": "C", "label": "互动参与", "description": "comments、DMs"},
                        {"key": "D", "label": "商业转化", "description": "链接点击、销售"}
                    ]
                }
            ],
            "pinterest": [
                {
                    "id": 1,
                    "question": f"Pinterest Pin '{keyword}' 的内容类型？",
                    "options": [
                        {"key": "A", "label": "教程指南", "description": "How-to、DIY"},
                        {"key": "B", "label": "产品展示", "description": "电商产品"},
                        {"key": "C", "label": "灵感收集", "description": "创意、想法"},
                        {"key": "D", "label": "文章链接", "description": "博客引流"}
                    ]
                },
                {
                    "id": 2,
                    "question": "Pinterest Pin 的搜索策略？",
                    "options": [
                        {"key": "A", "label": "视觉关键词", "description": "图片描述性 SEO"},
                        {"key": "B", "label": "长尾关键词", "description": "具体搜索词"},
                        {"key": "C", "label": "趋势词汇", "description": "热门话题"},
                        {"key": "D", "label": "品牌词汇", "description": "企业/品牌名"}
                    ]
                },
                {
                    "id": 3,
                    "question": "希望 Pinterest Pin 达成什么效果？",
                    "options": [
                        {"key": "A", "label": "Pin 病毒传播", "description": "大量 repin、保存"},
                        {"key": "B", "label": "网站引流", "description": "点击链接到网站"},
                        {"key": "C", "label": "品牌曝光", "description": "提高认知"},
                        {"key": "D", "label": "销售转化", "description": "电商销售"}
                    ]
                }
            ]
        }

        # 获取平台问题，如果没有则使用通用问题
        questions = platform_questions.get(platform, self._get_generic_social_questions(keyword))

        return questions

    def _get_generic_social_questions(self, keyword: str) -> List[Dict[str, Any]]:
        """通用社交媒体问题（当平台没有特定问题时使用）"""
        return [
            {
                "id": 1,
                "question": f"根据热门趋势，'{keyword}' 的内容应该侧重什么？",
                "options": [
                    {"key": "A", "label": "教程分享", "description": "教学、指南类"},
                    {"key": "B", "label": "观点评论", "description": "个人见解、分析"},
                    {"key": "C", "label": "娱乐轻松", "description": "搞笑、轻松"},
                    {"key": "D", "label": "新闻资讯", "description": "信息、资讯"}
                ]
            },
            {
                "id": 2,
                "question": "目标受众是谁？",
                "options": [
                    {"key": "A", "label": "年轻用户 (18-30岁)", "description": "Z世代、千禧一代"},
                    {"key": "B", "label": "职场人士 (30-45岁)", "description": "工作人群"},
                    {"key": "C", "label": "成熟用户 (45岁+)", "description": "中老年用户"},
                    {"key": "D", "label": "全年龄段", "description": "大众向"}
                ]
            },
            {
                "id": 3,
                "question": "希望内容达成什么效果？",
                "options": [
                    {"key": "A", "label": "快速传播", "description": "高分享、高互动"},
                    {"key": "B", "label": "粉丝增长", "description": "长期关注者"},
                    {"key": "C", "label": "互动参与", "description": "评论、点赞"},
                    {"key": "D", "label": "转化引流", "description": "链接点击、转化"}
                ]
            }
        ]

    def _add_custom_option_to_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为所有问题添加"其他"自定义输入选项"""
        for q in questions:
            if q.get("options"):
                # Find the highest key letter
                existing_keys = [opt.get("key", "") for opt in q["options"]]
                max_key = max(existing_keys, key=lambda x: ord(x) if x.isalpha() else 0, default="E")

                # Next letter after the highest key
                next_key = chr(ord(max_key) + 1) if max_key.isalpha() else "X"

                # Add "Other" option
                q["options"].append({
                    "key": next_key,
                    "label": "其他",
                    "description": "手动输入自定义内容",
                    "allow_custom": True
                })

        return questions

    def _get_type_based_questions(
        self,
        keyword: str,
        keyword_type_str: str
    ) -> List[Dict[str, Any]]:
        """Get questions 1 & 2 based on keyword type"""

        question_templates = {
            "service": [
                {
                    "id": 1,
                    "question": f"根据 Google 搜索数据，'{keyword}' 相关搜索量最高的是哪个方面？",
                    "options": [
                        {"key": "A", "label": "服务功能与流程", "description": "提供什么服务，如何运作"},
                        {"key": "B", "label": "价格与方案", "description": "收费标准，性价比分析"},
                        {"key": "C", "label": "客户评价", "description": "真实用户反馈和使用效果"},
                        {"key": "D", "label": "竞品对比", "description": "与市场上其他服务商比较"}
                    ]
                },
                {
                    "id": 2,
                    "question": "目标客户类型是什么？",
                    "options": [
                        {"key": "A", "label": "独立站卖家", "description": "Shopify、WooCommerce等独立站运营者"},
                        {"key": "B", "label": "平台型卖家", "description": "Amazon、eBay、Etsy等平台卖家"},
                        {"key": "C", "label": "中大型客户", "description": "月销售额$50K+的成熟企业"},
                        {"key": "D", "label": "小型客户/新手", "description": "月销售额$10K以下的初创卖家"},
                        {"key": "E", "label": "全类型客户", "description": "覆盖所有规模的电商卖家"}
                    ]
                }
            ],
            "course": [
                {
                    "id": 1,
                    "question": f"根据 Google 搜索数据，'{keyword}' 相关搜索量最高的是哪个方面？",
                    "options": [
                        {"key": "A", "label": "课程内容与大纲", "description": "学什么，课程结构"},
                        {"key": "B", "label": "讲师/创作者资质", "description": "谁创建的，背景如何"},
                        {"key": "C", "label": "学员成果与案例", "description": "成功案例和学习效果"},
                        {"key": "D", "label": "价值与价格", "description": "是否值得投资"}
                    ]
                },
                {
                    "id": 2,
                    "question": "目标客户类型是什么？",
                    "options": [
                        {"key": "A", "label": "独立站卖家", "description": "Shopify、WooCommerce等独立站运营者"},
                        {"key": "B", "label": "平台型卖家", "description": "Amazon、eBay、Etsy等平台卖家"},
                        {"key": "C", "label": "中大型客户", "description": "月销售额$50K+的成熟企业"},
                        {"key": "D", "label": "小型客户/新手", "description": "月销售额$10K以下的初创卖家"},
                        {"key": "E", "label": "全类型客户", "description": "覆盖所有规模的电商卖家"}
                    ]
                }
            ],
            "software": [
                {
                    "id": 1,
                    "question": f"根据 Google 搜索数据，'{keyword}' 相关搜索量最高的是哪个方面？",
                    "options": [
                        {"key": "A", "label": "功能与特性", "description": "能做什么，核心功能"},
                        {"key": "B", "label": "价格与价值", "description": "收费标准、免费替代方案"},
                        {"key": "C", "label": "用户评价", "description": "真实用户反馈"},
                        {"key": "D", "label": "集成与生态", "description": "与其他工具的配合"}
                    ]
                },
                {
                    "id": 2,
                    "question": "目标客户类型是什么？",
                    "options": [
                        {"key": "A", "label": "独立站卖家", "description": "Shopify、WooCommerce等独立站运营者"},
                        {"key": "B", "label": "平台型卖家", "description": "Amazon、eBay、Etsy等平台卖家"},
                        {"key": "C", "label": "中大型客户", "description": "月销售额$50K+的成熟企业"},
                        {"key": "D", "label": "小型客户/新手", "description": "月销售额$10K以下的初创卖家"},
                        {"key": "E", "label": "全类型客户", "description": "覆盖所有规模的电商卖家"}
                    ]
                }
            ],
            "product": [
                {
                    "id": 1,
                    "question": f"根据 Google 搜索数据，'{keyword}' 相关搜索量最高的是哪个方面？",
                    "options": [
                        {"key": "A", "label": "质量与功能", "description": "产品规格和特性"},
                        {"key": "B", "label": "价格与价值", "description": "价格、去哪买、优惠"},
                        {"key": "C", "label": "使用体验", "description": "评价、开箱、实际使用"},
                        {"key": "D", "label": "替代品", "description": "与竞争产品对比"}
                    ]
                },
                {
                    "id": 2,
                    "question": "目标客户类型是什么？",
                    "options": [
                        {"key": "A", "label": "独立站卖家", "description": "Shopify、WooCommerce等独立站运营者"},
                        {"key": "B", "label": "平台型卖家", "description": "Amazon、eBay、Etsy等平台卖家"},
                        {"key": "C", "label": "中大型客户", "description": "月销售额$50K+的成熟企业"},
                        {"key": "D", "label": "小型客户/新手", "description": "月销售额$10K以下的初创卖家"},
                        {"key": "E", "label": "全类型客户", "description": "覆盖所有规模的电商卖家"}
                    ]
                }
            ],
            "other": [
                {
                    "id": 1,
                    "question": f"根据 Google 搜索数据，'{keyword}' 相关搜索量最高的是哪个方面？",
                    "options": [
                        {"key": "A", "label": "概述与说明", "description": "是什么，如何运作"},
                        {"key": "B", "label": "优势与价值", "description": "为什么重要，有什么好处"},
                        {"key": "C", "label": "实施方法", "description": "如何使用/应用"},
                        {"key": "D", "label": "对比分析", "description": "与替代方案比较"}
                    ]
                },
                {
                    "id": 2,
                    "question": "目标客户类型是什么？",
                    "options": [
                        {"key": "A", "label": "独立站卖家", "description": "Shopify、WooCommerce等独立站运营者"},
                        {"key": "B", "label": "平台型卖家", "description": "Amazon、eBay、Etsy等平台卖家"},
                        {"key": "C", "label": "中大型客户", "description": "月销售额$50K+的成熟企业"},
                        {"key": "D", "label": "小型客户/新手", "description": "月销售额$10K以下的初创卖家"}
                    ]
                }
            ]
        }

        return question_templates.get(keyword_type_str, question_templates["other"])

    async def _generate_search_intent_question(
        self,
        keyword: str,
        keyword_type_str: str,
        serp_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate Question 3: Dynamic search intent options based on Google SERP analysis

        Search Intent Types:
        - Informational: 用户想学习、了解某事
        - Navigational: 用户想找特定网站/页面
        - Commercial Investigation: 用户想比较产品/服务
        - Transactional: 用户准备购买/注册
        - Local: 用户找本地服务/商家
        """
        # Analyze SERP to determine dominant search intents
        search_intents = []

        if serp_data:
            # Extract search intent from SERP data
            detected_intent = serp_data.get("searchIntent", "")
            related_searches = serp_data.get("relatedSearches", [])
            results = serp_data.get("searchResults", [])

            # Build dynamic options based on actual SERP data
            search_intents = self._analyze_search_intents_from_serp(
                keyword,
                detected_intent,
                related_searches,
                results,
                keyword_type_str
            )

        # If no SERP data or analysis failed, use default intents
        if not search_intents:
            search_intents = self._get_default_search_intents(keyword_type_str)

        return {
            "id": 3,
            "question": f"根据 Google 搜索意图分析，'{keyword}' 的主要搜索意图是什么？这将决定文章的写作方向和内容策略。",
            "options": search_intents
        }

    def _analyze_search_intents_from_serp(
        self,
        keyword: str,
        detected_intent: str,
        related_searches: List[str],
        results: List[Dict[str, Any]],
        keyword_type_str: str
    ) -> List[Dict[str, Any]]:
        """Analyze SERP data to extract relevant search intent options"""

        intents = []

        # Map detected intent to Chinese option
        intent_mapping = {
            "informational": {
                "key": "A",
                "label": "信息性搜索 (Informational)",
                "description": "用户想了解和学习，写教程/指南/科普文章"
            },
            "navigational": {
                "key": "B",
                "label": "导航性搜索 (Navigational)",
                "description": "用户找特定网站/品牌，写官方介绍/直达链接"
            },
            "commercial": {
                "key": "C",
                "label": "商业调查 (Commercial Investigation)",
                "description": "用户想比较选择，写评测/对比/推荐"
            },
            "transactional": {
                "key": "D",
                "label": "交易性搜索 (Transactional)",
                "description": "用户准备购买，写优惠/折扣/购买指南"
            },
            "local": {
                "key": "E",
                "label": "本地搜索 (Local)",
                "description": "用户找本地服务，写区域/本地化内容"
            }
        }

        # Add detected intent first (highest priority)
        if detected_intent and detected_intent.lower() in intent_mapping:
            base_intent = detected_intent.lower()
            if base_intent == "commercial investigation":
                base_intent = "commercial"
            intents.append(intent_mapping[base_intent])

        # Analyze related searches for additional intent clues
        intent_keywords = {
            "informational": ["how to", "what is", "guide", "tutorial", "tips", "如何", "什么是", "教程", "指南"],
            "navigational": ["official", "login", "website", "官网", "登录", "网站"],
            "commercial": ["best", "top", "vs", "review", "comparison", "最好的", "对比", "评测", "推荐"],
            "transactional": ["buy", "price", "cheap", "discount", "deal", "购买", "价格", "优惠", "折扣"],
            "local": ["near me", "location", "store", "附近", "地址", "门店"]
        }

        detected_other_intents = set()
        for search in related_searches[:5]:  # Check top 5 related searches
            search_lower = search.lower()
            for intent_type, keywords in intent_keywords.items():
                if any(kw in search_lower for kw in keywords):
                    if intent_type != base_intent and intent_type in intent_mapping:
                        detected_other_intents.add(intent_type)

        # Add other detected intents
        for intent in detected_other_intents:
            if len(intents) < 4:  # Max 4 preset options
                # Find next available key
                used_keys = {opt["key"] for opt in intents}
                for key, intent_data in intent_mapping.items():
                    if key == intent and intent_data["key"] not in used_keys:
                        intents.append(intent_data)
                        break

        # Ensure we have at least 3-4 options
        default_order = ["informational", "commercial", "transactional", "navigational"]
        for intent_type in default_order:
            if len(intents) >= 4:
                break
            used_keys = {opt["key"] for opt in intents}
            if intent_type in intent_mapping and intent_mapping[intent_type]["key"] not in used_keys:
                intents.append(intent_mapping[intent_type])

        return intents[:4]  # Return max 4 preset options

    def _get_default_search_intents(self, keyword_type_str: str) -> List[Dict[str, Any]]:
        """Get default search intents when SERP data is not available"""

        # Type-specific default intents
        type_defaults = {
            "service": [
                {"key": "A", "label": "信息性搜索 (Informational)", "description": "用户想了解服务如何运作"},
                {"key": "B", "label": "商业调查 (Commercial Investigation)", "description": "用户想比较不同服务商"},
                {"key": "C", "label": "交易性搜索 (Transactional)", "description": "用户准备购买服务"},
                {"key": "D", "label": "品牌搜索 (Branded)", "description": "用户搜索特定品牌服务"}
            ],
            "course": [
                {"key": "A", "label": "信息性搜索 (Informational)", "description": "用户想了解课程内容"},
                {"key": "B", "label": "商业调查 (Commercial Investigation)", "description": "用户想比较不同课程"},
                {"key": "C", "label": "交易性搜索 (Transactional)", "description": "用户准备购买课程"},
                {"key": "D", "label": "验证搜索 (Verification)", "description": "用户验证课程是否可信"}
            ],
            "software": [
                {"key": "A", "label": "信息性搜索 (Informational)", "description": "用户想了解软件功能"},
                {"key": "B", "label": "商业调查 (Commercial Investigation)", "description": "用户想比较软件工具"},
                {"key": "C", "label": "交易性搜索 (Transactional)", "description": "用户准备购买/订阅"},
                {"key": "D", "label": "替代搜索 (Alternative)", "description": "用户找免费或更便宜的替代品"}
            ],
            "product": [
                {"key": "A", "label": "信息性搜索 (Informational)", "description": "用户想了解产品信息"},
                {"key": "B", "label": "商业调查 (Commercial Investigation)", "description": "用户想比较产品"},
                {"key": "C", "label": "交易性搜索 (Transactional)", "description": "用户准备购买"},
                {"key": "D", "label": "评价搜索 (Reviews)", "description": "用户看真实评价"}
            ]
        }

        return type_defaults.get(
            keyword_type_str,
            [
                {"key": "A", "label": "信息性搜索 (Informational)", "description": "用户想学习和了解"},
                {"key": "B", "label": "商业调查 (Commercial Investigation)", "description": "用户想比较选择"},
                {"key": "C", "label": "交易性搜索 (Transactional)", "description": "用户准备行动"},
                {"key": "D", "label": "验证搜索 (Verification)", "description": "用户验证真伪/可信度"}
            ]
        )

    def _fallback_analysis(
        self,
        keyword: str,
        serp_data: Optional[Dict[str, Any]] = None,
        platform: str = "article"
    ) -> Dict[str, Any]:
        """Fallback analysis when LLM unavailable"""
        if platform == "article":
            # 使用同步方式生成默认问题
            questions = self._get_default_article_questions(keyword)
        else:
            questions = self._get_platform_specific_questions(keyword, platform, serp_data)
            questions = self._add_custom_option_to_questions(questions)

        return {
            "keyword": keyword,
            "type": "other",
            "category": "General",
            "confidence": 0.5,
            "platform": platform,
            "questions": questions
        }

    def _get_default_article_questions(self, keyword: str) -> List[Dict[str, Any]]:
        """获取默认的文章策略问题（同步方法）"""
        # 使用 "other" 类型的默认问题
        questions = self._get_type_based_questions(keyword, "other")

        # 添加默认的搜索意图问题
        search_intent_question = {
            "id": 3,
            "question": f"根据 Google 搜索意图分析，'{keyword}' 的主要搜索意图是什么？这将决定文章的写作方向和内容策略。",
            "options": [
                {"key": "A", "label": "信息性搜索 (Informational)", "description": "用户想学习和了解"},
                {"key": "B", "label": "商业调查 (Commercial Investigation)", "description": "用户想比较选择"},
                {"key": "C", "label": "交易性搜索 (Transactional)", "description": "用户准备行动"},
                {"key": "D", "label": "验证搜索 (Verification)", "description": "用户验证真伪/可信度"}
            ]
        }
        questions.append(search_intent_question)

        # 添加 "其他" 选项
        return self._add_custom_option_to_questions(questions)

    def parse_user_answers(
        self,
        answers: str,
        custom_inputs: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Parse user answers including custom inputs

        Args:
            answers: Format like "1A;2B;3A" or ["1A", "2B", "3A"]
            custom_inputs: Custom input values {"1": "custom content", "2": "...", "3": "..."}

        Returns:
            {"1": "A", "2": "B", "3": "A"} or {"1": "CUSTOM:value", "2": "B", ...}
        """
        if isinstance(answers, str):
            parts = answers.split(";")
        elif isinstance(answers, list):
            parts = answers
        else:
            return {}

        result = {}
        for part in parts:
            part = part.strip()
            if len(part) >= 2 and part[0].isdigit():
                q_id = part[0]
                answer = part[1].upper()

                # Check if this answer has a custom input
                if custom_inputs and q_id in custom_inputs and custom_inputs[q_id].strip():
                    result[q_id] = f"CUSTOM:{custom_inputs[q_id].strip()}"
                else:
                    result[q_id] = answer

        return result

    def build_enhanced_search_queries(
        self,
        keyword: str,
        answers: Dict[str, str],
        questions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Build enhanced search queries based on user answers (including custom inputs)

        Args:
            keyword: Original keyword
            answers: User answers {"1": "A", "2": "B", "3": "A"} or {"1": "CUSTOM:custom value", ...}
            questions: Question list

        Returns:
            Enhanced search query list
        """
        queries = [keyword]  # Base search

        # Based on question 1 answer - add content type keywords
        q1_answer = answers.get("1")
        if q1_answer:
            q1 = next((q for q in questions if q.get("id") == 1), None)
            if q1:
                # Check if custom input
                if q1_answer.startswith("CUSTOM:"):
                    custom_value = q1_answer.split(":", 1)[1].strip()
                    # Use custom value directly as search keywords
                    queries.append(f"{keyword} {custom_value}")
                    # Also try English translation of common terms
                    queries.append(f"{keyword} {custom_value} review")
                    queries.append(f"{keyword} {custom_value} guide")
                else:
                    option = next((o for o in q1.get("options", []) if o.get("key") == q1_answer), None)
                    if option:
                        label = option.get("label", "")
                        # Map Chinese labels to search keywords
                        label_keywords = {
                            "服务功能与流程": ["features", "how it works", "functionality"],
                            "价格与方案": ["pricing", "cost", "reviews", "price", "plans"],
                            "客户评价": ["reviews", "testimonials", "customer feedback", "experience"],
                            "竞品对比": ["vs alternatives", "comparison", "competitors"],
                            "课程内容与大纲": ["curriculum", "content", "syllabus"],
                            "讲师/创作者资质": ["instructor", "creator", "background", "credentials"],
                            "学员成果与案例": ["results", "testimonials", "success stories", "outcomes"],
                            "价值与价格": ["value", "worth", "price", "cost"],
                            "功能与特性": ["features", "functionality", "capabilities"],
                            "用户评价": ["reviews", "user feedback", "ratings"],
                            "集成与生态": ["integration", "ecosystem", "compatibility"],
                            "质量与功能": ["quality", "features", "specs"],
                            "使用体验": ["experience", "user reviews", "hands-on"],
                            "替代品": ["alternatives", "similar", "competing products"],
                            "概述与说明": ["overview", "introduction", "what is", "explanation"],
                            "优势与价值": ["benefits", "advantages", "value", "why"],
                            "实施方法": ["tutorial", "how to", "guide", "implementation"],
                            "对比分析": ["comparison", "vs", "alternatives"],
                        }
                        for label_key, keywords in label_keywords.items():
                            if label_key in label:
                                for kw in keywords:
                                    queries.append(f"{keyword} {kw}")

        # Based on question 2 answer - add platform-specific searches
        q2_answer = answers.get("2")
        if q2_answer:
            # Check if custom input
            if q2_answer.startswith("CUSTOM:"):
                custom_value = q2_answer.split(":", 1)[1].strip()
                # If custom input is a website, add site: search
                if "." in custom_value and not custom_value.startswith("http"):
                    domain = custom_value.replace("https://", "").replace("http://", "").strip().split("/")[0]
                    queries.append(f"{keyword} site:{domain}")
                else:
                    queries.append(f"{keyword} {custom_value}")
            else:
                platform_sites = {
                    "A": ["site:trustpilot.com"],
                    "B": ["site:reddit.com"],
                    "C": ["site:bbb.org"],
                    "D": ["site:sitejabber.com", "google reviews"],
                    "E": ["site:youtube.com"]
                }
                if q2_answer in platform_sites:
                    for site in platform_sites[q2_answer]:
                        queries.append(f"{keyword} {site}")

        # Based on question 3 answer - search intent keywords
        q3_answer = answers.get("3")
        if q3_answer:
            # Check if custom input
            if q3_answer.startswith("CUSTOM:"):
                custom_value = q3_answer.split(":", 1)[1].strip()
                queries.append(f"{keyword} {custom_value}")
            else:
                intent_keywords = {
                    "A": ["guide", "tutorial", "introduction", "what is", "指南", "教程"],  # Informational
                    "B": ["official", "website", "login", "官网", "登录"],  # Navigational/Branded
                    "C": ["review", "comparison", "best", "top", "vs", "评测", "对比"],  # Commercial
                    "D": ["buy", "price", "discount", "deal", "offer", "购买", "价格", "优惠"],  # Transactional
                    "E": ["near me", "location", "store", "address", "附近", "地址"]  # Local
                }
                if q3_answer in intent_keywords:
                    for kw in intent_keywords[q3_answer]:
                        queries.append(f"{keyword} {kw}")

        return list(set(queries))  # Deduplicate


# Global singleton
_keyword_analyzer: Optional[KeywordAnalyzer] = None


def get_keyword_analyzer() -> KeywordAnalyzer:
    """Get global keyword analyzer singleton"""
    global _keyword_analyzer
    if _keyword_analyzer is None:
        from seo_gen.modules.llm import get_llm_client
        _keyword_analyzer = KeywordAnalyzer(get_llm_client())
    return _keyword_analyzer
