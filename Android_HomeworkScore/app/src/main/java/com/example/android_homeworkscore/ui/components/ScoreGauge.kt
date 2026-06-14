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

        // Gradient progress bar
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

        // Dimension cards
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
