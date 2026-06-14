/**
 * AES 自动作文评分系统 — 答辩报告 Word 文档生成脚本
 *
 * Usage: node scripts/gen_defense_report_v2.js
 */

'use strict';

const fs   = require('fs');
const path = require('path');

const {
  Document, Packer,
  Paragraph, TextRun, Math, MathRun,
  Table, TableRow, TableCell,
  Header, Footer,
  PageNumber, AlignmentType, LineRuleType, HeadingLevel,
  LevelFormat, LevelSuffix, BorderStyle, WidthType, ShadingType, VerticalAlign,
  TableOfContents, PageBreak, ImageRun, SequentialIdentifier,
} = require('docx');

const { mathmlToDocxChildren } = require('/home/jianp/.claude/skills/docx-editor-cn/scripts/mathml-to-docx');
const temml = require('temml');

// ── Constants ─────────────────────────────────────────────────────────────
const OUTPUT_PATH = 'doc/AES_答辩报告.docx';
const PAGE_W  = 11906;   // A4
const PAGE_H  = 16838;
const MARGIN  = 1418;    // 2.5cm
const CONTENT_W = PAGE_W - 2 * MARGIN;  // 9070 DXA

const THICK = { style: BorderStyle.SINGLE, size: 12, color: '000000' };
const THIN  = { style: BorderStyle.SINGLE, size: 6,  color: '000000' };
const NONE  = { style: BorderStyle.NONE,   size: 0,  color: 'FFFFFF' };

let _chapter = 0;
const TOTAL_CHAPTERS = 6;

// ── Helpers ─────────────────────────────────────────────────────────────

function h1Chinese(text) {
  _chapter++;
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    indent: { firstLine: 0 },
    children: [new TextRun(text)],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    numbering: { reference: `sections_c${_chapter}`, level: 0 },
    indent: { firstLine: 0 },
    children: [new TextRun(text)],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    numbering: { reference: `sections_c${_chapter}`, level: 1 },
    indent: { firstLine: 0 },
    children: [new TextRun(text)],
  });
}

function body(text) {
  return new Paragraph({ children: [new TextRun(text)] });
}

function bodyMulti(runs) {
  return new Paragraph({ children: runs });
}

function blank() {
  return new Paragraph({ children: [] });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function tableCaption(text) {
  return new Paragraph({
    style: 'TableCaption',
    children: [
      new TextRun(`表 ${_chapter}-`),
      new SequentialIdentifier(`table_c${_chapter}`),
      new TextRun(` ${text}`),
    ],
  });
}

function figCaption(text) {
  return new Paragraph({
    style: 'FigureCaption',
    children: [
      new TextRun(`图 ${_chapter}-`),
      new SequentialIdentifier(`figure_c${_chapter}`),
      new TextRun(` ${text}`),
    ],
  });
}

function threeLineTable(headers, rows, colWidths) {
  const n = headers.length;
  if (!colWidths) {
    const w = Math.floor(CONTENT_W / n);
    colWidths = Array(n).fill(w);
    colWidths[n - 1] = CONTENT_W - w * (n - 1);
  }
  const cellOf = (text, w, borders, bold = false) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    borders,
    shading: { fill: 'FFFFFF', type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      indent: { firstLine: 0 },
      children: [new TextRun({ text: String(text), bold })],
    })],
  });

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => cellOf(h, colWidths[i], { top: THICK, bottom: THIN, left: NONE, right: NONE }, true)),
  });
  const bodyRows = rows.map((row, ri) => {
    const isLast = ri === rows.length - 1;
    return new TableRow({
      children: row.map((cell, i) => cellOf(String(cell), colWidths[i], {
        top: NONE, bottom: isLast ? THICK : NONE, left: NONE, right: NONE,
      })),
    });
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...bodyRows],
  });
}

function ref(text) {
  return new Paragraph({
    style: 'Reference',
    numbering: { reference: 'references', level: 0 },
    children: [new TextRun(text)],
  });
}

// formula support
function latexToMath(latex) {
  try {
    const mathml = temml.renderToString(latex, { displayMode: true, throwOnError: false });
    const children = mathmlToDocxChildren(mathml);
    if (children && children.length) return new Math({ children });
  } catch (e) {}
  return new Math({ children: [new MathRun(latex)] });
}

