# -*- coding: utf-8 -*-
import os
from contextlib import ExitStack
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from core.quick_entry import parse


def _mock_claude(response):
    """Patch both the API key env var and _call_claude for a unit test."""
    stack = ExitStack()
    stack.enter_context(patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}))
    stack.enter_context(patch("core.quick_entry._call_claude", return_value=response))
    return stack


class QuickEntryParserTestCase(TestCase):
    def setUp(self):
        self.now = timezone.localtime()

    def test_left_breast_feeding(self):
        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "breast milk", "method": "left breast", "duration_minutes": 15}
        ):
            result = parse("nursed on left for 15 min", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("left breast", result["preview"])
        self.assertIn("15m", result["preview"])
        self.assertIn("method=left+breast", result["redirect_url"])
        self.assertIn("type=breast+milk", result["redirect_url"])

    def test_right_breast_feeding(self):
        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "breast milk", "method": "right breast", "duration_minutes": 20}
        ):
            result = parse("breastfed right 20 minutes", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("right breast", result["preview"])
        self.assertIn("method=right+breast", result["redirect_url"])

    def test_both_breasts_feeding(self):
        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "breast milk", "method": "both breasts", "duration_minutes": 30}
        ):
            result = parse("nursed for 30 min", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("both breasts", result["preview"])

    def test_bottle_formula(self):
        # 3 oz = 88.71 ml → rounds to 89 ml in the preview
        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "formula", "method": "bottle", "amount_ml": 88.71}
        ):
            result = parse("bottle of formula 3 oz", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("89ml", result["preview"])
        self.assertIn("formula", result["redirect_url"])
        self.assertIn("method=bottle", result["redirect_url"])

    def test_bottle_no_amount(self):
        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "breast milk", "method": "bottle", "duration_minutes": 20}
        ):
            result = parse("gave a bottle for 20 min", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("20m", result["preview"])

    def test_wet_diaper(self):
        with _mock_claude({"entry_type": "diaper", "wet": True, "solid": False}):
            result = parse("wet diaper", now=self.now)
        self.assertEqual(result["entry_type"], "diaperchange")
        self.assertIn("wet", result["preview"])
        self.assertIn("wet=true", result["redirect_url"])
        self.assertIn("solid=false", result["redirect_url"])

    def test_dirty_diaper(self):
        with _mock_claude({"entry_type": "diaper", "wet": False, "solid": True}):
            result = parse("dirty diaper", now=self.now)
        self.assertEqual(result["entry_type"], "diaperchange")
        self.assertIn("dirty", result["preview"])
        self.assertIn("solid=true", result["redirect_url"])

    def test_wet_and_dirty_diaper(self):
        with _mock_claude({"entry_type": "diaper", "wet": True, "solid": True}):
            result = parse("wet and dirty diaper", now=self.now)
        self.assertEqual(result["entry_type"], "diaperchange")
        self.assertIn("wet=true", result["redirect_url"])
        self.assertIn("solid=true", result["redirect_url"])

    def test_nap(self):
        with _mock_claude({"entry_type": "sleep", "duration_minutes": 45}):
            result = parse("nap for 45 min", now=self.now)
        self.assertEqual(result["entry_type"], "sleep")
        self.assertIn("Sleep", result["preview"])
        self.assertIn("45m", result["preview"])

    def test_sleep(self):
        with _mock_claude({"entry_type": "sleep", "duration_minutes": 120}):
            result = parse("slept for 2 hours", now=self.now)
        self.assertEqual(result["entry_type"], "sleep")
        self.assertIn("Sleep", result["preview"])
        self.assertIn("2h", result["preview"])

    def test_sleep_with_child_slug(self):
        with _mock_claude({"entry_type": "sleep", "duration_minutes": 60}):
            result = parse("nap 1 hour", child_slug="alice", now=self.now)
        self.assertIn("child=alice", result["redirect_url"])

    def test_duration_hour_and_minutes(self):
        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "breast milk", "method": "left breast", "duration_minutes": 75}
        ):
            result = parse("nursed left 1 hour 15 min", now=self.now)
        self.assertIn("1h 15m", result["preview"])

    def test_unknown_input_returns_error(self):
        with _mock_claude({"error": "not a baby event"}):
            result = parse("went to the store", now=self.now)
        self.assertIn("error", result)
        self.assertNotIn("entry_type", result)

    def test_empty_input_returns_error(self):
        result = parse("   ", now=self.now)
        self.assertIn("error", result)

    def test_start_time_set_from_duration(self):
        from urllib.parse import unquote

        with _mock_claude(
            {"entry_type": "feeding", "feed_type": "breast milk", "method": "left breast", "duration_minutes": 30}
        ):
            result = parse("nursed left for 30 min", now=self.now)
        expected_start = self.now - timedelta(minutes=30)
        self.assertIn(expected_start.strftime("%H:%M"), unquote(result["redirect_url"]))

    def test_no_api_key_returns_error(self):
        with patch("os.environ.get", return_value=""):
            result = parse("wet diaper", now=self.now)
        self.assertIn("error", result)
        self.assertIn("ANTHROPIC_API_KEY", result["error"])
