<div align="center">

# Meeting Summarizer Ai MCP

**MCP server for meeting summarizer ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-meeting-summarizer-ai-mcp)](https://pypi.org/project/meok-meeting-summarizer-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Meeting Summarizer Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `summarize_meeting` | Summarize a meeting transcript into key points, topics discussed, and participan |
| `extract_action_items` | Extract action items and tasks from meeting transcript with assignee detection. |
| `identify_decisions` | Identify key decisions made during a meeting from the transcript. |
| `generate_followup` | Generate a follow-up email draft from a meeting transcript. |

## Installation

```bash
pip install meok-meeting-summarizer-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "meeting-summarizer-ai": {
      "command": "python",
      "args": ["-m", "meok_meeting_summarizer_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 4 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
