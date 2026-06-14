# MULTI_AGENT_PLAN.md

## 基于深度学习的自动文本评分系统 (AES) — 简化版（MVP）

---

## 1. 项目概述

**性质**：学校工程实践项目

**目标**：构建一个自动文本评分系统，使用预训练 BERT 模型理解语义内容、生成评分，并通过 Web 界面提交和查看结果。

**MVP 范围**：
- 使用 ASAP 数据集训练一个 BERT-base 评分模型
- 提供 REST API 进行单篇文本评分
- 提供 Streamlit 界面提交文本并查看评分结果

**硬件**：RTX 5060（8GB 显存）

**成功标准（MVP）**：
- ASAP 数据集上 QWK >= 0.70
- API 单篇评分响应 < 5 秒
- Streamlit 界面可提交文本并展示评分结果

**团队**：1 组，4 人。

**时间线**：12 周（3 个阶段，每阶段 4 周）

---

## 2. 技术方案（简明）

### 2.1 模型方案

采用 **BERT-base + 回归头** 架构（模式 A），这是最简单且研究最充分的方案：

```
输入文本 -> BERT 分词器 -> BERT-base 编码器 -> [CLS] 向量 -> Linear + Sigmoid -> 分数
```

- 模型：`bert-base-uncased`（1.1 亿参数，512 token 上限）
- 损失函数：均方误差（MSE）
- 评估指标：QWK（二次加权 Kappa）、MAE（平均绝对误差）

### 2.2 训练要点

- 5 折交叉验证，按 prompt 隔离划分（防止数据泄露）
- 学习率 2e-5，batch size 16，epoch 3-5，早停 patience=3
- 混合精度训练（fp16）节省显存
- RTX 5060 完全够用，无需梯度累积

### 2.3 系统架构

```
Streamlit UI  -->  Flask REST API  -->  BERT 模型推理  -->  返回分数
```

- API：Flask，单端点 `POST /api/v1/score`
- UI：Streamlit，文本输入 + 评分展示
- 部署：本地运行，暂不容器化

---

## 3. 多智能体分工

### 智能体 A：数据工程师
**负责**：ASAP 数据下载、清洗、BERT 分词、训练/测试集划分
**输出**：预处理后的 HuggingFace Dataset、数据统计

### 智能体 B：机器学习工程师
**负责**：BERT 模型搭建、训练、评估
**输出**：训练好的模型权重、评估报告（QWK/MAE）

### 智能体 C：后端工程师
**负责**：Flask API、模型加载与推理
**输出**：`POST /api/v1/score` 端点

### 智能体 D：前端工程师
**负责**：Streamlit 评分界面
**输出**：文本输入页 + 结果展示页

---

## 4. 项目结构（简化版）

```
gcsj/
├── MULTI_AGENT_PLAN.md
├── README.md
├── data/
│   ├── raw/asap/                  # 原始 ASAP 数据
│   └── processed/                 # 预处理后的数据
├── configs/
│   ├── data_config.yaml
│   └── model_config.yaml
├── src/
│   ├── data_preprocessing/        # 数据加载、清洗、分词
│   ├── models/                    # BERT + 回归头模型
│   ├── training/                  # 训练循环、损失函数
│   ├── evaluation/                # QWK、MAE 指标
│   └── inference/                 # 模型加载、预测
├── api/
│   └── app.py                     # Flask 应用 + 评分路由
├── ui/
│   └── app.py                     # Streamlit 界面
├── notebooks/
│   ├── 01_eda.ipynb               # 数据探索
│   └── 02_experiment.ipynb        # 模型实验
├── tests/
├── requirements.txt
└── scripts/
    ├── train.sh
    └── serve.sh
```

---

## 5. 任务分解

### 阶段 1：数据 + 模型（第 1-4 周）

| 任务 ID | 描述 | 负责 | 复杂度 |
|---------|------|------|--------|
| T-001 | 搭建项目目录结构、Python 环境、`requirements.txt` | 全部 | 低 |
| T-002 | 下载 ASAP 数据集，完成探索性数据分析（分数分布、文本长度统计） | 数据工程师 | 低 |
| T-003 | 实现数据预处理：文本清洗、BERT 分词、训练/测试划分（prompt 隔离） | 数据工程师 | 中 |
| T-004 | 实现 BERT + 回归头模型（`AESModel`） | ML 工程师 | 中 |
| T-005 | 实现训练循环：MSE 损失、fp16、早停、检查点保存 | ML 工程师 | 中 |
| T-006 | 训练 BERT 基线模型，评估 QWK/MAE | ML 工程师 | 中 |
| T-007 | 验收：QWK >= 0.70，无数据泄露 | 全部 | 中 |

