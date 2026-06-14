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
        val inputTensor = Tensor.fromBlob(inputIds, longArrayOf(1, 512))
        val output = model.forward(org.pytorch.IValue.from(inputTensor)).toTensor()
        val totalScore = output.dataAsFloatArray[0]

        val content = (totalScore * 0.95f).coerceIn(0f, 1f)
        val structure = (totalScore * 1.02f).coerceIn(0f, 1f)
        val lang = (totalScore * 1.03f).coerceIn(0f, 1f)

        val scores = mapOf(
            "total" to totalScore.toDouble(),
            "content" to content.toDouble(),
            "structure" to structure.toDouble(),
            "language" to lang.toDouble()
        )
        val feedback = generateFeedback(scores, detectedLang)
        val elapsed = System.currentTimeMillis() - start

        return ScoreResult(
            total = totalScore,
            content = content,
            structure = structure,
            language = lang,
            feedback = feedback,
            detectedLanguage = detectedLang,
            elapsedMs = elapsed
        )
    }

    private fun generateFeedback(scores: Map<String, Double>, language: String): Map<String, String> {
        val total = scores["total"] ?: 0.5
        val level = when {
            total >= 0.7 -> "high"
            total >= 0.4 -> "mid"
            else -> "low"
        }

        val templates = mapOf(
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

        val overallTemplates = mapOf(
            "high" to "总分表现优秀（%.1f分），文章在内容、结构和语言方面均表现良好。",
            "mid" to "总分中等（%.1f分），文章有一定基础，建议针对反馈意见进行修改提升。",
            "low" to "总分偏低（%.1f分），需要在内容深度、文章结构和语言表达方面进行系统提升。"
        )

        return mapOf(
            "content" to (templates["content"]?.get(level) ?: ""),
            "structure" to (templates["structure"]?.get(level) ?: ""),
            "language" to (templates["language"]?.get(level) ?: ""),
            "overall" to String.format(overallTemplates[level] ?: "", total * 100)
        )
    }
}
