package com.example.android_homeworkscore.ui.screen

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
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
import kotlinx.coroutines.launch
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
    val scope = rememberCoroutineScope()

    val filePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            selectedFileName = it.lastPathSegment ?: "unknown.csv"
            items = readCsvFromUri(context, it)
            results = emptyList()
        }
    }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        OutlinedCard(
            onClick = { filePicker.launch("text/*") },
            modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(
                modifier = Modifier.padding(24.dp).fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text("点击选择 CSV 文件", style = MaterialTheme.typography.bodyMedium)
                Text("列: essay_id, text, language", style = MaterialTheme.typography.labelSmall, color = Color.Gray)
            }
        }

        if (selectedFileName != null) {
            Text("已选择: $selectedFileName (${items.size} 篇)", style = MaterialTheme.typography.titleSmall)
            Spacer(modifier = Modifier.height(8.dp))
        }

        if (items.isNotEmpty()) {
            Button(
                onClick = {
                    isProcessing = true
                    progress = 0
                    scope.launch(Dispatchers.Default) {
                        val newResults = mutableListOf<BatchResult>()
                        items.forEachIndexed { index, item ->
                            try {
                                val res = predictor.predict(item.text, item.language)
                                newResults.add(BatchResult(item.id, "${(res.total * 100).toInt()}分", "OK"))
                            } catch (e: Exception) {
                                newResults.add(BatchResult(item.id, "失败", e.message ?: "error"))
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
                Text(if (isProcessing) "评分中..." else "开始批量评分")
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
