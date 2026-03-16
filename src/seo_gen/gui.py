"""
SEO Content Generator - GUI 主程序

基于 CustomTkinter 的图形界面
内置终端输出显示，通过回调获取进度
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Thread

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from seo_gen.config import settings
from seo_gen.modules.workflow import get_workflow_orchestrator
from seo_gen.modules.keyword_analyzer import get_keyword_analyzer


class ArticleTypeConfirmDialog(ctk.CTkToplevel):
    """文章类型确认对话框 - 在标题生成后让用户确认/修改写作类型"""

    # 类型对应的详细信息
    TYPE_INFO = {
        "pillar": {
            "name": "顶梁柱型 (Pillar Post)",
            "description": "深度全面指南，如 complete guide、ultimate guide",
            "word_count": "4000-6000 字",
            "structure": "H1 → 引言 → 摘要答案 → 目录 → 3个H2深潜(各含3-5个H3) → 结论 → FAQ",
            "search_intent": "学习型意图 - 用户希望全面了解一个主题",
            "color": "#3B82F6",  # 蓝色
            "icon": "📚"
        },
        "response": {
            "name": "回答型 (Response Post)",
            "description": "直接回答问题，如 how to、what is、why",
            "word_count": "3000-4000 字",
            "structure": "H1 → 引言 → 核心答案 → 引导阅读 → H2深潜 → H3×2-3组 → 结论 → FAQ",
            "search_intent": "信息型意图 - 用户有具体问题需要直接答案",
            "color": "#10B981",  # 绿色
            "icon": "❓"
        },
        "share": {
            "name": "分享型 (Share Post)",
            "description": "清单排名对比，如 10 best、top 5、vs",
            "word_count": "3000-4000 字",
            "structure": "H1 → 引言 → 快速回答 → H2编号列表(4-8个) → 结论 → FAQ",
            "search_intent": "探索型意图 - 用户希望浏览选项、比较或学习多个技巧",
            "color": "#F59E0B",  # 橙色
            "icon": "📊"
        }
    }

    def __init__(self, parent, keyword: str, suggested_type: str, classification_data: dict,
                 generated_title: str, on_confirm_callback):
        super().__init__(parent)
        self.keyword = keyword
        self.suggested_type = suggested_type
        self.classification_data = classification_data
        self.generated_title = generated_title
        self.on_confirm_callback = on_confirm_callback
        self.selected_type = suggested_type

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        self.title("📝 确认文章写作类型")

        # 设置窗口大小并居中
        window_width = 800
        window_height = 850
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (window_width // 2)
        y = (self.winfo_screenheight() // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 设置最小窗口大小
        self.minsize(750, 800)

        # 主容器
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题区域
        title_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 10))

        header_label = ctk.CTkLabel(
            title_frame,
            text="🎯 选择文章写作类型",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        header_label.pack()

        # 生成的标题显示
        title_box = ctk.CTkFrame(main_container, fg_color="#1a1a1a", corner_radius=8)
        title_box.pack(fill="x", pady=(0, 10))

        title_label = ctk.CTkLabel(
            title_box,
            text="📋 生成的标题:",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        title_label.pack(anchor="w", padx=10, pady=(8, 2))

        title_text = ctk.CTkLabel(
            title_box,
            text=self.generated_title,
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=680,
            justify="left"
        )
        title_text.pack(anchor="w", padx=10, pady=(0, 8))

        # 系统推荐提示
        recommend_frame = ctk.CTkFrame(main_container, fg_color="#1a3d2e", corner_radius=8)
        recommend_frame.pack(fill="x", pady=(0, 15))

        confidence = self.classification_data.get("confidence", 0)
        reasons = self.classification_data.get("reasons", [])

        recommend_label = ctk.CTkLabel(
            recommend_frame,
            text=f"💡 系统推荐: {self.TYPE_INFO[self.suggested_type]['name']} (置信度: {confidence:.0%})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2CC985"
        )
        recommend_label.pack(anchor="w", padx=10, pady=(8, 4))

        if reasons:
            reason_text = "判断依据: " + ", ".join(reasons[:2])
            reason_label = ctk.CTkLabel(
                recommend_frame,
                text=reason_text,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            reason_label.pack(anchor="w", padx=10, pady=(0, 8))

        # 类型选择区域
        selection_label = ctk.CTkLabel(
            main_container,
            text="请选择写作类型（点击确认或修改）:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        selection_label.pack(anchor="w", pady=(0, 10))

        # 类型选择容器 - 使用普通 Frame，点击可以传递
        self.types_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.types_frame.pack(fill="x", pady=(0, 10))

        self.type_var = ctk.StringVar(value=self.suggested_type)
        self.type_cards = {}  # 保存卡片引用

        print(f"[DEBUG] 开始创建类型卡片,共 {len(self.TYPE_INFO)} 个")
        for type_key, type_info in self.TYPE_INFO.items():
            print(f"[DEBUG] 创建卡片: {type_key} - {type_info['name']}")
            type_card = self._create_type_card(self.types_frame, type_key, type_info)
            type_card.pack(fill="x", pady=3)
            self.type_cards[type_key] = type_card
        print(f"[DEBUG] 类型卡片创建完成")

        # 功能介绍区域
        intro_frame = ctk.CTkFrame(main_container, fg_color="#1a1a1a", corner_radius=8)
        intro_frame.pack(fill="x", pady=(0, 15))

        intro_header = ctk.CTkLabel(
            intro_frame,
            text="📖 写作类型说明",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        intro_header.pack(anchor="w", padx=10, pady=(10, 8))

        intro_text = """
• 顶梁柱型 (Pillar): 深度全面的内容，建立权威性，适合核心主题
• 回答型 (Response): 直接解决用户问题，高转化率，适合长尾关键词
• 分享型 (Share): 列表/排名/对比类内容，易被引用和分享

