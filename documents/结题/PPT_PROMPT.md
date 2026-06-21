# 项目结题 PPT 生成提示词

请你根据以下项目详细信息，制作一份**软件工程实践项目结题答辩 PPT**。要求专业、结构清晰、适合学术场景展示。

---

## 一、PPT 基本要求

- **页数**：12-16 页
- **语言**：中文
- **风格**：简洁学术风，蓝色/深灰为主色调，避免花哨动画
- **图表**：系统架构图、流程图、模型性能对比表格、界面截图
- **适用场景**：软件工程实践结题答辩（15 分钟汇报 + 5 分钟提问）

---

## 二、项目核心信息

### 项目基本信息

- **项目名称**：基于深度学习的作文自动评分系统（AES — Automated Essay Scoring）
- **副标题**：中英文双语 BERT 模型 + Android 离线推理
- **类型**：软件工程实践项目（4人团队）
- **时间**：2025-2026 学年
- **地点**：苏州

### 项目摘要（建议放在第2页）

本系统基于 BERT 预训练语言模型，实现了中英文双语作文的自动评分功能。核心创新点在于将深度学习模型从 Web 端成功部署到 Android 移动端，实现**完全离线**的本地推理。系统采用 BERT-base 编码器 + 回归头架构，在 ASAP 作文数据集上训练，英文模型 QWK 达 0.58，中文翻译数据模型 QWK 达 0.79。Android 端使用 PyTorch Mobile 2.1.0 运行时，配合 Jetpack Compose 现代化 UI，支持单篇评分、批量 CSV 评分、中英模型对比、雷达图可视化等完整功能。

---

## 三、各页内容安排

### 第 1 页：封面
- 项目标题：「基于深度学习的作文自动评分系统」
- 副标题：中英文双语 BERT 模型 + Android 离线推理
- 团队、时间、学校/院系

### 第 2 页：项目概述
- 一句话总结：将 BERT 作文评分模型从服务器搬到手机上，实现完全离线推理
- 核心价值：
  - ✅ 离线可用（无需网络，隐私安全）
  - ✅ 中英文双语（BERT-base-uncased + BERT-base-chinese）
  - ✅ 多维度反馈（总分 + 内容/结构/语言 + 智能评语）
  - ✅ 批量处理（CSV 导入，一键评分）
  - ✅ 现代化 UI（Material 3 + Compose + 雷达图）

### 第 3 页：系统总架构
请绘制一个三层架构图：
```
┌─────────────────────────────────────────────┐
│              展示层 (Android UI)              │
│  Jetpack Compose │ Material 3 │ Canvas 雷达图  │
│  底部导航 Tab │ 实时状态更新 │ 响应式布局      │
├─────────────────────────────────────────────┤
│              业务逻辑层                       │
│  AESPredictor │ BertTokenizer │ LanguageDetector │
│  协程异步推理 │ WordPiece 分词 │ 中英自动检测   │
├─────────────────────────────────────────────┤
│              推理引擎层 (PyTorch Mobile)       │
│  Module.load() │ IValue 张量 │ 415MB 模型权重  │
│  完全离线推理 │ 无服务器依赖 │ ARM CPU 优化    │
└─────────────────────────────────────────────┘
```

### 第 4 页：模型架构
- **基础模型**：
  - 英文：BERT-base-uncased（110M 参数，12层，768维）
  - 中文：BERT-base-chinese（102M 参数，12层，768维）
- **评分头**：Dropout(0.1) → Linear(768→1) → Sigmoid
- **训练策略**：冻结 BERT 编码器，仅训练回归头（~770 可训练参数）
- **输入**：Token IDs (1 × 512)
- **输出**：归一化分数 [0, 1] → 映射到 0-100 分
- 建议用一张图展示：Input → BERT Encoder (frozen) → CLS Pooling → Regressor → Score

### 第 5 页：数据集与训练
- **英文数据集**：ASAP (Automated Student Assessment Prize)
  - 12,976 篇英文作文，8 个评分集
  - 按 essay_set 隔离划分训练/验证/测试（防数据泄露）
  - 分数按 essay_set 归一化至 [0, 1]
- **中文数据集**：ASAP 翻译版
  - 3,950 篇（Google 翻译英→中，保留原始评分标签）
  - 分层采样，覆盖全部 8 个题目集
- **训练配置**：
  - Epochs: 3-5 | Batch: 16 | LR: 1e-3 (head only)
  - Loss: MSE | 早停: patience=2 | Optimizer: AdamW
  - 训练设备: RTX 5060 8GB / CPU

