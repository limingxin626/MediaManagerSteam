package com.example.myapplication

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModelProvider
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.service.SyncWorker
import com.example.myapplication.navigation.Routes
import com.example.myapplication.navigation.navigateToMediaFullscreen
import com.example.myapplication.ui.screens.actor.ActorListScreen
import com.example.myapplication.ui.screens.home.HomeScreen
import com.example.myapplication.ui.screens.media.MediaListScreen
import com.example.myapplication.ui.screens.message.MessageListScreen
import com.example.myapplication.ui.screens.message.MessageEditScreen
import com.example.myapplication.ui.screens.tag.TagEditScreen
import com.example.myapplication.ui.screens.tag.TagListScreen
import com.example.myapplication.ui.screens.system.SystemGalleryScreen
import com.example.myapplication.ui.screens.system.SystemMediaDetailScreen
import com.example.myapplication.ui.screens.system.SystemMediaEditScreen
import com.example.myapplication.ui.screens.system.SystemFolderViewScreen
import com.example.myapplication.ui.screens.system.FolderDetailScreen
import com.example.myapplication.ui.components.SystemMediaPickerScreen
import com.example.myapplication.ui.screens.media.MediaViewerScreen
import com.example.myapplication.ui.screens.settings.SettingsScreen
import com.example.myapplication.ui.theme.MyApplicationTheme
import com.example.myapplication.ui.navigation.NavigationAnimations
import com.example.myapplication.ui.viewmodel.ActorViewModel
import com.example.myapplication.ui.viewmodel.HomeViewModel
import com.example.myapplication.ui.viewmodel.MediaViewModel
import com.example.myapplication.ui.viewmodel.MessageViewModel
import com.example.myapplication.ui.viewmodel.SettingsViewModel
import com.example.myapplication.ui.viewmodel.SystemGalleryViewModel
import com.example.myapplication.ui.viewmodel.TagViewModel
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.runBlocking
import java.net.URLDecoder


// 定义 CompositionLocal 来控制底部导航栏的可见性
val LocalBottomBarVisible = compositionLocalOf<MutableState<Boolean>> { error("No BottomBarVisible provided") }


class MainActivity : ComponentActivity() {

    private lateinit var databaseManager: DatabaseManager

    // 使用 viewModels() 委托来管理 ViewModel 生命周期
    private val actorViewModel: ActorViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return ActorViewModel(databaseManager) as T
            }
        }
    }

    private val mediaViewModel: MediaViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return MediaViewModel(databaseManager) as T
            }
        }
    }

    private val tagViewModel: TagViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return TagViewModel(databaseManager) as T
            }
        }
    }

    private val systemGalleryViewModel: SystemGalleryViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return SystemGalleryViewModel(this@MainActivity) as T
            }
        }
    }

    private val messageViewModel: MessageViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return MessageViewModel(databaseManager.messageRepository) as T
            }
        }
    }

    private val homeViewModel: HomeViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return HomeViewModel(databaseManager.tagRepository, databaseManager.messageRepository) as T
            }
        }
    }

    private val settingsViewModel: SettingsViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return SettingsViewModel(databaseManager) as T
            }
        }
    }


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // 初始化数据库
        databaseManager = DatabaseManager.getInstance(this)

        // 调度后台定期同步（15 分钟，WiFi 下执行）
        SyncWorker.schedulePeriodicSync(this)

        // 网络恢复时立即触发同步
        val networkMonitor = databaseManager.networkMonitor
        var wasConnected = networkMonitor.isWifiConnected.value
        lifecycleScope.launch {
            networkMonitor.isWifiConnected.collect { connected ->
                if (connected && !wasConnected) {
                    SyncWorker.scheduleImmediateSync(this@MainActivity)
                }
                wasConnected = connected
            }
        }

        setContent {
            MyApplicationTheme {
                MyApplicationApp(
                    databaseManager,
                    actorViewModel,
                    mediaViewModel,
                    tagViewModel,
                    systemGalleryViewModel,
                    messageViewModel,
                    homeViewModel,
                    settingsViewModel
                )
            }
        }
    }
}

