#!/usr/bin/env python3
"""MEOK AI Labs — meeting-summarizer-ai-mcp MCP Server. Summarize meeting transcripts into action items and decisions."""

import json
import re
from datetime import datetime, timezone
from collections import defaultdict

from mcp.server.fastmcp import FastMCP
import sys, os
sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

ACTION_PATTERNS = [
    r"(?:will|shall|going to)\s+(.+?)(?:\.|$)",
    r"(?:need to|needs to|have to|has to)\s+(.+?)(?:\.|$)",
    r"(?:action item|todo|task)[:\s]+(.+?)(?:\.|$)",
    r"(?:responsible for|assigned to|owns)\s+(.+?)(?:\.|$)",
    r"(?:please|should)\s+(.+?)(?:\.|$)",
]

DECISION_PATTERNS = [
    r"(?:decided|agreed|approved|confirmed)\s+(?:to\s+|that\s+)?(.+?)(?:\.|$)",
    r"(?:decision|resolution)[:\s]+(.+?)(?:\.|$)",
    r"(?:we will go with|going with|chosen|selected)\s+(.+?)(?:\.|$)",
    r"(?:consensus|unanimous)\s+(?:on\s+|that\s+)?(.+?)(?:\.|$)",
]

TOPIC_MARKERS = ["regarding", "about", "discuss", "topic", "agenda", "update on", "status of", "review"]

mcp = FastMCP("meeting-summarizer-ai", instructions="Summarize meeting transcripts, extract action items, identify decisions, and generate follow-up emails.")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _extract_speakers(text: str) -> list[str]:
    """Extract speaker names from transcript (Name: format)."""
    speakers = re.findall(r'^([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*:', text, re.MULTILINE)
    return list(dict.fromkeys(speakers))


@mcp.tool()
def summarize_meeting(transcript: str, max_sentences: int = 5, api_key: str = "") -> str:
    """Summarize a meeting transcript into key points, topics discussed, and participant info."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    sentences = _split_sentences(transcript)
    speakers = _extract_speakers(transcript)
    word_count = len(transcript.split())

    # Extract key sentences (those with important markers)
    important_markers = ["decided", "agreed", "important", "critical", "deadline", "budget", "launch", "milestone",
                         "priority", "blocker", "risk", "concern", "approved", "rejected", "next steps"]
    scored = []
    for s in sentences:
        lower = s.lower()
        score = sum(1 for m in important_markers if m in lower)
        if any(p in lower for p in ["action", "decision", "conclude", "summary"]):
            score += 2
        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    key_points = [s for _, s in scored[:max_sentences]]

    # Detect topics
    topics = []
    for s in sentences:
        lower = s.lower()
        for marker in TOPIC_MARKERS:
            if marker in lower:
                topic = s[:100]
                if topic not in topics:
                    topics.append(topic)
                break

    # Estimate duration from word count (avg 150 wpm speaking)
    est_minutes = round(word_count / 150)

    return json.dumps({
        "summary": " ".join(key_points) if key_points else " ".join(sentences[:3]),
        "key_points": key_points,
        "topics_discussed": topics[:10],
        "participants": speakers if speakers else ["Unable to detect speakers"],
        "word_count": word_count,
        "sentence_count": len(sentences),
        "estimated_duration_minutes": est_minutes,
    }, indent=2)


@mcp.tool()
def extract_action_items(transcript: str, api_key: str = "") -> str:
    """Extract action items and tasks from meeting transcript with assignee detection."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    sentences = _split_sentences(transcript)
    speakers = _extract_speakers(transcript)
    actions = []
    seen = set()

    for sentence in sentences:
        for pattern in ACTION_PATTERNS:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                action_text = match.group(1).strip()
                if len(action_text) < 5 or action_text in seen:
                    continue
                seen.add(action_text)

                # Try to detect assignee
                assignee = "Unassigned"
                for speaker in speakers:
                    if speaker.lower() in sentence.lower():
                        assignee = speaker
                        break

                # Detect priority
                lower = sentence.lower()
                priority = "high" if any(w in lower for w in ["urgent", "asap", "critical", "immediately"]) else \
                           "medium" if any(w in lower for w in ["important", "soon", "priority"]) else "normal"

                # Detect deadline
                deadline = None
                date_match = re.search(r'(?:by|before|due|until)\s+(\w+\s+\d+|\w+day|end of \w+|next \w+)', lower)
                if date_match:
                    deadline = date_match.group(1)

                actions.append({
                    "action": action_text[:200],
                    "assignee": assignee,
                    "priority": priority,
                    "deadline": deadline,
                    "source_sentence": sentence[:150],
                })

    return json.dumps({
        "total_action_items": len(actions),
        "high_priority": sum(1 for a in actions if a["priority"] == "high"),
        "action_items": actions,
    }, indent=2)


