# AES 自动作文评分系统 — Android 版操作指南

## 1. 项目简介

基于 PyTorch Mobile 的离线作文评分 Android 应用，支持中英文双语作文的自动评分。不依赖网络，模型推理完全在本地设备完成。

**核心功能：**

- 自动检测中/英文语种
- 返回 0-100 分总分 + 三个维度评分（内容、结构、语言）
- 雷达图可视化 + 智能评语反馈
- 批量 CSV 评分
- 中英文模型对比评分

---

## 2. 技术栈

| 组件 | 版本 |
|------|------|
| Kotlin | 2.2.10 |
| AGP (Android Gradle Plugin) | 9.1.0 |
| Compose BOM | 2024.09.00 |
| Material 3 | Compose Material 3 |
| minSdk | 29 (Android 10) |
| targetSdk | 36 |
| PyTorch Mobile Lite | 1.13.1 (通过 libs 引用) |
| Retrofit + OkHttp | (预留，当前离线推理不依赖) |

---

## 3. 环境准备

### 3.1 必需工具

- **Android Studio** (推荐 2024.2+ Hedgehog 或更新版本)
- **JDK 11 或 17**
- **Gradle 8.x**（通过 `./gradlew` wrapper 自动下载）

### 3.2 模型文件准备

将以下模型文件放入 `app/src/main/assets/` 目录：

```
app/src/main/assets/
├── bert_model.pt       # 英文模型（PyTorch Mobile .pt 格式）
├── zh_model.pt         # 中文模型（PyTorch Mobile .pt 格式）
├── vocab.txt           # 英文 BERT 词表（默认已提供）
└── zh_vocab.txt        # 中文 BERT 词表（默认已提供）
```

**生成 .pt 模型文件的方法**（在项目根目录执行）：

```bash
# 1. 安装依赖
pip install torch transformers

# 2. 导出英文模型
python -c "
import torch
from transformers import AutoModel
# 加载训练好的模型权重
model = AutoModel.from_pretrained('path/to/en/model')
# 添加评分头
class AESModel(torch.nn.Module):
    def __init__(self, bert):
        super().__init__()
        self.bert = bert
        self.dropout = torch.nn.Dropout(0.1)
        self.fc = torch.nn.Linear(768, 1)
        self.sigmoid = torch.nn.Sigmoid()
    def forward(self, input_ids):
        x = self.bert(input_ids).last_hidden_state[:, 0, :]
        x = self.dropout(x)
        x = self.fc(x)
        return self.sigmoid(x)

model = AESModel(model)
model.eval()
# 导出为 TorchScript
scripted = torch.jit.trace(model, torch.randint(0, 1000, (1, 512)))
scripted.save('Android_HomeworkScore/app/src/main/assets/bert_model.pt')
print('bert_model.pt exported')
"
```

> 注意：中文模型使用 BERT-base-chinese，导出步骤同上，文件命名为 `zh_model.pt`。

---

## 4. 项目结构

```
Android_HomeworkScore/
├── build.gradle.kts          # 根构建文件
├── settings.gradle.kts       # 项目设置
├── gradle/
│   ├── libs.versions.toml    # 版本目录（统一依赖版本）
│   └── wrapper/              # Gradle Wrapper
├── gradlew / gradlew.bat     # Gradle 命令行入口
└── app/
    ├── build.gradle.kts      # 应用级构建文件
    └── src/main/
        ├── AndroidManifest.xml
        ├── assets/
        │   ├── vocab.txt          # 英文 BERT 词表（30522 词）
        │   ├── zh_vocab.txt       # 中文 BERT 词表（21128 词）
        │   ├── bert_model.pt      # 英文模型文件（需要自行生成）
        │   └── zh_model.pt        # 中文模型文件（需要自行生成）
        ├── java/com/example/android_homeworkscore/
        │   ├── MainActivity.kt          # 应用入口
        │   ├── inference/
        │   │   ├── AESPredictor.kt      # 推理引擎（模型加载、预测）
        │   │   ├── BertTokenizer.kt     # BERT WordPiece 分词器
        │   │   └── LanguageDetector.kt  # 中英文自动检测
        │   └── ui/
        │       ├── components/
        │       │   ├── ScoreGauge.kt    # 总分配分仪表 + 维度卡片
        │       │   ├── RadarChart.kt    # Canvas 手绘雷达图
        │       │   └── FeedbackCard.kt  # 智能评语卡片
        │       ├── navigation/
        │       │   └── AppNavigation.kt # 底部导航栏 + 路由
        │       ├── screen/
        │       │   ├── ScoreScreen.kt   # 单篇评分页面
        │       │   ├── BatchScreen.kt   # 批量评分页面
        │       │   ├── CompareScreen.kt # 中英对比页面
        │       │   └── SettingsScreen.kt # 设置页面
        │       └── theme/
        │           ├── Color.kt         # 颜色定义
        │           ├── Theme.kt         # Material3 主题
        │           └── Type.kt          # 字体样式
        └── res/
            ├── values/
            │   ├── strings.xml
            │   ├── colors.xml
            │   └── themes.xml
            └── drawable/ / mipmap-*/   # 图标资源
```

