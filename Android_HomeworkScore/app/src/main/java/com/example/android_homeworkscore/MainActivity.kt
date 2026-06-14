package com.example.android_homeworkscore

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.ui.navigation.AppNavigation

class MainActivity : ComponentActivity() {

    private lateinit var predictor: AESPredictor

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        predictor = AESPredictor(applicationContext)
        Thread { predictor.loadModels() }.start()

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AppNavigation(predictor)
                }
            }
        }
    }
}
