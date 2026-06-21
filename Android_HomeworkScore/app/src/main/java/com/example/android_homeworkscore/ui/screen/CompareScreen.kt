package com.example.android_homeworkscore.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.inference.ScoreResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Composable
fun CompareScreen(predictor: AESPredictor) {
    var inputText by remember { mutableStateOf("") }
    var enResult by remember { mutableStateOf<ScoreResult?>(null) }
    var cnResult by remember { mutableStateOf<ScoreResult?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        OutlinedTextField(
            value = inputText,
            onValueChange = { if (it.length <= 10000) inputText = it },
            modifier = Modifier.fillMaxWidth().height(140.dp),
            placeholder = { Text("输入文本，同时用中英文模型评分对比") },
            shape = RoundedCornerShape(12.dp)
        )

        Spacer(modifier = Modifier.height(12.dp))

        Button(
            onClick = {
                isLoading = true
                scope.launch(Dispatchers.Default) {
                    try {
                        enResult = predictor.predict(inputText, "en")
                    } catch (e: Exception) {
                        enResult = null
                    }
                    // Only attempt Chinese if model is available
                    if (predictor.canScore("zh")) {
                        try {
                            cnResult = predictor.predict(inputText, "zh")
                        } catch (e: Exception) {
                            cnResult = null
                        }
                    }
                    isLoading = false
                }
            },
            modifier = Modifier.fillMaxWidth().height(48.dp),
            enabled = inputText.isNotBlank() && !isLoading
        ) {
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White)
            } else Text("开始对比")
        }

        if (enResult != null && cnResult != null) {
            Spacer(modifier = Modifier.height(20.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                CompareCard("英文模型", enResult!!, Color(0xFF6366F1), Modifier.weight(1f))
                CompareCard("中文模型", cnResult!!, Color(0xFFF59E0B), Modifier.weight(1f))
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
            Text("${(result.total * 100).toInt()}分", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = color)
            Text("内容: ${(result.content * 100).toInt()}", fontSize = 12.sp)
            Text("结构: ${(result.structure * 100).toInt()}", fontSize = 12.sp)
            Text("语言: ${(result.language * 100).toInt()}", fontSize = 12.sp)
        }
    }
}
