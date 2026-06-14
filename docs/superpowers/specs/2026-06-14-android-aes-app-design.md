# Android AES 作文评分应用 — 设计规格

> 日期: 2026-06-14 | 状态: 已确认

## 1. 概述

在现有 Android 骨架 (`Android_HomeworkScore/`) 基础上，升级为完整的中文 AES 作文评分客户端应用。通过 HTTP 调用 Python Flask API 完成推理，应用本身不运行 AI 模型。

### 核心约束

- 客户端-服务器架构，Android App 仅做 UI + 网络请求
- 最低 SDK 29 (Android 10)
- 中文界面，不实现 i18n
- 在已有 Kotlin + Jetpack Compose 项目上改造，不推倒重来

## 2. 导航结构

底部 Tab 导航（Material3 NavigationBar），4 个 Tab：

| Tab | 图标 | 功能 |
|-----|------|------|
| 评分 | 📝 | 单篇文本输入 → 多维评分 → 雷达图 + 评语 |
| 批量 | 📊 | CSV 文件上传 → 批量评分 → 结果列表 + 下载 |
| 对比 | 🔄 | 同一文本中英文模型分别评分 → 并排对比 |
| 设置 | ⚙️ | 服务器地址配置、连接测试、模型状态、版本信息 |

## 3. 各 Tab 详细设计

### 3.1 评分 Tab (主页面)

**输入区**
- 三段式 Chip 语言选择器：`自动 / 英文 / 中文`，默认"自动"
- 多行文本输入框（OutlinedTextField），placeholder: "请输入作文内容...（中英文均可）"
- 实时统计栏：字符数/10000、词数、检测语言标签
- 提交按钮 → Loading 状态（CircularProgressIndicator + "评分中..."）

**结果区**（评分成功后展示）
- **总分仪表盘**：大号数字（×/100）+ 渐变进度条（红 0-40 / 黄 40-70 / 绿 70-100）
- **三维度卡片**：内容/结构/语言 各占一列，不同颜色标识（绿/靛/橙），显示 0-100 分数
- **雷达图**：Compose Canvas 自绘，三角形闭合，三轴分别对应内容/结构/语言，范围 [0,1]
- **评语卡片**：根据总分等级（高/中/低）显示不同颜色左边框，文字为模板评语
- **耗时显示**：elapsed_ms 换算显示，如 "耗时 1.2s"

**API 调用**：`POST /api/v1/score`，body: `{"text": "...", "language": "auto"}`

**状态处理**
- 空文本 → Toast 提示
- 超 10000 字符 → 截断警告
- 网络不通 → 错误卡片（红色），列出排查项
- API 返回 error → 显示 error 字段内容

### 3.2 批量 Tab

**布局**
- 文件选择区：虚线框 + "点击选择 CSV 文件" + 格式提示
- 文件信息栏：选中后显示文件名、预估篇数
- 开始按钮 → 进度条 + 实时进度文字
- 结果列表：LazyColumn，每项显示 id、语言、分数、状态（✅/❌）
- 下载按钮：将结果保存为 CSV 到 Downloads 目录

**API 调用**：`POST /api/v1/batch`，multipart form-data 上传 CSV 文件

**限制**
- 最多 100 篇（API 限制）
- CSV 编码自动检测 UTF-8/GBK

### 3.3 对比 Tab

**布局**
- 文本输入区（同评分 Tab，无语言选择器）
- 提交按钮 → 并发调用英文模型和中文模型
- 结果：左右两列并排展示
  - 左：🇬🇧 英文模型 (bert-base-uncased) — 总分 + 维度分
  - 右：🇨🇳 中文模型 (bert-base-chinese) — 总分 + 维度分
  - 中间分隔线 + 分数差值标注

**实现方式**：调用两次 `/api/v1/score`，分别指定 `language: "en"` 和 `language: "zh"`

### 3.4 设置 Tab

