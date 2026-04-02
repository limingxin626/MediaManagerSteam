# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# Keep line number information for debugging stack traces.
-keepattributes SourceFile,LineNumberTable

# Keep source file name
-renamesourcefileattribute SourceFile

# Keep all Room entities and DAOs
-keep class com.example.myapplication.data.database.entities.** { *; }
-keep class com.example.myapplication.data.database.dao.** { *; }

# Keep all ViewModel classes
-keep class com.example.myapplication.ui.viewmodel.** { *; }

# Keep Gson and related classes
-keepattributes Signature
-keepattributes *Annotation*
-keepattributes EnclosingMethod
-keepattributes InnerClasses

-keep class com.google.gson.** { *; }
-keep class com.google.gson.reflect.TypeToken { *; }
-keep class * extends com.google.gson.reflect.TypeToken { *; }
-keep public class * implements java.lang.reflect.Type

# Retrofit rules
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response
-keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations

# Keep Retrofit service interfaces
-keep interface com.example.myapplication.data.service.SyncService { *; }
-keep class com.example.myapplication.data.service.SyncConfig { *; }

# Keep all sync/remote data models for JSON serialization
-keep class com.example.myapplication.data.model.** { *; }
-keepclassmembers class com.example.myapplication.data.model.** { *; }

# Keep Media entity for JSON serialization
-keep class com.example.myapplication.data.database.entities.Media { *; }
-keepclassmembers class com.example.myapplication.data.database.entities.Media { *; }

# Keep MediaType and other enums with their values
-keepclassmembers enum com.example.myapplication.data.model.RemoteMediaType {
    <fields>;
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep SyncResult sealed class
-keep class com.example.myapplication.data.repository.SyncResult { *; }
-keep class com.example.myapplication.data.repository.SyncResult$* { *; }

# Keep Enum classes (important for your filter functionality)
-keep enum com.example.myapplication.data.database.entities.** { *; }

# Room specific rules
-keep class * extends androidx.room.RoomDatabase
-keep @androidx.room.Entity class *
-keep @androidx.room.Dao class *

# Compose specific rules
-keep class androidx.compose.** { *; }
-dontwarn androidx.compose.**

# Coil specific rules (for image loading)
-keep class coil.** { *; }
-dontwarn coil.**

# ExoPlayer specific rules (for video playback)
-keep class com.google.android.exoplayer2.** { *; }
-keep class androidx.media3.** { *; }
-dontwarn com.google.android.exoplayer2.**
-dontwarn androidx.media3.**

# Keep Kotlin Coroutines
-keep class kotlinx.coroutines.** { *; }
-dontwarn kotlinx.coroutines.**

# Keep main activity
-keep class com.example.myapplication.MainActivity { *; }