const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak
} = require("docx");

// ========== Styles ==========
const styles = {
  default: { document: { run: { font: "SimSun", size: 24 } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 32, bold: true, font: "SimHei", color: "1F3864" },
      paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, bold: true, font: "SimHei", color: "2E75B6" },
      paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 26, bold: true, font: "SimHei" },
      paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
  ]
};

const numbering = {
  config: [
    { reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: "numbers",
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ]
};

// ========== Helpers ==========
const P = (text, opts = {}) => new Paragraph({
  spacing: { after: 120, line: 360 },
  ...opts,
  children: [new TextRun({ text, size: 24, font: "SimSun", ...opts.run })]
});

const Heading = (level, text) => new Paragraph({
  heading: level,
  children: [new TextRun({ text, font: "SimHei" })]
});

const Bullet = (text) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  spacing: { after: 80 },
  children: [new TextRun({ text, size: 24, font: "SimSun" })]
});

const cellBorder = { style: BorderStyle.SINGLE, size: 1, color: "BFBFBF" };
const cellBorders = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder };
const headerShading = { fill: "1F3864", type: ShadingType.CLEAR };

function headerCell(text, width) {
  return new TableCell({
    borders: cellBorders, width: { size: width, type: WidthType.DXA },
    shading: headerShading,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 22, font: "SimHei" })] })]
  });
}

