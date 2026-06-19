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
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("模型状态", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(12.dp))

        ModelStatusCard("英文模型 (BERT-base-uncased)", predictor.isEnLoaded(), predictor.getEnError())
        Spacer(modifier = Modifier.height(8.dp))
        ModelStatusCard("中文模型 (BERT-base-chinese)", predictor.isCnLoaded(), predictor.getCnError())

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
            Text("重新加载模型")
        }
    }
}

@Composable
fun ModelStatusCard(name: String, loaded: Boolean, error: String? = null) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = if (loaded) Color(0xFFF0FDF4) else Color(0xFFFEF2F2)
        )
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(name, style = MaterialTheme.typography.bodyMedium)
                Text(
                    if (loaded) "已加载" else "未加载",
                    color = if (loaded) Color(0xFF16A34A) else Color(0xFFDC2626),
                    fontWeight = FontWeight.Medium
                )
            }
            if (!loaded && error != null) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "错误: $error",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF991B1B),
                    maxLines = 4
                )
            }
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
