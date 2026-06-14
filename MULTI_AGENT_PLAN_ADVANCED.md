# 进阶版 AES 系统 — 工程实践方案

## 项目定位

在 MVP 基础上进行模型升级和功能扩展，目标是构建一个**支持中英文双语**、**多维度评分**、**界面精美**的自动文本评分系统，适合工程实践作业答辩演示。

**硬件**：RTX 5060 8GB VRAM
**基线**：ASAP QWK ~0.70，BERT-base，仅英文，单页 UI
**目标**：中英文评分 + 三维度反馈 + 多页面演示 UI

---

## 核心升级方向

| 维度 | MVP | 进阶版 |
|------|-----|--------|
| 英文模型 | BERT-base | DeBERTa-v3-base |
| 长文本 | 截断 512 token | Longformer + 分块策略 |
| 中文 | 无 | BERT-base-chinese |
| 输出 | 单一分数 | 总分 + 内容/结构/语言三维度 + 反馈文字 |
| 批量 | 无 | CSV 上传批量评分（同步） |
| 界面 | 单页 | 多页面（评分/批量/历史/对比） |
| 部署 | 本地裸跑 | 本地裸跑（不容器化） |

**不引入的内容**：数据库（无 SQLite/PostgreSQL）、用户认证（无 JWT/登录）、任务队列（无 Celery/Redis）、Docker、监控仪表板。保持工程实践作业的合理复杂度。

---

## 模型方案

### AD-001：英文主模型 — DeBERTa-v3-base

- DeBERTa-v3-base（86M 参数），比 BERT-base（110M）更小但 GLUE 表现更强
- 8GB 显存下 batch_size=16 训练，fp16 推理 ~0.8GB
- DeBERTa-v3-large（304M）作为可选升级路径

### AD-002：长文本 — Longformer-base + 分块降级

- Longformer-base（149M，4096 token 上限）处理 >512 token 的长作文
- 分块策略（sliding window + mean pooling）作为轻量降级方案
- 推理时根据 token 数自动选择

### AD-003：中文支持 — BERT-base-chinese + jieba

- BERT-base-chinese（110M），与 DeBERTa 共存时推理显存 ~1.4GB
- jieba 中文分词 + 中文特征提取（虚词比例、成语使用等）
- 语言自动检测（langdetect）+ 手动切换

### AD-004：多任务学习 — 共享编码器 + 4 个回归头

```
输入文本
  → DeBERTa-v3 编码器
    → [CLS] 向量
      → 总评分头 (Linear + Sigmoid)
      → 内容头 (Linear + Sigmoid)
      → 结构头 (Linear + Sigmoid)
      → 语言头 (Linear + Sigmoid)
→ 4 个分数 → 模板化反馈生成器 → 反馈文字
```

- 显存开销仅增加几个 Linear 层（<1MB），几乎无额外负担
- 维度分可以用启发式规则从总评分特征中拆解（无需维度标注）
- 反馈用模板+特征生成，不走生成式模型，CPU 运行

### AD-005：模型集成 — 顺序推理

- 主模型 DeBERTa-v3 + Longformer 加权平均
- 顺序加载推理（8GB 显存放不下两模型同时运行），单次延时 ~3s
- 中文场景额外加入 BERT-base-chinese 的加权

---

## 系统架构（简化版）

```
┌──────────────────┐      ┌──────────────────┐
│  Streamlit UI    │      │   Flask API       │
│  (多页面)        │─────▶│   (REST 端点)     │
│  8501 端口       │      │   5000 端口        │
└──────────────────┘      └────────┬─────────┘
                                   │
                          ┌────────▼─────────┐
                          │   推理引擎        │
                          │  模型注册表       │
                          │  DeBERTa-v3       │
                          │  Longformer       │
                          │  BERT-chinese     │
                          └──────────────────┘
```

---

## 项目目录（仅新增部分）

```
gcsj/
├── data/
│   ├── raw/
│   │   └── chinese/                 # 中文作文数据（新增）
│   └── models/                      # 模型权重（新增）
│       ├── en_deberta/
│       ├── en_longformer/
│       └── zh_bert/
│
├── src/
│   ├── models/
│   │   ├── advanced_model.py        # 多任务 DeBERTa-v3 模型（新增）
│   │   ├── longformer_model.py      # Longformer 长文本模型（新增）
│   │   ├── cn_model.py              # 中文模型封装（新增）
│   │   ├── ensemble.py              # 模型集成（新增）
│   │   └── feedback_generator.py    # 模板反馈生成（新增）
│   ├── training/
│   │   ├── advanced_trainer.py      # 多任务训练器（新增）
│   │   └── cn_trainer.py            # 中文模型训练器（新增）
│   ├── inference/
│   │   ├── advanced_predictor.py    # 多任务/集成预测（新增）
│   │   └── cn_preprocessor.py       # 中文预处理（新增）
│   └── utils/
│       ├── language_detector.py     # 语言检测（新增）
│       └── model_registry.py        # 模型注册表（新增）
│
├── api/
│   └── app.py                       # Flask API（重构，增加路由）
│
├── ui/
│   ├── app.py                       # Streamlit 主页（已存在，微调）
│   ├── pages/
│   │   ├── scoring.py               # 评分页面（新增）
│   │   ├── batch.py                 # 批量评分（新增）
│   │   └── comparison.py            # 中英文对比展示（新增）
│   ├── components/
│   │   ├── score_gauge.py           # 分数仪表盘（新增）
│   │   ├── feedback_card.py         # 反馈卡片（新增）
│   │   └── radar_chart.py           # 维度雷达图（新增）
│   └── i18n/
│       ├── zh.json                  # 中文文案（新增）
│       └── en.json                  # 英文文案（新增）
│
├── tests/
│   ├── test_advanced_models.py      # 进阶模型测试（新增）
│   └── test_api_advanced.py         # 进阶 API 测试（新增）
│
└── notebooks/
    ├── 03_advanced_models.ipynb     # 进阶模型实验（新增）
    └── 04_chinese_support.ipynb     # 中文支持实验（新增）
```