### 阶段 2：API + UI（第 5-8 周）

| 任务 ID | 描述 | 负责 | 复杂度 |
|---------|------|------|--------|
| T-008 | 实现推理模块：模型加载、文本预处理、预测 | 后端工程师 | 中 |
| T-009 | 实现 Flask API：`POST /api/v1/score`，输入验证，返回分数 | 后端工程师 | 中 |
| T-010 | 实现 Streamlit 界面：文本输入框 + 评分提交按钮 | 前端工程师 | 低 |
| T-011 | 实现评分结果展示：分数显示、简单的反馈文字 | 前端工程师 | 低 |
| T-012 | 端到端联调：UI -> API -> 模型 -> 返回分数 | 全部 | 中 |

### 阶段 3：完善与交付（第 9-12 周）

| 任务 ID | 描述 | 负责 | 复杂度 |
|---------|------|------|--------|
| T-013 | 错误处理完善：API 异常、输入校验、超时处理 | 后端工程师 | 低 |
| T-014 | UI 优化：加载状态、错误提示、结果展示美化 | 前端工程师 | 低 |
| T-015 | 编写测试：数据流水线测试、API 测试 | 全部 | 中 |
| T-016 | 撰写项目文档：README、使用说明 | 全部 | 低 |
| T-017 | 最终验收：完整流程测试，准备答辩材料 | 全部 | 中 |

---

## 6. 依赖关系图

```
阶段 1:
  T-001 -> T-002 -> T-003
  T-001 -> T-004 -> T-005 -> T-006
  T-003 + T-006 -> T-007

阶段 2:
  T-006 -> T-008 -> T-009
  T-009 -> T-010 -> T-011
  T-009 + T-011 -> T-012

阶段 3:
  T-012 -> T-013, T-014
  T-013 + T-014 -> T-015 -> T-016 -> T-017
```

---

## 7. 架构决策记录（简化）

| 决策 | 理由 |
|------|------|
| BERT-base 而非 RoBERTa | RTX 5060 8GB 显存，BERT-base 更稳；MVP 先跑通 |
| MSE 损失而非 QWK 损失 | 简单，训练稳定，QWK 作为评估指标即可 |
| 单篇评分，不做批量 | 减少 API 复杂度 |
| 不区分教师/学生角色 | 项目演示只需一套界面 |
| 本地运行，不容器化 | 减少部署工作量 |
| 不用数据库 | MVP 不需要持久化历史记录 |

---

## 8. 风险与应对

| 风险 | 应对 |
|------|------|
| GPU 不够（8GB 跑 BERT-base 没问题，但 batch size 受限） | batch size 降到 8，使用 fp16 |
| 512 token 限制导致长文本截断 | MVP 阶段接受截断，后续再优化 |
| QWK 达不到 0.70 | 调学习率、增加 epoch、检查数据划分 |

---

## 9. 实现指南

### 数据工程师
- 务必按 prompt 隔离划分训练/测试集（`sklearn.model_selection.GroupKFold`）
- BERT 分词参数：`max_length=512, truncation=True, padding='max_length'`

### ML 工程师
- 使用 HuggingFace `Trainer` 快速搭建训练流程
- 模型保存用 `model.save_pretrained()`，加载用 `AutoModel.from_pretrained()`
- 每个 epoch 评估一次 QWK

### 后端工程师
- Flask API 返回统一格式：`{"score": float, "model_version": str}`
- 模型在应用启动时加载一次，常驻内存

### 前端工程师
- Streamlit 单页应用：输入区 + 提交按钮 + 结果区
- 处理 loading 状态（`st.spinner`）和错误状态

---

## 10. 环境配置

```
# requirements.txt
torch>=2.0.0
transformers>=4.30.0
datasets>=2.12.0
scikit-learn>=1.2.0
pandas>=2.0.0
flask>=2.3.0
streamlit>=1.24.0
accelerate>=0.20.0
```

---

## 11. 已确认事项

- GPU：RTX 5060（8GB）
- 隐私问题：无
- API 批量评分：MVP 阶段仅支持单篇评分
- UI 用户：不区分教师和学生，统一界面
