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
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

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

        // Draw grid (3 levels)
        for (level in 1..3) {
            val r = radius * level / 3
            val path = Path()
            for (i in 0 until n) {
                val angle = -PI / 2 + 2 * PI * i / n
                val x = centerX + r * cos(angle).toFloat()
                val y = centerY + r * sin(angle).toFloat()
                if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
            }
            path.close()
            drawPath(path, Color(0xFFE5E7EB), style = Stroke(1.dp.toPx()))
        }

        // Draw axes
        for (i in 0 until n) {
            val angle = -PI / 2 + 2 * PI * i / n
            val x = centerX + radius * cos(angle).toFloat()
            val y = centerY + radius * sin(angle).toFloat()
            drawLine(Color(0xFFE5E7EB), Offset(centerX, centerY), Offset(x, y), 1.dp.toPx())
        }

        // Draw data area
        val dataPath = Path()
        for (i in 0 until n) {
            val angle = -PI / 2 + 2 * PI * i / n
            val v = values[i].coerceIn(0f, 1f)
            val x = centerX + radius * v * cos(angle).toFloat()
            val y = centerY + radius * v * sin(angle).toFloat()
            if (i == 0) dataPath.moveTo(x, y) else dataPath.lineTo(x, y)
        }
        dataPath.close()
        drawPath(dataPath, color.copy(alpha = 0.3f))
        drawPath(dataPath, color, style = Stroke(2.dp.toPx()))

        // Draw data points
        for (i in 0 until n) {
            val angle = -PI / 2 + 2 * PI * i / n
            val v = values[i].coerceIn(0f, 1f)
            val x = centerX + radius * v * cos(angle).toFloat()
            val y = centerY + radius * v * sin(angle).toFloat()
            drawCircle(color, 4.dp.toPx(), Offset(x, y))
        }

        // Labels
        val paint = android.graphics.Paint().apply {
            textAlign = android.graphics.Paint.Align.CENTER
            textSize = 12.dp.toPx()
            this.color = 0xFF6B7280.toInt()
        }
        for (i in 0 until n) {
            val angle = -PI / 2 + 2 * PI * i / n
            val labelR = radius + 24.dp.toPx()
            val x = centerX + labelR * cos(angle).toFloat()
            val y = centerY + labelR * sin(angle).toFloat() + 5.dp.toPx()
            drawContext.canvas.nativeCanvas.drawText(labels[i], x, y, paint)
        }
    }
}
