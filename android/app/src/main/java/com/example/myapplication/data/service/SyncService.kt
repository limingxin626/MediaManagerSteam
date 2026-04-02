package com.example.myapplication.data.service

import com.example.myapplication.data.model.RemoteActor
import com.example.myapplication.data.model.RemoteMessage
import retrofit2.http.GET

interface SyncService {
    @GET("actors/sync")
    suspend fun getActors(): List<RemoteActor>

    @GET("messages/sync")
    suspend fun getMessages(): List<RemoteMessage>
}
