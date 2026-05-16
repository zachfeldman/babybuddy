# -*- coding: utf-8 -*-
import re
from datetime import timedelta
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone


def _parse_duration(text):
    """Return total minutes from text, or None if no duration found."""
    total = 0.0
    found = False
    hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hr)s?", text)
    if hour_match:
        total += float(hour_match.group(1)) * 60
        found = True
    min_match = re.search(r"(\d+)\s*min(?:ute)?s?", text)
    if min_match:
        total += int(min_match.group(1))
        found = True
    return int(total) if found else None


def _format_duration(minutes):
    if minutes >= 60:
        h = minutes // 60
        m = minutes % 60
        return f"{h}h {m}m" if m else f"{h}h"
    return f"{minutes}m"


def _build_redirect_url(url_name, params):
    url = reverse(url_name)
    if params:
        url += "?" + urlencode(params)
    return url


def _parse_feeding(text, child_slug, now):
    is_breast = bool(re.search(r"nurs|breastfe|breast[\s-]?fed|breast[\s-]?feed", text))
    is_bottle = bool(re.search(r"bottle|formula", text))

    if not is_breast and not is_bottle:
        return None

    if is_bottle:
        feed_type = "formula" if re.search(r"formula", text) else "breast milk"
        amount = None
        amount_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:oz|ounce|ml)", text)
        if amount_match:
            amount = float(amount_match.group(1))
        duration_mins = _parse_duration(text)
        start = (now - timedelta(minutes=duration_mins)) if duration_mins else now
        end = now

        params = {
            "type": feed_type,
            "method": "bottle",
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        if amount is not None:
            params["amount"] = str(amount)
        if child_slug:
            params["child"] = child_slug

        preview = f"Bottle ({feed_type})"
        if amount is not None:
            preview += f", {amount} oz"
        if duration_mins:
            preview += f", {_format_duration(duration_mins)}"
        preview += f", ending {now.strftime('%-I:%M %p')}"

        return {
            "entry_type": "feeding",
            "preview": preview,
            "redirect_url": _build_redirect_url("core:feeding-add", params),
        }

    # Breast feeding — detect side
    if re.search(r"\bleft\b", text):
        method = "left breast"
    elif re.search(r"\bright\b", text):
        method = "right breast"
    else:
        method = "both breasts"

    duration_mins = _parse_duration(text)
    start = (now - timedelta(minutes=duration_mins)) if duration_mins else now
    end = now

    params = {
        "type": "breast milk",
        "method": method,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
    if child_slug:
        params["child"] = child_slug

    preview = f"Feeding ({method})"
    if duration_mins:
        preview += f", {_format_duration(duration_mins)}"
    preview += f", ending {now.strftime('%-I:%M %p')}"

    return {
        "entry_type": "feeding",
        "preview": preview,
        "redirect_url": _build_redirect_url("core:feeding-add", params),
    }


def _parse_diaper(text, child_slug, now):
    if not re.search(r"diaper|nappy|wet|dirty|poop|pee|soil|bm\b|bowel|change", text):
        return None

    wet = bool(re.search(r"wet|pee|urine", text))
    solid = bool(re.search(r"dirty|poop|solid|soil|bm\b|bowel", text))

    if re.search(r"both|wet.{0,5}dirty|dirty.{0,5}wet", text):
        wet = True
        solid = True

    # Plain "diaper change" with no qualifier defaults to wet
    if not wet and not solid:
        wet = True

    params = {
        "time": now.isoformat(),
        "wet": "true" if wet else "false",
        "solid": "true" if solid else "false",
    }
    if child_slug:
        params["child"] = child_slug

    contents = []
    if wet:
        contents.append("wet")
    if solid:
        contents.append("dirty")
    preview = f"Diaper change ({' & '.join(contents)}) at {now.strftime('%-I:%M %p')}"

    return {
        "entry_type": "diaperchange",
        "preview": preview,
        "redirect_url": _build_redirect_url("core:diaperchange-add", params),
    }


def _parse_sleep(text, child_slug, now):
    if not re.search(r"sleep|slept|nap", text):
        return None

    duration_mins = _parse_duration(text)
    start = (now - timedelta(minutes=duration_mins)) if duration_mins else now
    end = now

    params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
    }
    if child_slug:
        params["child"] = child_slug

    preview = "Nap" if re.search(r"nap", text) else "Sleep"
    if duration_mins:
        preview += f", {_format_duration(duration_mins)}"
    preview += f", ending {now.strftime('%-I:%M %p')}"

    return {
        "entry_type": "sleep",
        "preview": preview,
        "redirect_url": _build_redirect_url("core:sleep-add", params),
    }


def parse(text, child_slug=None, now=None):
    """
    Parse natural language text into a BabyBuddy entry.

    Returns a dict with entry_type, preview, and redirect_url on success,
    or {"error": "..."} if the text could not be understood.
    """
    if now is None:
        now = timezone.localtime()
    normalized = text.strip().lower()
    result = (
        _parse_feeding(normalized, child_slug, now)
        or _parse_diaper(normalized, child_slug, now)
        or _parse_sleep(normalized, child_slug, now)
    )
    if not result:
        return {
            "error": (
                "Could not understand that. Try: "
                "‘nursed left 15 min’, ‘wet diaper’, "
                "‘bottle formula 3 oz’, ‘nap 2 hours’."
            )
        }
    return result
