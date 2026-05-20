# -*- coding: utf-8 -*-
import json
import os
from datetime import timedelta
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone


def _build_redirect_url(url_name, params):
    url = reverse(url_name)
    if params:
        url += "?" + urlencode(params)
    return url


def _format_duration(minutes):
    if minutes >= 60:
        h = minutes // 60
        m = minutes % 60
        return f"{h}h {m}m" if m else f"{h}h"
    return f"{minutes}m"


def _call_claude(text, now_str):
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system = (
        "You are a baby tracking assistant. Parse natural language text describing a baby event "
        "into structured JSON. Return ONLY a raw JSON object — no markdown, no code fences, no explanation.\n\n"
        "The JSON must include an 'entry_type' field set to one of: 'feeding', 'diaper', 'sleep'.\n\n"
        "Fields per entry_type:\n"
        '- "feeding": feed_type ("formula"|"breast milk"|"fortified breast milk"), '
        'method ("bottle"|"left breast"|"right breast"|"both breasts"), '
        "amount_ml (number in ml, convert oz*29.57 if needed, or null), "
        "duration_minutes (number or null)\n"
        '- "diaper": wet (bool), solid (bool), notes (string or null)\n'
        '- "sleep": duration_minutes (number or null)\n\n'
        f"Current local time is {now_str}. "
        "If the text mentions a specific time (e.g. 'at 3pm', 'starting at 10:30'), "
        "include start_time as HH:MM (24h) in the JSON.\n\n"
        'If the text cannot be understood as a baby event, return {"error": "brief explanation"}.'
    )
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": text}],
        system=system,
    )
    raw = response.content[0].text.strip() if response.content else ""
    # Strip markdown code fences if the model added them despite instructions
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"Model returned non-JSON: {raw!r}")


def parse(text, child_slug=None, now=None):
    """
    Parse natural language text into a BabyBuddy entry using the Claude API.

    Returns a dict with entry_type, preview, and redirect_url on success,
    or {"error": "..."} if the text could not be understood.
    """
    if now is None:
        now = timezone.localtime()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return {
            "error": "No Anthropic API key configured. Add ANTHROPIC_API_KEY in the addon settings."
        }

    try:
        data = _call_claude(text.strip(), now.strftime("%H:%M"))
    except Exception as e:
        return {"error": f"AI parsing failed: {e}"}

    if "error" in data:
        return {"error": data["error"]}

    entry_type = data.get("entry_type")

    if entry_type == "feeding":
        feed_type = data.get("feed_type", "breast milk")
        method = data.get("method", "both breasts")
        amount_ml = data.get("amount_ml")
        duration_mins = data.get("duration_minutes")

        if "start_time" in data:
            h, m = map(int, data["start_time"].split(":"))
            start = now.replace(hour=h, minute=m, second=0, microsecond=0)
            end = start + timedelta(minutes=duration_mins) if duration_mins else now
        elif duration_mins:
            end = now
            start = now - timedelta(minutes=duration_mins)
        else:
            start = end = now

        params = {
            "type": feed_type,
            "method": method,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        if amount_ml is not None:
            params["amount"] = str(round(amount_ml, 1))
        if child_slug:
            params["child"] = child_slug

        preview = f"Feeding ({method}, {feed_type})"
        if amount_ml is not None:
            preview += f", {round(amount_ml)}ml"
        if duration_mins:
            preview += f", {_format_duration(duration_mins)}"
        preview += f", ending {end.strftime('%-I:%M %p')}"

        return {
            "entry_type": "feeding",
            "preview": preview,
            "redirect_url": _build_redirect_url("core:feeding-add", params),
        }

    if entry_type == "diaper":
        wet = bool(data.get("wet", False))
        solid = bool(data.get("solid", False))
        notes = data.get("notes") or ""

        if not wet and not solid:
            wet = True

        params = {
            "time": now.isoformat(),
            "wet": "true" if wet else "false",
            "solid": "true" if solid else "false",
        }
        if notes:
            params["notes"] = notes
        if child_slug:
            params["child"] = child_slug

        contents = []
        if wet:
            contents.append("wet")
        if solid:
            contents.append("dirty")
        preview = f"Diaper ({' & '.join(contents)}) at {now.strftime('%-I:%M %p')}"
        if notes:
            preview += f" — {notes}"

        return {
            "entry_type": "diaperchange",
            "preview": preview,
            "redirect_url": _build_redirect_url("core:diaperchange-add", params),
        }

    if entry_type == "sleep":
        duration_mins = data.get("duration_minutes")
        end = now
        start = (now - timedelta(minutes=duration_mins)) if duration_mins else now

        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        if child_slug:
            params["child"] = child_slug

        preview = "Sleep"
        if duration_mins:
            preview += f", {_format_duration(duration_mins)}"
        preview += f", ending {end.strftime('%-I:%M %p')}"

        return {
            "entry_type": "sleep",
            "preview": preview,
            "redirect_url": _build_redirect_url("core:sleep-add", params),
        }

    return {"error": "Could not determine entry type from text."}
