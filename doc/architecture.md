# AES 系统设计文档

## 1. 系统概述

自动文本评分系统（Automated Essay Scoring, AES）是一个基于深度学习的**中英文双语**作文评分平台。系统接收学生作文文本，通过预训练 BERT 模型理解语义内容并自动产出分数与反馈。

### 1.1 核心功能

- 中英文双语评分（自动检测 / 手动切换）
- 多维度评分输出（总分 + 内容/结构/语言）
- 智能评语反馈（中英文模板）
- 批量评分（CSV）
- Web 可视化界面（Streamlit）
- Android 本地推理版（PyTorch Mobile，离线可用）

### 1.2 运行环境

- Python 3.10 / PyTorch 2.x
- RTX 5060 (8GB VRAM)
- 模型总大小 ~1.3 GB（英文 BERT 418M + RoBERTa 499M + 中文 BERT 391M）

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                      用户浏览器                           │
│                  http://localhost:8501                    │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼───────────────────────────────┐
│                   Streamlit UI (ui/)                      │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐             │
│  │ 评分页面 │  │ 批量评分  │  │ 中英对比     │             │
│  │ 仪表盘   │  │ CSV 上传  │  │ 并排展示     │             │
│  │ 雷达图   │  │ 结果下载  │  │              │             │
│  └─────────┘  └──────────┘  └──────────────┘             │
│  组件：score_gauge | radar_chart | feedback_card         │
│  国际化：i18n/zh.json | i18n/en.json                      │
└──────────────────────────┬───────────────────────────────┘
                           │ REST API
┌──────────────────────────▼───────────────────────────────┐
│                   Flask API (api/app.py)                  │
│                                                          │
│  GET  /api/v1/health    健康检查 + 模型状态               │
│  GET  /api/v1/models    模型注册表信息                    │
│  POST /api/v1/score     单篇评分（中/英文）               │
│  POST /api/v1/batch     批量评分（CSV）                   │
│                                                          │
│  错误处理：400(参数) / 404(路由) / 500(服务)               │
└──────────────────────────┬───────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────┐
│               推理引擎 (src/inference/)                    │
│                                                          │
│  AdvancedPredictor.predict(text, language)               │
│    │                                                     │
│    ├─ language="auto" → language_detector.py              │
│    │     ├─ 中文 → CNScoringModel (bert-base-chinese)     │
│    │     └─ 英文 → AESModel (bert-base-uncased)           │
│    │                                                     │
│    ├─ 文本预处理                                          │
│    │     ├─ 英文: preprocessor.py (HTML清理/URL移除)      │
│    │     └─ 中文: cn_preprocessor.py (jieba分词/全半角)  │
│    │                                                     │
│    ├─ 模型推理 → 得分 [0,1]                               │
│    │                                                     │
│    └─ 反馈生成 → feedback_generator.py                    │
│         ├─ 中文模板 (zh)                                  │
│         └─ 英文模板 (en)                                  │
│                                                          │
│  输出: {score, scores{total/content/structure/language}, │
│          feedback{...}, language, elapsed_ms}             │
└──────────────────────────────────────────────────────────┘
```

### 2.1 数据流 (单次评分)

```
用户输入文本
  → UI (st.text_area)
  → HTTP POST /api/v1/score {text, language}
  → Flask 路由 (api/app.py score())
  → 参数校验 (非空、≤10000字符、合法 JSON)
  → AdvancedPredictor.predict()
    → 语言检测 (langdetect + 字符规则)
    → 文本预处理 (clean → tokenize)
    → 模型推理 (GPU, fp16)
    → 分数后处理 (NaN保护)
    → 反馈生成 (分数→等级→模板→文字)
  → JSON 响应 {success, score, scores, feedback, language, elapsed_ms}
  → UI 渲染 (仪表盘 + 雷达图 + 反馈卡片)
```

---

## 3. 模型架构

### 3.1 英文模型

```
输入文本 (英文)
  → BERT Tokenizer (WordPiece, 30522 vocab)
  → BERT-base-uncased (12层, 768维, 110M参数)
  → [CLS] 向量 (768维)
  → Dropout (0.1) → Linear (768→1) → Sigmoid
  → 输出分数 ∈ [0, 1]