### 第 6 页：模型性能
用表格展示：

| 模型 | 数据量 | Val QWK | Test QWK | Val Corr | 大小 |
|------|--------|---------|----------|----------|------|
| BERT-base-uncased (英文) | 12,976 | 0.58 | — | 0.69 | 415 MB |
| BERT-base-chinese (中文) | 3,950 | 0.79 | 0.76 | — | 388 MB |

- QWK (Quadratic Weighted Kappa) 是作文评分领域的主要指标
- 英文模型 QWK 0.58 为跨题目泛化合理水平（业内 0.55-0.70）
- 中文模型 0.79 受益于数据同质性较高

### 第 7 页：Android 端技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 语言 | Kotlin | 2.2.10 |
| 构建 | Android Gradle Plugin | 9.2.1 |
| UI 框架 | Jetpack Compose + Material 3 | BOM 2024.09 |
| 推理引擎 | PyTorch Mobile | 2.1.0 |
| 异步处理 | Kotlin Coroutines | 1.7.3 |
| 最低系统 | Android 10 (API 29) | — |
| 目标系统 | Android 16 (API 36) | — |

### 第 8 页：Android App 功能模块
用表格或图标卡片展示四个主要功能：

| 功能 | 描述 | 技术要点 |
|------|------|----------|
| 📝 单篇评分 | 输入文本 → 语言检测 → BERT 推理 → 总分 + 三个维度分 + 雷达图 + 智能评语 | Compose + 协程异步推理 + Canvas 雷达图 |
| 📊 批量评分 | 选择 CSV → 逐行推理 → 进度条 + 结果列表 | 文件选择器 + LazyColumn |
| 🔄 中英对比 | 同一文本同时用中/英文模型评分，左右卡片并排对比 | 双模型并行推理 |
| ⚙️ 设置 | 模型加载状态（实时显示已加载/未加载+错误信息）+ 重新加载 + 模型信息 | 状态查询 + 错误展示 |

### 第 9 页：核心技术挑战与解决方案（重点！）
这是答辩的关键部分，请详细列出：

| 挑战 | 问题描述 | 解决方案 |
|------|---------|---------|
| **1. AGP 版本兼容** | AGP 9.2.1 要求 Build Tools 36.0.0，但本地 SDK 仅有 36.1.0 和 37.0.0 | 显式指定 `buildToolsVersion = "36.1.0"` |
| **2. PyTorch 原生库闪退** | `pytorch_android_lite` 打包 `libpytorch_jni_lite.so` 但 NativePeer 加载 `libpytorch_jni.so` | 改用 `pytorch_android` (full) 2.1.0 |
| **3. 模型算子不兼容** | 训练导出使用 SDPA 注意力（`aten::scaled_dot_product_attention`），PyTorch Mobile 不支持 | 重建模型时强制 `_attn_implementation='eager'`，无 SDPA 导出 |
| **4. 模型接口不匹配** | 训练模型接收 2 个输入（input_ids + attention_mask），Android 端仅传 1 个 | 包装为单输入模型：内部自动计算 attention_mask = (input_ids != 0) |
| **5. 大文件加载可靠性** | 415 MB 模型从 assets 复制到内部存储可能中途失败 | 原子化文件写入（先写 .tmp 再 renameTo）+ 错误信息 UI 展示 |
| **6. ABI 兼容** | x86 模拟器的 .so 文件与真机 ARM 冲突 | ndk.abiFilters 仅保留 arm64-v8a + armeabi-v7a |
| **7. 网络限制** | 国内网络无法直接访问 HuggingFace / Google Maven | settings.gradle.kts 配置腾讯云镜像；Python 侧使用 hf-mirror.com |

### 第 10 页：移动端部署流程
```
训练完成模型 (best_model.pt)
    ↓
加载权重 → 配置 eager attention
    ↓
包装为单输入接口 (AndroidWrapper)
    ↓
torch.jit.trace → torch.jit.freeze
    ↓
验证无 SDPA 算子 → 保存 .pt
    ↓
放入 app/src/main/assets/
    ↓
Gradle 打包 → APK (817 MB)
    ↓
无线 ADB → 真机安装运行
```

