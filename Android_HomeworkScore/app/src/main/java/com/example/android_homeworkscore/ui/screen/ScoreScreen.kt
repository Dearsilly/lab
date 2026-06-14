package com.example.android_homeworkscore.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
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
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun ScoreScreen(predictor: AESPredictor) {
    var inputText by remember { mutableStateOf("") }
    var selectedLang by remember { mutableStateOf("auto") }
    var result by remember { mutableStateOf<ScoreResult?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    val scrollState = rememberScrollState()
    val scope = rememberCoroutineScope()
    val langOptions = listOf("auto" to "自动", "en" to "英文", "zh" to "中文")
    val detectedLang = if (inputText.isNotBlank()) LanguageDetector.detect(inputText) else null

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Language chips
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

        OutlinedTextField(
            value = inputText,
            onValueChange = { if (it.length <= 10000) inputText = it },
            modifier = Modifier.fillMaxWidth().height(160.dp),
            placeholder = { Text("请输入作文内容...（中英文均可）") },
            shape = RoundedCornerShape(12.dp)
        )

        Row(
            modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text("字符: ${inputText.length}/10000", style = MaterialTheme.typography.labelSmall)
            Text("词数: ${inputText.split("\\s+".toRegex()).size}", style = MaterialTheme.typography.labelSmall)
            Text("检测: ${if (detectedLang == "zh") "中文" else "英文"}", style = MaterialTheme.typography.labelSmall)
        }

        Button(
            onClick = {
                isLoading = true
                error = null
                result = null
                scope.launch(Dispatchers.Default) {
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
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1))
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(22.dp), color = Color.White, strokeWidth = 2.dp)
                Text(" 评分中...", modifier = Modifier.padding(start = 8.dp))
            } else {
                Text("提交评分")
            }
        }

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

        error?.let { msg ->
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFFFEF2F2)),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("错误: $msg", modifier = Modifier.padding(16.dp), color = Color(0xFFDC2626))
            }
        }
    }
}