系统会根据选择的类型加载对应的写作提示词模板，确保内容风格匹配搜索意图。
        """
        intro_content = ctk.CTkLabel(
            intro_frame,
            text=intro_text.strip(),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left",
            wraplength=680
        )
        intro_content.pack(anchor="w", padx=10, pady=(0, 10))

        # 按钮区域 - 放在最后,使用正常的pack顺序
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))

        # 确认按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="✓ 确认选择，开始写作",
            command=self.on_confirm,
            height=45,
            width=200,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2CC985",
            hover_color="#24a37d"
        )
        confirm_btn.pack(side="left", padx=(0, 10))

        # 取消按钮
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            command=self.destroy,
            height=45,
            width=100,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="#666"
        )
        cancel_btn.pack(side="left")

    def _create_type_card(self, parent, type_key: str, type_info: dict):
        """创建类型选择卡片"""
        is_selected = type_key == self.suggested_type
        border_color = type_info["color"] if is_selected else "#444444"

        # 使用明显的背景色,确保卡片可见
        card = ctk.CTkFrame(
            parent,
            fg_color="#2a2a2a" if is_selected else "#1a1a1a",
            border_width=2,
            border_color=border_color,
            corner_radius=8,
            height=100  # 设置最小高度
        )

        # 单选按钮行
        radio_frame = ctk.CTkFrame(card, fg_color="transparent")
        radio_frame.pack(fill="x", padx=10, pady=(8, 4))

        radio = ctk.CTkRadioButton(
            radio_frame,
            text=f"{type_info['icon']} {type_info['name']}",
            variable=self.type_var,
            value=type_key,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._on_type_selected(type_key)
        )
        radio.pack(side="left")

        # 绑定点击事件到整个卡片
        def on_card_click(event):
            self.type_var.set(type_key)
            self._on_type_selected(type_key)

        # 字数标签
        word_label = ctk.CTkLabel(
            radio_frame,
            text=type_info["word_count"],
            font=ctk.CTkFont(size=10),
            text_color=type_info["color"]
        )
        word_label.pack(side="right")

        # 描述
        desc_label = ctk.CTkLabel(
            card,
            text=type_info["description"],
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        desc_label.pack(fill="x", padx=10, pady=(0, 4))

        # 搜索意图
        intent_label = ctk.CTkLabel(
            card,
            text=f"意图: {type_info['search_intent'][:50]}...",
            font=ctk.CTkFont(size=10),
            text_color="#666",
            anchor="w"
        )
        intent_label.pack(fill="x", padx=10, pady=(0, 8))

        # 绑定点击事件到卡片和所有子组件
        def bind_click_recursive(widget, depth=0):
            if depth > 3:  # 防止无限递归
                return
            widget.bind("<Button-1>", on_card_click)
            try:
                for child in widget.winfo_children():
                    bind_click_recursive(child, depth + 1)
            except Exception:
                pass

        bind_click_recursive(card)

        return card

    def _on_type_selected(self, type_key: str):
        """类型选择变化"""
        print(f"[DEBUG] 类型选择变化: {type_key}")
        self.selected_type = type_key

        # 更新所有卡片的样式
        for key, card in self.type_cards.items():
            is_selected = (key == type_key)
            type_info = self.TYPE_INFO[key]

            # 更新卡片边框和背景
            if is_selected:
                card.configure(
                    fg_color="#2a2a2a",
                    border_width=2,
                    border_color=type_info["color"]
                )
            else:
                card.configure(
                    fg_color="#1a1a1a",
                    border_width=2,
                    border_color="#444444"
                )

    def on_confirm(self):
        """确认选择"""
        selected_type = self.type_var.get()
        print(f"[DEBUG] 确认按钮被点击 - 选择的类型: {selected_type}")

        # 关闭对话框
        self.destroy()

        # 调用回调
        if self.on_confirm_callback:
            print(f"[DEBUG] 调用回调函数,传递类型: {selected_type}")
            self.on_confirm_callback(selected_type)


class KeywordQuestionsDialog(ctk.CTkToplevel):
    """关键词问答对话框 - 支持自定义输入"""

    def __init__(self, parent, keyword: str, questions_data: dict, on_confirm_callback):
        super().__init__(parent)
        self.keyword = keyword
        self.questions_data = questions_data
        self.on_confirm_callback = on_confirm_callback
        self.selected_answers = {}  # {question_id: answer_key}
        self.custom_inputs = {}  # {question_id: custom_text}
        self.custom_entry_widgets = {}  # {question_id: CTkEntry widget}
        self.option_keys_map = {}  # {question_id: [(opt_key, allow_custom), ...]}

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        self.title("关键词分析 - 确认文章策略")
        self.geometry("750x700")

        # 使窗口居中
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (750 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"750x700+{x}+{y}")

        # 主容器
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 标题 - 关键词分析结果
        type_label = ctk.CTkLabel(
            main_container,
            text=f"📊 关键词: {self.keyword}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        type_label.pack(pady=(0, 5))

        category_info = f"检测类型: {self.questions_data.get('type', 'unknown').upper()} | {self.questions_data.get('category', '')}"
        category_label = ctk.CTkLabel(
            main_container,
            text=category_info,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        category_label.pack(pady=(0, 15))

        # 说明文字
        instruction_label = ctk.CTkLabel(
            main_container,
            text="❓ 请回答以下3个问题以优化文章策略（基于 Google 搜索数据分析）",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        instruction_label.pack(pady=(0, 10))

        # 问题和选项容器
        questions_container = ctk.CTkScrollableFrame(main_container, height=420)
        questions_container.pack(fill="both", expand=True, pady=(0, 15))

        self.answer_vars = {}  # {question_id: StringVar}
        self.other_radio_commands = {}  # Store commands for "Other" radio buttons

        for question in self.questions_data.get("questions", []):
            q_id = question.get("id")
            q_text = question.get("question")
            options = question.get("options", [])

            # 问题标题
            q_label = ctk.CTkLabel(
                questions_container,
                text=f"{q_id}. {q_text}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            q_label.pack(fill="x", pady=(15, 8))

            # 选项容器
            options_frame = ctk.CTkFrame(questions_container, fg_color="transparent")
            options_frame.pack(fill="x", padx=(20, 0))

            # 单选按钮组
            answer_var = ctk.StringVar(value="")
            self.answer_vars[q_id] = answer_var

            # Track option keys and custom flag
            option_keys = []
            has_custom_option = False

            for i, option in enumerate(options):
                opt_key = option.get("key")
                opt_label = option.get("label")
                opt_desc = option.get("description", "")
                allow_custom = option.get("allow_custom", False)

                option_keys.append((opt_key, allow_custom))
                if allow_custom:
                    has_custom_option = True

                # 创建单选按钮
                radio = ctk.CTkRadioButton(
                    options_frame,
                    text=f"{opt_key}) {opt_label}",
                    variable=answer_var,
                    value=opt_key,
                    command=lambda qid=q_id, key=opt_key, custom=allow_custom: self._on_option_changed(qid, key, custom)
                )
                radio.pack(anchor="w", pady=(5, 0))

                # 描述文字
                desc_label = ctk.CTkLabel(
                    options_frame,
                    text=f"   {opt_desc}",
                    font=ctk.CTkFont(size=11),
                    text_color="gray",
                    anchor="w"
                )
                desc_label.pack(anchor="w", pady=(0, 5))

            # Store option info for this question
            self.option_keys_map[q_id] = option_keys

            # Custom input field (hidden by default, shown when "Other" selected)
            if has_custom_option:
                custom_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
                custom_frame.pack(fill="x", pady=(5, 8))

                custom_label = ctk.CTkLabel(
                    custom_frame,
                    text="   → 自定义内容:",
                    font=ctk.CTkFont(size=11),
                    text_color="#2CC985"
                )
                custom_label.pack(anchor="w")

                custom_entry = ctk.CTkEntry(
                    custom_frame,
                    placeholder_text="请输入自定义内容...",
                    height=32
                )
                custom_entry.pack(fill="x", padx=(20, 0))
                self.custom_entry_widgets[q_id] = custom_entry
                custom_frame.pack_forget()  # Initially hidden

        # 按钮区域
        button_frame = ctk.CTkFrame(main_container)
        button_frame.pack(fill="x", pady=(10, 0))

        # 确认按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="✓ 确认选择，开始生成",
            command=self.on_confirm,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2CC985",
            hover_color="#24a37d"
        )
        confirm_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))

        # 取消按钮
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            command=self.destroy,
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="gray",
            hover_color="#666"
        )
        cancel_btn.pack(side="left", expand=True, fill="x")

    def _on_option_changed(self, q_id: str, opt_key: str, allow_custom: bool):
        """选项改变时的回调"""
        # Show/hide custom input field
        if allow_custom:
            # Show custom input field
            # Find the custom frame (parent of the entry widget)
            if q_id in self.custom_entry_widgets:
                entry = self.custom_entry_widgets[q_id]
                # The custom_frame is the parent of the entry
                custom_frame = entry.master
                custom_frame.pack(fill="x", pady=(5, 8))
                # Focus the entry
                entry.focus()
        else:
            # Hide custom input field
            if q_id in self.custom_entry_widgets:
                entry = self.custom_entry_widgets[q_id]
                custom_frame = entry.master
                custom_frame.pack_forget()
                # Clear the entry
                entry.delete(0, "end")

    def on_confirm(self):
        """确认选择"""
        # 收集答案
        answers = {}
        custom_inputs = {}

        for q_id, var in self.answer_vars.items():
            answer = var.get()
            if not answer:
                messagebox.showwarning("提示", f"请完成问题 {q_id} 的选择")
                return

            # Check if this is a custom option
            option_keys = self.option_keys_map.get(q_id, [])
            is_custom = False
            for opt_key, allow_custom in option_keys:
                if opt_key == answer and allow_custom:
                    is_custom = True
                    # Get custom input value
                    if q_id in self.custom_entry_widgets:
                        custom_value = self.custom_entry_widgets[q_id].get().strip()
                        if not custom_value:
                            messagebox.showwarning("提示", f"问题 {q_id} 选择了'其他'，请输入自定义内容")
                            return
                        custom_inputs[str(q_id)] = custom_value
                    break

            answers[str(q_id)] = answer

        # 关闭对话框
        self.destroy()

        # 调用回调 - 传递答案和自定义输入
        if self.on_confirm_callback:
            self.on_confirm_callback(answers, custom_inputs)


class ScrollableFrame(ctk.CTkScrollableFrame):
    """可滚动框架"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)


