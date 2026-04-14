package com.example.myapplication.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.example.myapplication.data.database.entities.Actor
import com.example.myapplication.ui.theme.InstagramGradientEnd
import com.example.myapplication.ui.theme.InstagramGradientMiddle
import com.example.myapplication.ui.theme.InstagramGradientStart
import java.io.File

/**
 * Instagram 风格演员卡片组件 - 横向布局
 * 类似 Instagram 的用户列表项设计
 */
@Composable
fun ActorCard(
    actor: Actor, onClick: () -> Unit, modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    // 缓存计算结果
    val displayName = remember(actor.name) { actor.name }

    // Instagram 渐变色
    val instagramGradient = Brush.linearGradient(
        colors = listOf(
            InstagramGradientStart, InstagramGradientMiddle, InstagramGradientEnd
        )
    )

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // 圆形头像 with Instagram 渐变边框
            Box(
                modifier = Modifier.size(64.dp), contentAlignment = Alignment.Center
            ) {
                // 渐变边框背景
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(instagramGradient, CircleShape)
                        .padding(3.dp)
                ) {
                    // 白色间隔
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(MaterialTheme.colorScheme.surface, CircleShape)
                            .padding(2.dp), contentAlignment = Alignment.Center
                    ) {
                        // 头像内容
                        if (!actor.avatarPath.isNullOrBlank() && File(actor.avatarPath).exists()) {
                            AsyncImage(
                                model = ImageRequest.Builder(context).data(File(actor.avatarPath))
                                    .crossfade(true).build(),
                                contentDescription = "演员头像",
                                modifier = Modifier
                                    .fillMaxSize()
                                    .clip(CircleShape),
                                contentScale = ContentScale.Crop
                            )
                        } else {
                            // 占位头像
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(
                                        MaterialTheme.colorScheme.surfaceVariant, CircleShape
                                    ), contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    Icons.Default.Person,
                                    contentDescription = "默认头像",
                                    modifier = Modifier.size(32.dp),
                                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }

            // 演员信息
            Column(
                modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                // 演员姓名 - 加粗
                Text(
                    text = displayName,
                    style = MaterialTheme.typography.bodyLarge.copy(
                        fontWeight = FontWeight.SemiBold, fontSize = 15.sp
                    ),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
        }
    }
}