function formula(latex, number) {
  const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE };
  const leftCell = new TableCell({
    width: { size: 567, type: WidthType.DXA }, borders: noBorders,
    shading: { fill: 'FFFFFF', type: ShadingType.CLEAR },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ indent: { firstLine: 0 }, children: [] })],
  });
  const mathObj = latexToMath(latex);
  const formulaCell = new TableCell({
    width: { size: 7936, type: WidthType.DXA }, borders: noBorders,
    shading: { fill: 'FFFFFF', type: ShadingType.CLEAR },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, children: [mathObj] })],
  });
  const numberCell = new TableCell({
    width: { size: 567, type: WidthType.DXA }, borders: noBorders,
    shading: { fill: 'FFFFFF', type: ShadingType.CLEAR },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: AlignmentType.RIGHT, indent: { firstLine: 0 }, children: [new TextRun(`(${number})`)] })],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [567, 7936, 567],
    borders: { top: NONE, bottom: NONE, left: NONE, right: NONE, insideHorizontal: NONE, insideVertical: NONE },
    rows: [new TableRow({ children: [leftCell, formulaCell, numberCell] })],
  });
}

// ── Numbering ─────────────────────────────────────────────────────────

function buildNumberingConfig(chapterCount) {
  const configs = [
    { reference: 'references', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '[%1]', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 480 } } } }] },
    { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ];
  for (let c = 1; c <= chapterCount; c++) {
    configs.push({ reference: `sections_c${c}`, levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: `${c}.%1`, suffix: LevelSuffix.SPACE, alignment: AlignmentType.LEFT },
      { level: 1, format: LevelFormat.DECIMAL, text: `${c}.%1.%2`, suffix: LevelSuffix.SPACE, alignment: AlignmentType.LEFT },
    ]});
  }
  return { config: configs };
}

const NUMBERING = buildNumberingConfig(TOTAL_CHAPTERS);

// ── Styles ────────────────────────────────────────────────────────────

const STYLES = {
  default: {
    document: {
      run: { font: { ascii: 'Cambria Math', hAnsi: 'Cambria Math', eastAsia: 'SimSun' }, size: 24 },
      paragraph: { spacing: { line: 240, lineRule: LineRuleType.AUTO }, indent: { firstLine: 480 } },
    },
  },
  paragraphStyles: [
    { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' }, size: 32, bold: true },
      paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { line: 288, lineRule: LineRuleType.AUTO }, outlineLevel: 0 } },
    { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' }, size: 28, bold: true },
      paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { line: 360, lineRule: LineRuleType.AUTO }, outlineLevel: 1 } },
    { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' }, size: 24, bold: true },
      paragraph: { alignment: AlignmentType.LEFT, indent: { firstLine: 0 }, spacing: { line: 264, lineRule: LineRuleType.AUTO }, outlineLevel: 2 } },
    { id: 'FigureCaption', name: 'Figure Caption', basedOn: 'Normal',
      run: { font: { ascii: 'Cambria Math', eastAsia: 'SimSun', hAnsi: 'Cambria Math' }, size: 22, bold: true },
      paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 120, after: 60, line: 240, lineRule: LineRuleType.AUTO } } },
    { id: 'TableCaption', name: 'Table Caption', basedOn: 'Normal',
      run: { font: { ascii: 'Cambria Math', eastAsia: 'SimSun', hAnsi: 'Cambria Math' }, size: 22, bold: true },
      paragraph: { alignment: AlignmentType.CENTER, indent: { firstLine: 0 }, spacing: { before: 120, after: 60, line: 240, lineRule: LineRuleType.AUTO } } },
    { id: 'Reference', name: 'Reference', basedOn: 'Normal',
      run: { font: { ascii: 'Cambria Math', hAnsi: 'Cambria Math', eastAsia: 'SimSun' }, size: 24 },
      paragraph: { spacing: { line: 240, lineRule: LineRuleType.AUTO }, indent: { left: 480, hanging: 480, firstLine: 0 } } },
  ],
};

// ── CONTENT ────────────────────────────────────────────────────────────