---

## 5. 构建与运行

### 5.1 使用 Android Studio

1. 打开 Android Studio，选择 **"Open"**
2. 选择 `Android_HomeworkScore/` 目录
3. 等待 Gradle 同步完成
4. 将模型文件放入 `app/src/main/assets/`（见 3.2 节）
5. 连接 Android 设备 或 启动模拟器（API ≥ 29）
6. 点击 **Run 'app'** ▶ 按钮

### 5.2 使用命令行

```bash
# 进入 Android 项目目录
cd Android_HomeworkScore

# 构建 APK（Debug）
./gradlew assembleDebug

# 安装到已连接的设备
adb install app/build/outputs/apk/debug/app-debug.apk

# 或者一步完成
./gradlew installDebug
```

---

## 6. 页面功能介绍

应用使用底部 4 个 Tab 导航：

### 6.1 评分（Tab 1 — 📝 评分）

单篇作文评分，主界面。

| 操作 | 说明 |
|------|------|
| 选择语言 | 顶部 FilterChip：自动 / 英文 / 中文，默认"自动" |
| 输入文本 | 文本框粘贴或输入作文，上限 10000 字符 |
| 字数统计 | 输入时实时显示字符数、词数、检测到的语种 |
| 提交评分 | 点击"提交评分"按钮，等待推理（约 0.5-2 秒） |
| 查看结果 | 总分（大号数字）+ 渐变色进度条 + 三维度卡片 |
| 雷达图 | Canvas 绘制的三轴雷达图（内容/结构/语言） |
| 智能评语 | 整体 + 三个维度的中文反馈评语 |

**提示：**
- 中文作文建议 200-2000 字，英文建议 100-1000 词
- 混合语言文本可能影响检测和评分精度

### 6.2 批量评分（Tab 2 — 📊 批量）

批量处理多篇作文。

| 操作 | 说明 |
|------|------|
| 选择文件 | 点击卡片，从系统文件选择器选择 CSV 文件 |
| 查看列表 | 选择后显示文件名和作文数量 |
| 开始评分 | 点击"开始批量评分"，逐篇推理 |
| 进度条 | 实时显示处理进度 |
| 查看结果 | LazyColumn 列表，每篇显示编号和得分 |

**CSV 文件格式：**

```csv
essay_id,text,language
1,"This is an English essay content...",en
2,"这是一篇中文作文...",zh
3,"Another essay here...",auto
```

- `essay_id`: 作文唯一标识
- `text`: 作文文本（建议不加引号包裹用逗号隔开，如果文本中含逗号需要双引号包裹）
- `language`: `en` / `zh` / `auto`（自动检测）

### 6.3 对比（Tab 3 — 🔄 对比）

同一篇文本同时用英文和中文模型分别评分。

| 操作 | 说明 |
|------|------|
| 输入文本 | 文本框粘贴或输入作文 |
| 开始对比 | 点击按钮，同时发起两次推理 |
| 查看结果 | 左右两张卡片并排显示 |

