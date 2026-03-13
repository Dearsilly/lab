package com.example.android_homeworkscore

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST

// 适配 Flask /predict 接口的请求参数（参数名必须和Flask一致：essay/essay_set）
data class ScoreRequest(
    val essay: String,       // 对应 Flask 的 essay 参数（必填，文本内容）
    val essay_set: Int = 1   // 对应 Flask 的 essay_set 参数（1-8）
)

// 适配 Flask /predict 接口的返回格式
data class ScoreResponse(
    val predicted_score: Float,  // 预测分数
    val essay_set: Int,          // 作文集编号
    val score_range: List<Int>,  // 分数范围
    val error: String? = null    // 错误信息
)

// Retrofit API 接口定义
interface ScoreApiService {
    @POST("/predict")  // 匹配 Flask 原有接口路径
    suspend fun getHomeworkScore(@Body request: ScoreRequest): ScoreResponse
}

// Retrofit 单例（替换为你的 Flask 服务器 IP）
object ScoreApi {
    private const val BASE_URL = "http://10.151.186.50:5000/"

    val scoreApi: ScoreApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ScoreApiService::class.java)
    }
}