"""
MediaManagerSteam MCP Server — 独立轻量 MCP 服务器。
通过 HTTP 调用后端 FastAPI API，不直接依赖后端代码。

依赖：mcp, httpx
配置：环境变量 API_BASE_URL（默认 http://localhost:8002）

使用方式：
  API_BASE_URL=http://192.168.31.146:8002 uv run python mcp_server.py
"""

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")

mcp = FastMCP("media-manager")


async def _request(
    method: str, path: str, *, params: dict | None = None, json_body: dict | None = None
) -> str:
    """发起 HTTP 请求并返回 JSON 字符串，非 2xx 时返回错误信息。"""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30) as client:
        resp = await client.request(method, path, params=params, json=json_body)
        if resp.status_code >= 400:
            return json.dumps(
                {"error": True, "status": resp.status_code, "detail": resp.text},
                ensure_ascii=False,
            )
        return resp.text


def _compact(d: dict[str, Any]) -> dict[str, Any]:
    """移除值为 None 的键，用于构建干净的 query params。"""
    return {k: v for k, v in d.items() if v is not None}


# ── Tools ──────────────────────────────────────────────


@mcp.tool()
async def write_message(
    text: str | None = None,
    actor_id: int | None = None,
    file_paths: list[str] | None = None,
) -> str:
    """创建一条新消息。

    Args:
        text: 消息文本，支持 #hashtag 自动提取标签
        actor_id: 关联的 Actor ID
        file_paths: 要附加的本地文件路径列表（后端可访问的路径）
    """
    body: dict[str, Any] = {}
    if text is not None:
        body["text"] = text
    if actor_id is not None:
        body["actor_id"] = actor_id
    if file_paths is not None:
        body["files"] = file_paths
    return await _request("POST", "/messages", json_body=body)


@mcp.tool()
async def search_messages(
    query_text: str | None = None,
    actor_id: int | None = None,
    tag_id: int | None = None,
    starred: bool | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> str:
    """搜索消息，返回含媒体和标签的详情列表（游标分页）。

    Args:
        query_text: 搜索文本（模糊匹配消息内容）
        actor_id: 按 Actor 过滤
        tag_id: 按 Tag 过滤
        starred: 仅返回收藏消息
        cursor: 分页游标（上一页返回的 next_cursor）
        limit: 每页条数，默认 20，最大 100
    """
    params = _compact(
        {
            "query_text": query_text,
            "actor_id": actor_id,
            "tag_id": tag_id,
            "starred": starred,
            "cursor": cursor,
            "limit": limit,
        }
    )
    return await _request("GET", "/messages/with-detail", params=params)


@mcp.tool()
async def read_message(message_id: int) -> str:
    """读取单条消息的完整详情（含所有媒体和标签）。

    Args:
        message_id: 消息 ID
    """
    return await _request("GET", f"/messages/{message_id}")


@mcp.tool()
async def list_actors(name: str | None = None) -> str:
    """列出所有 Actor（含消息数），按消息数降序排列。

    Args:
        name: 按名称模糊搜索
    """
    params = _compact({"name": name})
    return await _request("GET", "/actors", params=params)


@mcp.tool()
async def list_tags(name: str | None = None) -> str:
    """列出所有 Tag（含消息数），按消息数降序排列。

    Args:
        name: 按名称模糊搜索
    """
    params = _compact({"name": name})
    return await _request("GET", "/tags", params=params)


if __name__ == "__main__":
    mcp.run()
