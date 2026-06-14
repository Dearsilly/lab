# Android AES 作文评分应用 — 设计规格 (v2)

> 日期: 2026-06-14 | 状态: 已确认 | 推理: PyTorch Mobile 本地

## 1. 概述

在现有 Android 骨架 (`Android_HomeworkScore/`) 基础上，升级为完整的本地 AES 作文评分应用。模型推理在手机本地执行，无需服务器。

### 核心约束

- 本地推理（PyTorch Mobile），无需网络
- 最低 SDK 29 (Android 10)
- 中文界面
- 在已有 Kotlin + Jetpack Compose 项目上改造
- 本地演示用途，不追求生产级优化

## 2. 架构

```
┌─────────────────────────────────────┐
│          Jetpack Compose UI         │
│  评分Tab / 批量Tab / 对比Tab / 设置  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         推理引擎 (Kotlin)            │
│  ┌─────────┐  ┌──────────────────┐  │
│  │ Tokenizer│  │ PyTorch Mobile   │  │
│  │ vocab.txt│  │ .pt 模型加载      │  │
│  └─────────┘  └──────────────────┘  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         assets/ (本地文件)           │
│  bert_model.pt  +  vocab.txt       │
│  zh_model.pt  +  zh_vocab.txt      │
└─────────────────────────────────────┘
```

## 3. 导航结构

底部 Tab 导航（Material3 NavigationBar），4 个 Tab：评分、批量、对比、设置。

## 4. 各 Tab 详细设计

### 4.1 评分 Tab (主页面)

- 语言选择 Chip：自动 / 英文 / 中文，默认"自动"
- 多行文本输入框
- 统计栏：字符数、词数、检测语言
- 提交 → Loading 动画 → 结果展示

**结果区：**
- 总分仪表盘（大号数字 + 渐变进度条）
- 三维度卡片：内容(绿)/结构(靛)/语言(橙)
- 雷达图：Compose Canvas 自绘
- 评语卡片：带颜色左边框

**语言检测：** Kotlin 端实现字符规则检测（中文字符占比 >50% → zh）

### 4.2 批量 Tab

- 文件选择（CSV）
- 进度条 + 逐条结果 LazyColumn
- 结果导出

### 4.3 对比 Tab

- 单文本 → 分别用英文和中文模型推理 → 并排展示

### 4.4 设置 Tab

- 模型加载状态
- 模型信息（名称、QWK）
- 应用版本

## 5. 核心技术方案

### 5.1 PyTorch Mobile 推理

```kotlin
// 加载模型
val module = Module.load(assetFilePath(context, "bert_model.pt"))
// 前向推理
val input = Tensor.fromBlob(inputIds, longArrayOf(1, maxLength))
val output = module.forward(IValue.from(input)).toTensor()
```

### 5.2 Tokenizer

- 读取 `vocab.txt` 构建 HashMap<String, Int>
- 实现基本 BERT tokenization：小写化 → 分词 → WordPiece → [CLS]/[SEP]
- 中文：字符级分词（BERT Chinese tokenizer 是基于字的）
- 不使用 jieba 分词（简化实现，字符级即可）

### 5.3 维度分生成

单任务模型只输出总分，维度分沿用 `_expand_to_dimensions()` 逻辑：
- content = total * 0.95
- structure = total * 1.02
- language = total * 1.03

## 6. 依赖

```
dependencies {
    // PyTorch Mobile
    implementation("org.pytorch:pytorch_android_lite:1.13.1")
    implementation("org.pytorch:pytorch_android_torchvision_lite:1.13.1")
    // Compose Navigation
    implementation("androidx.navigation:navigation-compose:2.7.7")
}
```

## 7. 模型文件处理

- 英文模型 `models/best_model.pt` → 复制到 `app/src/main/assets/bert_model.pt`
- 中文模型 `models/zh_bert/best_model.pt` → 复制到 `app/src/main/assets/zh_model.pt`
- 英文 vocab `models/en_bert/vocab.txt` → 复制到 `app/src/main/assets/vocab.txt`
- 中文 vocab `models/zh_bert/vocab.txt` → 复制到 `app/src/main/assets/zh_vocab.txt`

模型文件通过 git-lfs 或直接从项目 models/ 目录手动复制。

## 8. 与现有代码的关系

**保留并修改：**
- MainActivity.kt — 改为 NavHost 入口
- HomeworkScoreScreen.kt — 重构为评分 Tab
- build.gradle.kts — 更新依赖
- 主题文件

**新增：**
- `ui/screen/BatchScreen.kt`
- `ui/screen/ComparisonScreen.kt`
- `ui/screen/SettingsScreen.kt`
- `ui/navigation/AppNavigation.kt`
- `ui/components/RadarChart.kt`
- `ui/components/ScoreGauge.kt`
- `ui/components/FeedbackCard.kt`
- `inference/BertTokenizer.kt` — WordPiece 分词
- `inference/AESPredictor.kt` — 模型推理封装
- `inference/LanguageDetector.kt` — 中英文检测

**删除：**
- ScoreApi.kt (Retrofit 网络层)
- essay_set 下拉选择器
- 网络权限（保留 INTERNET 用于未来扩展）

## 9. 错误处理

| 场景 | UI 表现 |
|------|---------|
| 未输入文本 | Snackbar "请输入作文内容" |
| 模型未加载 | 设置页 ❌ 状态 + 错误提示 |
| 推理异常 | 错误卡片 + 异常信息 |
| 文本超长 (512 token) | 自动截断 |

## 10. 测试

- Compose UI 使用 `createComposeRule()` 测试交互
- Tokenizer 单元测试
- 不做 E2E（本地演示）