```

- 模型类：`src/models/aes_model.py::AESModel`
- 推理引擎：`src/inference/advanced_predictor.py::AdvancedPredictor`
- 多维分数通过启发式拆分（总分 ± 微小偏移）

### 3.2 中文模型

```
输入文本 (中文)
  → jieba 分词 (词间加空格)
  → BERT Tokenizer (WordPiece, 21128 vocab)
  → BERT-base-chinese (12层, 768维, 110M参数)
  → [CLS] 向量 (768维)
  → Dropout (0.1) → Linear (768→1) → Sigmoid
  → 输出分数 ∈ [0, 1]
```

- 模型类：`src/models/advanced_model.py::CNScoringModel`

### 3.3 多任务模型（已实现，未部署）

进阶多任务变体在同一个编码器上添加 4 个回归头，分别预测总评分、内容、结构、语言：

```
BERT/DeBERTa 编码器 → [CLS] 向量
  ├→ Head_0: 总评分 (Linear + Sigmoid)
  ├→ Head_1: 内容   (Linear + Sigmoid)
  ├→ Head_2: 结构   (Linear + Sigmoid)
  └→ Head_3: 语言   (Linear + Sigmoid)
```

- 模型类：`src/models/advanced_model.py::AESMultiTaskModel`

---

## 4. 数据处理流水线

### 4.1 英文数据预处理

```
原始 ASAP CSV
  → HTML unescape (&amp; → & 等)
  → @mention / URL 移除
  → 空白规范化 (\s+ → 单个空格)
  → 按 essay_set 归一化分数 (min-max → [0,1])
  → BERT 分词 (max_length=512, truncation, padding)
  → 按 essay_set 隔离划分 (train/val/test)
```

### 4.2 中文数据预处理

```
原始 ASAP CSV (英文)
  → Google Translate (deep-translator, en→zh)
  → 全角转半角、控制字符移除
  → jieba 分词 (词间空格)
  → 按 essay_set 归一化分数
  → BERT 分词 (max_length=512)
  → 随机划分 (翻译数据同源)
```

### 4.3 训练配置

| 参数 | 英文 | 中文 |
|------|------|------|
| 模型 | bert-base-uncased | bert-base-chinese |
| 学习率 | 2e-5 | 2e-5 |
| Batch Size | 16 | 8 |
| Epochs | 5 | 5 |
| 早停 Patience | 3 | 3 |
| 精度 | fp16 | fp32 |
| 优化器 | AdamW (wd=0.01) | AdamW (wd=0.01) |
| 调度器 | Linear warmup (10%) + decay | Linear warmup (10%) + decay |
| 划分策略 | Essay-set 隔离 | 随机 |

---

## 5. 评估指标

### 5.1 QWK (Quadratic Weighted Kappa)

主要评估指标，衡量模型评分与人工评分的一致性：

$$\kappa = 1 - \frac{\sum w_{ij} O_{ij}}{\sum w_{ij} E_{ij}}$$

其中 $w_{ij} = (i-j)^2$ 为二次权重矩阵，$O_{ij}$ 为观测一致矩阵，$E_{ij}$ 为期
望一致矩阵。QWK ∈ [-1, 1]，0.70+ 为可接受水平。

### 5.2 MAE (Mean Absolute Error)

$$MAE = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$$

### 5.3 模型表现

| 模型 | Val QWK | Test QWK | 备注 |
|------|---------|----------|------|
| BERT-base 英文 | 0.58 | — | 严格的 prompt 隔离评估 |
| BERT-base 中文 | 0.79 | 0.76 | 翻译数据，随机划分评估 |

---

## 6. API 接口设计

### 6.1 通用约定

- Content-Type: `application/json`
- 成功响应：`{"success": true, ...}`
- 错误响应：`{"success": false, "error": "描述"}`
- HTTP 状态码：200(成功) / 400(参数错误) / 404(路由不存在) / 500(服务错误)

### 6.2 端点一览

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/v1/health | 健康检查 |
| GET | /api/v1/models | 模型信息 |
| POST | /api/v1/score | 单篇评分 |
| POST | /api/v1/batch | 批量评分(CSV) |

---

## 7. 反馈生成

反馈基于维度分数区间模板映射：

```
得分 ∈ [0, 1] → 等级判断:
  ≥ 0.7 → "high"
  ≥ 0.4 → "mid"
  < 0.4 → "low"

各维度 × 等级 → 预定义模板文字

