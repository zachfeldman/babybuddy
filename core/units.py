# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

# Volume (liquid feeding, pumping)
VOLUME_UNIT_ML = "ml"
VOLUME_UNIT_OZ = "oz"
VOLUME_UNIT_CHOICES = [
    (VOLUME_UNIT_ML, _("mL")),
    (VOLUME_UNIT_OZ, _("fl oz")),
]

# Mass (weight)
WEIGHT_UNIT_KG = "kg"
WEIGHT_UNIT_LB = "lb"
WEIGHT_UNIT_CHOICES = [
    (WEIGHT_UNIT_KG, _("kg")),
    (WEIGHT_UNIT_LB, _("lb")),
]

# Length (height, head circumference)
HEIGHT_UNIT_CM = "cm"
HEIGHT_UNIT_IN = "in"
HEIGHT_UNIT_CHOICES = [
    (HEIGHT_UNIT_CM, _("cm")),
    (HEIGHT_UNIT_IN, _("in")),
]

# Temperature
TEMP_UNIT_C = "c"
TEMP_UNIT_F = "f"
TEMP_UNIT_CHOICES = [
    (TEMP_UNIT_C, _("°C")),
    (TEMP_UNIT_F, _("°F")),
]

# Diaper amount (solid content by weight)
DIAPER_UNIT_G = "g"
DIAPER_UNIT_OZ = "oz"
DIAPER_UNIT_CHOICES = [
    (DIAPER_UNIT_G, _("g")),
    (DIAPER_UNIT_OZ, _("oz")),
]

# Maps the site default_unit_system setting to per-field defaults.
METRIC_DEFAULTS = {
    "volume": VOLUME_UNIT_ML,
    "weight": WEIGHT_UNIT_KG,
    "height": HEIGHT_UNIT_CM,
    "temperature": TEMP_UNIT_C,
    "diaper": DIAPER_UNIT_G,
}

US_CUSTOMARY_DEFAULTS = {
    "volume": VOLUME_UNIT_OZ,
    "weight": WEIGHT_UNIT_LB,
    "height": HEIGHT_UNIT_IN,
    "temperature": TEMP_UNIT_F,
    "diaper": DIAPER_UNIT_OZ,
}


def get_default_unit(field_type: str) -> str:
    """Return the default unit for field_type based on the site measurement setting."""
    from babybuddy.site_settings import measurement_settings

    system = getattr(measurement_settings, "default_unit_system", None) or "metric"
    defaults = US_CUSTOMARY_DEFAULTS if system == "us_customary" else METRIC_DEFAULTS
    return defaults[field_type]


# ---------------------------------------------------------------------------
# Conversion helpers — convert value FROM `from_unit` TO `to_unit`.
# All functions return float. Callers round for display.
# ---------------------------------------------------------------------------


def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between mL and fl oz."""
    if from_unit == to_unit:
        return value
    if from_unit == VOLUME_UNIT_ML and to_unit == VOLUME_UNIT_OZ:
        return value / 29.5735
    if from_unit == VOLUME_UNIT_OZ and to_unit == VOLUME_UNIT_ML:
        return value * 29.5735
    raise ValueError(f"Unknown volume units: {from_unit!r} -> {to_unit!r}")


def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between kg and lb."""
    if from_unit == to_unit:
        return value
    if from_unit == WEIGHT_UNIT_KG and to_unit == WEIGHT_UNIT_LB:
        return value * 2.20462
    if from_unit == WEIGHT_UNIT_LB and to_unit == WEIGHT_UNIT_KG:
        return value / 2.20462
    raise ValueError(f"Unknown weight units: {from_unit!r} -> {to_unit!r}")


def convert_height(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between cm and inches."""
    if from_unit == to_unit:
        return value
    if from_unit == HEIGHT_UNIT_CM and to_unit == HEIGHT_UNIT_IN:
        return value / 2.54
    if from_unit == HEIGHT_UNIT_IN and to_unit == HEIGHT_UNIT_CM:
        return value * 2.54
    raise ValueError(f"Unknown height units: {from_unit!r} -> {to_unit!r}")


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between Celsius and Fahrenheit."""
    if from_unit == to_unit:
        return value
    if from_unit == TEMP_UNIT_C and to_unit == TEMP_UNIT_F:
        return value * 9 / 5 + 32
    if from_unit == TEMP_UNIT_F and to_unit == TEMP_UNIT_C:
        return (value - 32) * 5 / 9
    raise ValueError(f"Unknown temperature units: {from_unit!r} -> {to_unit!r}")


def convert_diaper(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between grams and ounces (weight)."""
    if from_unit == to_unit:
        return value
    if from_unit == DIAPER_UNIT_G and to_unit == DIAPER_UNIT_OZ:
        return value / 28.3495
    if from_unit == DIAPER_UNIT_OZ and to_unit == DIAPER_UNIT_G:
        return value * 28.3495
    raise ValueError(f"Unknown diaper units: {from_unit!r} -> {to_unit!r}")
