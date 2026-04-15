#!/usr/bin/env python3
"""MEOK AI Labs — meeting-summarizer-ai-mcp MCP Server. Summarize meeting transcripts into action items and decisions."""

import asyncio
import json
from datetime import datetime
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent)
import mcp.types as types
import sys, os
sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

from datetime import datetime, timezone
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

# In-memory store (replace with DB in production)
_store = {}

server = Server("meeting-summarizer-ai")

@server.list_resources()
def handle_list_resources() -> list[Resource]:
    return []

@server.list_tools()
def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="summarize_transcript", description="Summarize a meeting transcript", inputSchema={"type":"object","properties":{"transcript":{"type":"string"}},"required":["transcript"]}),
    ]

@server.call_tool()
def handle_call_tool(name: str, arguments: Any | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [TextContent(type="text", text=json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"}))]
    if err := _rl():
        return [TextContent(type="text", text=err)]
    if name == "summarize_transcript":
            sentences = args["transcript"].split(".")
            summary = " ".join(sentences[:3]) + "."
            actions = [s.strip() for s in sentences if "will" in s or "need to" in s]
            return [TextContent(type="text", text=json.dumps({"summary": summary, "action_items": actions[:5]}, indent=2))]
    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}, indent=2))]

async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="meeting-summarizer-ai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={})))

if __name__ == "__main__":
    asyncio.run(main())