中英文各 3×3 = 9 条维度模板 + 3 条总结模板
```

---

## 8. 测试策略

| 层级 | 工具 | 覆盖 |
|------|------|------|
| 单元测试 (17项) | pytest | 数据预处理、API 端点、评估指标 |
| E2E 测试 (41项) | Playwright | API 全端点 + UI 全页面交互 |

运行：
```bash
pytest tests/ -v          # 单元测试
python tests/test_e2e.py  # E2E 测试
```

---

## 9. 技术决策记录

| 决策 | 理由 |
|------|------|
| BERT-base 为主模型的优先顺序 | 8GB 显存稳定运行，生态成熟 |
| 中文采用翻译数据而非收集真实数据 | 快速启动，作为概念验证 |
| 评分归一化按 essay_set 而非全局 | 避免分数挤压，保持各题目的可比性 |
| Prompt 隔离划分（英文） | 防止题目级别的数据泄露 |
| 随机划分（中文） | 翻译数据同源，prompt 隔离意义有限 |
| Flask + Streamlit 而非 FastAPI + React | 团队技能栈匹配，快速开发 |
| 不引入数据库/Docker/认证 | 工程实践项目的合理复杂度边界 |

---

## 10. 已知限制

1. **中文模型领域偏移**：翻译数据训练的模型对自然中文表达适应性有限
2. **维度评分非真正多任务**：当前维度分通过启发式拆分得到
3. **512 token 限制**：超长作文会被截断
4. **DeBERTa-v3 兼容性**：当前 transformers 版本下训练不稳定
5. **Android 模型体积**：双模型 ~800MB，APK 体积过大，需优化为首次启动下载

---

## 11. Android App 架构

Android 版与 Web 版共享模型权重，但推理在手机本地执行，不依赖服务器。

### 11.1 系统架构

```
┌──────────────────────────────────────────────────┐
│              Jetpack Compose UI                   │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │ 评分  │  │ 批量  │  │ 对比  │  │ 设置  │         │
│  │Tab   │  │Tab   │  │Tab   │  │Tab   │         │
│  └──────┘  └──────┘  └──────┘  └──────┘         │
│  Material3 NavigationBar                         │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│            推理引擎 (inference/)                   │
│                                                   │
│  AESPredictor.predict(text, language)            │
│    │                                              │
│    ├─ LanguageDetector (字符规则，零依赖)          │
│    ├─ BertTokenizer (Kotlin WordPiece 实现)       │
│    ├─ PyTorch Mobile 模型加载 (.pt from assets)    │
│    └─ 反馈生成 (中文模板，同 Python 版)            │
│                                                   │
│  依赖: org.pytorch:pytorch_android_lite:1.13.1   │
└──────────────────────┬───────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────┐
│                 assets/ (本地文件)                 │
│  bert_model.pt (英文, 418MB)                     │
│  zh_model.pt   (中文, 391MB)                     │
│  vocab.txt     (英文词表, 30522 tokens)           │
│  zh_vocab.txt  (中文词表, 21128 tokens)           │
└──────────────────────────────────────────────────┘
```

### 11.2 与 Web 版的对比

| 维度 | Web 版 | Android 版 |
|------|--------|-----------|
| 推理位置 | Flask 服务器 (GPU) | 手机本地 (CPU) |
| 模型加载 | Python PyTorch | PyTorch Mobile Lite |
| 分词器 | HuggingFace Transformers | Kotlin 自实现 WordPiece |
| 语言检测 | langdetect + 字符规则 | 字符规则（零依赖） |
| UI 框架 | Streamlit + Plotly | Jetpack Compose + Canvas |
| 网络依赖 | 需要 HTTP 连接 | 完全离线 |
| 推理速度 | ~200ms (fp16 GPU) | ~1-5s (CPU) |

### 11.3 分词器实现

Android 版分词器约 100 行 Kotlin 代码，不依赖任何 Java NLP 库：

```
输入文本
  → basicTokenize(): 按空格/标点分词，中文逐字切分
  → wordPieceTokenize(): 贪心最长子词匹配，##前缀标记
  → [CLS] + tokens + [SEP] → LongArray(512)
```

词表从 assets/vocab.txt 读取（每行一个 token），构建 HashMap<String, Int>。中文检测通过 Unicode 范围 `一-鿿` 统计中文字符占比。

### 11.4 技术栈

| 层级 | 技术 |
|------|------|
| UI | Jetpack Compose + Material3 |
| 导航 | Compose Navigation (Bottom Bar) |
| 推理 | PyTorch Mobile Lite 1.13.1 |
| 图表 | Compose Canvas 自绘雷达图 |
| 异步 | Kotlin Coroutines |
| 最低 SDK | 29 (Android 10) |
| 语言 | Kotlin |