@mcp.tool()
def identify_decisions(transcript: str, api_key: str = "") -> str:
    """Identify key decisions made during a meeting from the transcript."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    sentences = _split_sentences(transcript)
    decisions = []
    seen = set()

    for sentence in sentences:
        for pattern in DECISION_PATTERNS:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                decision_text = match.group(1).strip()
                if len(decision_text) < 5 or decision_text in seen:
                    continue
                seen.add(decision_text)

                # Categorize
                lower = sentence.lower()
                category = "budget" if any(w in lower for w in ["budget", "cost", "spend", "invest"]) else \
                           "technical" if any(w in lower for w in ["technical", "architecture", "stack", "tool"]) else \
                           "process" if any(w in lower for w in ["process", "workflow", "procedure"]) else \
                           "timeline" if any(w in lower for w in ["timeline", "deadline", "schedule", "date"]) else \
                           "staffing" if any(w in lower for w in ["hire", "team", "resource", "role"]) else "general"

                decisions.append({
                    "decision": decision_text[:200],
                    "category": category,
                    "context": sentence[:200],
                })

    # Also check for explicit rejections
    rejections = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(w in lower for w in ["rejected", "declined", "not approved", "decided against", "ruled out"]):
            rejections.append(sentence[:200])

    return json.dumps({
        "total_decisions": len(decisions),
        "decisions": decisions,
        "rejections": rejections,
        "categories_found": list(set(d["category"] for d in decisions)),
    }, indent=2)


@mcp.tool()
def generate_followup(transcript: str, meeting_title: str = "Team Meeting", recipients: list[str] = [], api_key: str = "") -> str:
    """Generate a follow-up email draft from a meeting transcript."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    sentences = _split_sentences(transcript)
    speakers = _extract_speakers(transcript)
    to_list = recipients if recipients else speakers

    # Extract summary points
    important = ["decided", "agreed", "action", "deadline", "next", "follow", "update"]
    key_sentences = [s for s in sentences if any(w in s.lower() for w in important)][:5]

    # Extract actions
    actions = []
    for sentence in sentences:
        for pattern in ACTION_PATTERNS[:3]:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                action = match.group(1).strip()
                if len(action) >= 5 and action not in actions:
                    actions.append(action[:150])

    # Extract decisions
    decision_list = []
    for sentence in sentences:
        for pattern in DECISION_PATTERNS[:2]:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                dec = match.group(1).strip()
                if len(dec) >= 5 and dec not in decision_list:
                    decision_list.append(dec[:150])

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    subject = f"Follow-up: {meeting_title} - {today}"
    body_parts = [f"Hi team,", "", f"Here is a summary of our {meeting_title.lower()} held on {today}.", ""]

    if key_sentences:
        body_parts.append("KEY DISCUSSION POINTS:")
        for i, point in enumerate(key_sentences, 1):
            body_parts.append(f"  {i}. {point}")
        body_parts.append("")

    if decision_list:
        body_parts.append("DECISIONS MADE:")
        for i, dec in enumerate(decision_list, 1):
            body_parts.append(f"  {i}. {dec}")
        body_parts.append("")

    if actions:
        body_parts.append("ACTION ITEMS:")
        for i, action in enumerate(actions, 1):
            body_parts.append(f"  {i}. {action}")
        body_parts.append("")

    body_parts.extend(["Please let me know if I missed anything or if you have questions.", "", "Best regards"])

    return json.dumps({
        "subject": subject,
        "to": to_list,
        "body": "\n".join(body_parts),
        "action_items_count": len(actions),
        "decisions_count": len(decision_list),
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