**布局**
- 服务器地址：OutlinedTextField + "测试连接" 按钮
  - 成功 → 绿色 Toast "连接成功"
  - 失败 → 红色 Toast + 错误信息
  - 地址保存到 SharedPreferences，下次启动自动填充
- 模型状态卡片：调用 `/api/v1/models` 和 `/api/v1/health`
  - 英文模型：名称 + ✅ 已加载 / ❌ 未加载
  - 中文模型：名称 + ✅ 已加载 / ❌ 未加载
- 应用信息：版本号、构建信息

## 4. 数据层设计

### 4.1 API 客户端 (Retrofit)

```kotlin
interface ScoreApiService {
    @POST("/api/v1/score")
    suspend fun score(@Body request: ScoreRequest): ScoreResponse

    @Multipart
    @POST("/api/v1/batch")
    suspend fun batchScore(@Part file: MultipartBody.Part): BatchResponse

    @GET("/api/v1/health")
    suspend fun health(): HealthResponse

    @GET("/api/v1/models")
    suspend fun models(): ModelsResponse
}
```

### 4.2 数据模型

- `ScoreRequest(text, language)` → `ScoreResponse(score, scores, feedback, language, elapsed_ms)`
- `BatchResponse(total, completed, elapsed_ms, results: List<BatchResult>)`
- `HealthResponse(status, en_model_loaded, cn_model_loaded)`
- `ModelsResponse(models: Map<String, ModelInfo>)`

### 4.3 动态 Base URL

- 默认值：`http://10.0.2.2:5000/`（模拟器本地映射）
- 用户在设置页修改后保存到 SharedPreferences
- Retrofit 实例根据当前 URL 动态创建（或使用 `@Url` 参数）

## 5. 主题与样式

- Material3 主题，主色 `#6366F1` (Indigo)
- 评分维度配色：
  - 内容：`#10B981` (绿)
  - 结构：`#6366F1` (靛)
  - 语言：`#F59E0B` (橙)
- 总分进度条：红→黄→绿 渐变
- 评语卡片：左侧 3px 彩色边框

## 6. 错误处理

| 场景 | UI 表现 |
|------|---------|
| 未输入文本 | Snackbar "请输入作文内容" |
| 文本超长 | 截断前 10000 字符，Snackbar 提示 |
| 网络超时 (30s) | 错误卡片 "连接超时" + 排查建议 |
| 服务器 500 | 错误卡片 "服务器错误" |
| 模型未加载 | 设置页显示 ❌ 状态 |
| CSV 格式错误 | 错误卡片 "CSV 格式不符" + 期望列名 |

## 7. 与现有代码的关系

**保留并修改：**
- `MainActivity.kt` — 改为 NavHost 入口
- `ScoreApi.kt` — 重写数据模型和 API 接口
- `HomeworkScoreScreen.kt` — 重构为评分 Tab
- `build.gradle.kts` — 添加 Compose Navigation 依赖
- 主题文件保持不变

**新增：**
- `ui/screen/BatchScreen.kt`
- `ui/screen/ComparisonScreen.kt`
- `ui/screen/SettingsScreen.kt`
- `ui/navigation/AppNavigation.kt`
- `ui/components/RadarChart.kt`
- `ui/components/ScoreGauge.kt`
- `ui/components/FeedbackCard.kt`
- `data/` — API 客户端 + 数据模型
- `data/PreferencesManager.kt` — SharedPreferences 封装

**删除：**
- essay_set 下拉选择器（新 API 不需要）
- 旧版 ScoreRequest/ScoreResponse（改用新 API 数据结构）

## 8. 测试策略

- Retrofit API 接口使用 MockWebServer 进行单元测试
- Compose UI 使用 `createComposeRule()` 测试关键交互
- 不做 E2E 测试（依赖真实服务器环境）

## 9. 构建与部署

- Gradle + Kotlin DSL
- 构建产物：APK (debug) + AAB (release)
- 最低 SDK 29，目标 SDK 36