### 第 11 页：项目文件结构
```
lab/
├── Android_HomeworkScore/          ← Android 应用
│   └── app/src/main/
│       ├── assets/                 ← 模型 .pt + 词表 .txt
│       └── java/.../              ← Kotlin 源码
│           ├── inference/          ← 推理引擎
│           └── ui/                 ← Compose UI
├── models/                         ← 训练好的模型权重
│   ├── en_bert/                   ← 英文 BERT（best_model.pt / bert_scripted.pt）
│   ├── en_bert_local/             ← 本地下载的原始 BERT
│   └── zh_bert/                   ← 中文 BERT（待训练）
├── now-work/data/                 ← ASAP 训练数据（12,976 篇）
├── train_and_export.py            ← 完整训练 + 导出脚本
├── generate_android_models.py     ← 占位模型快速生成
├── api/app.py                     ← Flask API
├── ui/app.py                      ← Streamlit Web UI
└── tests/                         ← 单元 + E2E 测试
```

### 第 12 页：Web 版 vs Android 版对比

| 特性 | Web 版 | Android 版 |
|------|--------|-----------|
| 架构 | Flask API + Streamlit UI | PyTorch Mobile 本地推理 |
| 网络依赖 | 需要服务器 | 完全离线 |
| 模型加载 | 服务启动时预加载 | App 启动时后台加载 |
| UI 框架 | Streamlit (Python) | Jetpack Compose (Kotlin) |
| 部署方式 | 浏览器访问 | APK 安装包 |
| 文件大小 | N/A | 817 MB (含双模型) |
| 推理速度 | GPU 加速 | CPU 推理 |

### 第 13 页：局限性与改进方向
- 中文模型基于翻译数据，自然中文作文评分能力有限 → 采集真实中文作文数据
- 英文 QWK 0.58 受跨题目泛化影响 → 尝试 DeBERTa-v3 或模型集成
- 维度评分基于启发系数拆分（非真实多任务模型）→ 训练多任务版本
- 模型体积大（415MB 单模型），APK 817MB → 量化压缩或云端下载方案
- 不支持 512 token 以上长文本 → Longformer 或分块策略
- Android 端中文模型尚未完成真实训练（目前为占位模型）→ 后续使用中文数据集训练

### 第 14 页：总结与展望
- **已实现**：
  - ✅ BERT 作文评分模型训练（英文 QWK 0.58，中文 QWK 0.79）
  - ✅ Android 端完全离线推理（英文真实模型可用）
  - ✅ 四个完整功能模块（评分/批量/对比/设置）
  - ✅ Material 3 现代化 UI + 错误诊断展示
  - ✅ 解决了全部 7 项核心技术挑战
- **展望**：
  - 中文模型本地训练与部署
  - 模型量化（INT8）减少体积
  - 多任务维度评分（替代启发系数）
  - Google Play 发布

### 第 15 页（可选）：致谢 / Q&A
- 感谢指导老师
- 感谢团队成员
- Q&A 环节

---

## 四、制作注意事项

1. **代码展示**：第 9 页「技术挑战」建议每项用 1-2 行简洁代码展示修复前后对比
2. **数据可视化**：第 6 页建议用柱状图展示 QWK，第 5 页用饼图展示训练/验证/测试分割
3. **架构图**：第 3 页和第 10 页建议使用流程图/架构图，文字描述仅为参考
4. **截图**：第 8 页建议配合 App 实际运行截图（从 README 或实际运行中获取）
5. **字体建议**：标题使用黑体/微软雅黑加粗，正文使用宋体/微软雅黑
6. **页码**：每页添加页码（第 X 页 / 共 Y 页）
7. **页脚**：可添加项目名 + 团队名

---

## 五、补充说明

### 关于技术深度的强调
本项目不同于常规的「调包」项目，解决了以下深层工程问题：
- PyTorch TorchScript 模型从服务器（Python 2.5）到移动端（PyTorch Mobile 2.1）的**跨版本兼容**
- BERT 模型中 SDPA 注意力算子的**移动端不支持问题**
- **2-input → 1-input 模型接口转换**（机器学习与移动端协同）
- 415 MB 大文件的**原子化写入**与加载可靠性设计
- 国内网络环境下的**依赖镜像配置**（Gradle + Maven + HuggingFace）

### 关于数据
- 英文 ASAP 数据为公开学术数据集（Kaggle 竞赛）
- 中文数据通过 Google 翻译生成，标签继承原文

### 关于团队分工（如需要）
- 可根据实际团队分工补充：模型训练 / Android 开发 / Web 开发 / 测试

---

请严格按照以上结构和内容生成 PPT，确保技术信息准确、逻辑清晰、适合结题答辩展示。