---

## 任务分解

### 阶段 1：模型升级（第 1-4 周）— ML 工程师 + 数据工程师

| 任务 ID | 描述 | 负责 | 优先级 | 复杂度 |
|---------|------|------|--------|--------|
| A-001 | 准备中文作文数据集（≥2000 篇），清洗、标注 | 数据工程师 | P0 | 高 |
| A-002 | 实现中文文本预处理：jieba 分词、BERT tokenizer | 数据工程师 | P0 | 中 |
| A-003 | 实现语言检测模块 `language_detector.py` | 数据工程师 | P0 | 低 |
| A-004 | 实现多任务模型 `advanced_model.py`（DeBERTa-v3 + 4 头） | ML 工程师 | P0 | 中 |
| A-005 | 实现多任务训练器（加权 MSE 损失、fp16、早停） | ML 工程师 | P0 | 中 |
| A-006 | 训练 DeBERTa-v3-base 英文多任务模型，目标 QWK ≥ 0.75 | ML 工程师 | P0 | 高 |
| A-007 | 实现 Longformer 长文本模型，训练，目标 QWK ≥ 0.70 | ML 工程师 | P1 | 中 |
| A-008 | 实现中文模型封装 `cn_model.py`，训练中文评分模型 | ML 工程师 | P0 | 中 |
| A-009 | 实现反馈生成器 `feedback_generator.py`（基于维度分的模板反馈） | ML 工程师 | P0 | 中 |
| A-010 | 实现模型集成 `ensemble.py`（加权平均、顺序推理） | ML 工程师 | P1 | 中 |
| A-011 | 实现模型注册表 `model_registry.py` | ML 工程师 | P0 | 低 |

### 阶段 2：API 与推理升级（第 5-7 周）— 后端工程师

| 任务 ID | 描述 | 负责 | 优先级 | 复杂度 |
|---------|------|------|--------|--------|
| A-012 | 实现高级推理引擎 `advanced_predictor.py`（多任务+语言路由+集成） | 后端工程师 | P0 | 中 |
| A-013 | 重构 API：`POST /api/v1/score` 增加语言检测、多维输出 | 后端工程师 | P0 | 中 |
| A-014 | 新增 `POST /api/v1/batch` 批量评分（CSV 上传，同步返回） | 后端工程师 | P0 | 中 |
| A-015 | 新增 `GET /api/v1/models` 模型信息端点 | 后端工程师 | P1 | 低 |

### 阶段 3：前端升级（第 6-9 周）— 前端工程师

| 任务 ID | 描述 | 负责 | 优先级 | 复杂度 |
|---------|------|------|--------|--------|
| A-016 | Streamlit 多页面架构重构（`ui/pages/`） | 前端工程师 | P0 | 中 |
| A-017 | 实现评分页面：语言选择、文本输入、多维结果展示（仪表盘+雷达图） | 前端工程师 | P0 | 中 |
| A-018 | 实现反馈卡片组件：内容/结构/语言三维度文字反馈 | 前端工程师 | P0 | 中 |
| A-019 | 实现批量评分页面：CSV 上传、进度条、结果表格、下载 | 前端工程师 | P0 | 中 |
| A-020 | 实现中英文对比页面：同一文本中英文模型评分的对比展示 | 前端工程师 | P1 | 低 |
| A-021 | 实现双语切换功能（`ui/i18n/` JSON + session_state） | 前端工程师 | P0 | 中 |
| A-022 | UI 美化：主题配色、动画过渡、响应式布局、加载动效 | 前端工程师 | P0 | 低 |

### 阶段 4：测试与交付（第 10-12 周）— 全部

| 任务 ID | 描述 | 负责 | 优先级 | 复杂度 |
|---------|------|------|--------|--------|
| A-023 | 编写模型测试：多任务输出形状、异常输入处理 | ML 工程师 | P0 | 中 |
| A-024 | 编写 API 测试：单篇评分、批量评分、语言路由、错误处理 | 后端工程师 | P0 | 中 |
| A-025 | 端到端联调：UI → API → 中英文模型 → 多维展示 | 全部 | P0 | 中 |
| A-026 | 撰写项目文档：README、架构说明、答辩 PPT 素材 | 全部 | P0 | 低 |
| A-027 | 最终验收：中英文评分流程完整、界面美观、演示脚本准备 | 全部 | P0 | 中 |

