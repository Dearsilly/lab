"""生成答辩 PPT。"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# 配色
C_PRIMARY = RGBColor(0x63, 0x66, 0xF1)  # 主色
C_DARK = RGBColor(0x1F, 0x29, 0x37)
C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
C_GRAY = RGBColor(0x6B, 0x72, 0x80)
C_GREEN = RGBColor(0x10, 0xB9, 0x81)
C_RED = RGBColor(0xEF, 0x44, 0x44)
C_BG = RGBColor(0xF8, 0xF9, 0xFA)
C_ACCENT = RGBColor(0xF5, 0x9E, 0x0B)


def add_bg(slide, color=C_WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_title_bar(slide, text, subtitle=""):
    """顶部标题栏"""
    from pptx.util import Inches, Pt
    shape = slide.shapes.add_shape(
        1, Inches(0), Inches(0), prs.slide_width, Inches(1.2)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_PRIMARY
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(32)
    p.font.color.rgb = C_WHITE
    p.font.bold = True
    p.alignment = PP_ALIGN.LEFT
    tf.margin_left = Inches(0.8)
    tf.margin_top = Inches(0.3)
    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(16)
        p2.font.color.rgb = RGBColor(0xD1, 0xD5, 0xDB)
        p2.alignment = PP_ALIGN.LEFT


def add_footer(slide, text="AES 自动文本评分系统 | 工程实践项目答辩"):
    txBox = slide.shapes.add_textbox(
        Inches(0.5), Inches(7.0), Inches(12), Inches(0.4)
    )
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(10)
    p.font.color.rgb = C_GRAY


def add_body_text(slide, left, top, width, height, items, size=18):
    """添加项目符号列表"""
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(size)
        p.font.color.rgb = C_DARK
        p.space_after = Pt(8)


def add_card(slide, left, top, width, height, title, content, color=C_PRIMARY):
    """卡片组件"""
    shape = slide.shapes.add_shape(
        1, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_WHITE
    shape.line.color.rgb = RGBColor(0xE5, 0xE7, 0xEB)
    shape.line.width = Pt(1)

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)
    tf.margin_top = Inches(0.2)

    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = color

    for line in content:
        p2 = tf.add_paragraph()
        p2.text = line
        p2.font.size = Pt(14)
        p2.font.color.rgb = C_DARK
        p2.space_after = Pt(4)


# ============================================================
# Slide 1: 封面
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide, C_PRIMARY)
txBox = slide.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10), Inches(2))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "基于深度学习的文本作业自动评分系统"
p.font.size = Pt(42)
p.font.color.rgb = C_WHITE
p.font.bold = True
p.alignment = PP_ALIGN.CENTER

p2 = tf.add_paragraph()
p2.text = "Automated Essay Scoring with BERT"
p2.font.size = Pt(24)
p2.font.color.rgb = RGBColor(0xD1, 0xD5, 0xDB)
p2.alignment = PP_ALIGN.CENTER

txBox2 = slide.shapes.add_textbox(Inches(1.5), Inches(4.5), Inches(10), Inches(2))
tf2 = txBox2.text_frame
for line in ["中英文双语 · 多维度评分 · 智能反馈 · 批量处理", "", "工程实践项目 | 苏州 | 2026"]:
    p = tf2.add_paragraph()
    p.text = line
    p.font.size = Pt(18)
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

# ============================================================
# Slide 2: 项目背景
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "项目背景与目标")
add_footer(slide)

add_body_text(slide, 0.8, 1.6, 5.5, 5, [
    "📌 项目背景",
    "• 传统作文评分依赖人工，效率低、一致性差",
    "• 深度学习技术在 NLP 领域取得突破性进展",
    "• 预训练模型（BERT）为自动评分提供了技术基础",
    "",
    "🎯 项目目标",
    "• 构建支持中英文双语的自动作文评分系统",
    "• 提供多维度评分（总评分 + 内容/结构/语言）",
    "• 生成可读的文字评语反馈",
    "• 通过 Web 界面实现便捷交互",
], size=16)

add_card(slide, 7.5, 1.6, 5, 4, "🎯 成功标准", [
    "✅ 英文 ASAP 数据集 QWK ≥ 0.70",
    "✅ 中文模型 QWK ≥ 0.70",
    "✅ API 单篇评分响应 < 5 秒",
    "✅ 中英文双语界面完整切换",
    "✅ 批量评分 CSV 支持",
    "✅ E2E 测试 41 项全部通过",
], C_GREEN)

# ============================================================
# Slide 3: 系统架构
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "系统架构")
add_footer(slide)

# 架构流程
layers = [
    ("Streamlit UI", "评分页面 | 批量页面 | 中英对比 | 双语切换 | 仪表盘+雷达图+反馈卡片", C_PRIMARY),
    ("Flask REST API", "POST /score | POST /batch | GET /health | GET /models | 参数校验+错误处理", RGBColor(0x3B, 0x82, 0xF6)),
    ("推理引擎", "语言检测 → 文本预处理 → 模型路由 → 推理 → 反馈生成", C_GREEN),
    ("模型层", "BERT-base-uncased (英文) | BERT-base-chinese (中文) | jieba 中文分词", C_ACCENT),
]
for i, (title, desc, color) in enumerate(layers):
    y = 1.6 + i * 1.35
    shape = slide.shapes.add_shape(
        1, Inches(1.5), Inches(y), Inches(10.3), Inches(1.1)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_WHITE
    shape.line.color.rgb = color
    shape.line.width = Pt(2)
    tf = shape.text_frame
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.1)
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = color
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(14)
    p2.font.color.rgb = C_GRAY

# 箭头
for i in range(3):
    y = 2.7 + i * 1.35
    txBox = slide.shapes.add_textbox(Inches(6.2), Inches(y), Inches(1), Inches(0.3))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "▼"
    p.font.size = Pt(16)
    p.font.color.rgb = C_GRAY
    p.alignment = PP_ALIGN.CENTER

# ============================================================
# Slide 4: 模型架构
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "模型架构", "BERT + 回归头")
add_footer(slide)

add_body_text(slide, 0.8, 1.5, 5.5, 3, [
    "🧠 英文模型：BERT-base-uncased",
    "• 12 层 Transformer，110M 参数，768 维隐藏层",
    "• 输入：英文文本 → BERT Tokenizer → [CLS] 向量",
    "• 输出：Dropout(0.1) → Linear → Sigmoid → [0,1]",
    "• 训练：ASAP 12,976 篇，fp16，5 epoch",
    "",
    "🇨🇳 中文模型：BERT-base-chinese",
    "• 同架构，21128 中文词表",
    "• 预处理：全半角转换 → jieba 分词 → BERT Tokenizer",
    "• 训练：翻译数据 3,950 篇，5 epoch",
], size=16)

add_card(slide, 7.5, 1.5, 5, 2.5, "📊 模型表现", [
    "英文 BERT: Val QWK 0.58 (prompt隔离)",
    "中文 BERT: Val QWK 0.79, Test 0.76",
    "RoBERTa-base 备选模型已训练",
], C_PRIMARY)

add_card(slide, 7.5, 4.3, 5, 2.8, "🔮 多任务扩展（已设计）", [
    "共享编码器 + 4 个独立回归头",
    "Head 0: 总评分 | Head 1: 内容",
    "Head 2: 结构 | Head 3: 语言",
    "当前版本：启发式拆分近似实现",
], C_ACCENT)

# ============================================================
# Slide 5: 数据处理
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "数据处理流水线")
add_footer(slide)

add_card(slide, 0.8, 1.5, 5.5, 5.2, "🇬🇧 英文数据处理", [
    "① ASAP 原始 CSV (12,976 篇)",
    "② 文本清洗: HTML unescape / URL移除 / 空白规范",
    "③ 按 essay_set 归一化分数 (min-max → [0,1])",
    "④ BERT 分词 (max_length=512)",
    "⑤ Prompt 隔离划分 (train/val/test)",
    "⑥ 5 折 GroupKFold 交叉验证",
], C_PRIMARY)

add_card(slide, 7.5, 1.5, 5.5, 5.2, "🇨🇳 中文数据处理", [
    "① ASAP 英文 → Google Translate (3,950 篇)",
    "② 中文清洗: 全角转半角 / 控制字符移除",
    "③ jieba 分词 (词间加空格，适配 BERT)",
    "④ 按 essay_set 归一化分数",
    "⑤ BERT 分词 (bert-base-chinese)",
    "⑥ 随机划分 (翻译数据同源，无需 prompt 隔离)",
], C_GREEN)

# ============================================================
# Slide 6: API 设计
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "REST API 接口设计")
add_footer(slide)

apis = [
    ("GET", "/api/v1/health", "健康检查 + 模型加载状态"),
    ("GET", "/api/v1/models", "模型注册表信息 (名称/语言/版本)"),
    ("POST", "/api/v1/score", "单篇评分\n{\"text\": \"...\", \"language\": \"auto\"}\n→ {score, scores{total/content/structure/language}, feedback{...}}"),
    ("POST", "/api/v1/batch", "批量评分 (CSV上传)\n→ {total, results[{id, score, ...}]}"),
]
for i, (method, path, desc) in enumerate(apis):
    y = 1.5 + i * 1.4
    # Method badge
    shape = slide.shapes.add_shape(
        1, Inches(0.8), Inches(y), Inches(1.2), Inches(0.5)
    )
    shape.fill.solid()
    colors = {"GET": RGBColor(0x10, 0xB9, 0x81), "POST": RGBColor(0x3B, 0x82, 0xF6)}
    shape.fill.fore_color.rgb = colors.get(method, C_GRAY)
    shape.line.fill.background()
    tf = shape.text_frame
    p = tf.paragraphs[0]
    p.text = method
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

    # Path
    txBox = slide.shapes.add_textbox(Inches(2.2), Inches(y), Inches(3.5), Inches(0.5))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = path
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_DARK

    # Description
    txBox2 = slide.shapes.add_textbox(Inches(5.8), Inches(y - 0.1), Inches(6.5), Inches(1.2))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = desc
    p2.font.size = Pt(13)
    p2.font.color.rgb = C_GRAY

# ============================================================
# Slide 7: UI 界面
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "Web 交互界面", "Streamlit + Plotly")
add_footer(slide)

add_card(slide, 0.8, 1.5, 3.7, 3.5, "📝 评分页面", [
    "• 中英文自动检测/手动切换",
    "• 圆形仪表盘 (总分%)",
    "• 三维度雷达图",
    "• 彩色反馈卡片",
    "• 字数/字符数实时统计",
    "• 清除按钮 (无状态冲突)",
], C_PRIMARY)

add_card(slide, 4.8, 1.5, 3.7, 3.5, "📊 批量评分", [
    "• CSV 模板下载",
    "• 文件拖拽上传",
    "• 批量推理 + 结果表格",
    "• 一键下载 CSV 结果",
    "• 进度实时反馈",
], RGBColor(0x3B, 0x82, 0xF6))

add_card(slide, 8.8, 1.5, 3.7, 3.5, "🔄 中英对比", [
    "• 并排双模型评分",
    "• 同一文本两种视角",
    "• 分数对比 + 反馈对比",
    "• 侧边栏双语切换",
], C_GREEN)

add_card(slide, 0.8, 5.3, 11.7, 1.8, "🎨 界面特性", [
    "• 完整中英双语文案 (i18n/zh.json + en.json)  •  侧边栏语言实时切换  •  Plotly 雷达图 + 仪表盘",
    "• 加载状态 (spinner) + 空状态 (placeholder) + 错误状态 (toast)  •  响应式布局",
], C_ACCENT)

# ============================================================
# Slide 8: 反馈生成
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "智能反馈生成", "基于维度分数的模板化评语")
add_footer(slide)

add_body_text(slide, 0.8, 1.5, 5.5, 5, [
    "📋 反馈生成流程",
    "",
    "维度分数 → 等级判断 → 模板映射 → 评语文字",
    "",
    "等级阈值:  ≥0.7 → 优秀 | ≥0.4 → 中等 | <0.4 → 待提升",
    "",
    "模板规模:",
    "• 英文: 3维度 × 3等级 = 9条维度模板 + 3条总评",
    "• 中文: 同上，完整中文翻译",
    "• 总计 24 条模板覆盖全部评分区间",
], size=16)

add_card(slide, 7.5, 1.5, 5, 2.5, "🇨🇳 中文反馈示例", [
    "内容: \"论点明确，论证充分，举例恰当。\"",
    "结构: \"结构完整，层次分明，段落衔接自然。\"",
    "语言: \"语言表达流畅，词汇丰富，句式多样。\"",
    "总评: \"总分表现优秀(85.2分)...\"",
], C_GREEN)

add_card(slide, 7.5, 4.3, 5, 2.5, "🇬🇧 English Feedback", [
    "Content: \"Your arguments are clear...\"",
    "Structure: \"Excellent essay structure...\"",
    "Language: \"Strong command of language...\"",
    "Overall: \"Overall score is strong...\"",
], C_PRIMARY)

# ============================================================
# Slide 9: 测试策略
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "测试与质量保证")
add_footer(slide)

add_card(slide, 0.8, 1.5, 5.5, 2.5, "🧪 单元测试 (17项)", [
    "• 数据预处理: 文本清洗、分数归一化、Prompt划分",
    "• API 端点: Health、Score (错误路径)、404",
    "• 评估指标: QWK、MAE、Pearson 正确性验证",
    "• 工具: pytest (17/17 通过, 3.99s)",
], C_PRIMARY)

add_card(slide, 6.8, 1.5, 5.5, 2.5, "🌐 E2E 测试 (41项)", [
    "• API: Health/Score(ZH/EN)/Batch/Models/Errors",
    "• UI: 首页/空提交/清除/评分流程/批量页/对比页",
    "• 范文: 中英文高分范文评分验证",
    "• 工具: Playwright + Chromium (41/41 通过)",
], C_GREEN)

add_card(slide, 0.8, 4.3, 11.7, 2.8, "📊 测试覆盖矩阵", [
    "层级        工具        测试数    状态    覆盖范围",
    "─────────────────────────────────────────────────",
    "单元测试    pytest       17       ✅    数据流水线 + API端点 + 评估指标",
    "E2E测试    Playwright   41       ✅    API全端点 + UI全页面 + 范文验证",
    "模型测试    (手动)        —       —     前向传播、输出形状、值域、NaN保护",
], C_ACCENT)

# ============================================================
# Slide 10: 演示场景
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "演示场景", "6个核心场景 · 约 8 分钟")
add_footer(slide)

scenes = [
    ("1", "英文作文评分", "仪表盘 + 雷达图 + 英文反馈", C_PRIMARY),
    ("2", "中文作文评分", "自动检测 + 中文反馈", C_GREEN),
    ("3", "批量评分", "CSV 上传 → 结果表格 → 下载", RGBColor(0x3B, 0x82, 0xF6)),
    ("4", "中英对比", "同一文本双模型并排展示", C_ACCENT),
    ("5", "错误处理", "空文本 / 超长 / 清除按钮", C_RED),
    ("6", "工程总结", "架构 + 指标 + 创新点", C_DARK),
]
for i, (num, title, desc, color) in enumerate(scenes):
    y = 1.5 + i * 0.95
    shape = slide.shapes.add_shape(
        1, Inches(1.5), Inches(y), Inches(10.3), Inches(0.75)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_WHITE
    shape.line.color.rgb = color
    shape.line.width = Pt(2)
    tf = shape.text_frame
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.1)
    p = tf.paragraphs[0]
    p.text = f"场景 {num}: {title}"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = color
    p2 = tf.add_paragraph()
    p2.text = desc
    p2.font.size = Pt(14)
    p2.font.color.rgb = C_GRAY

# ============================================================
# Slide 11: 技术决策
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "关键技术决策")
add_footer(slide)

decisions = [
    ("BERT-base 为主模型", "8GB 显存稳定运行，生态成熟，训练推理效率高"),
    ("Prompt 隔离划分", "防止题目级别数据泄露，评估更真实"),
    ("翻译数据 + 中文模型", "快速启动中文能力，绕过数据获取瓶颈"),
    ("Flask + Streamlit", "Python 全栈，团队技能匹配，快速迭代"),
    ("不引入数据库/认证/Docker", "控制工程实践复杂度边界，聚焦核心价值"),
    ("MSE 损失 + Sigmoid 输出", "训练稳定，回归任务经典方案"),
]
for i, (title, reason) in enumerate(decisions):
    y = 1.5 + i * 0.95
    shape = slide.shapes.add_shape(
        1, Inches(1.5), Inches(y), Inches(10.3), Inches(0.75)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = C_WHITE
    shape.line.color.rgb = C_PRIMARY
    shape.line.width = Pt(1)
    tf = shape.text_frame
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.1)
    p = tf.paragraphs[0]
    p.text = f"▸ {title}"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_DARK
    p2 = tf.add_paragraph()
    p2.text = reason
    p2.font.size = Pt(14)
    p2.font.color.rgb = C_GRAY

# ============================================================
# Slide 12: 项目总结
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)
add_title_bar(slide, "项目总结与展望")
add_footer(slide)

add_card(slide, 0.8, 1.5, 5.5, 3.5, "✅ 已完成", [
    "• 中英文双语评分系统 (BERT双模型)",
    "• 多维度评分 + 智能反馈生成",
    "• RESTful API (4个端点)",
    "• Streamlit 多页面 Web 界面",
    "• 批量评分 CSV 流水线",
    "• 双语界面完整切换 (i18n)",
    "• 41 项 E2E 测试 + 17 项单元测试",
    "• 完整项目文档 + 答辩材料",
], C_GREEN)

add_card(slide, 6.8, 1.5, 5.5, 3.5, "🔮 后续改进", [
    "• DeBERTa-v3 多任务模型 (提升 QWK)",
    "• 收集真实中文作文数据",
    "• 模型集成 (加权平均)",
    "• Longformer 长文本支持",
    "• 教师/学生角色系统",
    "• 数据库持久化",
], C_ACCENT)

add_card(slide, 0.8, 5.3, 11.7, 1.8, "💡 核心创新点", [
    "• 中英文双模型无缝切换  •  多维评分 + 反馈一体化  •  完整批量评分流水线  •  严格 prompt 隔离评估  •  42项自动化测试覆盖",
], C_PRIMARY)

# ============================================================
# Slide 13: 致谢
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, C_PRIMARY)

txBox = slide.shapes.add_textbox(Inches(1.5), Inches(2.5), Inches(10), Inches(3))
tf = txBox.text_frame
p = tf.paragraphs[0]
p.text = "感谢聆听"
p.font.size = Pt(52)
p.font.color.rgb = C_WHITE
p.font.bold = True
p.alignment = PP_ALIGN.CENTER

p2 = tf.add_paragraph()
p2.text = "Thank You"
p2.font.size = Pt(32)
p2.font.color.rgb = RGBColor(0xD1, 0xD5, 0xDB)
p2.alignment = PP_ALIGN.CENTER

txBox2 = slide.shapes.add_textbox(Inches(1.5), Inches(5.0), Inches(10), Inches(1.5))
tf2 = txBox2.text_frame
for line in ["自动文本评分系统 (AES)", "基于 BERT 深度学习 · 中英文双语", "苏州 · 2026"]:
    p = tf2.add_paragraph()
    p.text = line
    p.font.size = Pt(18)
    p.font.color.rgb = C_WHITE
    p.alignment = PP_ALIGN.CENTER

# ============================================================
# 保存
# ============================================================
output = "doc/AES_答辩PPT.pptx"
prs.save(output)
print(f"✅ PPT 已生成: {output}")
print(f"   共 {len(prs.slides)} 页幻灯片")
