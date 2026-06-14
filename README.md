# 自动文本评分系统 (AES)

基于 BERT 深度学习的**中英文双语**作文自动评分系统，学校工程实践项目。

## 功能特性

- **中英文双语评分**: 自动检测或手动切换语言，英文 BERT-base + 中文 BERT-base-chinese 双模型
- **多维度评分**: 总评分 + 内容/结构/语言三维度打分 + 雷达图可视化
- **智能反馈**: 基于维度分数的中英文模板化评语反馈
- **批量评分**: 上传 CSV 文件，批量评分并下载结果
- **中英对比**: 同一文本中英文模型分别评分，对比展示
- **双语界面**: 完整中英文界面切换
- **模型信息**: 实时查看各模型加载状态

## 环境要求

- Python 3.10+
- PyTorch 2.0+ (CUDA 推荐)
- RTX 5060 / 8GB 显存
- 约 6GB 磁盘空间（模型权重）

## 安装

```bash
# conda 环境（推荐）
conda create -n pytorch python=3.10
conda activate pytorch

# 安装依赖
pip install torch transformers datasets scikit-learn pandas flask flask-cors streamlit accelerate pyyaml plotly langdetect jieba deep-translator
```

## 项目结构

```
gcsj/
├── data/
│   ├── raw/asap/                  # ASAP 英文原始数据（12,979 篇）
│   └── raw/chinese/               # 中文翻译数据（3,950 篇）
├── models/
│   ├── best_model.pt              # 英文 BERT-base 模型
│   ├── en_roberta/                # 英文 RoBERTa-base 模型
│   ├── en_bert/                   # 英文 BERT-base 备份
│   └── zh_bert/                   # 中文 BERT-base-chinese 模型
├── configs/                       # 配置文件（数据/模型/API）
├── src/
│   ├── data_preprocessing/        # 数据加载、清洗、分词、划分
│   ├── models/                    # 模型定义（AESModel / 多任务 / 中文）
│   ├── training/                  # 训练器（BERT / 进阶 / 中文）
│   ├── evaluation/                # QWK、MAE、Pearson 评估指标
│   ├── inference/                 # 推理引擎、模型加载、中文预处理
│   └── utils/                     # 语言检测、模型注册表、配置加载
├── api/app.py                     # Flask REST API
├── ui/
│   ├── app.py                     # Streamlit 主页（评分）
│   ├── pages/                     # 批量评分、中英对比
│   ├── components/                # 雷达图、反馈卡片
│   └── i18n/                      # 中英双语文案
├── scripts/                       # 训练/翻译脚本
├── samples/                       # 范文（中英文各一篇）
├── tests/                         # 单元测试 + E2E 测试
└── notebooks/                     # 数据探索与实验
```

## 数据集

### 英文：ASAP (Automated Student Assessment Prize)
- 12,976 篇英文作文，8 个评分集（不同题目/学段）
- 分数范围 0-55，按 essay_set 归一化至 [0, 1]
- 按 essay_set 隔离划分训练/验证/测试集（防止数据泄露）

### 中文：ASAP 翻译版
- 3,950 篇，Google 翻译英→中，保留原始评分标签
- 分层采样，覆盖全部 8 个题目集
- 按 essay_set 归一化，随机划分训练/验证/测试集

## 模型

| 模型 | 数据 | Val QWK | Test QWK | 大小 |
|------|------|---------|----------|------|
| BERT-base-uncased (英文) | ASAP 12,976 | 0.58 | — | 418 MB |
| RoBERTa-base (英文备选) | ASAP 12,976 | 0.58 | — | 499 MB |
| BERT-base-chinese (中文) | 翻译 3,950 | 0.79 | 0.76 | 391 MB |

> QWK (Quadratic Weighted Kappa) 取值范围 [-1, 1]，越高越好。当前使用严格的 prompt 隔离评估，跨题目泛化的 QWK 约 0.55-0.60 为合理水平。

## 训练

```bash
# 英文模型
python -m src.training.trainer --model_name bert-base-uncased --batch_size 16 --epochs 5 --fp16

# RoBERTa 模型
python -m src.training.trainer --model_name roberta-base --batch_size 8 --epochs 5 --fp16

# 中文模型（需先翻译数据）
python -m src.training.cn_trainer --data_path data/raw/chinese/asap_zh.csv --batch_size 8 --epochs 5
```

### 翻译中文数据
```bash
python scripts/translate_data.py --max-samples 4000
```

## 启动服务

**终端 1 — 启动 API：**
```bash
python api/app.py
# API: http://localhost:5000
```

**终端 2 — 启动 UI：**
```bash
streamlit run ui/app.py
# UI: http://localhost:8501
```

## API 文档

所有响应格式：`{"success": bool, ...}`。错误时 `success=false` 且包含 `error` 字段。

### `GET /api/v1/health`
```json
{"status": "ok", "en_model_loaded": true, "cn_model_loaded": true}
```

### `GET /api/v1/models`
```json
{"success": true, "models": {"en": {...}, "zh": {...}}}
```

### `POST /api/v1/score`
**请求：**
```json
{"text": "作文内容...", "language": "auto"}
```
`language` 可选 `"auto"` / `"en"` / `"zh"`。

**响应：**
```json
{
  "success": true,
  "score": 0.82,
  "scores": {"total": 0.82, "content": 0.80, "structure": 0.85, "language": 0.81},
  "feedback": {
    "content": "论点清晰...",
    "structure": "结构完整...",
    "language": "语言流畅...",
    "overall": "总分表现优秀..."
  },
  "language": "zh",
  "elapsed_ms": 1234
}
```

### `POST /api/v1/batch`
上传 CSV 文件（列：`essay_id, text, language`），返回批量评分结果。
```json
{"success": true, "total": 50, "results": [...]}
```

## 测试

```bash
# 单元测试
python3 -m pytest tests/ -v

# E2E 端到端测试
python3 tests/test_e2e.py
```

## 评估指标

| 指标 | 说明 |
|------|------|
| QWK | 二次加权 Kappa，衡量人机评分一致性，主要指标 |
| MAE | 平均绝对误差 |
| Pearson r | Pearson 相关系数 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 模型 | BERT-base-uncased / BERT-base-chinese / RoBERTa-base |
| 损失函数 | MSE |
| 训练优化 | fp16 混合精度、早停 patience=3、梯度裁剪 |
| 中文分词 | jieba |
| 语言检测 | langdetect |
| 后端 | Flask + Flask-CORS |
| 前端 | Streamlit + Plotly |
| 翻译 | deep-translator (Google Translate) |
| 测试 | pytest + Playwright |

## 限制与后续改进

- 中文模型基于翻译数据训练，自然中文评分能力有限——可收集真实中文作文数据提升
- 英文模型 QWK 受严格 prompt 隔离评估影响偏低——可尝试 DeBERTa-v3 或模型集成
- 维度评分基于启发式拆分（非真实多任务模型）——可训练多任务版本来替代
- 不支持超长文本（>512 token）——可引入 Longformer 或分块策略

## 团队

4 人工程实践项目 · 苏州 · 2026