function dataCell(text, width) {
  return new TableCell({
    borders: cellBorders, width: { size: width, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: [new Paragraph({ children: [new TextRun({ text, size: 22, font: "SimSun" })] })]
  });
}

// ========== Cover Page ==========
const coverPage = [
  new Paragraph({ spacing: { before: 2400 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: "工程实践项目答辩报告", size: 52, bold: true, font: "SimHei", color: "1F3864" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
    children: [new TextRun({ text: "中英文双语作文自动评分系统 (AES)", size: 36, font: "SimHei", color: "2E75B6" })] }),
  new Paragraph({ spacing: { before: 1200 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: "团队：4 人工程实践项目", size: 24, font: "SimSun", color: "404040" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: "地点：苏州", size: 24, font: "SimSun", color: "404040" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "日期：2026 年 6 月", size: 24, font: "SimSun", color: "404040" })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== TOC ==========
const tocSection = [
  Heading(HeadingLevel.HEADING_1, "目录"),
  new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== Chapter 1: Project Background ==========
const ch1 = [
  Heading(HeadingLevel.HEADING_1, "一、项目背景与意义"),
  Heading(HeadingLevel.HEADING_2, "1.1 问题描述"),
  P("作文评分是教育领域最耗时的工作之一。以中学语文教学为例，一位教师通常负责 3-4 个班级，每次布置作文后需要批改 150-200 篇。按照每篇认真批改 10 分钟计算，完成一轮作文批改需要 25-33 小时。实际操作中，教师往往前 30 篇精批细改，随后因疲劳导致评分质量下降，评语越来越简略，到后期只能给出一个总分。"),
  P("此外，人工评分存在以下固有问题：(1) 评分一致性难以保证，同一篇作文在不同时间、不同评分者之间可能产生显著偏差；(2) 缺乏细粒度的分项反馈，学生无法了解自己在内容、结构、语言等具体维度的表现；(3) 评分效率低，无法满足大规模考试或日常练习的快速反馈需求。"),

  Heading(HeadingLevel.HEADING_2, "1.2 项目目标"),
  P("本项目旨在构建一个基于深度学习的端到端自动作文评分系统，核心目标包括："),
  Bullet("支持中英文双语作文的自动评分，覆盖常见教学场景"),
  Bullet("输出多维度评分（总评分 + 内容/结构/语言）和文字评语反馈"),
  Bullet("提供 Web 和 Android 双平台访问方式，适应不同使用场景"),
  Bullet("Android 版实现完全本地推理，无需网络连接即可使用"),

  Heading(HeadingLevel.HEADING_2, "1.3 国内外研究现状"),
  P("自动作文评分 (Automated Essay Scoring, AES) 是自然语言处理领域的经典问题。自 1960 年代 Page 提出 PEG 系统以来，AES 技术经历了从手工特征提取到深度学习的发展。2012 年 Kaggle 举办的 ASAP (Automated Student Assessment Prize) 竞赛是重要里程碑，参赛者需要在 8 个不同作文题目上实现自动化评分，推动了深度学习在该领域的应用。"),
  P("当前主流方法基于预训练语言模型（如 BERT），通过对作文文本进行语义编码和回归预测来实现自动评分。代表性工作包括：BERT-based AES (Mayfield & Black, 2020)、多任务学习框架 (Do et al., 2023) 等。本项目采用 BERT-base 作为基础编码器，并结合实际工程需求进行了多平台部署。"),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== Chapter 2: System Architecture ==========
const ch2 = [
  Heading(HeadingLevel.HEADING_1, "二、系统架构"),

  Heading(HeadingLevel.HEADING_2, "2.1 整体架构"),
  P("系统采用分层架构设计，包含数据层、模型层、推理引擎层和应用层四个层次。支持两个平台版本：基于 Flask + Streamlit 的 Web 版和基于 Kotlin + Jetpack Compose 的 Android 版，两个版本共享同一套训练好的 BERT 模型权重。"),

  Heading(HeadingLevel.HEADING_2, "2.2 数据层"),
  P("数据层负责数据的加载、清洗和预处理。英文方面使用 ASAP 竞赛公开数据集，包含 12,979 篇英文作文，覆盖 8 个不同题目集，分数范围 0-55。中文方面将 ASAP 数据集通过 Google Translate 翻译为中文，保留原始评分标签，共 3,950 篇。"),
  P("数据预处理流水线包括：HTML 实体转义、@mention/URL 移除、空白规范化、按 essay_set 归一化分数至 [0,1] 区间、BERT 分词（max_length=512）。训练集/验证集/测试集按 essay_set 级别隔离划分，防止题目级别的数据泄露。"),

  Heading(HeadingLevel.HEADING_2, "2.3 模型层"),
  P("模型层基于 BERT 预训练语言模型构建回归评分模型。英文采用 bert-base-uncased（110M 参数，12 层 Transformer，768 维隐藏层），中文采用 bert-base-chinese（110M 参数，21128 词表）。架构为 BERT 编码器 + [CLS] 池化 + Dropout(0.1) + Linear(768→1) + Sigmoid，输出 [0,1] 区间的连续分数。"),
  P("此外，还实现了基于 DeBERTa-v3 的多任务模型 AESMultiTaskModel，在共享编码器基础上添加 4 个独立回归头，分别预测总评分、内容、结构、语言四个维度。每个回归头额外显存开销小于 1MB。"),

  Heading(HeadingLevel.HEADING_2, "2.4 推理引擎层"),
  P("推理引擎层负责文本预处理、语言检测、模型调度和反馈生成。Web 版使用 Python 实现，集成 langdetect 语言检测和 jieba 中文分词。Android 版使用 Kotlin 重新实现了 BERT WordPiece 分词器（约 100 行代码），通过字符规则进行语言检测，借助 PyTorch Mobile Lite 加载 .pt 模型文件在手机 CPU 上执行本地推理。"),

  Heading(HeadingLevel.HEADING_2, "2.5 应用层"),
  P("Web 版提供 Flask REST API（4 个端点）和 Streamlit 可视化界面（4 个页面）。Android 版基于 Jetpack Compose + Material3 构建，采用底部 Tab 导航（评分/批量/对比/设置），雷达图使用 Compose Canvas 自绘。两个版本功能一一对应。"),

  // Architecture comparison table
  new Paragraph({ spacing: { before: 200, after: 100 },
    children: [new TextRun({ text: "表 1：Web 版与 Android 版架构对比", bold: true, size: 22, font: "SimHei" })] }),
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2200, 3580, 3580],
    rows: [
      new TableRow({ children: [headerCell("维度", 2200), headerCell("Web 版", 3580), headerCell("Android 版", 3580)] }),
      new TableRow({ children: [dataCell("推理位置", 2200), dataCell("Flask 服务器 (GPU)", 3580), dataCell("手机本地 (CPU)", 3580)] }),
      new TableRow({ children: [dataCell("模型加载", 2200), dataCell("Python PyTorch", 3580), dataCell("PyTorch Mobile Lite", 3580)] }),
      new TableRow({ children: [dataCell("分词器", 2200), dataCell("HuggingFace Transformers", 3580), dataCell("Kotlin 自实现 WordPiece", 3580)] }),
      new TableRow({ children: [dataCell("UI 框架", 2200), dataCell("Streamlit + Plotly", 3580), dataCell("Jetpack Compose + Canvas", 3580)] }),
      new TableRow({ children: [dataCell("推理速度", 2200), dataCell("~200ms (fp16 GPU)", 3580), dataCell("~1-5s (CPU)", 3580)] }),
    ]
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== Chapter 3: Technical Approach ==========
const ch3 = [
  Heading(HeadingLevel.HEADING_1, "三、核心技术方案"),

  Heading(HeadingLevel.HEADING_2, "3.1 BERT 回归模型"),
  P("模型的核心是 BERT + 回归头的端到端架构。BERT 编码器将输入文本转换为 768 维的上下文语义向量，取 [CLS] token 的输出作为整个序列的语义表示，经过 Dropout 和全连接层后通过 Sigmoid 激活函数输出 [0,1] 区间的评分。选用 Sigmoid 而非无界输出的原因：(1) 保证训练稳定性，梯度有上界；(2) 推理时不需要后处理裁剪；(3) MSE Loss + Sigmoid 的组合避免了 BCE Loss 在极端预测时的梯度爆炸。"),

  Heading(HeadingLevel.HEADING_2, "3.2 训练策略"),
  P("训练配置：优化器 AdamW (weight_decay=0.01)，学习率 2e-5，批次大小 16（英文）/ 8（中文），训练 5 个 epoch，早停 patience=3。学习率调度采用 Linear Warmup (10%) + Linear Decay。英文模型使用 fp16 混合精度训练以节省显存。"),
  P("数据划分方面，英文模型采用 essay_set 级别的 prompt 隔离策略——将 8 个不同的作文题目集整体分配到训练/验证/测试集，确保同一题目的作文不会同时出现在不同集合中。这比样本级别的随机划分更为严格，虽然导致 QWK 偏低（约 0.58），但更能反映模型在真实场景下对新题目的泛化能力。中文翻译数据因同源性采用随机划分。"),

  Heading(HeadingLevel.HEADING_2, "3.3 语言检测与分词"),
  P("Web 版采用 langdetect 库进行细粒度语言识别，配合字符规则快速初筛。Android 版仅使用字符规则（统计 Unicode 范围 一-鿿 中的中文字符占比，>50% 判为中文），零外部 NLP 依赖。"),
  P("Android 版分词器为从零实现的 BERT WordPiece 算法：basicTokenize 处理中英文边界（中文逐字切分、英文按空格/标点拆分），wordPieceTokenize 执行贪心最长子词匹配（首次匹配不加前缀，后续匹配加 ## 前缀）。词表从 assets/vocab.txt 读取，约 100 行 Kotlin 代码，无需任何 Java NLP 库。"),

  Heading(HeadingLevel.HEADING_2, "3.4 多维度评分与反馈"),
  P("单任务模型只输出总评分。维度分（内容/结构/语言）通过启发式拆分生成：content = total × 0.95，structure = total × 1.02，language = total × 1.03。反馈基于分数等级（高 ≥0.7 / 中 ≥0.4 / 低）映射到预定义的中文评语模板，三个维度 + 总结共 12 条模板。"),

  Heading(HeadingLevel.HEADING_2, "3.5 Android 本地推理"),
  P("Android 版使用 PyTorch Mobile Lite (1.13.1) 加载训练好的 .pt 模型文件。模型文件（英文 418MB + 中文 391MB）从 assets 复制到内部存储后加载。推理在 Kotlin 协程中异步执行，结果通过 StateFlow 驱动 Compose UI 更新。分词器、语言检测、反馈生成全部在 Kotlin 层实现，无需桥接 Python。"),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== Chapter 4: Implementation Details ==========
const ch4 = [
  Heading(HeadingLevel.HEADING_1, "四、系统实现"),

  Heading(HeadingLevel.HEADING_2, "4.1 Web 版实现"),
  P("Web 版后端使用 Flask 框架提供 RESTful API，共 4 个端点：GET /api/v1/health（健康检查）、GET /api/v1/models（模型信息）、POST /api/v1/score（单篇评分）、POST /api/v1/batch（批量评分）。API 遵循统一的 JSON 响应格式（{success: bool, ...}），错误时包含 error 字段和对应的 HTTP 状态码。"),
  P("前端使用 Streamlit 框架构建，包含 4 个页面：评分主页（仪表盘 + 雷达图 + 反馈卡片）、批量评分（CSV 上传 + 结果表格）、中英对比（并排展示）、模型信息。通过 Streamlit 的 session_state 管理应用状态，Plotly 绘制仪表盘和雷达图。界面支持中英文完整切换（i18n JSON 文件）。"),

  Heading(HeadingLevel.HEADING_2, "4.2 Android 版实现"),
  P("Android 版使用 Kotlin + Jetpack Compose + Material3 构建。采用单 Activity 架构（MainActivity），通过 Compose Navigation 实现底部 Tab 导航（评分/批量/对比/设置 4 个 Tab）。关键技术决策包括："),

  Heading(HeadingLevel.HEADING_3, "4.2.1 项目结构"),
  P("应用采用分层包结构组织代码：inference/（推理引擎：BertTokenizer、AESPredictor、LanguageDetector）、ui/navigation/（导航）、ui/screen/（4 个页面）、ui/components/（可复用组件：RadarChart、ScoreGauge、FeedbackCard）。总代码量约 800 行 Kotlin。"),

  Heading(HeadingLevel.HEADING_3, "4.2.2 雷达图实现"),
  P("雷达图使用 Compose Canvas 自绘，不依赖第三方图表库。绘制逻辑包括：3 层六边形网格（背景参考线）、3 条轴线（120° 夹角）、数据路径（闭合多边形 + 半透明填充 + 描边）、数据点（小圆点）、文字标签（使用 Android native Canvas 绘制中文）。"),

  Heading(HeadingLevel.HEADING_3, "4.2.3 状态管理"),
  P("采用 Compose 标准状态管理：remember + mutableStateOf 管理 UI 状态，Kotlin Coroutines (Dispatchers.Default) 处理异步推理任务，通过 withContext(Dispatchers.Main) 切回主线程更新 UI。推理引擎 AESPredictor 使用懒加载模式，模型仅在首次使用时从 assets 加载到内存。"),

  Heading(HeadingLevel.HEADING_2, "4.3 API 接口设计"),
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [1400, 3000, 4960],
    rows: [
      new TableRow({ children: [headerCell("方法", 1400), headerCell("路径", 3000), headerCell("功能", 4960)] }),
      new TableRow({ children: [dataCell("GET", 1400), dataCell("/api/v1/health", 3000), dataCell("健康检查 + 模型加载状态", 4960)] }),
      new TableRow({ children: [dataCell("GET", 1400), dataCell("/api/v1/models", 3000), dataCell("模型注册表信息（名称/版本/QWK）", 4960)] }),
      new TableRow({ children: [dataCell("POST", 1400), dataCell("/api/v1/score", 3000), dataCell("单篇评分，body: {text, language}", 4960)] }),
      new TableRow({ children: [dataCell("POST", 1400), dataCell("/api/v1/batch", 3000), dataCell("批量评分，multipart CSV 上传", 4960)] }),
    ]
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== Chapter 5: Testing ==========
const ch5 = [
  Heading(HeadingLevel.HEADING_1, "五、测试与评估"),

  Heading(HeadingLevel.HEADING_2, "5.1 模型评估指标"),
  P("采用三个标准指标评估模型性能：(1) QWK (Quadratic Weighted Kappa)——衡量人机评分一致性的主要指标，通过二次权重矩阵计算评分偏差的惩罚，取值范围 [-1,1]，0.70+ 为可接受水平；(2) MAE (Mean Absolute Error)——平均绝对误差；(3) Pearson r——线性相关系数。"),

  Heading(HeadingLevel.HEADING_2, "5.2 模型表现"),
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2600, 2000, 2000, 2760],
    rows: [
      new TableRow({ children: [headerCell("模型", 2600), headerCell("Val QWK", 2000), headerCell("Test QWK", 2000), headerCell("备注", 2760)] }),
      new TableRow({ children: [dataCell("BERT-base 英文", 2600), dataCell("0.58", 2000), dataCell("—", 2000), dataCell("Prompt 隔离评估", 2760)] }),
      new TableRow({ children: [dataCell("BERT-base 中文", 2600), dataCell("0.79", 2000), dataCell("0.76", 2000), dataCell("翻译数据，随机划分", 2760)] }),
      new TableRow({ children: [dataCell("RoBERTa-base 英文", 2600), dataCell("0.58", 2000), dataCell("—", 2000), dataCell("备选模型", 2760)] }),
    ]
  }),
  P("英文模型 QWK 偏低的主要原因是严格的 prompt 隔离评估策略——训练集和测试集包含完全不同的作文题目，这更能反映真实场景下的泛化能力。中文模型 QWK 偏高是因为翻译数据同源，随机划分导致题目级别的信息泄露。"),

  Heading(HeadingLevel.HEADING_2, "5.3 系统测试"),
  P("Web 版测试分为两层：单元测试（17 项，pytest）覆盖数据预处理、API 端点、评估指标；E2E 测试（41 项，Playwright）覆盖 API 全端点 + UI 全页面交互。Android 版因本地演示场景未纳入自动化测试体系，通过手动测试验证核心功能。"),

  Heading(HeadingLevel.HEADING_2, "5.4 技术决策记录"),
  new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [3100, 6260],
    rows: [
      new TableRow({ children: [headerCell("决策", 3100), headerCell("理由", 6260)] }),
      new TableRow({ children: [dataCell("BERT-base 为主模型", 3100), dataCell("8GB 显存稳定运行，HuggingFace 生态成熟", 6260)] }),
      new TableRow({ children: [dataCell("中文采用翻译数据", 3100), dataCell("快速启动概念验证，避免数据收集团队瓶颈", 6260)] }),
      new TableRow({ children: [dataCell("Prompt 隔离划分（英文）", 3100), dataCell("防止题目级别数据泄露，评估真实泛化能力", 6260)] }),
      new TableRow({ children: [dataCell("Flask + Streamlit", 3100), dataCell("团队技能栈匹配，纯 Python 快速开发", 6260)] }),
      new TableRow({ children: [dataCell("Android PyTorch Mobile", 3100), dataCell("本地推理无需服务器，离线可用", 6260)] }),
      new TableRow({ children: [dataCell("不引入数据库/Docker/认证", 3100), dataCell("工程实践项目合理复杂度边界", 6260)] }),
    ]
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ========== Chapter 6: Summary ==========
const ch6 = [
  Heading(HeadingLevel.HEADING_1, "六、总结与展望"),

  Heading(HeadingLevel.HEADING_2, "6.1 项目成果"),
  Bullet("实现中英文双语 BERT 作文评分，支持语言自动检测和手动切换"),
  Bullet("支持多维度评分输出（总评分 + 内容/结构/语言）+ 雷达图可视化 + 模板化评语反馈"),
  Bullet("完成 Web 版（Flask API + Streamlit UI）和 Android 版（Kotlin + Jetpack Compose + PyTorch Mobile）双平台"),
  Bullet("Android 版实现完全本地推理，分词器、语言检测、反馈生成全部在 Kotlin 层自主实现"),
  Bullet("17 项单元测试 + 41 项 E2E 测试覆盖（Web 版）"),
  Bullet("英文模型 QWK 0.58（严格 prompt 隔离），中文模型 QWK 0.79"),

  Heading(HeadingLevel.HEADING_2, "6.2 已知限制"),
  Bullet("中文模型基于翻译数据训练，对自然中文表达的适应性有限"),
  Bullet("维度评分基于启发式拆分，非真正的多任务模型预测"),
  Bullet("512 token 长度限制，超长作文会被截断"),
  Bullet("Android 双模型 APK 约 800MB，体积过大需优化为首次启动下载"),
  Bullet("DeBERTa-v3 多任务模型在当前 transformers 版本下训练不稳定"),

  Heading(HeadingLevel.HEADING_2, "6.3 后续改进方向"),
  Bullet("收集中文母语作文人工评分数据，训练真正的自然中文评分模型"),
  Bullet("部署多任务 DeBERTa-v3 模型，替代启发式维度拆分"),
  Bullet("引入 Longformer 或分块策略支持超长文本评分"),
  Bullet("Android 版接入 LLM API 实现个性化评语生成"),
  Bullet("建立模型版本管理和持续评估体系"),
];

// ========== Assemble Document ==========
const doc = new Document({
  styles,
  numbering,
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "AES 作文自动评分系统 · 答辩报告", size: 18, font: "SimSun", color: "808080" })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "第 ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }), new TextRun({ text: " 页", size: 18 })]
        })]
      })
    },
    children: [
      ...coverPage,
      ...tocSection,
      ...ch1,
      ...ch2,
      ...ch3,
      ...ch4,
      ...ch5,
      ...ch6,
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  const outPath = "doc/AES_答辩报告.docx";
  fs.writeFileSync(outPath, buffer);
  console.log(`Done: ${outPath} (${(buffer.length / 1024).toFixed(0)} KB)`);
});
