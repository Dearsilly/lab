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
