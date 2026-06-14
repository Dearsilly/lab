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
                    .padding(12.dp)
            ) {
                Text(it, fontSize = 14.sp, color = Color(0xFF374151))
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            val colors = listOf(Color(0xFF10B981), Color(0xFF6366F1), Color(0xFFF59E0B))
            val labels = listOf("内容", "结构", "语言")
            val dims = listOf("content", "structure", "language")

            dims.forEachIndexed { index, dim ->
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
