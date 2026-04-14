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

# In-memory store (replace with DB in production)
_store = {}

server = Server("meeting-summarizer-ai-mcp")

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return []

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="summarize_transcript", description="Summarize a meeting transcript", inputSchema={"type":"object","properties":{"transcript":{"type":"string"}},"required":["transcript"]}),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Any | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
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
