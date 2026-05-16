# -*- coding: utf-8 -*-
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.quick_entry import parse


class QuickEntryParserTestCase(TestCase):
    def setUp(self):
        self.now = timezone.localtime()

    def test_left_breast_feeding(self):
        result = parse("nursed on left for 15 min", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("left breast", result["preview"])
        self.assertIn("15m", result["preview"])
        self.assertIn("method=left+breast", result["redirect_url"])
        self.assertIn("type=breast+milk", result["redirect_url"])

    def test_right_breast_feeding(self):
        result = parse("breastfed right 20 minutes", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("right breast", result["preview"])
        self.assertIn("method=right+breast", result["redirect_url"])

    def test_both_breasts_feeding(self):
        result = parse("nursed for 30 min", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("both breasts", result["preview"])

    def test_bottle_formula(self):
        result = parse("bottle of formula 3 oz", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("3.0 oz", result["preview"])
        self.assertIn("formula", result["redirect_url"])
        self.assertIn("method=bottle", result["redirect_url"])

    def test_bottle_no_amount(self):
        result = parse("gave a bottle for 20 min", now=self.now)
        self.assertEqual(result["entry_type"], "feeding")
        self.assertIn("20m", result["preview"])

    def test_wet_diaper(self):
        result = parse("wet diaper", now=self.now)
        self.assertEqual(result["entry_type"], "diaperchange")
        self.assertIn("wet", result["preview"])
        self.assertIn("wet=true", result["redirect_url"])
        self.assertIn("solid=false", result["redirect_url"])

    def test_dirty_diaper(self):
        result = parse("dirty diaper", now=self.now)
        self.assertEqual(result["entry_type"], "diaperchange")
        self.assertIn("dirty", result["preview"])
        self.assertIn("solid=true", result["redirect_url"])

    def test_wet_and_dirty_diaper(self):
        result = parse("wet and dirty diaper", now=self.now)
        self.assertEqual(result["entry_type"], "diaperchange")
        self.assertIn("wet=true", result["redirect_url"])
        self.assertIn("solid=true", result["redirect_url"])

    def test_nap(self):
        result = parse("nap for 45 min", now=self.now)
        self.assertEqual(result["entry_type"], "sleep")
        self.assertIn("Nap", result["preview"])
        self.assertIn("45m", result["preview"])

    def test_sleep(self):
        result = parse("slept for 2 hours", now=self.now)
        self.assertEqual(result["entry_type"], "sleep")
        self.assertIn("Sleep", result["preview"])
        self.assertIn("2h", result["preview"])

    def test_sleep_with_child_slug(self):
        result = parse("nap 1 hour", child_slug="alice", now=self.now)
        self.assertIn("child=alice", result["redirect_url"])

    def test_duration_hour_and_minutes(self):
        result = parse("nursed left 1 hour 15 min", now=self.now)
        self.assertIn("1h 15m", result["preview"])

    def test_unknown_input_returns_error(self):
        result = parse("went to the store", now=self.now)
        self.assertIn("error", result)
        self.assertNotIn("entry_type", result)

    def test_empty_input_returns_error(self):
        result = parse("   ", now=self.now)
        self.assertIn("error", result)

    def test_start_time_set_from_duration(self):
        from urllib.parse import unquote

        result = parse("nursed left for 30 min", now=self.now)
        expected_start = self.now - timedelta(minutes=30)
        self.assertIn(expected_start.strftime("%H:%M"), unquote(result["redirect_url"]))
