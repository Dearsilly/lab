package com.example.android_homeworkscore.ui.screen

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.android_homeworkscore.ScoreApi
import com.example.android_homeworkscore.ScoreRequest
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

// 核心 UI 页面组件
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeworkScoreScreen() {
    // 状态管理
    var inputText by remember { mutableStateOf("") }
    var scoreResult by remember { mutableStateOf("") }
    var feedbackResult by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }

    // ===== 新增：Set集选择状态 =====
    var selectedSet by remember { mutableStateOf(1) } // 默认选中1
    var expanded by remember { mutableStateOf(false) } // 下拉框展开状态
    val setOptions = listOf(1,2,3,4,5,6,7,8) // Set集选项

    val context = LocalContext.current
    val scrollState = rememberScrollState()

    // 页面整体布局
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "作业自动评分系统",
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF6200EE),
                    titleContentColor = Color.White
                )
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 16.dp, vertical = 20.dp)
                .verticalScroll(scrollState),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Top
        ) {

            // ===== 新增：Set集下拉选择框 =====
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 16.dp),
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, Color.Gray.copy(alpha = 0.2f)),
                elevation = CardDefaults.cardElevation(4.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "选择作文集（Set）",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Medium,
                        color = Color.Black,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                    // 下拉选择框
                    Box(modifier = Modifier.fillMaxWidth()) {
                        Button(
                            onClick = { expanded = true },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(8.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color.White,
                                contentColor = Color.Black
                            ),
                            border = BorderStroke(1.dp, Color.Gray.copy(alpha = 0.5f))
                        ) {
                            Text(text = "当前选择：Set $selectedSet", fontSize = 14.sp)
                            Spacer(modifier = Modifier.weight(1f))
                            Icon(Icons.Default.ArrowDropDown, contentDescription = "展开下拉框")
                        }
                        // 下拉选项列表
                        DropdownMenu(
                            expanded = expanded,
                            onDismissRequest = { expanded = false },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            setOptions.forEach { set ->
                                DropdownMenuItem(
                                    text = { Text(text = "Set $set", fontSize = 14.sp) },
                                    onClick = {
                                        selectedSet = set
                                        expanded = false
                                    },
                                    modifier = Modifier.fillMaxWidth()
                                )
                            }
                        }
                    }
                }
            }

            // 作业文本输入卡片
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 20.dp),
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, Color.Gray.copy(alpha = 0.2f)),
                elevation = CardDefaults.cardElevation(4.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "请输入作业内容",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Medium,
                        color = Color.Black,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )
                    // 多行输入框
                    OutlinedTextField(
                        value = inputText,
                        onValueChange = { inputText = it },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp),
                        placeholder = {
                            Text(
                                text = "在这里输入你的作业文本...",
                                color = Color.Gray.copy(alpha = 0.6f)
                            )
                        },
                        maxLines = Int.MAX_VALUE,
                        singleLine = false,
                        shape = RoundedCornerShape(8.dp),
                        label = { Text("作业文本") }
                    )
                }
            }

            // 提交评分按钮
            Button(
                onClick = {
                    // 空输入校验
                    if (inputText.isBlank()) {
                        scoreResult = "⚠️ 请输入作业文本后再提交！"
                        feedbackResult = ""
                        return@Button
                    }
                    isLoading = true

                    // 协程发起网络请求（子线程）
                    CoroutineScope(Dispatchers.IO).launch {
                        try {
                            // ===== 关键：传递选中的set值 =====
                            val response = ScoreApi.scoreApi.getHomeworkScore(
                                ScoreRequest(essay = inputText, essay_set = selectedSet)
                            )
                            // 切回主线程更新 UI
                            withContext(Dispatchers.Main) {
                                isLoading = false
                                if (response.error.isNullOrEmpty()) {
                                    // 接口调用成功
                                    scoreResult = "✅ 本次得分：${response.predicted_score} 分"
                                    feedbackResult = "作文集：Set ${response.essay_set} | 分数范围：${response.score_range[0]}-${response.score_range[1]}"
                                } else {
                                    // 接口返回业务错误
                                    scoreResult = "❌ 评分失败"
                                    feedbackResult = response.error ?: "未知错误"
                                }
                            }
                        } catch (e: Exception) {
                            // 网络/解析异常
                            withContext(Dispatchers.Main) {
                                isLoading = false
                                scoreResult = "❌ 网络请求失败"
                                feedbackResult = """请检查：
1. Flask 服务是否正常运行
2. 手机与电脑在同一局域网
3. IP 地址是否正确（当前：10.151.186.50）
4. 防火墙是否拦截 5000 端口
错误详情：${e.message}"""
                            }
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(12.dp),
                enabled = !isLoading,
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF6200EE),
                    disabledContainerColor = Color(0xFF6200EE).copy(alpha = 0.6f)
                )
            ) {
                if (isLoading) {
                    // 加载中状态
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = Color.White,
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(text = "评分中...", fontSize = 16.sp)
                } else {
                    // 正常状态
                    Icon(Icons.Default.Send, contentDescription = "提交", tint = Color.White)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(text = "提交评分", fontSize = 16.sp, fontWeight = FontWeight.Medium)
                }
            }

            // 评分结果展示区
            if (scoreResult.isNotBlank()) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 30.dp),
                    shape = RoundedCornerShape(12.dp),
                    elevation = CardDefaults.cardElevation(4.dp)
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text(
                            text = scoreResult,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = when {
                                scoreResult.startsWith("✅") -> Color(0xFF2E7D32) // 成功绿
                                scoreResult.startsWith("❌") -> Color(0xFFD32F2F) // 失败红
                                scoreResult.startsWith("⚠️") -> Color(0xFFFF8F00) // 警告橙
                                else -> Color.Black
                            },
                            modifier = Modifier.padding(bottom = 12.dp)
                        )
                        if (feedbackResult.isNotBlank()) {
                            Text(
                                text = feedbackResult,
                                fontSize = 15.sp,
                                color = Color.Black.copy(alpha = 0.8f),
                                lineHeight = 22.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }
            }

            // 底部留白
            Spacer(modifier = Modifier.height(50.dp))
        }
    }
}

// 预览函数
@Preview(showBackground = true, device = "spec:width=412dp,height=915dp")
@Composable
fun HomeworkScoreScreenPreview() {
    MaterialTheme {
        HomeworkScoreScreen()
    }
}