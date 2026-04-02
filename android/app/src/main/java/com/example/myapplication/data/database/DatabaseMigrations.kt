package com.example.myapplication.data.database

import androidx.room.migration.Migration

/**
 * 数据库迁移
 *
 * 当前策略：不做增量迁移，版本升级时通过 fallbackToDestructiveMigration() 清空重建。
 * 如果未来需要保留用户数据，在此添加对应版本的迁移脚本。
 */
object DatabaseMigrations {

    val ALL_MIGRATIONS: Array<Migration> = emptyArray()

}