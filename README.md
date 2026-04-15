# Meeting Summarizer AI

> By [MEOK AI Labs](https://meok.ai) — Summarize meeting transcripts into action items, decisions, and follow-ups

## Installation

```bash
pip install meeting-summarizer-ai-mcp
```

## Usage

```bash
python server.py
```

## Tools

### `summarize_meeting`
Summarize a meeting transcript into key points, topics discussed, and participant info.

**Parameters:**
- `transcript` (str): Full meeting transcript text
- `max_sentences` (int): Maximum summary sentences (default: 5)

### `extract_action_items`
Extract action items and tasks from meeting transcript with assignee detection and priority levels.

**Parameters:**
- `transcript` (str): Meeting transcript

### `identify_decisions`
Identify key decisions made during a meeting from the transcript, categorized by type.

**Parameters:**
- `transcript` (str): Meeting transcript

### `generate_followup`
Generate a follow-up email draft from a meeting transcript.

**Parameters:**
- `transcript` (str): Meeting transcript
- `meeting_title` (str): Title of the meeting (default: "Team Meeting")
- `recipients` (list[str]): Email recipients

## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs
