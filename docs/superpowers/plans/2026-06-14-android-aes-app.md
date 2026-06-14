# Android AES 作文评分应用 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 Android 骨架之上，构建基于 PyTorch Mobile 本地推理的中英双语作文评分 App。

**Architecture:** 单一 Activity + Jetpack Compose Navigation，4 个底部 Tab 页面。PyTorch Mobile 加载 .pt 模型文件，Kotlin 实现 BERT WordPiece 分词器，Compose Canvas 绘制雷达图。

**Tech Stack:** Kotlin, Jetpack Compose, Material3, PyTorch Mobile 1.13.1, Compose Navigation

**分支:** `feature/android-app` | **工作目录:** `Android_HomeworkScore/`

---

### Task 1: 项目基础搭建

**Files:**
- Modify: `Android_HomeworkScore/app/build.gradle.kts`
- Modify: `Android_HomeworkScore/gradle/libs.versions.toml`
- Modify: `Android_HomeworkScore/app/src/main/AndroidManifest.xml`
- Create: `Android_HomeworkScore/app/src/main/assets/` (目录)

**描述:** 从 main 分支引入 Android 项目，更新依赖，配置 PyTorch Mobile 和 Compose Navigation。

- [ ] **Step 1: 将 main 分支的 Android 项目拉入当前分支**

```bash
git checkout main -- Android_HomeworkScore/
```

- [ ] **Step 2: 更新 `gradle/libs.versions.toml`，添加导航和 PyTorch 版本**

打开 `gradle/libs.versions.toml`，在 `[versions]` 块追加：
```toml
navigationCompose = "2.7.7"
pytorch = "1.13.1"
```

在 `[libraries]` 块追加：
```toml
androidx-navigation-compose = { group = "androidx.navigation", name = "navigation-compose", version.ref = "navigationCompose" }
pytorch-android = { group = "org.pytorch", name = "pytorch_android_lite", version.ref = "pytorch" }
```

- [ ] **Step 3: 更新 `app/build.gradle.kts`，添加依赖**

在 `dependencies` 块追加：
```kotlin
// Compose Navigation
implementation(libs.androidx.navigation.compose)

// PyTorch Mobile
implementation(libs.pytorch.android)
```

- [ ] **Step 4: 简化 `AndroidManifest.xml`**

移除不必要的权限（不再需要网络），保留基础配置。确保 `application` 块包含：
```xml
<application
    android:allowBackup="true"
    android:icon="@mipmap/ic_launcher"
    android:label="@string/app_name"
    android:theme="@style/Theme.Android_HomeworkScore">
    <activity
        android:name=".MainActivity"
        android:exported="true"
        android:label="@string/app_name"
        android:theme="@style/Theme.Android_HomeworkScore">
        <intent-filter>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent-filter>
    </activity>
</application>
```

- [ ] **Step 5: 创建 assets 目录**

```bash
mkdir -p Android_HomeworkScore/app/src/main/assets/
```

- [ ] **Step 6: Commit**

```bash
git add Android_HomeworkScore/
git commit -m "build: set up Android project with PyTorch Mobile and Navigation"
```

---

### Task 2: BERT 分词器

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/inference/BertTokenizer.kt`

**描述:** 在 Kotlin 中实现基本 BERT WordPiece 分词器，从 assets 读取 vocab.txt 构建词表，支持中英文。

- [ ] **Step 1: 创建 `inference/BertTokenizer.kt`**

```kotlin
package com.example.android_homeworkscore.inference

import android.content.Context
import java.io.BufferedReader
import java.io.InputStreamReader

class BertTokenizer(private val context: Context, vocabAsset: String = "vocab.txt") {

    private val vocab: MutableMap<String, Int> = mutableMapOf()
    private val idToToken: MutableMap<Int, String> = mutableMapOf()

    val clsTokenId: Int get() = vocab["[CLS]"] ?: 101
    val sepTokenId: Int get() = vocab["[SEP]"] ?: 102
    val padTokenId: Int get() = vocab["[PAD]"] ?: 0
    val unkTokenId: Int get() = vocab["[UNK]"] ?: 100

    init {
        loadVocab(vocabAsset)
    }

    private fun loadVocab(assetName: String) {
        context.assets.open(assetName).use { stream ->
            BufferedReader(InputStreamReader(stream)).useLines { lines ->
                lines.forEachIndexed { index, token ->
                    val clean = token.trim()
                    vocab[clean] = index
                    idToToken[index] = clean
                }
            }
        }
    }

    fun tokenize(text: String, maxLength: Int = 512): LongArray {
        val tokens = mutableListOf<Int>()
        tokens.add(clsTokenId)

        val words = basicTokenize(text.lowercase())
        for (word in words) {
            if (word.isEmpty()) continue
            val subTokens = wordPieceTokenize(word)
            tokens.addAll(subTokens)
            if (tokens.size >= maxLength - 1) break
        }

        tokens.add(sepTokenId)

        // Padding
        val result = LongArray(maxLength) { padTokenId.toLong() }
        val attentionMask = IntArray(maxLength) { 0 }
        for (i in tokens.indices) {
            if (i >= maxLength) break
            result[i] = tokens[i].toLong()
            attentionMask[i] = 1
        }

        return result
    }

    fun basicTokenize(text: String): List<String> {
        // 按空格和标点分词，中文按字符拆分
        val result = mutableListOf<String>()
        val sb = StringBuilder()

        for (ch in text) {
            when {
                ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' -> {
                    if (sb.isNotEmpty()) { result.add(sb.toString()); sb.clear() }
                }
                ch in '一'..'鿿' || ch in '㐀'..'䶿' -> {
                    // 中文字符：单独成词
                    if (sb.isNotEmpty()) { result.add(sb.toString()); sb.clear() }
                    result.add(ch.toString())
                }
                ch.isLetterOrDigit() -> sb.append(ch)
                else -> {
                    // 标点符号
                    if (sb.isNotEmpty()) { result.add(sb.toString()); sb.clear() }
                    if (!ch.isWhitespace()) result.add(ch.toString())
                }
            }
        }
        if (sb.isNotEmpty()) result.add(sb.toString())
        return result
    }

    private fun wordPieceTokenize(word: String): List<Int> {
        val tokens = mutableListOf<Int>()
        var remaining = word
        var isFirst = true

        while (remaining.isNotEmpty()) {
            val prefix = if (isFirst) "" else "##"
            var found = false

            // 从最长匹配开始尝试
            for (end in remaining.length downTo 1) {
                val candidate = prefix + remaining.substring(0, end)
                val id = vocab[candidate]
                if (id != null) {
                    tokens.add(id)
                    remaining = remaining.substring(end)
                    found = true
                    break
                }
            }

            if (!found) {
                // 未匹配，使用 [UNK]
                tokens.add(unkTokenId)
                break
            }
            isFirst = false
        }
        return tokens
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/inference/BertTokenizer.kt
git commit -m "feat: add BERT WordPiece tokenizer in Kotlin"
```

---

### Task 3: 推理引擎

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/inference/AESPredictor.kt`
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/inference/LanguageDetector.kt`

**描述:** 封装 PyTorch Mobile 模型加载和推理，支持中英文双模型，实现语言检测和维度分生成。

- [ ] **Step 1: 创建 `LanguageDetector.kt`**

```kotlin
package com.example.android_homeworkscore.inference

object LanguageDetector {
    fun detect(text: String): String {
        if (text.isBlank()) return "en"
        val chineseChars = text.count { it in '一'..'鿿' || it in '㐀'..'䶿' }
        val englishChars = text.count { it in 'a'..'z' || it in 'A'..'Z' }
        val total = chineseChars + englishChars
        if (total == 0) return "en"
        return if (chineseChars.toDouble() / total > 0.5) "zh" else "en"
    }
}
```

- [ ] **Step 2: 创建 `AESPredictor.kt`**

```kotlin
package com.example.android_homeworkscore.inference

import android.content.Context
import org.pytorch.Module
import org.pytorch.Tensor
import java.io.File
import java.io.FileOutputStream

data class ScoreResult(
    val total: Float,
    val content: Float,
    val structure: Float,
    val language: Float,
    val feedback: Map<String, String>,
    val detectedLanguage: String,
    val elapsedMs: Long
)

class AESPredictor(private val context: Context) {
    private var enModel: Module? = null
    private var cnModel: Module? = null
    private var enTokenizer: BertTokenizer? = null
    private var cnTokenizer: BertTokenizer? = null
    private var enLoaded = false
    private var cnLoaded = false

    fun isEnLoaded(): Boolean = enLoaded
    fun isCnLoaded(): Boolean = cnLoaded

    fun loadModels() {
        try {
            enTokenizer = BertTokenizer(context, "vocab.txt")
            val enModelFile = copyAssetToFile("bert_model.pt")
            enModel = Module.load(enModelFile.absolutePath)
            enLoaded = true
        } catch (e: Exception) {
            enLoaded = false
        }

        try {
            cnTokenizer = BertTokenizer(context, "zh_vocab.txt")
            val cnModelFile = copyAssetToFile("zh_model.pt")
            cnModel = Module.load(cnModelFile.absolutePath)
            cnLoaded = true
        } catch (e: Exception) {
            cnLoaded = false
        }
    }

    private fun copyAssetToFile(assetName: String): File {
        val file = File(context.filesDir, assetName)
        if (!file.exists()) {
            context.assets.open(assetName).use { input ->
                FileOutputStream(file).use { output ->
                    input.copyTo(output)
                }
            }
        }
        return file
    }

    fun predict(text: String, language: String = "auto"): ScoreResult {
        val start = System.currentTimeMillis()
        val detectedLang = if (language == "auto") LanguageDetector.detect(text) else language

        val (model, tokenizer) = when (detectedLang) {
            "zh" -> {
                if (cnLoaded && cnModel != null && cnTokenizer != null)
                    Pair(cnModel!!, cnTokenizer!!)
                else if (enLoaded && enModel != null && enTokenizer != null)
                    Pair(enModel!!, enTokenizer!!)
                else throw IllegalStateException("No model loaded")
            }
            else -> {
                if (enLoaded && enModel != null && enTokenizer != null)
                    Pair(enModel!!, enTokenizer!!)
                else throw IllegalStateException("English model not loaded")
            }
        }

        val inputIds = tokenizer.tokenize(text, 512)
        val attentionMask = LongArray(512) { if (it < inputIds.count { id -> id != tokenizer.padTokenId.toLong() }) 1L else 0L }

        val inputTensor = Tensor.fromBlob(inputIds, longArrayOf(1, 512))
        val output = model.forward(org.pytorch.IValue.from(inputTensor)).toTensor()
        val totalScore = output.dataAsFloatArray[0]

        // 维度分 = 启发式拆分
        val content = (totalScore * 0.95f).coerceIn(0f, 1f)
        val structure = (totalScore * 1.02f).coerceIn(0f, 1f)
        val langScore = (totalScore * 1.03f).coerceIn(0f, 1f)

        val scores = mapOf("total" to totalScore.toDouble(), "content" to content.toDouble(), "structure" to structure.toDouble(), "language" to langScore.toDouble())
        val feedback = generateFeedback(scores, detectedLang)
        val elapsed = System.currentTimeMillis() - start

        return ScoreResult(
            total = totalScore,
            content = content,
            structure = structure,
            language = langScore,
            feedback = feedback,
            detectedLanguage = detectedLang,
            elapsedMs = elapsed
        )
    }

    private fun generateFeedback(scores: Map<String, Double>, language: String): Map<String, String> {
        // 模板化反馈，同 Python 版
        val total = scores["total"] ?: 0.5
        val level = when { total >= 0.7 -> "high"; total >= 0.4 -> "mid"; else -> "low" }

        val enTemplates = mapOf(
            "content" to mapOf(
                "high" to "论点明确，论证充分，举例恰当。展现了较强的思辨能力。",
                "mid" to "主要观点清晰，但论证深度和具体例证方面仍有提升空间。",
                "low" to "文章观点不够明确，缺乏有力的论证支撑。"
            ),
            "structure" to mapOf(
                "high" to "结构完整，层次分明。开头点题、段落衔接自然、结尾有力。",
                "mid" to "基本结构完整，但段落之间的过渡可以更加流畅。",
                "low" to "文章结构需要优化。建议增加明确的开头引入、合理安排段落层次。"
            ),
            "language" to mapOf(
                "high" to "语言表达流畅，词汇丰富，句式多样。展现了良好的语言功底。",
                "mid" to "语言基本通顺，但词汇和句式较为单一。注意润色表达。",
                "low" to "存在较多语病和用词不当。建议从基础语法和常用词汇入手。"
            )
        )

        val overallZh = mapOf(
            "high" to "总分表现优秀（%.1f分），文章在内容、结构和语言方面均表现良好。",
            "mid" to "总分中等（%.1f分），文章有一定基础，建议针对反馈意见进行修改提升。",
            "low" to "总分偏低（%.1f分），需要在内容深度、文章结构和语言表达方面进行系统提升。"
        )

        return mapOf(
            "content" to (enTemplates["content"]?.get(level) ?: ""),
            "structure" to (enTemplates["structure"]?.get(level) ?: ""),
            "language" to (enTemplates["language"]?.get(level) ?: ""),
            "overall" to String.format(overallZh[level] ?: "", total * 100)
        )
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/inference/
git commit -m "feat: add PyTorch Mobile inference engine with language detection"
```

---

### Task 4: UI 组件 — 雷达图

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/components/RadarChart.kt`

**描述:** Compose Canvas 自绘三角形雷达图，显示内容/结构/语言三维度分数。

- [ ] **Step 1: 创建 `RadarChart.kt`**

```kotlin
package com.example.android_homeworkscore.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.unit.dp

@Composable
fun RadarChart(
    scores: Map<String, Float>,
    modifier: Modifier = Modifier,
    color: Color = Color(0xFF6366F1)
) {
    val dims = listOf("content", "structure", "language")
    val labels = listOf("内容", "结构", "语言")
    val values = dims.map { scores[it] ?: 0f }

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(260.dp)
    ) {
        val centerX = size.width / 2
        val centerY = size.height / 2
        val radius = minOf(centerX, centerY) * 0.6f
        val n = 3

        // 绘制网格（3 层）
        for (level in 1..3) {
            val r = radius * level / 3
            val path = Path()
            for (i in 0 until n) {
                val angle = -Math.PI / 2 + 2 * Math.PI * i / n
                val x = centerX + r * Math.cos(angle).toFloat()
                val y = centerY + r * Math.sin(angle).toFloat()
                if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
            }
            path.close()
            drawPath(path, Color(0xFFE5E7EB), style = Stroke(1.dp.toPx()))
        }

        // 绘制轴线
        for (i in 0 until n) {
            val angle = -Math.PI / 2 + 2 * Math.PI * i / n
            val x = centerX + radius * Math.cos(angle).toFloat()
            val y = centerY + radius * Math.sin(angle).toFloat()
            drawLine(Color(0xFFE5E7EB), Offset(centerX, centerY), Offset(x, y), 1.dp.toPx())
        }

        // 绘制数据区域
        val dataPath = Path()
        for (i in 0 until n) {
            val angle = -Math.PI / 2 + 2 * Math.PI * i / n
            val v = values[i].coerceIn(0f, 1f)
            val x = centerX + radius * v * Math.cos(angle).toFloat()
            val y = centerY + radius * v * Math.sin(angle).toFloat()
            if (i == 0) dataPath.moveTo(x, y) else dataPath.lineTo(x, y)
        }
        dataPath.close()
        drawPath(dataPath, color.copy(alpha = 0.3f))
        drawPath(dataPath, color, style = Stroke(2.dp.toPx()))

        // 绘制数据点
        for (i in 0 until n) {
            val angle = -Math.PI / 2 + 2 * Math.PI * i / n
            val v = values[i].coerceIn(0f, 1f)
            val x = centerX + radius * v * Math.cos(angle).toFloat()
            val y = centerY + radius * v * Math.sin(angle).toFloat()
            drawCircle(color, 4.dp.toPx(), Offset(x, y))
        }

        // 标签文字
        val paint = android.graphics.Paint().apply {
            textAlign = android.graphics.Paint.Align.CENTER
            textSize = 12.dp.toPx()
            this.color = 0xFF6B7280.toInt()
        }
        for (i in 0 until n) {
            val angle = -Math.PI / 2 + 2 * Math.PI * i / n
            val labelR = radius + 24.dp.toPx()
            val x = centerX + labelR * Math.cos(angle).toFloat()
            val y = centerY + labelR * Math.sin(angle).toFloat() + 5.dp.toPx()
            drawContext.canvas.nativeCanvas.drawText(labels[i], x, y, paint)
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/components/RadarChart.kt
git commit -m "feat: add radar chart component with Compose Canvas"
```

---

### Task 5: UI 组件 — 分数仪表盘和评语卡片

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/components/ScoreGauge.kt`
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/components/FeedbackCard.kt`

**描述:** 分数仪表盘（总分大数字+渐变进度条+三维度卡片）和评语卡片组件。

- [ ] **Step 1: 创建 `ScoreGauge.kt`**

```kotlin
package com.example.android_homeworkscore.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ScoreGauge(total: Float, content: Float, structure: Float, language: Float) {
    val percent = (total * 100).toInt()

    // 总分仪表盘
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "$percent",
            fontSize = 48.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF6366F1)
        )
        Text("总分 / 100", fontSize = 13.sp, color = Color(0xFF9CA3AF))

        Spacer(modifier = Modifier.height(8.dp))

        // 渐变进度条
        Box(
            modifier = Modifier
                .fillMaxWidth(0.7f)
                .height(8.dp)
                .clip(RoundedCornerShape(4.dp))
                .background(Color(0xFFE5E7EB))
        ) {
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .fillMaxWidth(total.coerceIn(0f, 1f))
                    .clip(RoundedCornerShape(4.dp))
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(
                                Color(0xFFEF4444),
                                Color(0xFFF59E0B),
                                Color(0xFF10B981)
                            ),
                            startX = 0f,
                            endX = Float.POSITIVE_INFINITY
                        )
                    )
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        // 维度分卡片
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            DimensionCard("内容", content, Color(0xFF10B981), Modifier.weight(1f))
            DimensionCard("结构", structure, Color(0xFF6366F1), Modifier.weight(1f))
            DimensionCard("语言", language, Color(0xFFF59E0B), Modifier.weight(1f))
        }
    }
}

@Composable
fun DimensionCard(label: String, score: Float, color: Color, modifier: Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(color.copy(alpha = 0.1f))
            .padding(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "${(score * 100).toInt()}",
            fontSize = 22.sp,
            fontWeight = FontWeight.Bold,
            color = color
        )
        Text(label, fontSize = 13.sp, color = Color(0xFF6B7280))
    }
}
```

- [ ] **Step 2: 创建 `FeedbackCard.kt`**

```kotlin
package com.example.android_homeworkscore.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun FeedbackCard(feedback: Map<String, String>, total: Float) {
    val borderColor = when {
        total >= 0.7f -> Color(0xFF10B981)
        total >= 0.4f -> Color(0xFFF59E0B)
        else -> Color(0xFFEF4444)
    }

    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            "评语",
            fontSize = 16.sp,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        feedback["overall"]?.let {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0xFFF3F4F6))
                    .padding(start = 12.dp, end = 12.dp, top = 10.dp, bottom = 10.dp)
            ) {
                Text(it, fontSize = 14.sp, color = Color(0xFF374151))
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            listOf("content", "structure", "language").forEachIndexed { index, dim ->
                val colors = listOf(Color(0xFF10B981), Color(0xFF6366F1), Color(0xFFF59E0B))
                val labels = listOf("内容", "结构", "语言")
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .clip(RoundedCornerShape(8.dp))
                        .background(colors[index].copy(alpha = 0.08f))
                        .padding(10.dp)
                ) {
                    Column {
                        Text(labels[index], fontSize = 12.sp, fontWeight = FontWeight.Bold, color = colors[index])
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(feedback[dim] ?: "", fontSize = 12.sp, color = Color(0xFF4B5563))
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/components/ScoreGauge.kt Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/components/FeedbackCard.kt
git commit -m "feat: add score gauge and feedback card components"
```

---

### Task 6: 导航结构

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/navigation/AppNavigation.kt`

**描述:** 定义 Bottom Navigation Bar 和 NavHost，连接 4 个 Tab 页面。

- [ ] **Step 1: 创建 `AppNavigation.kt`**

```kotlin
package com.example.android_homeworkscore.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.ui.screen.*

sealed class Screen(val route: String, val label: String) {
    object Score : Screen("score", "评分")
    object Batch : Screen("batch", "批量")
    object Compare : Screen("compare", "对比")
    object Settings : Screen("settings", "设置")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppNavigation(predictor: AESPredictor) {
    val navController = rememberNavController()
    val screens = listOf(Screen.Score, Screen.Batch, Screen.Compare, Screen.Settings)

    Scaffold(
        bottomBar = {
            NavigationBar {
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentRoute = navBackStackEntry?.destination?.route

                screens.forEach { screen ->
                    NavigationBarItem(
                        icon = { Text(when (screen) {
                            Screen.Score -> "📝"
                            Screen.Batch -> "📊"
                            Screen.Compare -> "🔄"
                            Screen.Settings -> "⚙️"
                        }, fontSize = androidx.compose.ui.unit.TextUnit(20f, androidx.compose.ui.unit.TextUnitType.Sp)) },
                        label = { Text(screen.label) },
                        selected = currentRoute == screen.route,
                        onClick = {
                            if (currentRoute != screen.route) {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.startDestinationId) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Score.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Score.route) { ScoreScreen(predictor) }
            composable(Screen.Batch.route) { BatchScreen(predictor) }
            composable(Screen.Compare.route) { CompareScreen(predictor) }
            composable(Screen.Settings.route) { SettingsScreen(predictor) }
        }
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/navigation/AppNavigation.kt
git commit -m "feat: add bottom tab navigation with 4 screens"
```

---

### Task 7: 评分页面

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/ScoreScreen.kt`
- Delete/Move: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/HomeworkScoreScreen.kt` (旧文件，重命名)

**描述:** 实现评分 Tab：语言选择 Chip、文本输入、提交评分、结果展示（仪表盘+雷达图+评语）。

- [ ] **Step 1: 创建 `ScoreScreen.kt`**

```kotlin
package com.example.android_homeworkscore.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.inference.LanguageDetector
import com.example.android_homeworkscore.inference.ScoreResult
import com.example.android_homeworkscore.ui.components.FeedbackCard
import com.example.android_homeworkscore.ui.components.RadarChart
import com.example.android_homeworkscore.ui.components.ScoreGauge
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun ScoreScreen(predictor: AESPredictor) {
    var inputText by remember { mutableStateOf("") }
    var selectedLang by remember { mutableStateOf("auto") }
    var result by remember { mutableStateOf<ScoreResult?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    val scrollState = rememberScrollState()
    val langOptions = listOf("auto" to "自动", "en" to "英文", "zh" to "中文")
    val detectedLang = if (inputText.isNotBlank()) LanguageDetector.detect(inputText) else null

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // 语言选择 Chip
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            langOptions.forEach { (code, label) ->
                FilterChip(
                    selected = selectedLang == code,
                    onClick = { selectedLang = code },
                    label = { Text(label) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = Color(0xFF6366F1),
                        selectedLabelColor = Color.White
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // 文本输入
        OutlinedTextField(
            value = inputText,
            onValueChange = { if (it.length <= 10000) inputText = it },
            modifier = Modifier.fillMaxWidth().height(160.dp),
            placeholder = { Text("请输入作文内容...（中英文均可）") },
            shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
        )

        // 统计栏
        Row(
            modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text("字符: ${inputText.length}/10000", style = MaterialTheme.typography.labelSmall)
            Text("词数: ${inputText.split("\\s+".toRegex()).size}", style = MaterialTheme.typography.labelSmall)
            Text("检测: ${if (detectedLang == "zh") "🇨🇳 中文" else "🌐 英文"}", style = MaterialTheme.typography.labelSmall)
        }

        // 提交按钮
        Button(
            onClick = {
                isLoading = true
                error = null
                result = null
                kotlinx.coroutines.CoroutineScope(Dispatchers.Default).launch {
                    try {
                        result = predictor.predict(inputText, selectedLang)
                    } catch (e: Exception) {
                        error = e.message ?: "推理失败"
                    } finally {
                        isLoading = false
                    }
                }
            },
            modifier = Modifier.fillMaxWidth().height(52.dp),
            enabled = inputText.isNotBlank() && !isLoading,
            shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1))
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(22.dp), color = Color.White, strokeWidth = 2.dp)
                Text(" 评分中...", modifier = Modifier.padding(start = 8.dp))
            } else {
                Text("🚀 提交评分")
            }
        }

        // 结果显示
        result?.let { res ->
            Spacer(modifier = Modifier.height(20.dp))

            Text("耗时 ${res.elapsedMs}ms", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
            Spacer(modifier = Modifier.height(8.dp))

            ScoreGauge(res.total, res.content, res.structure, res.language)

            Spacer(modifier = Modifier.height(16.dp))

            RadarChart(
                scores = mapOf("content" to res.content, "structure" to res.structure, "language" to res.language)
            )

            Spacer(modifier = Modifier.height(16.dp))

            FeedbackCard(feedback = res.feedback, total = res.total)
        }

        // 错误显示
        error?.let { msg ->
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFFFEF2F2)),
                shape = androidx.compose.foundation.shape.RoundedCornerShape(8.dp)
            ) {
                Text("❌ $msg", modifier = Modifier.padding(16.dp), color = Color(0xFFDC2626))
            }
        }
    }
}
```

- [ ] **Step 2: 删除旧文件 `HomeworkScoreScreen.kt`**

```bash
rm Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/HomeworkScoreScreen.kt
```

- [ ] **Step 3: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/
git commit -m "feat: add scoring screen with language chips, gauge, and radar chart"
```

---

### Task 8: 批量评分页面

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/BatchScreen.kt`

**描述:** 批量评分页面，CSV 文件选择、逐条评分、结果列表。

- [ ] **Step 1: 创建 `BatchScreen.kt`**

```kotlin
package com.example.android_homeworkscore.ui.screen

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.android_homeworkscore.inference.AESPredictor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader

data class BatchItem(val id: String, val text: String, val language: String)
data class BatchResult(val id: String, val score: String, val status: String)

@Composable
fun BatchScreen(predictor: AESPredictor) {
    var items by remember { mutableStateOf<List<BatchItem>>(emptyList()) }
    var results by remember { mutableStateOf<List<BatchResult>>(emptyList()) }
    var isProcessing by remember { mutableStateOf(false) }
    var progress by remember { mutableStateOf(0) }
    var selectedFileName by remember { mutableStateOf<String?>(null) }

    val context = LocalContext.current

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            selectedFileName = it.lastPathSegment ?: "unknown.csv"
            val csv = readCsvFromUri(context, it)
            items = csv
            results = emptyList()
        }
    }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        // 文件选择
        OutlinedCard(
            onClick = { filePicker.launch("text/*") },
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
            shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
        ) {
            Column(
                modifier = Modifier.padding(24.dp).fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("📁", fontSize = androidx.compose.ui.unit.TextUnit(32f, androidx.compose.ui.unit.TextUnitType.Sp))
                Text(
                    if (selectedFileName != null) "已选择: $selectedFileName" else "点击选择 CSV 文件",
                    style = MaterialTheme.typography.bodyMedium
                )
                Text("列: essay_id, text, language", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
            }
        }

        if (items.isNotEmpty()) {
            Text("共 ${items.size} 篇作文", style = MaterialTheme.typography.titleSmall)
            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = {
                    isProcessing = true
                    progress = 0
                    kotlinx.coroutines.CoroutineScope(Dispatchers.Default).launch {
                        val newResults = mutableListOf<BatchResult>()
                        items.forEachIndexed { index, item ->
                            try {
                                val res = predictor.predict(item.text, item.language)
                                newResults.add(BatchResult(item.id, "${(res.total * 100).toInt()}分", "✅"))
                            } catch (e: Exception) {
                                newResults.add(BatchResult(item.id, "失败", "❌ ${e.message}"))
                            }
                            progress = index + 1
                            withContext(Dispatchers.Main) { results = newResults.toList() }
                        }
                        isProcessing = false
                    }
                },
                modifier = Modifier.fillMaxWidth().height(48.dp),
                enabled = !isProcessing
            ) {
                Text(if (isProcessing) "评分中..." else "🚀 开始批量评分")
            }

            if (isProcessing) {
                Spacer(modifier = Modifier.height(8.dp))
                LinearProgressIndicator(
                    progress = { progress.toFloat() / items.size },
                    modifier = Modifier.fillMaxWidth()
                )
                Text("进度: $progress / ${items.size}", style = MaterialTheme.typography.labelSmall)
            }
        }

        // 结果列表
        if (results.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            LazyColumn {
                itemsIndexed(results) { index, r ->
                    ListItem(
                        headlineContent = { Text("#${r.id}  ${r.score}") },
                        supportingContent = { Text(r.status) },
                        leadingContent = { Text("${index + 1}", fontWeight = FontWeight.Bold) }
                    )
                }
            }
        }
    }
}

fun readCsvFromUri(context: android.content.Context, uri: Uri): List<BatchItem> {
    val items = mutableListOf<BatchItem>()
    context.contentResolver.openInputStream(uri)?.use { stream ->
        BufferedReader(InputStreamReader(stream)).use { reader ->
            val header = reader.readLine() ?: return items
            reader.forEachLine { line ->
                val parts = line.split(",")
                if (parts.size >= 2) {
                    items.add(BatchItem(
                        id = parts.getOrNull(0)?.trim() ?: "${items.size}",
                        text = parts.getOrNull(1)?.trim() ?: "",
                        language = parts.getOrNull(2)?.trim() ?: "auto"
                    ))
                }
            }
        }
    }
    return items
}
```

- [ ] **Step 2: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/BatchScreen.kt
git commit -m "feat: add batch scoring screen with CSV import"
```

---

### Task 9: 中英对比 + 设置页面

**Files:**
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/CompareScreen.kt`
- Create: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/SettingsScreen.kt`

**描述:** 对比页（中英文模型分别评分并排展示）和设置页（模型状态、版本信息）。

- [ ] **Step 1: 创建 `CompareScreen.kt`**

```kotlin
package com.example.android_homeworkscore.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.inference.ScoreResult
import kotlinx.coroutines.Dispatchers

@Composable
fun CompareScreen(predictor: AESPredictor) {
    var inputText by remember { mutableStateOf("") }
    var enResult by remember { mutableStateOf<ScoreResult?>(null) }
    var cnResult by remember { mutableStateOf<ScoreResult?>(null) }
    var isLoading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        OutlinedTextField(
            value = inputText,
            onValueChange = { if (it.length <= 10000) inputText = it },
            modifier = Modifier.fillMaxWidth().height(140.dp),
            placeholder = { Text("输入文本，同时用中英文模型评分对比") },
            shape = androidx.compose.foundation.shape.RoundedCornerShape(12.dp)
        )

        Spacer(modifier = Modifier.height(12.dp))

        Button(
            onClick = {
                isLoading = true
                kotlinx.coroutines.CoroutineScope(Dispatchers.Default).launch {
                    enResult = predictor.predict(inputText, "en")
                    cnResult = predictor.predict(inputText, "zh")
                    isLoading = false
                }
            },
            modifier = Modifier.fillMaxWidth().height(48.dp),
            enabled = inputText.isNotBlank() && !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White)
                Text(" 评分中...", modifier = Modifier.padding(start = 8.dp))
            } else Text("🔄 开始对比")
        }

        if (enResult != null && cnResult != null) {
            Spacer(modifier = Modifier.height(20.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                CompareCard("🇬🇧 英文模型", enResult!!, Color(0xFF6366F1), Modifier.weight(1f))
                CompareCard("🇨🇳 中文模型", cnResult!!, Color(0xFFF59E0B), Modifier.weight(1f))
            }
        }
    }
}

@Composable
fun CompareCard(title: String, result: ScoreResult, color: Color, modifier: Modifier) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.05f))
    ) {
        Column(modifier = Modifier.padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(title, fontWeight = FontWeight.Bold, color = color)
            Text("${(result.total * 100).toInt()}分", fontSize = androidx.compose.ui.unit.TextUnit(28f, androidx.compose.ui.unit.TextUnitType.Sp), fontWeight = FontWeight.Bold, color = color)
            Text("内容: ${(result.content * 100).toInt()}", fontSize = androidx.compose.ui.unit.TextUnit(12f, androidx.compose.ui.unit.TextUnitType.Sp))
            Text("结构: ${(result.structure * 100).toInt()}", fontSize = androidx.compose.ui.unit.TextUnit(12f, androidx.compose.ui.unit.TextUnitType.Sp))
            Text("语言: ${(result.language * 100).toInt()}", fontSize = androidx.compose.ui.unit.TextUnit(12f, androidx.compose.ui.unit.TextUnitType.Sp))
        }
    }
}
```

- [ ] **Step 2: 创建 `SettingsScreen.kt`**

```kotlin
package com.example.android_homeworkscore.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.android_homeworkscore.inference.AESPredictor

@Composable
fun SettingsScreen(predictor: AESPredictor) {
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp)
    ) {
        Text("模型状态", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(12.dp))

        ModelStatusCard("英文模型 (BERT-base-uncased)", predictor.isEnLoaded())
        Spacer(modifier = Modifier.height(8.dp))
        ModelStatusCard("中文模型 (BERT-base-chinese)", predictor.isCnLoaded())

        Spacer(modifier = Modifier.height(24.dp))

        Text("模型信息", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(8.dp))

        InfoRow("英文 QWK", "0.58")
        InfoRow("中文 QWK", "0.79")
        InfoRow("应用版本", "v1.0")

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = { predictor.loadModels() },
            modifier = Modifier.fillMaxWidth().height(48.dp)
        ) {
            Text("🔄 重新加载模型")
        }
    }
}

@Composable
fun ModelStatusCard(name: String, loaded: Boolean) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (loaded) Color(0xFFF0FDF4) else Color(0xFFFEF2F2)
        )
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(14.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(name, style = MaterialTheme.typography.bodyMedium)
            Text(
                if (loaded) "✅ 已加载" else "❌ 未加载",
                color = if (loaded) Color(0xFF16A34A) else Color(0xFFDC2626),
                fontWeight = FontWeight.Medium
            )
        }
    }
}

@Composable
fun InfoRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, color = Color.Gray)
        Text(value, fontWeight = FontWeight.Medium)
    }
}
```

- [ ] **Step 3: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/CompareScreen.kt Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ui/screen/SettingsScreen.kt
git commit -m "feat: add comparison and settings screens"
```

---

### Task 10: MainActivity 集成

**Files:**
- Modify: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/MainActivity.kt`
- Delete: `Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ScoreApi.kt`

**描述:** 改造 MainActivity 为 Compose Navigation 入口，初始化推理引擎，删除旧的 Retrofit 网络层。

- [ ] **Step 1: 重写 `MainActivity.kt`**

```kotlin
package com.example.android_homeworkscore

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.ui.navigation.AppNavigation

class MainActivity : ComponentActivity() {

    private lateinit var predictor: AESPredictor

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        predictor = AESPredictor(applicationContext)
        Thread { predictor.loadModels() }.start()

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AppNavigation(predictor)
                }
            }
        }
    }
}
```

- [ ] **Step 2: 删除旧文件**

```bash
rm Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ScoreApi.kt
```

- [ ] **Step 3: Commit**

```bash
git add Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/MainActivity.kt
git rm Android_HomeworkScore/app/src/main/java/com/example/android_homeworkscore/ScoreApi.kt
git commit -m "feat: integrate navigation and inference engine into MainActivity"
```

---

### Task 11: 模型文件复制 + 最终验证

**描述:** 复制 Python 训练的模型和分词器文件到 Android assets，验证构建。

- [ ] **Step 1: 复制模型文件到 assets**

```bash
cp models/best_model.pt Android_HomeworkScore/app/src/main/assets/bert_model.pt
cp models/zh_bert/best_model.pt Android_HomeworkScore/app/src/main/assets/zh_model.pt
```

- [ ] **Step 2: 生成 vocab.txt**

从 HuggingFace 缓存或 transformers 库导出 vocab 文件：
```bash
python3 -c "
from transformers import AutoTokenizer
# 英文
tok = AutoTokenizer.from_pretrained('bert-base-uncased')
with open('Android_HomeworkScore/app/src/main/assets/vocab.txt', 'w') as f:
    for token, id in sorted(tok.vocab.items(), key=lambda x: x[1]):
        f.write(token + '\n')
# 中文
tok = AutoTokenizer.from_pretrained('bert-base-chinese')
with open('Android_HomeworkScore/app/src/main/assets/zh_vocab.txt', 'w') as f:
    for token, id in sorted(tok.vocab.items(), key=lambda x: x[1]):
        f.write(token + '\n')
print('vocab files generated')
"
```

- [ ] **Step 3: Commit**

```bash
git add Android_HomeworkScore/app/src/main/assets/vocab.txt Android_HomeworkScore/app/src/main/assets/zh_vocab.txt
git commit -m "chore: add tokenizer vocab files for Android"
```

---

### 文件清单总结

| 操作 | 文件 |
|------|------|
| 新建 | `inference/BertTokenizer.kt` |
| 新建 | `inference/AESPredictor.kt` |
| 新建 | `inference/LanguageDetector.kt` |
| 新建 | `ui/components/RadarChart.kt` |
| 新建 | `ui/components/ScoreGauge.kt` |
| 新建 | `ui/components/FeedbackCard.kt` |
| 新建 | `ui/navigation/AppNavigation.kt` |
| 新建 | `ui/screen/ScoreScreen.kt` |
| 新建 | `ui/screen/BatchScreen.kt` |
| 新建 | `ui/screen/CompareScreen.kt` |
| 新建 | `ui/screen/SettingsScreen.kt` |
| 修改 | `MainActivity.kt` |
| 修改 | `app/build.gradle.kts` |
| 修改 | `gradle/libs.versions.toml` |
| 删除 | `ScoreApi.kt` |
| 删除 | `HomeworkScoreScreen.kt` |