---

## 依赖关系

```
阶段 1（模型）：
  A-001 → A-002 → A-008         （中文数据流水线）
  A-004 → A-005 → A-006         （多任务模型训练）
                    A-006 → A-007 （Longformer 依赖 DeBERTa 完成）
                    A-006 → A-009 （反馈依赖模型）
                    A-006 → A-010 （集成依赖各模型）
  A-003 独立

阶段 2（API）：
  A-006, A-008 → A-012 → A-013  （高级推理引擎 + API 重构）
                  A-013 → A-014  （批量评分路由）
  A-011 → A-015                 （模型信息）

阶段 3（UI）：
  A-016 → A-017, A-018, A-019, A-020, A-021, A-022 （并行）

阶段 4（交付）：
  全部 → A-025 → A-026 → A-027

关键路径：A-001 → A-002 → A-008 → A-012 → A-013 → A-017 → A-025 → A-027
```

---

## API 接口设计

### POST /api/v1/score（升级版）

**请求**：
```json
{
  "text": "作文内容...",
  "language": "auto"
}
```

**响应**：
```json
{
  "success": true,
  "score": 0.85,
  "scores": {
    "total": 0.85,
    "content": 0.82,
    "structure": 0.88,
    "language": 0.85
  },
  "feedback": {
    "content": "论点清晰，但可增加具体例证。",
    "structure": "段落结构合理，过渡自然。",
    "language": "语法基本正确，部分句式可更丰富。"
  },
  "language": "en",
  "model": "deberta-v3-base-v1",
  "elapsed_ms": 1234
}
```

### POST /api/v1/batch（新增）

**请求**：multipart/form-data，上传 CSV（列：essay_id, text, language）

**响应**：
```json
{
  "success": true,
  "total": 50,
  "results": [
    {"essay_id": "1", "score": 0.85, "scores": {...}, "elapsed_ms": 1200},
    {"essay_id": "2", "score": 0.67, "scores": {...}, "elapsed_ms": 1100}
  ]
}
```

### GET /api/v1/models（新增）

```json
{
  "success": true,
  "models": {
    "en": {"name": "deberta-v3-base", "version": "v1.0", "qwk": 0.76},
    "en_long": {"name": "longformer-base", "version": "v1.0", "qwk": 0.72},
    "zh": {"name": "bert-base-chinese", "version": "v1.0", "qwk": 0.65}
  }
}
```

---

## UI 页面规划

### 页面 1：评分（scoring.py）
- 语言自动检测 + 手动切换（中/英按钮）
- 大面积文本输入区，字数/字符数实时统计
- 提交按钮 → 加载动画 → 结果区
- 结果区：总分数大号仪表盘 + 百分制转换
- 三维度雷达图（内容/结构/语言）
- 各维度反馈文字卡片

### 页面 2：批量评分（batch.py）
- CSV 模板下载按钮
- 文件拖拽上传区
- 评分进度条
- 结果表格（可排序、筛选）
- 一键下载结果 CSV

### 页面 3：中英对比（comparison.py）
- 输入一篇作文，同时用中英文模型评分
- 并排展示两个模型的分数和反馈
- 适合演示模型的跨语言能力

---

## GPU 显存预估

| 场景 | 模型 | 精度 | Batch | 显存 |
|------|------|------|-------|------|
| 训练 | DeBERTa-v3-base | fp16 | 16 | ~4.5 GB |
| 训练 | Longformer-base | fp16 | 4 | ~5.5 GB |
| 训练 | BERT-base-chinese | fp16 | 16 | ~3.2 GB |
| 推理 | DeBERTa-v3 + BERT-chinese | fp16 | 1+1 | ~1.4 GB |
| 推理 | 单模型（任一种） | fp16 | 1 | ~0.8 GB |

8GB 显存在推理时完全够用（最多同时加载中英文两个模型约 1.4GB）。训练时需分阶段进行。

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 中文数据不足或质量差 | 降级方案：减少中文维度分，只训练总评分；使用数据增强（回译） |
| DeBERTa-v3 训练 QWK 不达标 | 回退到 RoBERTa-base；增加训练 epoch；调学习率 |
| Longformer 8GB 下 OOM | 降级为分块推理，不单独训练 Longformer |
| 界面开发时间不足 | 优先完成评分和批量两个核心页面，对比页面可降级 |

---

## 环境依赖（新增）

```
# requirements-advanced.txt (在 MVP 基础上新增)
deberta-v3-base 相关：transformers>=4.30.0（已包含）
jieba>=0.42.1
langdetect>=1.0.9
plotly>=5.14.0       # 雷达图/图表
opencc>=1.1.7        # 繁简体转换（可选）
```
