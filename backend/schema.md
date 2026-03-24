# 🧱 最终数据库结构总结（个人 feed + media）

---

## 1️⃣ Message（Feed 核心）

```sql
Message
--------
id              BIGINT PRIMARY KEY
text            TEXT
actor_id        BIGINT NULL         -- FK -> Actor.id，发言者
created_at      TIMESTAMP NOT NULL
updated_at      TIMESTAMP NOT NULL
```

* 代表 feed 中的一条消息
* 一条消息可以包含多张图片/视频
* 所有 feed 的排序依据：`created_at DESC`
* actor_id 关联发言者，支持单人发言（未来可扩展为多人）

---

## 2️⃣ Actor（发言者）

```sql
Actor
------
id              BIGINT PRIMARY KEY
name            VARCHAR(256) NOT NULL
description     TEXT
avatar_path     VARCHAR(1024)
created_at      TIMESTAMP NOT NULL
updated_at      TIMESTAMP NOT NULL
```

* 存储发言者信息
* 可关联多个 Message

---

## 3️⃣ Media（资源层）

```sql
Media
------
id              BIGINT PRIMARY KEY
file_path       VARCHAR(255)        -- 文件存储路径
file_hash       VARCHAR(128)        -- 文件去重 key，可选唯一
file_size       BIGINT
mime_type       VARCHAR(100)
width           INT
height          INT
duration        INT                 -- 视频用
rating          INT                 -- 评分，默认 0
view_count      INT                 -- 查看次数，默认 0
last_viewed_at  TIMESTAMP NULL      -- 最后查看时间，默认 NULL

created_at      TIMESTAMP NOT NULL
updated_at      TIMESTAMP NOT NULL
```

* 存储实际资源（图片/视频）
* 可复用，不直接绑定 feed

---

## 4️⃣ MessageMedia（关系表，核心）

```sql
MessageMedia
-------------
id              BIGINT PRIMARY KEY
message_id      BIGINT NOT NULL     -- FK -> Message.id
media_id        BIGINT NOT NULL     -- FK -> Media.id
position        INT NOT NULL        -- feed 内顺序
created_at      TIMESTAMP NOT NULL  -- 出现在 feed 的时间
```

* 多对多关系：一条 message 可以有多张 media，一张 media 可以出现在多条 message
* position 控制 feed 内图片顺序
* created_at 用于 media 页面滚动排序

---

# 🔧 索引建议

```sql
-- Message
CREATE INDEX idx_message_created ON Message(created_at DESC);
CREATE INDEX idx_message_actor ON Message(actor_id);

-- Actor
CREATE INDEX idx_actor_name ON Actor(name);
CREATE INDEX idx_actor_category ON Actor(category);
CREATE INDEX idx_actor_country ON Actor(country);
CREATE INDEX idx_actor_rating ON Actor(rating DESC);

-- MessageMedia
CREATE INDEX idx_mm_message ON MessageMedia(message_id);
CREATE INDEX idx_mm_media ON MessageMedia(media_id);
CREATE INDEX idx_mm_created ON MessageMedia(created_at DESC);

-- Media
CREATE UNIQUE INDEX idx_media_file_hash ON Media(file_hash);
```

---

# ⚡ 核心设计原则

1. **Message 是 feed 唯一时间源**
2. **Media 只做资源存储**
3. **MessageMedia 是系统核心**，决定多图顺序 + 出现时间
4. **Actor 关联到 Message**，支持单人发言（未来可通过 MessageActor 表扩展为多人）
5. **添加/删除 feed 中图片** → 修改 MessageMedia，不删除 Media
6. **Media 页面滚动** → 基于 `MessageMedia.created_at + position`