**左侧卡片**（英文模型）：显示英文 BERT 模型评分  
**右侧卡片**（中文模型）：显示中文 BERT 模型评分

每张卡片显示：总分 + 内容/结构/语言三个维度分

### 6.4 设置（Tab 4 — ⚙️ 设置）

查看模型状态和系统信息。

| 信息 | 说明 |
|------|------|
| 模型状态 | 英文/中文模型是否已加载（绿色 ✅ / 红色 ❌） |
| 英文 QWK | 0.58（Quadratic Weighted Kappa，英文模型评估指标） |
| 中文 QWK | 0.79（中文模型评估指标） |
| 应用版本 | v1.0 |

**重新加载模型**按钮：如果模型加载失败，点击按钮尝试重新加载。

---

## 7. 评分说明

### 7.1 推理流程

```
输入文本 → 语言检测 → BERT 分词 → PyTorch Mobile 推理
→ 总分 → 维度分（按系数扩展） → 模板评语生成 → 返回结果
```

### 7.2 维度评分

维度分数由总分配合经验系数计算：

| 维度 | 系数 | 说明 |
|------|------|------|
| 内容 | ×0.95 | 论点的明确性、论证的深度和例证质量 |
| 结构 | ×1.02 | 开头引入、段落衔接、结尾总结的完整性 |
| 语言 | ×1.03 | 词汇丰富度、语法准确度、句式的多样性 |

### 7.3 智能评语

根据总分区间生成三档评语：

| 档位 | 分数范围 | 含义 |
|------|---------|------|
| 优秀（high） | 70-100 | 文章在各方面均表现良好 |
| 中等（mid） | 40-69 | 有一定基础，有提升空间 |
| 待提升（low） | 0-39 | 需要系统性改进 |

---

## 8. 常见问题

### Q: 打开项目后 Gradle sync 失败？

- 检查是否安装了 JDK 11+（Android Studio → Settings → Build → Build Tools → Gradle → Gradle JDK）
- 确保网络稳定，Gradle wrapper 会自动下载对应版本

### Q: 应用闪退 / 模型加载失败？

- 确认 `assets/` 目录下有 `bert_model.pt` 和 `zh_model.pt`
- 模型文件必须是用 PyTorch Mobile 导出的 TorchScript 格式
- 查看 Logcat 输出：`adb logcat | grep AESPredictor`

### Q: BERT 分词器报错？

- 确认 `assets/vocab.txt` 和 `assets/zh_vocab.txt` 存在
- 词表文件必须是 UTF-8 编码，每行一个 token

### Q: 推理很慢？

- 首次推理可能需要更长时间（模型初始化）
- 无 GPU 加速，推理时间取决于设备 CPU 性能
- 建议在 Android 12+ (API 31) 设备上运行以获得更优性能

---

## 9. 开发说明

### 依赖管理

项目使用 `gradle/libs.versions.toml` 统一管理版本，新增依赖先在 `[versions]` 中定义版本号，再在 `[libraries]` 中声明。

### 代码风格

- Kotlin 使用 Compose 声明式 UI 范式
- 文件按职责分层：`inference/`（推理层）、`ui/screen/`（页面层）、`ui/components/`（组件层）
- 协程 (`kotlinx.coroutines`) 处理异步推理，`Dispatchers.Default` 在后台线程运行，`Dispatchers.Main` 更新 UI

### 项目 JDK 配置

`gradle/gradle-daemon-jvm.properties` 指定 Gradle Daemon 的 JVM 路径。如果本地 JDK 路径不同，修改此文件或删除它让 Gradle 使用默认 JDK。

---

## 10. 与 Web 版的对比

| 特性 | Web 版 | Android 版 |
|------|--------|-----------|
| 架构 | Flask API + Streamlit UI | PyTorch Mobile 本地推理 |
| 网络依赖 | 需要 | 不需要 |
| 模型加载 | 启动时预加载 | 应用启动时加载 |
| 语言切换 | 中/英文 UI | 仅中文 UI |
| 批量评分 | JSON 输出下载 | CSV 直接读取 |
| 部署方式 | 浏览器访问 | APK 安装 |
