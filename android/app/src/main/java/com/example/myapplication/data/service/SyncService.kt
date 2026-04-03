package com.example.myapplication.data.service

import com.example.myapplication.data.model.RemoteActor
import com.example.myapplication.data.model.RemoteChangesResponse
import com.example.myapplication.data.model.RemoteMessage
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Query

interface SyncService {
    @GET("actors/sync")
    suspend fun getActors(): List<RemoteActor>

    @GET("messages/sync")
    suspend fun getMessages(): List<RemoteMessage>

    /** 增量拉取变更日志。since 为空时后端返回 410（需全量同步）。*/
    @GET("sync/changes")
    suspend fun getChanges(
        @Query("since") since: String,
        @Query("limit") limit: Int = 500
    ): Response<RemoteChangesResponse>
}
