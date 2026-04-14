package com.example.myapplication.data.service

import okhttp3.MultipartBody
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface MediaUploadService {
    @Multipart
    @POST("files/upload-media")
    suspend fun uploadMedia(@Part file: MultipartBody.Part): UploadMediaResponse
}

data class UploadMediaResponse(val message: String, val path: String)
