plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.android_homeworkscore"
    compileSdk {
        version = release(36) {
            minorApiLevel = 1
        }
    }

    defaultConfig {
        applicationId = "com.example.android_homeworkscore"
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    buildFeatures {
        compose = true
    }
}

dependencies {
    // ===================== 核心 Android 依赖 =====================
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)

    // ===================== Compose 核心依赖（统一BOM版本） =====================
    implementation(platform(libs.androidx.compose.bom)) // 项目原有统一版本管理
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)

    // ===================== 网络/数据解析依赖 =====================
    implementation("com.squareup.retrofit2:retrofit:2.9.0") // Retrofit网络请求
    implementation("com.squareup.retrofit2:converter-gson:2.9.0") // Retrofit Gson解析器
    implementation("com.squareup.okhttp3:okhttp:4.12.0") // OkHttp底层客户端（Retrofit依赖）
    implementation("com.google.code.gson:gson:2.10.1") // Gson JSON解析

    // ===================== 协程依赖（异步请求） =====================
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // ===================== 单元测试依赖 =====================
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)

    // ===================== Compose 测试依赖 =====================
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)

    // ===================== 调试依赖（仅Debug环境） =====================
    debugImplementation(libs.androidx.compose.ui.tooling)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
}