@Composable
fun MyApplicationApp(
    databaseManager: DatabaseManager,
    actorViewModel: ActorViewModel? = null,
    mediaViewModel: MediaViewModel? = null,
    tagViewModel: TagViewModel? = null,
    systemGalleryViewModel: SystemGalleryViewModel? = null,
    messageViewModel: MessageViewModel? = null,
    homeViewModel: HomeViewModel? = null,
    settingsViewModel: SettingsViewModel? = null
) {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    val haptic = LocalHapticFeedback.current

    // 控制底部导航栏的可见性状态（保留供子页面使用）
    val bottomBarVisible = remember { mutableStateOf(true) }

    // 判断当前路由是否在底部导航栏中
    val showBottomBar = currentRoute in listOf(
        Routes.HOME,
        Routes.ACTOR_LIST,
        Routes.MEDIA_LIST,
        Routes.SETTINGS
    )

    CompositionLocalProvider(LocalBottomBarVisible provides bottomBarVisible) {
        Scaffold(
            modifier = Modifier.fillMaxSize(),
            contentWindowInsets = WindowInsets(0),
            bottomBar = {
                if (showBottomBar) {
                    NavigationBar(
                        modifier = Modifier.height(60.dp),
                        windowInsets = WindowInsets(0)
                    ) {
                        AppDestinations.entries.forEach { destination ->
                            val selected = currentRoute == destination.route
                            val color = if (selected) MaterialTheme.colorScheme.primary
                                else MaterialTheme.colorScheme.onSurfaceVariant
                            NavigationBarItem(
                                icon = {
                                    Icon(
                                        destination.icon,
                                        contentDescription = destination.label,
                                        modifier = Modifier.size(20.dp),
                                        tint = color
                                    )
                                },
                                label = {
                                    Text(
                                        destination.label,
                                        style = MaterialTheme.typography.labelSmall,
                                        color = color
                                    )
                                },
                                selected = selected,
                                onClick = {
                                    haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                                    navController.navigate(destination.route) {
                                        popUpTo(Routes.HOME) {
                                            saveState = true
                                        }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                },
                                alwaysShowLabel = true
                            )
                        }
                    }
                }
            }
        ) { innerPadding ->
            AppNavHost(
                navController = navController,
                databaseManager = databaseManager,
                actorViewModel = actorViewModel,
                mediaViewModel = mediaViewModel,
                tagViewModel = tagViewModel,
                systemGalleryViewModel = systemGalleryViewModel,
                messageViewModel = messageViewModel,
                homeViewModel = homeViewModel,
                settingsViewModel = settingsViewModel,
                modifier = Modifier.padding(innerPadding)
            )
        }
    }
}



@Composable
fun AppNavHost(
    navController: NavHostController,
    databaseManager: DatabaseManager,
    actorViewModel: ActorViewModel?,
    mediaViewModel: MediaViewModel?,
    tagViewModel: TagViewModel?,
    systemGalleryViewModel: SystemGalleryViewModel?,
    messageViewModel: MessageViewModel?,
    homeViewModel: HomeViewModel?,
    settingsViewModel: SettingsViewModel?,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Routes.HOME,
        modifier = modifier,
        enterTransition = { EnterTransition.None },
        exitTransition = { ExitTransition.None },
        popEnterTransition = { EnterTransition.None },
        popExitTransition = { ExitTransition.None }
    ) {
        // 主页 - 无动画
        composable(
            Routes.HOME,
            enterTransition = { NavigationAnimations.noAnimation() },
            exitTransition = { NavigationAnimations.noExitAnimation() },
            popEnterTransition = { NavigationAnimations.noAnimation() },
            popExitTransition = { NavigationAnimations.noExitAnimation() }
        ) {
            HomeScreen(
                homeViewModel = homeViewModel!!,
                onNavigateToMessages = { tagId ->
                    navController.navigate(Routes.messageList(tagId))
                }
            )
        }

        // 演员列表 - 无动画（底部导航标签页）
        composable(
            Routes.ACTOR_LIST,
            enterTransition = { NavigationAnimations.noAnimation() },
            exitTransition = { NavigationAnimations.noExitAnimation() },
            popEnterTransition = { NavigationAnimations.noAnimation() },
            popExitTransition = { NavigationAnimations.noExitAnimation() }
        ) {
            ActorListScreen(
                viewModel = actorViewModel!!,
                onNavigateToMessages = { actorId ->
                    if (actorId == null) navController.navigate(Routes.messageList(null))
                    else navController.navigate(Routes.messageListByActor(actorId))
                }
            )
        }



        // 媒体列表 - 无动画
        composable(
            Routes.MEDIA_LIST,
            enterTransition = { EnterTransition.None },
            exitTransition = { ExitTransition.None },
            popEnterTransition = { EnterTransition.None },
            popExitTransition = { ExitTransition.None }
        ) {
            MediaListScreen(
                viewModel = mediaViewModel!!,
                databaseManager = databaseManager,
                onMediaClick = { media, _ ->
                    navController.navigateToMediaFullscreen(media.id)
                }
            )
        }

        // 消息列表 - 从右侧滑入
        composable(
            Routes.MESSAGE_LIST,
            arguments = listOf(
                navArgument("tagId") {
                    type = NavType.LongType
                    defaultValue = -1L
                }
            ),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { EnterTransition.None },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val tagId = backStackEntry.arguments?.getLong("tagId") ?: -1L
            val effectiveTagId = if (tagId == -1L) null else tagId

            LaunchedEffect(effectiveTagId) {
                messageViewModel!!.setTagId(effectiveTagId)
            }

            DisposableEffect(Unit) {
                onDispose {
                    messageViewModel!!.setTagId(null)
                }
            }

            MessageListScreen(
                viewModel = messageViewModel!!,
                databaseManager = databaseManager,
                onMessageClick = { messageId ->
                    navController.navigate(Routes.messageDetail(messageId))
                },
                onEditMessage = { messageId ->
                    navController.navigate(Routes.messageEdit(messageId))
                },
                onMediaClick = { mediaId, messageId, mediaList ->
                    navController.navigateToMediaFullscreen(mediaId, mediaList, messageId)
                }
            )
        }

        // 按演员过滤的消息列表 - 从右侧滑入
        composable(
            Routes.MESSAGE_LIST_BY_ACTOR,
            arguments = listOf(
                navArgument("actorId") {
                    type = NavType.LongType
                    defaultValue = -1L
                }
            ),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { EnterTransition.None },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val actorId = backStackEntry.arguments?.getLong("actorId") ?: -1L
            val effectiveActorId = if (actorId == -1L) null else actorId

            LaunchedEffect(effectiveActorId) {
                messageViewModel!!.setActorId(effectiveActorId)
            }

            DisposableEffect(Unit) {
                onDispose {
                    messageViewModel!!.setActorId(null)
                }
            }

            MessageListScreen(
                viewModel = messageViewModel!!,
                databaseManager = databaseManager,
                onMessageClick = { messageId ->
                    navController.navigate(Routes.messageDetail(messageId))
                },
                onEditMessage = { messageId ->
                    navController.navigate(Routes.messageEdit(messageId))
                },
                onMediaClick = { mediaId, messageId, mediaList ->
                    navController.navigateToMediaFullscreen(mediaId, mediaList, messageId)
                }
            )
        }



        // 消息编辑 - 从右侧滑入
        composable(
            route = Routes.MESSAGE_EDIT,
            arguments = listOf(navArgument("messageId") { type = NavType.LongType }),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val messageId = backStackEntry.arguments?.getLong("messageId") ?: return@composable
            MessageEditScreen(
                messageId = messageId,
                databaseManager = databaseManager,
                navController = navController
            )
        }

        // 全屏媒体查看器（图片/视频）- 右侧滑入/滑出，避免 fadeOut 时原生 PlayerView 残留
        composable(
            route = Routes.MEDIA_FULLSCREEN,
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() },
            arguments = listOf(
                navArgument("mediaId") { type = NavType.LongType },
                navArgument("mediaIdListJson") {
                    type = NavType.StringType
                    nullable = true
                    defaultValue = null
                },
                navArgument("messageId") {
                    type = NavType.LongType
                    defaultValue = -1L
                }
            )
        ) { backStackEntry ->
            val mediaId = backStackEntry.arguments?.getLong("mediaId") ?: return@composable
            val mediaIdListJson = backStackEntry.arguments?.getString("mediaIdListJson")
            val messageId = backStackEntry.arguments?.getLong("messageId") ?: -1L
            val mediaIdList = remember(mediaIdListJson) {
                if (mediaIdListJson != null) {
                    try {
                        val decoded = URLDecoder.decode(mediaIdListJson, "UTF-8")
                        Gson().fromJson<List<Long>>(
                            decoded,
                            object : TypeToken<List<Long>>() {}.type
                        ) ?: emptyList()
                    } catch (_: Exception) {
                        emptyList<Long>()
                    }
                } else {
                    emptyList<Long>()
                }
            }
            MediaViewerScreen(
                initialMediaId = mediaId,
                messageId = messageId,
                mediaIdList = mediaIdList,
                databaseManager = databaseManager,
                navController = navController
            )
        }

        // 系统相册 - 无动画
        composable(
            Routes.SYSTEM_GALLERY,
            enterTransition = { NavigationAnimations.noAnimation() },
            exitTransition = { NavigationAnimations.noExitAnimation() },
            popEnterTransition = { NavigationAnimations.noAnimation() },
            popExitTransition = { NavigationAnimations.noExitAnimation() }
        ) {
            SystemGalleryScreen(
                navController = navController,
                viewModel = systemGalleryViewModel!!
            )
        }

        // 系统媒体详情 - 滑入滑出动画
        composable(
            "system_media_detail/{mediaId}",
            arguments = listOf(navArgument("mediaId") { type = NavType.LongType }),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val mediaId = backStackEntry.arguments?.getLong("mediaId") ?: 0L
            SystemMediaDetailScreen(
                mediaId = mediaId,
                navController = navController,
                viewModel = systemGalleryViewModel!!
            )
        }

        // 系统媒体编辑 - 滑入滑出动画
        composable(
            "system_media_edit/{mediaId}",
            arguments = listOf(navArgument("mediaId") { type = NavType.LongType }),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val mediaId = backStackEntry.arguments?.getLong("mediaId") ?: 0L
            SystemMediaEditScreen(
                mediaId = mediaId,
                navController = navController,
                systemGalleryViewModel = systemGalleryViewModel!!,
                mediaViewModel = mediaViewModel!!
            )
        }

        // 系统文件夹视图 - 无动画
        composable(
            Routes.SYSTEM_FOLDER_VIEW,
            enterTransition = { NavigationAnimations.noAnimation() },
            exitTransition = { NavigationAnimations.noExitAnimation() },
            popEnterTransition = { NavigationAnimations.noAnimation() },
            popExitTransition = { NavigationAnimations.noExitAnimation() }
        ) {
            SystemFolderViewScreen(
                navController = navController,
                viewModel = systemGalleryViewModel!!
            )
        }

        // 文件夹详情 - 滑入滑出动画
        composable(
            Routes.FOLDER_DETAIL,
            arguments = listOf(navArgument("folderName") { type = NavType.StringType }),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val folderName = backStackEntry.arguments?.getString("folderName") ?: return@composable
            val decodedFolderName = java.net.URLDecoder.decode(folderName, "UTF-8")
            FolderDetailScreen(
                folderName = decodedFolderName,
                navController = navController,
                viewModel = systemGalleryViewModel!!
            )
        }

        // 系统媒体选择器 - 滑入滑出动画
        composable(
            Routes.SYSTEM_MEDIA_PICKER,
            arguments = listOf(navArgument("groupId") { type = NavType.LongType }),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val groupId = backStackEntry.arguments?.getLong("groupId") ?: return@composable
            //todo
        }

        // 标签列表 - 无动画
        composable(
            Routes.TAG_LIST,
            enterTransition = { NavigationAnimations.noAnimation() },
            exitTransition = { NavigationAnimations.noExitAnimation() },
            popEnterTransition = { NavigationAnimations.noAnimation() },
            popExitTransition = { NavigationAnimations.noExitAnimation() }
        ) {
            TagListScreen(
                viewModel = tagViewModel!!,
                onAddTag = {
                    navController.navigate(Routes.TAG_ADD)
                },
                onTagClick = { tag ->
                    navController.navigate(Routes.tagEdit(tag.id))
                }
            )
        }

        // 标签添加 - 从右侧滑入
        composable(
            Routes.TAG_ADD,
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) {
            TagEditScreen(
                tagId = null,
                databaseManager = databaseManager,
                navController = navController
            )
        }

        // 标签编辑 - 从右侧滑入
        composable(
            route = Routes.TAG_EDIT,
            arguments = listOf(navArgument("tagId") { type = NavType.LongType }),
            enterTransition = { NavigationAnimations.slideInFromRight() },
            exitTransition = { NavigationAnimations.slideOutToLeft() },
            popEnterTransition = { NavigationAnimations.slideInFromLeft() },
            popExitTransition = { NavigationAnimations.slideOutToRight() }
        ) { backStackEntry ->
            val tagId = backStackEntry.arguments?.getLong("tagId") ?: return@composable
            TagEditScreen(
                tagId = tagId,
                databaseManager = databaseManager,
                navController = navController
            )
        }

        // 设置页面 - 无动画（底部导航标签页）
        composable(
            Routes.SETTINGS,
            enterTransition = { NavigationAnimations.noAnimation() },
            exitTransition = { NavigationAnimations.noExitAnimation() },
            popEnterTransition = { NavigationAnimations.noAnimation() },
            popExitTransition = { NavigationAnimations.noExitAnimation() }
        ) {
            SettingsScreen(viewModel = settingsViewModel!!)
        }
    }
}

enum class AppDestinations(
    val label: String,
    val icon: ImageVector,
    val route: String
) {
    HOME("主页", Icons.Default.Home, Routes.HOME),
    ACTORS("演员", Icons.Default.Person, Routes.ACTOR_LIST),
    MEDIA("媒体", Icons.Default.PlayArrow, Routes.MEDIA_LIST),
    SETTINGS("设置", Icons.Default.Settings, Routes.SETTINGS),
}


@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    MyApplicationTheme {
        Greeting("Android")
    }
}