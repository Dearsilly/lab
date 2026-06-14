package com.example.android_homeworkscore.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.sp
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.android_homeworkscore.inference.AESPredictor
import com.example.android_homeworkscore.ui.screen.*

sealed class Screen(val route: String, val label: String) {
    object Score : Screen("score", "评分")
    object Batch : Screen("batch", "批量")
    object Compare : Screen("compare", "对比")
    object Settings : Screen("settings", "设置")
}

@Composable
fun AppNavigation(predictor: AESPredictor) {
    val navController = rememberNavController()
    val screens = listOf(Screen.Score, Screen.Batch, Screen.Compare, Screen.Settings)

    Scaffold(
        bottomBar = {
            NavigationBar {
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentRoute = navBackStackEntry?.destination?.route

                screens.forEach { screen ->
                    NavigationBarItem(
                        icon = {
                            Text(
                                when (screen) {
                                    Screen.Score -> "📝"
                                    Screen.Batch -> "📊"
                                    Screen.Compare -> "🔄"
                                    Screen.Settings -> "⚙️"
                                },
                                fontSize = 20.sp
                            )
                        },
                        label = { Text(screen.label) },
                        selected = currentRoute == screen.route,
                        onClick = {
                            if (currentRoute != screen.route) {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.startDestinationId) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Score.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Score.route) { ScoreScreen(predictor) }
            composable(Screen.Batch.route) { BatchScreen(predictor) }
            composable(Screen.Compare.route) { CompareScreen(predictor) }
            composable(Screen.Settings.route) { SettingsScreen(predictor) }
        }
    }
}
