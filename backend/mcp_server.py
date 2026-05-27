"""
NoteService MCP Server — 用户的个人工作笔记系统。
Agent 通过此服务将工作产出（简报、会议纪要、决策记录、任务结果等）持久化到笔记数据库中，
并可按标签、关键词、关联人检索历史笔记。贯穿所有对话使用。
"""

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8002")

mcp = FastMCP(
    "note-service",
    instructions=(
        "个人工作笔记系统，贯穿所有对话使用。"
        "当用户完成一项工作、整理信息、记录决策，或明确要求「记到笔记里」「发到笔记」时，"
        "使用 write_message 写入笔记。"
        "笔记通过 #tag 分类（如 #简报 #会议 #决策），通过 actor 关联到具体的人，"
        "也可以通过 issue_id 归到某个工作主题的时间线下。"
        "使用 search_messages 检索历史笔记，使用 list_tags 浏览已有分类，"
        "使用 list_issues / read_issue 查看进行中的工作主题。"
    ),
)


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
    issue_id: int | None = None,
    file_paths: list[str] | None = None,
    tag_list: list[str] | None = None,
) -> str:
    """写入一条笔记到笔记数据库。
    适用场景：用户要求记录工作产出（简报、总结、决策）、整理信息后存档、
    或明确说「记到笔记里」「发到笔记」时调用。
    若要把笔记归到某个 issue 的时间线下（例如 briefing 对 doing issue 的进展更新），
    传入 issue_id（通过 list_issues 获取）。

    Args:
        text: 笔记正文，支持 Markdown。正文中的 #hashtag 会被自动提取为标签
        actor_id: 关联的人物 ID（通过 list_actors 查询获得）
        issue_id: 关联的 Issue ID（通过 list_issues 查询获得），笔记会出现在该 issue 的时间线
        file_paths: 要附加的本地文件路径列表
        tag_list: 标签列表（如 ["简报", "周报"]）
    """
    body: dict[str, Any] = {}
    if text is not None:
        body["text"] = text
    if actor_id is not None:
        body["actor_id"] = actor_id
    if issue_id is not None:
        body["issue_id"] = issue_id
    if file_paths is not None:
        body["files"] = file_paths
    if tag_list is not None:
        body["tag_ids"] = await _resolve_tag_ids(tag_list)
    return await _request("POST", "/messages", json_body=body)


async def _resolve_tag_ids(names: list[str]) -> list[int]:
    """将标签名列表解析为 ID 列表，缺失的标签自动创建。"""
    ids: list[int] = []
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30) as client:
        for name in names:
            name = name.lstrip("#").strip()
            if not name:
                continue
            resp = await client.get("/tags", params={"name": name})
            tag_id: int | None = None
            if resp.status_code < 400:
                for t in resp.json():
                    if t.get("name") == name:
                        tag_id = t.get("id")
                        break
            if tag_id is None:
                created = await client.post("/tags", json={"name": name})
                if created.status_code < 400:
                    tag_id = created.json().get("id")
            if tag_id is not None:
                ids.append(tag_id)
    return ids


@mcp.tool()
async def write_message_from_md(
    file_path: str,
    actor_id: int | None = None,
    tag_list: list[str] | None = None,
    delete_after: bool = False,
) -> str:
    """读取本地 Markdown 文件内容，写入为一条笔记。适合将已有文档（报告、纪要等）归档到笔记库。

    Args:
        file_path: Markdown 文件的绝对路径
        actor_id: 关联的人物 ID
        tag_list: 标签列表（如 ["简报", "周报"]）
        delete_after: 写入成功后是否删除源 md 文件，默认 False
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return json.dumps({"error": True, "detail": f"文件不存在: {file_path}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": True, "detail": str(e)}, ensure_ascii=False)

    if not text.strip():
        return json.dumps({"error": True, "detail": "文件内容为空"}, ensure_ascii=False)

    result = await write_message(text=text, actor_id=actor_id, tag_list=tag_list)

    if delete_after:
        try:
            parsed = json.loads(result)
        except Exception:
            parsed = None
        if isinstance(parsed, dict) and not parsed.get("error"):
            try:
                os.remove(file_path)
            except Exception as e:
                return json.dumps(
                    {**parsed, "delete_warning": f"笔记已写入但删除文件失败: {e}"},
                    ensure_ascii=False,
                )

    return result


@mcp.tool()
async def search_messages(
    query_text: str,
    actor_id: int | None = None,
    issue_id: int | None = None,
    tag_id: int | None = None,
    starred: bool | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> str:
    """按关键词全文检索历史笔记（FTS5），返回精简结果（snippet + 元数据）。
    多个关键词之间隐式 AND（都要命中）。命中片段用 «…» 包裹。
    需要看完整笔记时，用返回的 id 调 read_message。

    Args:
        query_text: 搜索关键词，必填。多词空格分隔（隐式 AND），如 "briefing 周报"
        actor_id: 按关联人物过滤
        issue_id: 按 issue 过滤
        tag_id: 按标签 ID 过滤（通过 list_tags 查询获得）
        starred: 仅返回收藏的笔记
        cursor: 分页游标（上一页返回的 next_cursor）
        limit: 每页条数，默认 20，最大 100
    """
    params = _compact(
        {
            "q": query_text,
            "actor_id": actor_id,
            "issue_id": issue_id,
            "tag_id": tag_id,
            "starred": starred,
            "cursor": cursor,
            "limit": limit,
        }
    )
    return await _request("GET", "/messages/search", params=params)


@mcp.tool()
async def read_message(message_id: int) -> str:
    """读取单条笔记的完整内容（含所有附件和标签）。

    Args:
        message_id: 笔记 ID
    """
    return await _request("GET", f"/messages/{message_id}")


@mcp.tool()
async def list_tags(name: str | None = None) -> str:
    """列出所有标签分类及其笔记数量，按笔记数降序。用于了解笔记库的分类体系。

    Args:
        name: 按标签名模糊搜索
    """
    params = _compact({"name": name})
    return await _request("GET", "/tags", params=params)


@mcp.tool()
async def list_issues(status: str | None = "doing") -> str:
    """列出 issue（任务卡片）。用于 briefing 等场景获取进行中的工作主题，
    再结合昨日邮件/Teams/文件动态判断是否需要给某个 issue 推进展更新。

    Args:
        status: 过滤状态，"doing" / "done" / "archived" / "abandoned"；传 None 返回全部
    """
    params = _compact({"status": status})
    return await _request("GET", "/issues/list", params=params)


@mcp.tool()
async def read_issue(issue_id: int, history_limit: int = 5) -> str:
    """读取单个 issue 的详情，并附带最近若干条关联 message（按时间倒序）。
    在给 issue 发新更新前调用，避免重复昨天已经记录过的结论。

    Args:
        issue_id: Issue ID
        history_limit: 关联 message 返回条数上限，默认 5
    """
    issue_text = await _request("GET", f"/issues/{issue_id}")
    try:
        issue = json.loads(issue_text)
    except Exception:
        return issue_text
    if isinstance(issue, dict) and issue.get("error"):
        return issue_text

    msgs_text = await _request(
        "GET",
        "/messages/with-detail",
        params={"issue_id": issue_id, "limit": history_limit},
    )
    try:
        msgs = json.loads(msgs_text)
    except Exception:
        msgs = msgs_text
    return json.dumps({"issue": issue, "recent_messages": msgs}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