class ContentGeneratorGUI(ctk.CTk):
    """SEO 内容生成器 GUI"""

    def __init__(self):
        super().__init__()

        self.title("SEO 内容生成器 v2.0 - ASG 智能版")
        self.geometry("1300x750")

        # 设置外观
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # 工作流编排器
        self.orchestrator = None

        # 历史记录文件
        self.history_file = Path("gui_history.json")
        self.history_data = self.load_history()

        # UI 更新队列（线程安全）
        self.update_queue = Queue()

        # 批量生成状态变量
        self.batch_keywords_queue = []
        self.batch_current_index = 0
        self.batch_total_count = 0
        self.batch_image_style = "modern"
        self.batch_include_images = True
        self.batch_include_wp = True

        # 启动 UI 更新检查
        self.after(100, self.process_update_queue)

        # 构建界面
        self.setup_ui()

    @staticmethod
    def get_image_style_key(chinese_style: str) -> str:
        """将中文风格名称转换为英文key"""
        style_map = {
            "现代": "modern",
            "极简": "minimalist",
            "专业": "professional",
            "创意": "creative",
            "科技": "tech",
            "自然": "nature",
            "优雅": "elegant",
            "活泼": "playful",
        }
        return style_map.get(chinese_style, "modern")

    @staticmethod
    def get_platform_key(chinese_platform: str) -> str:
        """将中文平台名称转换为英文key"""
        platform_map = {
            "文章": "article",
            "TikTok": "tiktok",
            "YouTube": "youtube",
            "Facebook": "facebook",
            "LinkedIn": "linkedin",
            "X": "x",
            "Reddit": "reddit",
            "Instagram": "instagram",
            "Pinterest": "pinterest",
        }
        return platform_map.get(chinese_platform, "article")

    @staticmethod
    def get_platform_steps(platform_key: str) -> list:
        """获取不同平台的执行步骤"""
        # 文章平台 - 完整的两阶段工作流
        if platform_key == "article":
            return [
                "等待开始...",
                "分析 SERP (10-20秒)",
                "生成标题 (10-15秒)",
                "分析文章结构 (10-15秒)",
                "生成大纲 (15-20秒)",
                "撰写内容 (20-30秒)",
                "检测质量 (10-15秒)",
                "AI/原创检测 (5-10秒)",
                "生成配图 (30-60秒)",
                "保存文件 (2-5秒)",
                "发布 WordPress (10-20秒)"
            ]

        # 社交媒体平台 - 简化的工作流
        social_steps = [
            "等待开始...",
            "关键词 SERP 分析 (10-15秒)",
            "生成策略问题 (5-10秒)",
        ]

        # 根据平台添加定制步骤
        if platform_key == "tiktok":
            social_steps.extend([
                "创作 TikTok 钩子 (10-15秒)",
                "生成 TikTok 文案 (15-20秒)",
                "生成 Hashtag (5-10秒)",
            ])
        elif platform_key == "youtube":
            social_steps.extend([
                "创作视频标题 (10-15秒)",
                "生成视频文案 (15-20秒)",
                "生成 Hashtag (5-10秒)",
            ])
        elif platform_key == "facebook":
            social_steps.extend([
                "创作帖子标题 (10-15秒)",
                "生成 Facebook 文案 (15-20秒)",
                "生成 Hashtag (5-10秒)",
            ])
        elif platform_key == "linkedin":
            social_steps.extend([
                "创作专业标题 (10-15秒)",
                "生成 LinkedIn 文案 (15-20秒)",
            ])
        elif platform_key == "x":
            social_steps.extend([
                "创作 X 帖子 (15-20秒)",
                "优化推文格式 (5-10秒)",
            ])
        elif platform_key == "reddit":
            social_steps.extend([
                "创作 Reddit 帖子 (15-20秒)",
                "生成讨论引导 (5-10秒)",
            ])
        elif platform_key == "instagram":
            social_steps.extend([
                "创作 Instagram 文案 (15-20秒)",
                "生成 Hashtag (5-10秒)",
            ])
        elif platform_key == "pinterest":
            social_steps.extend([
                "创作 Pin 描述 (15-20秒)",
                "生成关键词标签 (5-10秒)",
            ])

        # 通用收尾步骤
        social_steps.extend([
            "生成配图 (30-60秒)",
            "保存文件 (2-5秒)",
        ])

        return social_steps

    def _on_platform_changed(self, choice: str):
        """平台选择变化回调"""
        platform_key = self.get_platform_key(choice)

        # 更新按钮文本
        if platform_key == "article":
            self.start_btn.configure(text="🚀 开始生成文章")
            # 显示 WordPress 发布选项
            self.wp_checkbox.pack(side="left", padx=(0, 15))
        else:
            self.start_btn.configure(text=f"🚀 开始生成{choice}内容")
            # 隐藏 WordPress 发布选项
            self.wp_checkbox.pack_forget()

        # 更新执行步骤显示
        self.update_steps_for_platform(platform_key)

    def _on_mode_changed(self):
        """创作模式变化回调"""
        mode = self.content_mode_var.get()
        if mode == "rewrite":
            # 显示二创输入框
            self.rewrite_frame.pack(fill="x", pady=(0, 10), after=self.keyword_entry)
        else:
            # 隐藏二创输入框
            self.rewrite_frame.pack_forget()

    def _is_url(self, text: str) -> bool:
        """检查文本是否为网址"""
        text = text.strip()
        if not text:
            return False

        # 简单的 URL 检测
        url_patterns = [
            r'^https?://',  # http:// 或 https:// 开头
            r'^www\.',       # www. 开头
            r'\.com$',       # .com 结尾
            r'\.net$',       # .net 结尾
            r'\.org$',       # .org 结尾
            r'\.io$',        # .io 结尾
            r'\.co$',        # .co 结尾
        ]

        for pattern in url_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def copy_generated_content(self):
        """复制生成的内容到剪贴板"""
        if not self.generated_copy_text:
            messagebox.showinfo("提示", "暂无可复制的内容")
            return

        try:
            import pyperclip
            pyperclip.copy(self.generated_copy_text)
            self.copy_btn.configure(text="✓ 已复制")
            self.after(2000, lambda: self.copy_btn.configure(text="📋 复制内容"))
        except ImportError:
            # 如果没有 pyperclip，使用 tkinter
            self.clipboard_clear()
            self.clipboard_append(self.generated_copy_text)
            self.update()
            self.copy_btn.configure(text="✓ 已复制")
            self.after(2000, lambda: self.copy_btn.configure(text="📋 复制内容"))

    def progress_callback(self, update_type, data):
        """工作流进度回调函数（从后台线程调用）"""
        self.update_queue.put((update_type, data))

    def setup_ui(self):
        """构建界面"""
        # 标题
        title_label = ctk.CTkLabel(
            self,
            text="SEO 内容生成器 v1.0",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(15, 5))

        # 选项卡
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        # 创建选项卡
        self.create_single_tab()
        self.create_batch_tab()
        self.create_history_tab()

        # 底部状态栏
        self.status_bar = ctk.CTkLabel(self, text="就绪", anchor="w")
        self.status_bar.pack(side="bottom", fill="x", padx=15, pady=(5, 10))

    def create_single_tab(self):
        """创建单个生成选项卡"""
        tab = self.tabview.add("单个生成")

        # 功能提示横幅
        banner_frame = ctk.CTkFrame(tab, fg_color="#1a3d2e", corner_radius=8)
        banner_frame.pack(fill="x", padx=15, pady=(15, 5))

        banner_content = ctk.CTkLabel(
            banner_frame,
            text="✨ 新功能：智能文章类型选择 - 系统会根据关键词自动推荐顶梁柱型/回答型/分享型，您可以在生成前确认或修改",
            font=ctk.CTkFont(size=11),
            text_color="#2CC985"
        )
        banner_content.pack(padx=10, pady=8)

        # 上部：输入和按钮区域
        top_frame = ctk.CTkFrame(tab)
        top_frame.pack(fill="x", padx=15, pady=15)

        # 第一行：平台选择和创作模式
        top_row = ctk.CTkFrame(top_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))

        # 平台选择
        platform_label = ctk.CTkLabel(top_row, text="写作方向:", font=ctk.CTkFont(size=13, weight="bold"))
        platform_label.pack(side="left", padx=(0, 5))

        self.platform_var = ctk.StringVar(value="article")
        platform_options = ["文章", "TikTok", "YouTube", "Facebook", "LinkedIn", "X", "Reddit", "Instagram", "Pinterest"]
        self.platform_menu = ctk.CTkOptionMenu(
            top_row,
            values=platform_options,
            variable=self.platform_var,
            width=120,
            height=32,
            font=ctk.CTkFont(size=12),
            command=self._on_platform_changed
        )
        self.platform_menu.pack(side="left", padx=(0, 20))

        # 创作模式
        mode_label = ctk.CTkLabel(top_row, text="创作模式:", font=ctk.CTkFont(size=13, weight="bold"))
        mode_label.pack(side="left", padx=(0, 5))

        self.content_mode_var = ctk.StringVar(value="original")
        self.original_radio = ctk.CTkRadioButton(
            top_row,
            text="原创",
            variable=self.content_mode_var,
            value="original",
            command=self._on_mode_changed,
            font=ctk.CTkFont(size=12)
        )
        self.original_radio.pack(side="left", padx=(0, 15))

        self.rewrite_radio = ctk.CTkRadioButton(
            top_row,
            text="二创",
            variable=self.content_mode_var,
            value="rewrite",
            command=self._on_mode_changed,
            font=ctk.CTkFont(size=12)
        )
        self.rewrite_radio.pack(side="left")

        # 关键词输入
        keyword_label = ctk.CTkLabel(top_frame, text="关键词:", font=ctk.CTkFont(size=13, weight="bold"))
        keyword_label.pack(anchor="w", pady=(0, 5))

        self.keyword_entry = ctk.CTkEntry(
            top_frame,
            placeholder_text="输入要生成内容的关键词...",
            height=38
        )
        self.keyword_entry.pack(fill="x", pady=(0, 10))

        # 二创输入框（默认隐藏）
        self.rewrite_frame = ctk.CTkFrame(top_frame)
        # 不pack，默认隐藏

        rewrite_label = ctk.CTkLabel(self.rewrite_frame, text="对标内容或网址:", font=ctk.CTkFont(size=12, weight="bold"))
        rewrite_label.pack(anchor="w", pady=(0, 5))

        self.rewrite_entry = ctk.CTkTextbox(
            self.rewrite_frame,
            height=80,
            font=ctk.CTkFont(size=12)
        )
        self.rewrite_entry.pack(fill="x", pady=(0, 5))

        rewrite_hint = ctk.CTkLabel(
            self.rewrite_frame,
            text="💡 提示：可以直接粘贴对标文案，或输入网址（系统会自动抓取）",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        rewrite_hint.pack(anchor="w")

        # 选项复选框
        options_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 10))

        self.include_images_var = ctk.BooleanVar(value=True)
        self.include_wp_var = ctk.BooleanVar(value=True)
        self.image_style_var = ctk.StringVar(value="modern")

        ctk.CTkCheckBox(
            options_frame,
            text="生成图片",
            variable=self.include_images_var,
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 15))

        # 只在选择"文章"时显示 WordPress 发布选项
        self.wp_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="发布到 WordPress",
            variable=self.include_wp_var,
            font=ctk.CTkFont(size=12)
        )
        self.wp_checkbox.pack(side="left", padx=(0, 15))

        # 图片风格选择器
        style_label = ctk.CTkLabel(options_frame, text="图片风格:", font=ctk.CTkFont(size=12))
        style_label.pack(side="left", padx=(0, 5))

        style_options = ["现代", "极简", "专业", "创意", "科技", "自然", "优雅", "活泼"]
        self.image_style_menu = ctk.CTkOptionMenu(
            options_frame,
            values=style_options,
            variable=self.image_style_var,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.image_style_menu.pack(side="left")

        # 开始按钮
        self.start_btn = ctk.CTkButton(
            top_frame,
            text="🚀 开始生成文章",
            command=self.start_single_generation,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2CC985",
            hover_color="#24a37d"
        )
        self.start_btn.pack(fill="x", pady=(5, 15))

        # 下部：输出显示区域（三栏布局）
        output_frame = ctk.CTkFrame(tab)
        output_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ========== 左侧：进度和步骤 ==========
        left_panel = ctk.CTkFrame(output_frame)
        left_panel.pack(side="left", fill="both", expand=False, padx=(0, 6))

        # 进度条
        progress_label = ctk.CTkLabel(left_panel, text="生成进度", font=ctk.CTkFont(size=13, weight="bold"))
        progress_label.pack(anchor="w", pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(left_panel)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # 步骤指示器
        steps_label = ctk.CTkLabel(left_panel, text="执行步骤", font=ctk.CTkFont(size=13, weight="bold"))
        steps_label.pack(anchor="w", pady=(5, 5))

        self.steps_container = ctk.CTkScrollableFrame(left_panel, height=300, width=220)
        self.steps_container.pack(fill="both", expand=True, pady=(0, 10))

        self.step_labels = []
        # 使用默认文章平台步骤初始化
        steps = self.get_platform_steps("article")

        for i, step in enumerate(steps):
            label = ctk.CTkLabel(
                self.steps_container,
                text=f"○ {step}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="#2CC985" if i == 0 else "gray"
            )
            label.pack(fill="x", pady=3)
            self.step_labels.append(label)

        # ========== 中间：终端输出 ==========
        center_panel = ctk.CTkFrame(output_frame)
        center_panel.pack(side="left", fill="both", expand=True, padx=6)

        # 标题和复制按钮行
        header_row = ctk.CTkFrame(center_panel, fg_color="transparent")
        header_row.pack(fill="x", pady=(10, 5))

        log_label = ctk.CTkLabel(header_row, text="📟 生成内容", font=ctk.CTkFont(size=13, weight="bold"))
        log_label.pack(side="left")

        self.copy_btn = ctk.CTkButton(
            header_row,
            text="📋 复制内容",
            command=self.copy_generated_content,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.copy_btn.pack(side="right")

        self.log_text = ctk.CTkTextbox(
            center_panel,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#00ff00",
            fg_color="#1a1a1a"
        )
        self.log_text.pack(fill="both", expand=True, pady=(0, 10))
        self.log_text.insert("1.0", "等待生成开始...\n\n")
        self.log_text.configure(state="disabled")

        # 存储生成的可复制内容
        self.generated_copy_text = ""

        # ========== 右侧：质量报告 ==========
        right_panel = ctk.CTkFrame(output_frame)
        right_panel.pack(side="right", fill="both", expand=False, padx=(6, 0))

        result_label = ctk.CTkLabel(right_panel, text="📊 质量报告", font=ctk.CTkFont(size=13, weight="bold"))
        result_label.pack(anchor="w", pady=(10, 5))

        self.result_text = ctk.CTkTextbox(
            right_panel,
            font=ctk.CTkFont(size=11),
            width=320
        )
        self.result_text.pack(fill="both", expand=True, pady=(0, 10))
        self.result_text.insert("1.0", "完成生成后将在此显示详细报告...")
        self.result_text.configure(state="disabled")

    def create_batch_tab(self):
        """创建批量生成选项卡"""
        tab = self.tabview.add("批量生成")

        # 输入框架
        input_frame = ctk.CTkFrame(tab)
        input_frame.pack(fill="x", padx=15, pady=15)

        # 关键词输入
        label = ctk.CTkLabel(input_frame, text="批量关键词 (每行一个):", font=ctk.CTkFont(size=13, weight="bold"))
        label.pack(anchor="w", pady=(0, 5))

        self.batch_text = ctk.CTkTextbox(
            input_frame,
            height=120,
            font=ctk.CTkFont(size=12)
        )
        self.batch_text.pack(fill="x", pady=(0, 10))
        self.batch_text.insert("1.0", "dropshipping automation\nshopify optimization\necommerce automation trends\n")

        # 选项
        options_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 10))

        self.batch_images_var = ctk.BooleanVar(value=True)
        self.batch_wp_var = ctk.BooleanVar(value=True)
        self.batch_image_style_var = ctk.StringVar(value="modern")

        ctk.CTkCheckBox(
            options_frame,
            text="生成图片",
            variable=self.batch_images_var,
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 15))

        ctk.CTkCheckBox(
            options_frame,
            text="发布到 WordPress",
            variable=self.batch_wp_var,
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 15))

        # 图片风格选择器
        batch_style_label = ctk.CTkLabel(options_frame, text="图片风格:", font=ctk.CTkFont(size=12))
        batch_style_label.pack(side="left", padx=(0, 5))

        style_options = ["现代", "极简", "专业", "创意", "科技", "自然", "优雅", "活泼"]
        self.batch_image_style_menu = ctk.CTkOptionMenu(
            options_frame,
            values=style_options,
            variable=self.batch_image_style_var,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        self.batch_image_style_menu.pack(side="left")

        # 批量生成按钮
        batch_btn = ctk.CTkButton(
            input_frame,
            text="🚀 批量生成文章",
            command=self.start_batch_generation,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2CC985",
            hover_color="#24a37d"
        )
        batch_btn.pack(fill="x", pady=(5, 15))

        # 下部：输出显示区域（三栏布局）
        output_frame = ctk.CTkFrame(tab)
        output_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ========== 左侧：进度和步骤 ==========
        left_panel = ctk.CTkFrame(output_frame)
        left_panel.pack(side="left", fill="both", expand=False, padx=(0, 6))

        progress_label = ctk.CTkLabel(left_panel, text="生成进度", font=ctk.CTkFont(size=13, weight="bold"))
        progress_label.pack(anchor="w", pady=(10, 5))

        self.batch_progress_bar = ctk.CTkProgressBar(left_panel)
        self.batch_progress_bar.pack(fill="x", pady=(0, 10))

        steps_label = ctk.CTkLabel(left_panel, text="执行步骤", font=ctk.CTkFont(size=13, weight="bold"))
        steps_label.pack(anchor="w", pady=(5, 5))

        self.batch_steps_container = ctk.CTkScrollableFrame(left_panel, height=300, width=220)
        self.batch_steps_container.pack(fill="both", expand=True, pady=(0, 10))

        # ========== 中间：终端输出 ==========
        center_panel = ctk.CTkFrame(output_frame)
        center_panel.pack(side="left", fill="both", expand=True, padx=6)

        log_label = ctk.CTkLabel(center_panel, text="📟 终端输出", font=ctk.CTkFont(size=13, weight="bold"))
        log_label.pack(anchor="w", pady=(10, 5))

        self.batch_log_text = ctk.CTkTextbox(
            center_panel,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#00ff00",
            fg_color="#1a1a1a"
        )
        self.batch_log_text.pack(fill="both", expand=True, pady=(0, 10))
        self.batch_log_text.insert("1.0", "等待批量生成开始...\n\n")
        self.batch_log_text.configure(state="disabled")

        # ========== 右侧：质量报告 ==========
        right_panel = ctk.CTkFrame(output_frame)
        right_panel.pack(side="right", fill="both", expand=False, padx=(6, 0))

        result_label = ctk.CTkLabel(right_panel, text="📊 质量报告", font=ctk.CTkFont(size=13, weight="bold"))
        result_label.pack(anchor="w", pady=(10, 5))

        self.batch_result_text = ctk.CTkTextbox(
            right_panel,
            font=ctk.CTkFont(size=11),
            width=320
        )
        self.batch_result_text.pack(fill="both", expand=True, pady=(0, 10))
        self.batch_result_text.insert("1.0", "完成生成后将在此显示详细报告...")
        self.batch_result_text.configure(state="disabled")

    def create_history_tab(self):
        """创建历史记录选项卡"""
        tab = self.tabview.add("历史记录")

        # 历史记录表格 - 增加更多列
        columns = ("keyword", "date", "grade", "score", "wp_link", "action")
        self.history_tree = ttk.Treeview(tab, columns=columns, show="headings", height=400)

        self.history_tree.heading("keyword", text="关键词")
        self.history_tree.heading("date", text="日期")
        self.history_tree.heading("grade", text="等级")
        self.history_tree.heading("score", text="分数")
        self.history_tree.heading("wp_link", text="WordPress链接")
        self.history_tree.heading("action", text="操作")

        self.history_tree.column("keyword", width=250)
        self.history_tree.column("date", width=140)
        self.history_tree.column("grade", width=70)
        self.history_tree.column("score", width=70)
        self.history_tree.column("wp_link", width=280)
        self.history_tree.column("action", width=90)

        self.history_tree.pack(fill="both", expand=True, padx=15, pady=15)

        # 绑定双击查看详情
        self.history_tree.bind("<Double-1>", self.view_history_detail)

        # 底部按钮区域
        button_frame = ctk.CTkFrame(tab)
        button_frame.pack(side="bottom", fill="x", padx=15, pady=10)

        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 刷新",
            command=self.refresh_history,
            height=38,
            width=120
        )
        refresh_btn.pack(side="left", padx=(0, 10))

        open_folder_btn = ctk.CTkButton(
            button_frame,
            text="📁 打开输出文件夹",
            command=self.open_outputs_folder,
            height=38,
            width=150
        )
        open_folder_btn.pack(side="left")

        # 加载历史记录
        self.refresh_history()

    def process_update_queue(self):
        """处理 UI 更新队列（从工作线程到主线程）"""
        try:
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()

                if update_type == "step":
                    # data = (step_index, status, message, progress)
                    step_index, status, message, progress = data
                    self.update_step_label(step_index, status, message)
                    self.progress_bar.set(progress)
                    if hasattr(self, 'batch_progress_bar'):
                        self.batch_progress_bar.set(progress)
                    self.status_bar.configure(text=message)

                elif update_type == "log":
                    # 添加到终端输出
                    log_message = data
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", log_message + "\n")
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")

                    # 也更新批量日志
                    if hasattr(self, 'batch_log_text'):
                        self.batch_log_text.configure(state="normal")
                        self.batch_log_text.insert("end", log_message + "\n")
                        self.batch_log_text.see("end")
                        self.batch_log_text.configure(state="disabled")

                elif update_type == "result":
                    result, keyword = data
                    self.display_result(result, keyword)
                    # 也显示在批量结果区域
                    if hasattr(self, 'batch_result_text'):
                        self.display_result_to(result, keyword, self.batch_result_text)

                elif update_type == "error":
                    error_msg = data
                    self.result_text.configure(state="normal")
                    self.result_text.delete("1.0", "end")
                    self.result_text.insert("1.0", f"❌ 生成失败:\n\n{error_msg}")
                    self.result_text.configure(state="disabled")

                    if hasattr(self, 'batch_result_text'):
                        self.batch_result_text.configure(state="normal")
                        self.batch_result_text.delete("1.0", "end")
                        self.batch_result_text.insert("1.0", f"❌ 生成失败:\n\n{error_msg}")
                        self.batch_result_text.configure(state="disabled")

                elif update_type == "status":
                    status_text = data
                    self.status_bar.configure(text=status_text)

        except:
            pass

        # 继续检查队列
        self.after(100, self.process_update_queue)

    def update_step_label(self, step_index, status, message):
        """更新步骤标签"""
        if step_index < len(self.step_labels):
            icons = {"pending": "○", "running": "●", "completed": "✓"}
            colors = {"pending": "gray", "running": "#FFA500", "completed": "#2CC985"}

            icon = icons.get(status, "○")
            color = colors.get(status, "gray")

            self.step_labels[step_index].configure(
                text=f"{icon} {message}",
                text_color=color
            )

    def update_steps_for_platform(self, platform_key: str):
        """根据平台更新执行步骤显示"""
        steps = self.get_platform_steps(platform_key)

        # 清除现有步骤标签
        for label in self.step_labels:
            label.destroy()
        self.step_labels.clear()

        # 创建新的步骤标签
        for i, step in enumerate(steps):
            label = ctk.CTkLabel(
                self.steps_container,
                text=f"○ {step}",
                font=ctk.CTkFont(size=12),
                anchor="w",
                text_color="gray" if i > 0 else "#2CC985"
            )
            label.pack(fill="x", pady=3)
            self.step_labels.append(label)

    def reset_steps(self):
        """重置步骤显示"""
        platform_key = self.get_platform_key(self.platform_var.get())
        steps = self.get_platform_steps(platform_key)

        for i, (label, default_text) in enumerate(zip(self.step_labels, steps)):
            label.configure(text=default_text, text_color="#2CC985" if i == 0 else "gray")

        self.progress_bar.set(0)
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "开始生成...\n\n正在处理，请稍候...")
        self.result_text.configure(state="disabled")

    def start_single_generation(self):
        """开始单个关键词生成"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入关键词")
            return

        # 获取平台和模式
        platform = self.get_platform_key(self.platform_var.get())
        mode = self.content_mode_var.get()

        # 获取二创内容（如果是二创模式）
        rewrite_content = None
        if mode == "rewrite":
            rewrite_content = self.rewrite_entry.get("1.0", "end-1c").strip()
            if not rewrite_content:
                messagebox.showwarning("提示", "请输入对标内容或网址")
                return

        # 获取图片风格
        image_style = self.get_image_style_key(self.image_style_var.get())

        # 步骤1：分析关键词
        self.progress_callback("log", f"正在分析关键词: {keyword}...")

        def analyze_and_show_questions():
            """分析关键词并显示问题对话框"""
            import asyncio

            # 在后台线程中分析关键词
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                analyzer = get_keyword_analyzer()
                questions_data = loop.run_until_complete(analyzer.analyze(keyword, platform=platform))

                # 在主线程中显示对话框
                def show_dialog():
                    dialog = KeywordQuestionsDialog(
                        self,
                        keyword,
                        questions_data,
                        on_confirm_callback=lambda answers, custom_inputs: self._proceed_with_generation(
                            keyword, platform, mode, rewrite_content, answers, custom_inputs, questions_data, image_style
                        )
                    )
                    # 等待对话框关闭
                    self.wait_window(dialog)

                self.after(0, show_dialog)

            except Exception as e:
                loop.close()
                # 如果分析失败，直接开始生成
                self.progress_callback("log", f"关键词分析失败，使用默认设置: {e}")
                self._proceed_with_generation(keyword, {}, {}, image_style)
            finally:
                loop.close()

        # 在后台线程中分析
        thread = Thread(target=analyze_and_show_questions, daemon=True)
        thread.start()

    def _proceed_with_generation(self, keyword: str, platform: str, mode: str, rewrite_content: str,
                                answers: dict, custom_inputs: dict, questions_data: dict, image_style: str):
        """确认答案后继续生成"""
        # 禁用按钮
        self.keyword_entry.configure(state="disabled")

        # 重置步骤显示
        self.reset_steps()

        # 清空日志
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", f"开始生成文章: {keyword}\n{'='*50}\n\n")

        # 显示用户选择的答案
        if answers:
            self.log_text.insert("end", "📋 文章策略配置:\n")
            for q_id, answer in answers.items():
                q = next((q for q in questions_data.get("questions", []) if q.get("id") == int(q_id)), None)
                if q:
                    # Check if this is a custom answer
                    if answer.startswith("CUSTOM:"):
                        custom_value = custom_inputs.get(q_id, "")
                        self.log_text.insert("end", f"  • {q.get('question')}: [自定义] {custom_value}\n")
                    else:
                        opt = next((o for o in q.get("options", []) if o.get("key") == answer), None)
                        if opt:
                            self.log_text.insert("end", f"  • {q.get('question')}: {opt.get('label')}\n")
            self.log_text.insert("end", "\n" + "="*50 + "\n\n")
        self.log_text.configure(state="disabled")

        # 对于文章平台，先进行分类并生成标题，然后弹出类型确认对话框
        if platform == "article":
            self._analyze_and_confirm_type(keyword, platform, mode, rewrite_content, answers,
                                          custom_inputs, questions_data, image_style)
        else:
            # 其他平台直接开始生成
            thread = Thread(
                target=self.run_single_generation,
                args=(keyword, platform, mode, rewrite_content, self.include_images_var.get(),
                      self.include_wp_var.get(), image_style, answers, custom_inputs, questions_data, None),
                daemon=True
            )
            thread.start()

    def _analyze_and_confirm_type(self, keyword: str, platform: str, mode: str, rewrite_content: str,
                                  answers: dict, custom_inputs: dict, questions_data: dict, image_style: str):
        """分析关键词并弹出类型确认对话框"""

        def do_analysis():
            """在后台线程中进行分类和标题生成"""
            import asyncio
            from seo_gen.modules.content_classifier import ContentClassifier
            from seo_gen.modules.title import TitleGenerator
            from seo_gen.modules.serp import SERPAnalyzer
            from seo_gen.modules.llm import LLMClient

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 1. 进行文章类型分类
                self.progress_callback("log", "🔍 正在分析关键词类型...")
                classifier = ContentClassifier()
                classification_result = classifier.classify(keyword)

                # 2. 获取 SERP 数据用于标题生成
                self.progress_callback("log", "📊 正在获取 SERP 数据...")
                llm_client = LLMClient()
                serp_analyzer = SERPAnalyzer(llm_client)
                serp_data = loop.run_until_complete(serp_analyzer.analyze(keyword))

                # 3. 生成候选标题
                self.progress_callback("log", "✏️ 正在生成候选标题...")
                title_generator = TitleGenerator(llm_client)
                title_candidates = loop.run_until_complete(
                    title_generator.generate_titles(keyword=keyword, serp_data=serp_data, count=5)
                )

                # 4. 选择最佳标题
                best_title = loop.run_until_complete(
                    title_generator.select_best_title(titles=title_candidates, serp_data=serp_data)
                )
                final_title = best_title.get("title", keyword)

                self.progress_callback("log", f"✓ 标题生成完成: {final_title}")

                # 5. 在主线程中显示类型确认对话框
                def show_type_dialog():
                    print(f"[DEBUG] 显示类型确认对话框 - 关键词: {keyword}, 推荐类型: {classification_result.article_type.value}")
                    dialog = ArticleTypeConfirmDialog(
                        self,
                        keyword=keyword,
                        suggested_type=classification_result.article_type.value,
                        classification_data={
                            "confidence": classification_result.confidence,
                            "reasons": classification_result.reasons,
                            "search_intent": classification_result.search_intent,
                            "recommended_word_count": classification_result.recommended_word_count,
                        },
                        generated_title=final_title,
                        on_confirm_callback=lambda selected_type: self._on_type_confirmed(
                            keyword, platform, mode, rewrite_content, answers, custom_inputs,
                            questions_data, image_style, selected_type, final_title
                        )
                    )
                    dialog.focus()  # 确保对话框获得焦点
                    print(f"[DEBUG] 对话框已创建并显示")

                self.after(0, show_type_dialog)

            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
                self.progress_callback("log", f"❌ 分析失败: {error_msg}")
                # 失败时直接使用默认类型开始生成
                self.after(0, lambda: self._on_type_confirmed(
                    keyword, platform, mode, rewrite_content, answers, custom_inputs,
                    questions_data, image_style, None, keyword
                ))
            finally:
                loop.close()

        # 在后台线程中执行分析
        thread = Thread(target=do_analysis, daemon=True)
        thread.start()

    def _on_type_confirmed(self, keyword: str, platform: str, mode: str, rewrite_content: str,
                          answers: dict, custom_inputs: dict, questions_data: dict, image_style: str,
                          confirmed_type: str, generated_title: str):
        """用户确认类型后的回调"""
        self.progress_callback("log", f"\n{'='*50}")
        self.progress_callback("log", f"📝 确认写作类型: {confirmed_type or '自动检测'}")
        self.progress_callback("log", f"📋 使用标题: {generated_title}")
        self.progress_callback("log", f"{'='*50}\n")

        # 开始正式生成
        thread = Thread(
            target=self.run_single_generation,
            args=(keyword, platform, mode, rewrite_content, self.include_images_var.get(),
                  self.include_wp_var.get(), image_style, answers, custom_inputs, questions_data, confirmed_type),
            daemon=True
        )
        thread.start()

    def start_batch_generation(self):
        """开始批量生成 - 使用单个生成的完整流程"""
        keywords_text = self.batch_text.get("1.0", "end-1c").strip()
        keywords = [k.strip() for k in keywords_text.split("\n") if k.strip()]

        if not keywords:
            messagebox.showwarning("提示", "请输入至少一个关键词")
            return

        # 清空文本框
        self.batch_text.delete("1.0", "end")

        # 保存批量关键词列表和设置
        self.batch_keywords_queue = keywords.copy()
        self.batch_current_index = 0
        self.batch_total_count = len(keywords)
        self.batch_image_style = self.get_image_style_key(self.batch_image_style_var.get())
        self.batch_include_images = self.batch_images_var.get()
        self.batch_include_wp = self.batch_wp_var.get()

        # 开始处理第一个关键词
        self._process_next_batch_keyword()

    def _process_next_batch_keyword(self):
        """处理批量队列中的下一个关键词 - 使用单个生成的完整流程"""
        if self.batch_current_index >= self.batch_total_count:
            # 所有关键词处理完成
            self.progress_callback("status", f"批量生成完成！共 {self.batch_total_count} 篇文章")
            self.after(0, lambda: messagebox.showinfo("完成", f"批量生成完成！\n共生成 {self.batch_total_count} 篇文章"))
            return

        keyword = self.batch_keywords_queue[self.batch_current_index]
        self.progress_callback("status", f"批量生成 [{self.batch_current_index + 1}/{self.batch_total_count}]: {keyword}")
        self.progress_callback("log", f"\n{'='*60}")
        self.progress_callback("log", f"📝 开始处理关键词 [{self.batch_current_index + 1}/{self.batch_total_count}]: {keyword}")
        self.progress_callback("log", f"{'='*60}\n")

        # 使用单个生成的流程：先分析关键词，显示策略问题对话框
        self._batch_analyze_keyword(keyword)

    def _batch_analyze_keyword(self, keyword: str):
        """批量模式：分析关键词并显示问题对话框"""
        import asyncio

        def analyze_and_show_questions():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                analyzer = get_keyword_analyzer()
                questions_data = loop.run_until_complete(analyzer.analyze(keyword, platform="article"))

                # 在主线程中显示对话框
                def show_dialog():
                    dialog = KeywordQuestionsDialog(
                        self,
                        keyword,
                        questions_data,
                        on_confirm_callback=lambda answers, custom_inputs: self._batch_proceed_with_generation(
                            keyword, answers, custom_inputs, questions_data
                        )
                    )
                    self.wait_window(dialog)

                self.after(0, show_dialog)

            except Exception as e:
                loop.close()
                self.progress_callback("log", f"关键词分析失败，使用默认设置: {e}")
                self._batch_proceed_with_generation(keyword, {}, {}, {})
            finally:
                loop.close()

        thread = Thread(target=analyze_and_show_questions, daemon=True)
        thread.start()

    def _batch_proceed_with_generation(self, keyword: str, answers: dict, custom_inputs: dict, questions_data: dict):
        """批量模式：确认答案后继续生成"""
        # 重置步骤显示
        self.reset_steps()

        # 显示用户选择的答案
        if answers:
            self.progress_callback("log", "📋 文章策略配置:")
            for q_id, answer in answers.items():
                q = next((q for q in questions_data.get("questions", []) if q.get("id") == int(q_id)), None)
                if q:
                    if answer.startswith("CUSTOM:"):
                        custom_value = custom_inputs.get(q_id, "")
                        self.progress_callback("log", f"  • {q.get('question')}: [自定义] {custom_value}")
                    else:
                        opt = next((o for o in q.get("options", []) if o.get("key") == answer), None)
                        if opt:
                            self.progress_callback("log", f"  • {q.get('question')}: {opt.get('label')}")

        # 进行文章类型分类和标题生成
        self._batch_analyze_and_confirm_type(keyword, answers, custom_inputs, questions_data)

    def _batch_analyze_and_confirm_type(self, keyword: str, answers: dict, custom_inputs: dict, questions_data: dict):
        """批量模式：分析关键词并弹出类型确认对话框"""

        def do_analysis():
            import asyncio
            from seo_gen.modules.content_classifier import ContentClassifier
            from seo_gen.modules.title import TitleGenerator
            from seo_gen.modules.serp import SERPAnalyzer
            from seo_gen.modules.llm import LLMClient

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 1. 进行文章类型分类
                self.progress_callback("log", "🔍 正在分析关键词类型...")
                classifier = ContentClassifier()
                classification_result = classifier.classify(keyword)

                # 2. 获取 SERP 数据用于标题生成
                self.progress_callback("log", "📊 正在获取 SERP 数据...")
                llm_client = LLMClient()
                serp_analyzer = SERPAnalyzer(llm_client)
                serp_data = loop.run_until_complete(serp_analyzer.analyze(keyword))

                # 3. 生成候选标题
                self.progress_callback("log", "✏️ 正在生成候选标题...")
                title_generator = TitleGenerator(llm_client)
                title_candidates = loop.run_until_complete(
                    title_generator.generate_titles(keyword=keyword, serp_data=serp_data, count=5)
                )

                # 4. 选择最佳标题
                best_title = loop.run_until_complete(
                    title_generator.select_best_title(titles=title_candidates, serp_data=serp_data)
                )
                final_title = best_title.get("title", keyword)

                self.progress_callback("log", f"✓ 标题生成完成: {final_title}")

                # 5. 在主线程中显示类型确认对话框
                def show_type_dialog():
                    dialog = ArticleTypeConfirmDialog(
                        self,
                        keyword=keyword,
                        suggested_type=classification_result.article_type.value,
                        classification_data={
                            "confidence": classification_result.confidence,
                            "reasons": classification_result.reasons,
                            "search_intent": classification_result.search_intent,
                            "recommended_word_count": classification_result.recommended_word_count,
                        },
                        generated_title=final_title,
                        on_confirm_callback=lambda selected_type: self._batch_on_type_confirmed(
                            keyword, answers, custom_inputs, questions_data, selected_type, final_title
                        )
                    )
                    dialog.focus()

                self.after(0, show_type_dialog)

            except Exception as e:
                import traceback
                error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
                self.progress_callback("log", f"❌ 分析失败: {error_msg}")
                self.after(0, lambda: self._batch_on_type_confirmed(
                    keyword, answers, custom_inputs, questions_data, None, keyword
                ))
            finally:
                loop.close()

        thread = Thread(target=do_analysis, daemon=True)
        thread.start()

    def _batch_on_type_confirmed(self, keyword: str, answers: dict, custom_inputs: dict,
                                  questions_data: dict, confirmed_type: str, generated_title: str):
        """批量模式：用户确认类型后开始生成"""
        self.progress_callback("log", f"\n{'='*50}")
        self.progress_callback("log", f"📝 确认写作类型: {confirmed_type or '自动检测'}")
        self.progress_callback("log", f"📋 使用标题: {generated_title}")
        self.progress_callback("log", f"{'='*50}\n")

        # 开始正式生成
        thread = Thread(
            target=self._batch_run_single_generation,
            args=(keyword, answers, custom_inputs, questions_data, confirmed_type),
            daemon=True
        )
        thread.start()

    def _batch_run_single_generation(self, keyword: str, answers: dict, custom_inputs: dict,
                                      questions_data: dict, confirmed_type: str):
        """批量模式：运行单个生成"""
        try:
            self.orchestrator = get_workflow_orchestrator(progress_callback=self.progress_callback)

            async def run_workflow():
                enhanced_keywords = [keyword]
                if answers and questions_data:
                    from seo_gen.modules.keyword_analyzer import KeywordAnalyzer
                    analyzer = KeywordAnalyzer(None)
                    parsed_answers = analyzer.parse_user_answers(
                        {f"{qid}{ans}" for qid, ans in answers.items()},
                        custom_inputs
                    )
                    enhanced_keywords = analyzer.build_enhanced_search_queries(
                        keyword, parsed_answers, questions_data.get("questions", [])
                    )
                    self.progress_callback("log", f"🔍 增强搜索策略: {len(enhanced_keywords)} 个查询")

                result = await self.orchestrator.run_advanced_workflow(
                    keyword=keyword,
                    slug=None,
                    skip_images=not self.batch_include_images,
                    skip_wordpress=not self.batch_include_wp,
                    image_style=self.batch_image_style,
                    user_answers=answers or {},
                    custom_inputs=custom_inputs or {},
                    questions_data=questions_data or {},
                    enhanced_keywords=enhanced_keywords,
                    confirmed_article_type=confirmed_type,
                )
                return result

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_workflow())
            finally:
                loop.close()

            # 更新UI
            self.progress_callback("result", (result, keyword))

            # 保存历史记录
            self.save_to_history(keyword, result)

            # 刷新历史记录表格
            self.after(0, self.refresh_history)

            self.progress_callback("log", f"\n✅ 关键词 [{self.batch_current_index + 1}/{self.batch_total_count}] 完成: {keyword}")

            # 处理下一个关键词
            self.batch_current_index += 1
            self.after(500, self._process_next_batch_keyword)  # 延迟500ms后处理下一个

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.progress_callback("error", error_msg)
            self.progress_callback("log", f"\n❌ 关键词 [{self.batch_current_index + 1}/{self.batch_total_count}] 失败: {keyword}")

            # 即使失败也继续处理下一个关键词
            self.batch_current_index += 1
            self.after(500, self._process_next_batch_keyword)

    def run_single_generation(self, keyword, platform, mode, rewrite_content,
                            include_images, include_wp, image_style="modern",
                            answers=None, custom_inputs=None, questions_data=None,
                            confirmed_article_type=None):
        """运行单个生成（在后台线程）"""
        try:
            # 初始化工作流（带进度回调）
            self.orchestrator = get_workflow_orchestrator(progress_callback=self.progress_callback)

            # 运行异步工作流
            async def run_workflow():
                # 基于答案增强搜索关键词
                enhanced_keywords = [keyword]
                if answers and questions_data:
                    from seo_gen.modules.keyword_analyzer import KeywordAnalyzer
                    analyzer = KeywordAnalyzer(None)  # 不需要LLM客户端

                    # Parse answers with custom inputs
                    parsed_answers = analyzer.parse_user_answers(
                        {f"{qid}{ans}" for qid, ans in answers.items()},
                        custom_inputs
                    )

                    enhanced_keywords = analyzer.build_enhanced_search_queries(
                        keyword, parsed_answers, questions_data.get("questions", [])
                    )
                    self.progress_callback("log", f"🔍 增强搜索策略: {len(enhanced_keywords)} 个查询")

                # 调用工作流（根据平台选择不同的生成方式）
                if platform == "article":
                    # 文章使用原有流程
                    result = await self.orchestrator.run_advanced_workflow(
                        keyword=keyword,
                        slug=None,
                        skip_images=not include_images,
                        skip_wordpress=not include_wp,
                        image_style=image_style,
                        user_answers=answers or {},
                        custom_inputs=custom_inputs or {},
                        questions_data=questions_data or {},
                        enhanced_keywords=enhanced_keywords,
                        confirmed_article_type=confirmed_article_type,  # 传递用户确认的类型
                    )
                else:
                    # 社交媒体平台使用新的内容生成器
                    from seo_gen.modules.platform_content import get_platform_content_generator
                    from seo_gen.modules.serp import get_serp_analyzer

                    # 步骤1: SERP 分析
                    step_index = 1
                    self.progress_callback("step", (step_index, "running", "关键词 SERP 分析", 0.1))
                    serp_analyzer = get_serp_analyzer()
                    serp_data = await serp_analyzer.analyze(keyword)
                    self.progress_callback("step", (step_index, "completed", "SERP 分析 - 完成", 0.2))

                    # 步骤2: 生成策略问题（通过关键词分析器完成）
                    step_index += 1
                    self.progress_callback("step", (step_index, "completed", "生成策略问题 - 完成", 0.3))

                    # 处理二创内容（如果是对标网址，则抓取内容）
                    reference_content = None
                    if mode == "rewrite" and rewrite_content:
                        # 检查是否为网址
                        if self._is_url(rewrite_content):
                            self.progress_callback("log", f"🌐 正在抓取对标网址内容: {rewrite_content}")
                            content_gen = get_platform_content_generator()
                            reference_content = await content_gen.fetch_url_content(rewrite_content)
                            self.progress_callback("log", f"✓ 网址内容抓取完成")
                        else:
                            reference_content = rewrite_content

                    # 步骤3-5: 根据平台生成不同内容
                    step_index += 1
                    if platform in ["tiktok", "youtube", "facebook", "instagram"]:
                        self.progress_callback("step", (step_index, "running", f"创作钩子/Hook", 0.35))
                        step_index += 1
                        self.progress_callback("step", (step_index, "running", f"生成{platform.upper()}文案", 0.5))
                        step_index += 1
                        self.progress_callback("step", (step_index, "running", "生成 Hashtag", 0.65))
                    elif platform == "linkedin":
                        self.progress_callback("step", (step_index, "running", "创作专业标题", 0.35))
                        step_index += 1
                        self.progress_callback("step", (step_index, "running", "生成 LinkedIn 文案", 0.65))
                    elif platform == "x":
                        self.progress_callback("step", (step_index, "running", "创作 X 帖子", 0.5))
                        step_index += 1
                        self.progress_callback("step", (step_index, "running", "优化推文格式", 0.65))
                    elif platform == "reddit":
                        self.progress_callback("step", (step_index, "running", "创作 Reddit 帖子", 0.5))
                        step_index += 1
                        self.progress_callback("step", (step_index, "running", "生成讨论引导", 0.65))
                    elif platform == "pinterest":
                        self.progress_callback("step", (step_index, "running", "创作 Pin 描述", 0.5))
                        step_index += 1
                        self.progress_callback("step", (step_index, "running", "生成关键词标签", 0.65))

                    # 生成平台内容
                    content_gen = get_platform_content_generator()
                    platform_result = await content_gen.generate_platform_content(
                        platform=platform,
                        keyword=keyword,
                        serp_data=serp_data,
                        user_answers=answers or {},
                        mode=mode,
                        reference_content=reference_content
                    )

                    # 标记文案创作完成
                    self.progress_callback("step", (step_index, "completed", "文案创作 - 完成", 0.7))

                    # 步骤: 生成配图
                    step_index += 1
                    images = []
                    if include_images:
                        self.progress_callback("step", (step_index, "running", "生成配图", 0.8))
                        from seo_gen.modules.image import get_image_generator
                        img_gen = get_image_generator()
                        image_bytes = await img_gen.generate_cover_image(keyword, keyword, image_style)
                        images.append({"type": "cover", "data": image_bytes})
                        self.progress_callback("step", (step_index, "completed", "生成配图 - 完成", 0.9))
                    else:
                        self.progress_callback("step", (step_index, "completed", "跳过配图生成", 0.9))

                    # 步骤: 保存文件
                    step_index += 1
                    self.progress_callback("step", (step_index, "running", "保存文件", 0.95))
                    # 保存图片
                    if images:
                        from pathlib import Path
                        output_dir = Path("outputs")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        for img in images:
                            filename = f"{keyword}_{img['type']}.png"
                            (output_dir / filename).write_bytes(img["data"])
                    self.progress_callback("step", (step_index, "completed", "保存文件 - 完成", 1.0))

                    # 构建结果格式
                    result = {
                        "success": True,
                        "keyword": keyword,
                        "platform": platform,
                        "mode": mode,
                        "content": platform_result.get("content", ""),
                        "copy_text": platform_result.get("copy_text", ""),
                        "hashtags": platform_result.get("hashtags", []),
                        "hook": platform_result.get("hook", ""),
                        "cta": platform_result.get("cta", ""),
                        "images": images,
                        "metadata": {
                            "serp_data": serp_data,
                            "platform_metadata": platform_result.get("metadata", {})
                        }
                    }

                    # 更新可复制文本
                    self.generated_copy_text = platform_result.get("copy_text", "")

                return result

            # 运行异步工作流
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_workflow())
            finally:
                loop.close()

            # 更新UI
            self.progress_callback("result", (result, keyword))

            # 保存历史记录
            self.save_to_history(keyword, result)

            # 刷新历史记录表格
            self.after(0, self.refresh_history)

            # 重新启用输入
            self.keyword_entry.configure(state="normal")
            self.progress_callback("status", "生成完成")

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.progress_callback("error", error_msg)
            self.keyword_entry.configure(state="normal")
            self.progress_callback("status", "生成失败")

    def display_result(self, result, keyword):
        """显示结果到单个生成区域"""
        self.display_result_to(result, keyword, self.result_text)

    def display_result_to(self, result, keyword, target_textbox):
        """显示结果到指定文本框"""
        if not result.get("success"):
            error_msg = result.get('error', '未知错误')
            target_textbox.configure(state="normal")
            target_textbox.delete("1.0", "end")
            target_textbox.insert("1.0", f"❌ 生成失败:\n\n{error_msg}")
            target_textbox.configure(state="disabled")
            return

        # 检查是否为平台内容
        if "platform" in result and result["platform"] != "article":
            # 显示平台内容
            self.display_platform_content(result, keyword, target_textbox)
        else:
            # 显示文章质量报告
            quality = result.get("quality", {})
            overall_score = quality.get("overallScore", 0)
            overall_grade = quality.get("overallGrade", "Unknown")

            # 格式化E-E-A-T报告
            report = self.format_quality_report(result, keyword)

            target_textbox.configure(state="normal")
            target_textbox.delete("1.0", "end")
            target_textbox.insert("1.0", report)
            target_textbox.configure(state="disabled")

    def display_platform_content(self, result, keyword, target_textbox):
        """显示平台内容"""
        platform = result.get("platform", "")
        platform_name = self.platform_var.get()  # 获取中文平台名

        # 构建平台质量报告
        report = self.format_platform_quality_report(result, keyword, platform_name)

        # 显示到终端输出区域（生成内容）
        content_text = result.get("copy_text", result.get("content", ""))
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", content_text)
        self.log_text.configure(state="disabled")

        # 显示报告到右侧质量报告区域
        target_textbox.configure(state="normal")
        target_textbox.delete("1.0", "end")
        target_textbox.insert("1.0", report)
        target_textbox.configure(state="disabled")

        # 保存可复制文本
        self.generated_copy_text = content_text

    def format_platform_quality_report(self, result, keyword, platform_name):
        """格式化平台质量报告"""
        platform = result.get("platform", "")
        mode_text = "二创" if result.get("mode") == "rewrite" else "原创"
        content = result.get("content", "")
        hook = result.get("hook", "")
        cta = result.get("cta", "")
        hashtags = result.get("hashtags", [])

        # 计算内容质量指标
        content_length = len(content)
        word_count = len([w for w in content.split() if w.strip()])
        hook_length = len(hook) if hook else 0
        cta_length = len(cta) if cta else 0
        hashtag_count = len(hashtags)

        # 获取平台质量标准
        platform_standards = self.get_platform_quality_standards(platform)
        quality_checks = []

        # 值映射表
        value_map = {
            "hook": hook_length,
            "content": content_length,
            "cta": cta_length,
            "hashtags": hashtag_count,
        }

        # 检查各项指标是否符合标准
        for standard_name, key, checker, recommended in platform_standards:
            actual_value = value_map.get(key, 0)
            is_ok = checker(actual_value)
            status_icon = "✓" if is_ok else "⚠️"
            quality_checks.append((status_icon, standard_name, actual_value, recommended, is_ok))

        lines = [
            "=" * 55,
            f"📱 {platform_name} 内容生成报告",
            "=" * 55,
            "",
            f"📝 关键词: {keyword}",
            f"📱 平台: {platform_name}",
            f"✍️  模式: {mode_text}",
            "",
            "-" * 55,
            "",
            "📊 内容质量指标",
            "",
            f"  • 内容长度: {content_length} 字符",
            f"  • 字数统计: {word_count} 词",
            f"  • Hook长度: {hook_length} 字符",
            f"  • CTA长度: {cta_length} 字符",
            f"  • Hashtag数量: {hashtag_count}",
            "",
            "-" * 55,
            "",
            "📋 平台标准对照",
            "",
        ]

        # 添加平台标准对比
        for status_icon, name, actual, recommended, is_ok in quality_checks:
            lines.append(f"  {status_icon} {name}: {actual} (推荐: {recommended})")

        lines.extend([
            "",
            "-" * 55,
            "",
            "🎣 开头钩子 (Hook):",
            "",
            hook if hook else "（无）",
            "",
            "-" * 55,
            "",
            "📢 行动号召 (CTA):",
            "",
            cta if cta else "（无）",
            "",
        ])

        # 添加 Hashtag
        if hashtags:
            lines.extend([
                "-" * 55,
                "",
                "🏷️  Hashtag:",
                "",
                " ".join(f"#{tag}" for tag in hashtags),
                "",
            ])

        # 内容预览
        preview_length = min(200, len(content))
        lines.extend([
            "-" * 55,
            "",
            f"📄 内容预览 (前{preview_length}字符):",
            "",
            content[:preview_length] + ("..." if len(content) > preview_length else ""),
            "",
            "-" * 55,
            "",
            "💡 提示: 点击「复制内容」按钮可一键复制完整文案",
            "",
            "=" * 55,
        ])

        return "\n".join(lines)

    def get_platform_quality_standards(self, platform: str):
        """获取平台质量标准和检查函数

        Returns:
            list of tuples: (name, actual_value, checker, recommended_range)
        """
        # 平台标准定义
        standards = {
            # TikTok
            "tiktok": [
                ("Hook长度", "hook", lambda v: 50 <= v <= 150, "50-150字符"),
                ("内容长度", "content", lambda v: 200 <= v <= 2000, "200-2000字符"),
                ("Hashtag数量", "hashtags", lambda v: 3 <= v <= 5, "3-5个"),
            ],
            # YouTube
            "youtube": [
                ("Hook长度", "hook", lambda v: 80 <= v <= 200, "80-200字符"),
                ("内容长度", "content", lambda v: 500 <= v <= 5000, "500-5000字符"),
                ("Hashtag数量", "hashtags", lambda v: 3 <= v <= 5, "3-5个"),
            ],
            # Facebook
            "facebook": [
                ("Hook长度", "hook", lambda v: 50 <= v <= 150, "50-150字符"),
                ("内容长度", "content", lambda v: 300 <= v <= 3000, "300-3000字符"),
                ("Hashtag数量", "hashtags", lambda v: 2 <= v <= 4, "2-4个"),
            ],
            # LinkedIn
            "linkedin": [
                ("Hook长度", "hook", lambda v: 80 <= v <= 200, "80-200字符"),
                ("内容长度", "content", lambda v: 500 <= v <= 3000, "500-3000字符"),
                ("CTA长度", "cta", lambda v: 30 <= v <= 100, "30-100字符"),
            ],
            # X (Twitter)
            "x": [
                ("内容长度", "content", lambda v: 100 <= v <= 280, "100-280字符"),
                ("Hashtag数量", "hashtags", lambda v: 2 <= v <= 3, "2-3个"),
            ],
            # Reddit
            "reddit": [
                ("Hook长度", "hook", lambda v: 100 <= v <= 200, "100-200字符"),
                ("内容长度", "content", lambda v: 500 <= v <= 5000, "500-5000字符"),
            ],
            # Instagram
            "instagram": [
                ("Hook长度", "hook", lambda v: 50 <= v <= 150, "50-150字符"),
                ("内容长度", "content", lambda v: 300 <= v <= 2200, "300-2200字符"),
                ("Hashtag数量", "hashtags", lambda v: 5 <= v <= 15, "5-15个"),
            ],
            # Pinterest
            "pinterest": [
                ("Hook长度", "hook", lambda v: 50 <= v <= 150, "50-150字符"),
                ("内容长度", "content", lambda v: 200 <= v <= 1500, "200-1500字符"),
                ("Hashtag数量", "hashtags", lambda v: 3 <= v <= 5, "3-5个"),
            ],
        }

        return standards.get(platform, [
            ("内容长度", "content", lambda v: v > 0, "根据平台"),
            ("Hashtag数量", "hashtags", lambda v: v >= 0, "根据平台"),
        ])

    def format_quality_report(self, result, keyword):
        """格式化质量检测报告"""
        quality = result.get("quality", {})

        # 基本信息
        lines = [
            "=" * 55,
            f"📊 质量检测报告",
            "=" * 55,
            "",
            f"📝 关键词: {keyword}",
            f"📌 标题: {result.get('article', {}).get('title', 'N/A')}",
            f"⭐ 总体评分: {quality.get('overallScore', 0)}/100",
            f"📊 总体等级: {quality.get('overallGrade', 'Unknown')}",
            "",
            "-" * 55,
            "",
            "📊 E-E-A-T 维度评估",
            "",
        ]

        # E-E-A-T 维度
        eeat_scores = quality.get("eeatScores", {})
        eeat_names = {
            "experience": ("经验", "Experience"),
            "expertise": ("专业度", "Expertise"),
            "authoritativeness": ("权威性", "Authoritativeness"),
            "trustworthiness": ("可信度", "Trustworthiness"),
        }

        for key, (cn_name, en_name) in eeat_names.items():
            data = eeat_scores.get(key, {})
            grade = data.get("grade", "N/A")
            reasoning = data.get("reasoning", "")
            score = data.get("score", 0)

            lines.extend([
                f"【{cn_name}】",
                f"  等级: {grade} | 得分: {score}/100",
                f"  说明: {reasoning[:80]}..." if len(reasoning) > 80 else f"  说明: {reasoning}",
                "",
            ])

        # 内容质量
        lines.extend([
            "-" * 55,
            "",
            "📝 主体内容质量",
            "",
        ])

        content_quality = quality.get("contentQuality", {})
        quality_names = {
            "engagement": ("投入度", "Engagement"),
            "accuracy": ("准确性", "Accuracy"),
            "talent": ("才华", "Talent"),
            "originality": ("原创性", "Originality"),
        }

        for key, (cn_name, en_name) in quality_names.items():
            data = content_quality.get(key, {})
            if isinstance(data, dict):
                grade = data.get("grade", "N/A")
                reasoning = data.get("reasoning", "")
            else:
                grade = data
                reasoning = ""

            lines.append(f"【{cn_name}】")
            lines.append(f"  等级: {grade}")
            if reasoning:
                lines.append(f"  说明: {reasoning[:80]}..." if len(reasoning) > 80 else f"  说明: {reasoning}")
            lines.append("")

        # 字数和建议
        lines.extend([
            "-" * 55,
            "",
            f"📈 字数: {quality.get('wordCount', 0)} / 3000 字符",
            "",
        ])

        # AI检测和原创性检测
        stages = result.get("stages", {})
        if "content_detection" in stages:
            detection = stages["content_detection"].get("data", {})
            ai_det = detection.get("ai_detection", {})
            pla_det = detection.get("plagiarism_detection", {})

            lines.extend([
                "-" * 55,
                "",
                "🤖 AI内容检测",
                "",
                f"  AI概率: {ai_det.get('ai_probability', 0)*100:.0f}%",
                f"  人类概率: {ai_det.get('human_probability', 0)*100:.0f}%",
                f"  置信度: {ai_det.get('confidence', 'Unknown')}",
                "",
                "-" * 55,
                "",
                "📝 原创性检测",
                "",
                f"  原创度: {pla_det.get('originality_score', 0)*100:.0f}%",
                f"  相似度: {pla_det.get('similarity_score', 0)*100:.0f}%",
                f"  匹配数: {pla_det.get('total_matches', 0)}",
                "",
                f"  综合评分: {detection.get('overall_score', 0):.0f}/100",
                "",
            ])

            if pla_det.get('total_matches', 0) > 0:
                lines.extend([
                    "  相似内容:",
                ])
                for match in pla_det.get('matches', [])[:3]:
                    lines.append(f"    • {match.get('name', 'N/A')} ({match.get('similarity', 0)*100:.0f}%)")
                lines.append("")

        suggestions = quality.get("suggestions", [])
        if suggestions:
            lines.append("💡 改进建议:")
            for suggestion in suggestions[:3]:
                lines.append(f"   • {suggestion}")
            lines.append("")

        # 文章链接
        stages = result.get("stages", {})
        if "wordpress_published" in stages:
            wp_data = stages["wordpress_published"]
            post_id = wp_data.get("post_id", "")
            if post_id:
                lines.extend([
                    "-" * 55,
                    "",
                    f"🔗 链接: https://asgdropshipping.com/?p={post_id}",
                    "",
                ])

        lines.append("=" * 55)

        return "\n".join(lines)

    def save_to_history(self, keyword, result):
        """保存到历史记录"""
        try:
            quality = result.get("quality", {})
            stages = result.get("stages", {})

            # 获取 WordPress 链接
            wp_link = ""
            if "wordpress_published" in stages:
                post_id = stages["wordpress_published"].get("post_id", "")
                if post_id:
                    wp_link = f"https://asgdropshipping.com/?p={post_id}"

            history_item = {
                "keyword": keyword,
                "title": result.get("article", {}).get("title", ""),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": "completed" if result.get("success") else "failed",
                "score": quality.get("overallScore", 0),
                "grade": quality.get("overallGrade", ""),
                "wp_link": wp_link,
                "stages": stages,
                "quality": quality,
                "article": result.get("article", {})
            }

            self.history_data.insert(0, history_item)

            # 只保留最近 50 条记录
            if len(self.history_data) > 50:
                self.history_data = self.history_data[:50]

            # 保存到文件
            self.history_file.write_text(json.dumps(self.history_data, ensure_ascii=False, indent=2))

        except Exception as e:
            pass  # 静默忽略保存错误

    def load_history(self):
        """加载历史记录"""
        try:
            if self.history_file.exists():
                data = json.loads(self.history_file.read_text(encoding="utf-8"))
                return data
        except:
            pass
        return []

    def refresh_history(self):
        """刷新历史记录表格"""
        # 清空表格
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # 加载数据
        for idx, item in enumerate(self.history_data):
            # 格式化状态
            status_icon = "✓" if item.get("status") == "completed" else "✗"
            score = item.get("score", 0)
            score_text = f"{score}" if score > 0 else "N/A"
            grade = item.get("grade", "N/A")
            wp_link = item.get("wp_link", "")

            self.history_tree.insert("", "end", values=(
                item.get("keyword", "")[:35],
                item.get("date", ""),
                grade,
                score_text,
                wp_link,
                "查看详情"
            ))

    def view_history_detail(self, event):
        """查看历史详情"""
        selection = self.history_tree.selection()
        if not selection:
            return

        # 获取选中项的索引
        for idx, item in enumerate(self.history_tree.get_children()):
            if item == selection[0]:
                item_data = self.history_data[idx]

                # 创建详情窗口
                detail_window = ctk.CTkToplevel(self)
                detail_window.title(f"详情: {item_data.get('keyword', '')}")
                detail_window.geometry("700x600")

                # 标题
                title_label = ctk.CTkLabel(
                    detail_window,
                    text="📊 质量检测报告详情",
                    font=ctk.CTkFont(size=18, weight="bold")
                )
                title_label.pack(pady=10)

                # 滚动文本框
                detail_text = ctk.CTkTextbox(
                    detail_window,
                    font=ctk.CTkFont(size=11),
                )
                detail_text.pack(fill="both", expand=True, padx=15, pady=(0, 10))

                # 显示报告
                report = self.format_quality_report(item_data, item_data.get("keyword", ""))
                detail_text.insert("1.0", report)
                detail_text.configure(state="disabled")
                break

    def open_outputs_folder(self):
        """打开输出文件夹"""
        import subprocess
        import platform

        outputs_dir = Path("outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)

        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(str(outputs_dir))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(outputs_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(outputs_dir)])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")


def main():
    """启动GUI应用"""
    app = ContentGeneratorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