const CONTENT = [
  // ── Cover Page ──────────────────────────────────────────────────────
  blank(), blank(), blank(), blank(), blank(),
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 },
    children: [new TextRun({ text: 'AES 自动作文评分系统', bold: true, size: 44, font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' } })] }),
  blank(),
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 },
    children: [new TextRun({ text: 'Automated Essay Scoring System', bold: true, size: 28, font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' } })] }),
  blank(), blank(),
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 },
    children: [new TextRun({ text: '答辩报告', size: 32, font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' } })] }),
  blank(), blank(), blank(),
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 },
    children: [new TextRun('基于深度学习的英文/中文作文智能评分系统')] }),
  blank(), blank(),
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 },
    children: [new TextRun('工程实践项目  2026年6月')] }),
  pageBreak(),
  pageBreak(),

  // ── TOC ─────────────────────────────────────────────────────────────
  new Paragraph({ alignment: AlignmentType.CENTER, indent: { firstLine: 0 },
    children: [new TextRun({ text: '目  录', bold: true, size: 32, font: { ascii: 'Cambria Math', eastAsia: 'SimHei', hAnsi: 'Cambria Math' } })] }),
  blank(),
  new TableOfContents('目录', { hyperlink: true, headingStyleRange: '1-3' }),
  pageBreak(),

  // ══════════════════════════════════════════════════════════════════════
  // Chapter 1: 项目背景
  // ══════════════════════════════════════════════════════════════════════
  h1Chinese('一、项目背景'),
  blank(),

  h2('问题定义'),
  blank(),
  body('作文评分是教育领域最耗时的工作之一。一名语文或英语教师通常需要批阅4-6个班级的作文，每篇作文的评分与评语撰写需要5-10分钟，单次作文批改工作量可达15-20小时。传统的自动评分方法依赖于人工定义的浅层特征（如词汇复杂度、句长、语法错误数等），这些方法难以捕捉文本的深层语义信息，评分准确度有限。'),
  blank(),
  body('本项目旨在利用深度学习技术，构建一个能够自动评估中英文作文质量的评分系统，通过预训练语言模型（BERT）理解文本的语义内容，输出总分、多维度分项分以及文字评语反馈。'),
  blank(),

  h2('研究意义'),
  blank(),
  body('自动作文评分（AES）在教育技术领域具有重要的应用价值：首先，它可以大幅减轻教师的批改负担，让教师有更多时间进行针对性教学设计；其次，它可以为学生提供即时的写作反馈，提高学习效率；第三，标准化的自动评分可以消除人工评分中的主观偏差，保证评分一致性。此外，完整的工程实现（包括Web端和移动端）也展示了从科研模型到可部署产品的完整技术链路。'),
  blank(),

  h2('现有方案与不足'),
  blank(),
  body('当前主流的AES方法主要分为两类：基于特征工程的传统方法和基于深度学习的方法。传统方法（如E-rater、Intelligent Essay Assessor）依赖手工设计的词汇、语法和篇章特征，浅层特征难以捕捉深层语义。深度学习方法（如基于LSTM或BERT的模型）虽然效果更好，但大多仅支持英文评分，且缺乏从Web到移动端的全平台覆盖。本项目同时支持中英文双语评分，并提供Web版和Android版两个完整前端。'),
  blank(),

  // ══════════════════════════════════════════════════════════════════════
  // Chapter 2: 系统架构
  // ══════════════════════════════════════════════════════════════════════
  h1Chinese('二、系统架构'),
  blank(),

  h2('整体架构设计'),
  blank(),
  body('系统采用分层架构，从下到上分为数据层、模型层和应用层三个层次。数据层负责文本数据的清洗、归一化和数据集划分；模型层基于预训练BERT模型构建回归网络，实现从文本到分数的端到端映射；应用层包含Flask REST API、Streamlit Web UI和Android原生App三个独立的前端。'),
  blank(),

  h2('Web版架构'),
  blank(),
  body('Web版采用经典的C/S架构：后端使用Flask框架提供RESTful API（4个端点：健康检查/模型信息/单篇评分/批量评分），前端使用Streamlit框架提供交互式Web界面（4个页面：评分/批量评分/中英对比/设置）。前后端通过HTTP JSON通信，模型在Flask服务启动时预加载到GPU内存，推理在GPU上以fp16精度执行。'),
  blank(),

  h2('Android版架构'),
  blank(),
  body('Android版采用纯本地推理架构，不需要网络连接和后端服务器。App使用PyTorch Mobile Lite加载TorchScript模型文件（.pt），BERT分词器由Kotlin从零实现（约100行代码，零外部NLP库依赖），语言检测通过简单的Unicode字符范围规则判断中英文。UI使用Jetpack Compose + Material3实现，包括4个底部Tab导航页面（评分/批量/对比/设置），雷达图使用Compose Canvas自绘，不依赖第三方图表库。'),
  blank(),

  tableCaption('Web版与Android版架构对比'),
  threeLineTable(
    ['维度', 'Web 版', 'Android 版'],
    [
      ['推理位置', 'Flask 服务器 (GPU)', '手机本地 (CPU)'],
      ['模型加载', 'Python PyTorch', 'PyTorch Mobile Lite'],
      ['分词器', 'HuggingFace Transformers', 'Kotlin 自实现 WordPiece'],
      ['UI 框架', 'Streamlit + Plotly', 'Jetpack Compose + Canvas'],
      ['网络依赖', '需要 HTTP 连接', '完全离线'],
      ['推理速度', '~200ms (fp16 GPU)', '~1-5s (CPU)'],
    ],
    [2200, 3435, 3435]
  ),
  blank(),

  // ══════════════════════════════════════════════════════════════════════
  // Chapter 3: 技术方案
  // ══════════════════════════════════════════════════════════════════════
  h1Chinese('三、技术方案'),
  blank(),

  h2('模型设计'),
  blank(),
  body('英文模型基于BERT-base-uncased（12层Transformer、768维隐藏层、110M参数），在[CLS]标记的输出向量上添加一个Dropout层（p=0.1）和一个线性回归头（768→1），最后通过Sigmoid函数将输出映射到[0,1]区间。中文模型基于BERT-base-chinese（相同架构，21128词汇表），采用相同的回归头设计。'),
  blank(),
  body('此外，架构上已预留了多任务变体（AESMultiTaskModel），在同一个编码器上添加4个独立的回归头，分别预测总评分、内容分、结构分和语言分，只需维度标注数据即可训练。'),
  blank(),

  h2('数据处理流水线'),
  blank(),
  body('英文数据来自ASAP自动作文评分竞赛数据集（12,979篇），预处理流程包括：HTML转义字符解码、@提及和URL移除、空白规范化、按essay_set归一化分数（min-max映射至[0,1]）、BERT分词和按essay_set级别的训练/验证/测试隔离划分。'),
  blank(),
  body('中文数据通过将英文作文经Google Translate翻译生成（3,950篇），预处理流程包括：全角转半角、控制字符移除、jieba分词（词间加空格）、归一化和BERT分词。翻译数据的局限性在于可能存在翻译腔，对自然中文表达的适应性有限。'),
  blank(),

  h2('训练策略'),
  blank(),
  body('英文模型采用AdamW优化器（weight_decay=0.01），学习率2e-5，batch size 16，训练5个epochs，配合线性预热（10%步数）和线性衰减调度，使用fp16混合精度训练。中文模型batch size降至8，使用fp32精度。两个模型均设置早停patience=3。英文模型采用严格的prompt隔离划分——不同essay_set的作文不会同时出现在训练集和测试集中，这避免了题目级别的数据泄露，是更真实的跨题目泛化评估。'),
  blank(),

  tableCaption('训练超参数配置'),
  threeLineTable(
    ['参数', '英文模型', '中文模型'],
    [
      ['基础模型', 'bert-base-uncased', 'bert-base-chinese'],
      ['学习率', '2e-5', '2e-5'],
      ['Batch Size', '16', '8'],
      ['训练轮数', '5', '5'],
      ['早停 Patience', '3', '3'],
      ['计算精度', 'fp16', 'fp32'],
      ['优化器', 'AdamW (wd=0.01)', 'AdamW (wd=0.01)'],
      ['数据集划分', 'Essay-set 隔离', '随机划分'],
    ],
    [2500, 3285, 3285]
  ),
  blank(),

  h2('评估指标'),
  blank(),
  body('主要评估指标为二次加权Kappa系数（QWK），用于衡量模型评分与人工评分之间的一致性。QWK = 1 - (Σw_ij O_ij) / (Σw_ij E_ij)，其中w_ij = (i-j)^2为二次权重矩阵，O_ij为观测一致矩阵，E_ij为期望一致矩阵。QWK ∈ [-1, 1]，0.70+为可接受水平。辅助指标包括MAE（平均绝对误差）和Pearson相关系数。'),
  blank(),

  // ══════════════════════════════════════════════════════════════════════
  // Chapter 4: 实现细节
  // ══════════════════════════════════════════════════════════════════════
  h1Chinese('四、实现细节'),
  blank(),

  h2('Python推理引擎'),
  blank(),
  body('推理引擎（AdvancedPredictor）负责管理模型生命周期和评分流水线。predict方法接收文本和语言参数，依次执行：语言自动检测（langdetect库 + 字符规则）、文本预处理（英文：HTML清理/URL移除，中文：jieba分词/全半角转换）、模型推理（GPU fp16）、分数后处理（NaN保护、维度分启发式拆分）和反馈生成（分数→等级→模板→文字）。'),
  blank(),

  h2('Flask REST API'),
  blank(),
  body('API层提供4个端点：GET /api/v1/health 返回服务状态和模型加载情况；GET /api/v1/models 返回模型注册表信息；POST /api/v1/score 接收{text, language}进行单篇评分；POST /api/v1/batch 接收CSV文件进行批量评分。所有响应采用统一的JSON格式（success + data/error），HTTP状态码明确区分成功(200)、参数错误(400)、路由不存在(404)和服务错误(500)。'),
  blank(),

  h2('Streamlit Web UI'),
  blank(),
  body('Web前端使用Streamlit构建，4个页面分别对应评分、批量评分、中英对比和模型设置。评分页面提供语言选择、文本输入、分数仪表盘、Plotly雷达图和反馈卡片。UI支持中英文两种语言切换（通过i18n JSON文件实现国际化）。核心UI组件包括：总分仪表盘（大号数字+渐变进度条）、三维度卡片（内容/结构/语言，带颜色编码）、雷达图可视化和模板化反馈评语。'),
  blank(),

  h2('Android端实现'),
  blank(),
  body('Android App使用Kotlin + Jetpack Compose开发，最低支持Android 10（API 29）。推理引擎使用PyTorch Mobile Lite 1.13.1加载TorchScript模型，模型文件（.pt）打包在APK的assets目录中。应用架构分为三层：推理层（inference/，包含AESPredictor、BertTokenizer、LanguageDetector）、UI组件层（ui/components/，包含ScoreGauge、RadarChart、FeedbackCard）和页面层（ui/screen/，4个Tab页面）。'),
  blank(),

  h2('BERT分词器实现'),
  blank(),
  body('Android版的核心技术亮点之一是Kotlin原生的BERT WordPiece分词器实现（约100行代码，零外部NLP库依赖）。分词过程分为三个步骤：basicTokenize阶段按空格/标点分词，中文字符逐字切分；wordPieceTokenize阶段进行贪心最长子词匹配，未匹配的词段使用##前缀的子词拼接；最后在序列前后添加[CLS]和[SEP]标记，截断或填充至512个token。词表从assets目录的vocab.txt文件加载，构建HashMap<String, Int>供快速查找。'),
  blank(),

  // ══════════════════════════════════════════════════════════════════════
  // Chapter 5: 测试结果
  // ══════════════════════════════════════════════════════════════════════
  h1Chinese('五、测试结果'),
  blank(),

  h2('模型表现'),
  blank(),

  tableCaption('模型评估结果'),
  threeLineTable(
    ['模型', 'Val QWK', 'Test QWK', '评估方式'],
    [
      ['BERT-base 英文', '0.58', '—', '严格 prompt 隔离评估'],
      ['BERT-base 中文', '0.79', '0.76', '翻译数据，随机划分评估'],
    ],
    [3000, 2000, 2000, 2070]
  ),
  blank(),
  body('英文模型QWK约0.58，数值看似偏低，但这是在严格的prompt隔离条件下的结果——训练集和测试集包含完全不同的作文题目，这比同题目内随机划分更严格，更能反映模型对新题目的泛化能力。中文模型QWK 0.79是在随机划分条件下得到的，偏高，因为翻译数据同源。'),
  blank(),

  h2('单元测试'),
  blank(),
  body('项目包含17项单元测试（pytest），覆盖数据预处理模块（cleaner、normalizer、splitter、tokenizer）和API端点（health、models、score、batch）。测试用例包括正常输入验证和边界条件（空文本、超长文本、缺失参数等）的异常处理。运行方式：pytest tests/ -v。'),
  blank(),

  h2('端到端测试'),
  blank(),
  body('项目包含41项端到端测试（Playwright），覆盖Flask API全部4个端点的正常/异常场景以及Streamlit UI全部4个页面的交互功能验证。测试自动启动Flask和Streamlit服务，在无界面浏览器中执行用户操作流程，验证响应数据的完整性和正确性。运行方式：python tests/test_e2e.py。'),
  blank(),

  // ══════════════════════════════════════════════════════════════════════
  // Chapter 6: 总结与展望
  // ══════════════════════════════════════════════════════════════════════
  h1Chinese('六、总结与展望'),
  blank(),

  h2('项目成果'),
  blank(),
  body('本项目完成了一个完整的AES自动作文评分系统，主要成果包括：实现了基于BERT的中英文双语作文自动评分模型（英文QWK 0.58 / 中文QWK 0.79）；构建了Flask REST API + Streamlit Web UI的完整Web服务；开发了基于PyTorch Mobile的Android原生App（离线推理、Kotlin自实现WordPiece分词器）；编写了17项单元测试和41项端到端测试；产出了完整的技术文档（架构设计、答辩脚本、Word报告、PPT）。'),
  blank(),

  h2('已知限制'),
  blank(),
  body('系统存在以下已知限制：中文模型基于翻译数据训练，对自然中文表达的适应性有限；当前维度评分通过启发式拆分得到（总分×系数），非真正的多任务联合推理；BERT的512 token输入限制导致超长作文被截断；Android双模型体积约800MB，APK过大需优化；DeBERTa-v3大模型在当前环境训练不稳定，未投入使用。'),
  blank(),

  h2('改进方向'),
  blank(),
  body('后续改进方向包括：收集真实中文作文数据替代翻译数据，提升中文模型的领域适应性；为多任务模型（AESMultiTaskModel，4个独立回归头）收集维度标注数据，实现真正的多维度联合评分；引入Longformer或BigBird等长文本模型支持超长作文；Android端考虑模型量化（INT8）以减小APK体积和加速推理；基于用户反馈持续优化评语模板的多样性和针对性。'),
  blank(),

  // ── References ───────────────────────────────────────────────────────
  pageBreak(),

  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    indent: { firstLine: 0 },
    children: [new TextRun('参考文献')],
  }),
  blank(),
  ref('Devlin J, Chang M W, Lee K, et al. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding[C]//Proceedings of NAACL-HLT. 2019: 4171-4186.'),
  ref('Vaswani A, Shazeer N, Parmar N, et al. Attention Is All You Need[C]//Advances in Neural Information Processing Systems. 2017: 5998-6008.'),
  ref('Taghipour K, Ng H T. A Neural Approach to Automated Essay Scoring[C]//Proceedings of EMNLP. 2016: 1882-1891.'),
  ref('Phandi P, Chai K M A, Ng H T. Flexible Domain Adaptation for Automated Essay Scoring Using Correlated Linear Regression[C]//Proceedings of EMNLP. 2015: 431-439.'),
  ref('Shermis M D, Burstein J. Automated Essay Scoring: A Cross-Disciplinary Perspective[M]. Lawrence Erlbaum Associates, 2003.'),
  ref('Wolf T, Debut L, Sanh V, et al. Transformers: State-of-the-Art Natural Language Processing[C]//Proceedings of EMNLP: System Demonstrations. 2020: 38-45.'),
];

// ── Build & Write ─────────────────────────────────────────────────────

const doc = new Document({
  styles: STYLES,
  numbering: NUMBERING,
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            indent: { firstLine: 0 },
            children: [new TextRun({ children: [PageNumber.CURRENT] })],
          }),
        ],
      }),
    },
    children: CONTENT,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.resolve(OUTPUT_PATH);
  fs.writeFileSync(out, buf);
  console.log(`Done: ${out}`);
}).catch(err => {
  console.error('Error building document:', err.message);
  process.exit(1);
});
