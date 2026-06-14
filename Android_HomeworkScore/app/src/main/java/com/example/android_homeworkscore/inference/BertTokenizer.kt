package com.example.android_homeworkscore.inference

import android.content.Context
import java.io.BufferedReader
import java.io.InputStreamReader

class BertTokenizer(private val context: Context, vocabAsset: String = "vocab.txt") {

    private val vocab: MutableMap<String, Int> = mutableMapOf()
    private val idToToken: MutableMap<Int, String> = mutableMapOf()

    val clsTokenId: Int get() = vocab["[CLS]"] ?: 101
    val sepTokenId: Int get() = vocab["[SEP]"] ?: 102
    val padTokenId: Int get() = vocab["[PAD]"] ?: 0
    val unkTokenId: Int get() = vocab["[UNK]"] ?: 100

    init {
        loadVocab(vocabAsset)
    }

    private fun loadVocab(assetName: String) {
        context.assets.open(assetName).use { stream ->
            BufferedReader(InputStreamReader(stream)).useLines { lines ->
                lines.forEachIndexed { index, token ->
                    val clean = token.trim()
                    vocab[clean] = index
                    idToToken[index] = clean
                }
            }
        }
    }

    fun tokenize(text: String, maxLength: Int = 512): LongArray {
        val tokens = mutableListOf<Int>()
        tokens.add(clsTokenId)

        val words = basicTokenize(text.lowercase())
        for (word in words) {
            if (word.isEmpty()) continue
            val subTokens = wordPieceTokenize(word)
            tokens.addAll(subTokens)
            if (tokens.size >= maxLength - 1) break
        }

        tokens.add(sepTokenId)

        val result = LongArray(maxLength) { padTokenId.toLong() }
        val attentionMask = IntArray(maxLength) { 0 }
        for (i in tokens.indices) {
            if (i >= maxLength) break
            result[i] = tokens[i].toLong()
        }
        return result
    }

    fun basicTokenize(text: String): List<String> {
        val result = mutableListOf<String>()
        val sb = StringBuilder()

        for (ch in text) {
            when {
                ch == ' ' || ch == '\t' || ch == '\n' || ch == '\r' -> {
                    if (sb.isNotEmpty()) { result.add(sb.toString()); sb.clear() }
                }
                ch in '一'..'鿿' || ch in '㐀'..'䶿' -> {
                    // Chinese character: treat as separate token
                    if (sb.isNotEmpty()) { result.add(sb.toString()); sb.clear() }
                    result.add(ch.toString())
                }
                ch.isLetterOrDigit() -> sb.append(ch)
                else -> {
                    if (sb.isNotEmpty()) { result.add(sb.toString()); sb.clear() }
                    if (!ch.isWhitespace()) result.add(ch.toString())
                }
            }
        }
        if (sb.isNotEmpty()) result.add(sb.toString())
        return result
    }

    private fun wordPieceTokenize(word: String): List<Int> {
        val tokens = mutableListOf<Int>()
        var remaining = word
        var isFirst = true

        while (remaining.isNotEmpty()) {
            val prefix = if (isFirst) "" else "##"
            var found = false

            for (end in remaining.length downTo 1) {
                val candidate = prefix + remaining.substring(0, end)
                val id = vocab[candidate]
                if (id != null) {
                    tokens.add(id)
                    remaining = remaining.substring(end)
                    found = true
                    break
                }
            }

            if (!found) {
                tokens.add(unkTokenId)
                break
            }
            isFirst = false
        }
        return tokens
    }
}
