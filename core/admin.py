# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin, messages
from django.conf import settings
from django.db import models as db_models
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _

from import_export import fields, resources
from import_export.admin import ImportExportMixin, ExportActionMixin

from core import models
from core.units import (
    DIAPER_UNIT_CHOICES,
    HEIGHT_UNIT_CHOICES,
    TEMP_UNIT_CHOICES,
    VOLUME_UNIT_CHOICES,
    WEIGHT_UNIT_CHOICES,
    convert_diaper,
    convert_height,
    convert_temperature,
    convert_volume,
    convert_weight,
    get_default_unit,
)


class ImportExportResourceBase(resources.ModelResource):
    id = fields.Field(attribute="id")
    child = fields.Field(attribute="child_id", column_name="child_id")
    child_first_name = fields.Field(attribute="child__first_name", readonly=True)
    child_last_name = fields.Field(attribute="child__last_name", readonly=True)

    class Meta:
        clean_model_instances = True
        exclude = ("duration",)
        export_order = ("id", "child_id", "child_first_name", "child_last_name")


class BMIImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.BMI


@admin.register(models.BMI)
class BMIAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "bmi",
        "date",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "bmi",
    )
    resource_class = BMIImportExportResource


class ChildImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Child
        exclude = ("picture", "slug")


@admin.register(models.Child)
class ChildAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("first_name", "last_name", "birth_date", "birth_time", "slug")
    list_filter = ("last_name",)
    search_fields = ("first_name", "last_name", "birth_date")
    fields = ["first_name", "last_name", "birth_date", "birth_time"]
    if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
        fields.append("picture")
    resource_class = ChildImportExportResource


class PumpingImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Pumping


@admin.register(models.Pumping)
class PumpingAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "start",
        "end",
        "duration",
        "child",
        "amount",
        "amount_unit",
    )
    list_filter = ("child", "amount_unit")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "amount",
    )
    resource_class = PumpingImportExportResource


class DiaperChangeImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.DiaperChange


@admin.register(models.DiaperChange)
class DiaperChangeAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("child", "time", "wet", "solid", "color", "amount", "amount_unit")
    list_filter = ("child", "wet", "solid", "color", "amount_unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
    )
    resource_class = DiaperChangeImportExportResource


class FeedingImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Feeding


@admin.register(models.Feeding)
class FeedingAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "start",
        "end",
        "duration",
        "child",
        "type",
        "method",
        "amount",
        "amount_unit",
    )
    list_filter = (
        "child",
        "type",
        "method",
        "amount_unit",
        "tags",
    )
    search_fields = (
        "child__first_name",
        "child__last_name",
        "type",
        "method",
    )
    resource_class = FeedingImportExportResource


class HeadCircumferenceImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.HeadCircumference


@admin.register(models.HeadCircumference)
class HeadCircumferenceAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "head_circumference",
        "unit",
        "date",
    )
    list_filter = ("child", "unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "head_circumference",
    )
    resource_class = HeadCircumferenceImportExportResource


class HeightImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Height


@admin.register(models.Height)
class HeightAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "height",
        "unit",
        "date",
    )
    list_filter = ("child", "unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "height",
    )
    resource_class = HeightImportExportResource


class MedicationImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Medication


@admin.register(models.Medication)
class MedicationAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "time",
        "child",
        "name",
        "dosage",
        "dosage_unit",
    )
    list_filter = ("child", "dosage_unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "name",
    )
    resource_class = MedicationImportExportResource


class NoteImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Note
        exclude = ("image",)


@admin.register(models.Note)
class NoteAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "time",
        "child",
        "note",
    )
    list_filter = ("child", "tags")
    search_fields = ("child__last_name",)
    resource_class = NoteImportExportResource


class SleepImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Sleep


@admin.register(models.Sleep)
class SleepAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("start", "end", "duration", "child", "nap")
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
    )
    resource_class = SleepImportExportResource


class TemperatureImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Temperature


@admin.register(models.Temperature)
class TemperatureAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "temperature",
        "temperature_unit",
        "time",
    )
    list_filter = ("child", "temperature_unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "temperature",
    )
    resource_class = TemperatureImportExportResource


@admin.register(models.Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ("name", "child", "start", "duration", "user")
    list_filter = ("child", "user")
    search_fields = ("child__first_name", "child__last_name", "name", "user")


class TummyTimeImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.TummyTime


@admin.register(models.TummyTime)
class TummyTimeAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "start",
        "end",
        "duration",
        "child",
        "milestone",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "milestone",
    )
    resource_class = TummyTimeImportExportResource


class WeightImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Weight


@admin.register(models.Weight)
class WeightAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "weight",
        "weight_unit",
        "date",
    )
    list_filter = ("child", "weight_unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "weight",
    )
    resource_class = WeightImportExportResource


class TaggedItemInline(admin.StackedInline):
    model = models.Tagged


class TagImportExportResource(resources.ModelResource):
    id = fields.Field(attribute="id")

    class Meta:
        model = models.Tag
        exclude = ("slug", "last_used")


@admin.register(models.Tag)
class TagAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "color", "last_used")
    ordering = ("name", "slug")
    search_fields = ("name", "color")
    prepopulated_fields = {"slug": ["name"]}
    resource_class = TagImportExportResource


# ---------------------------------------------------------------------------
# Unit migration tool
# ---------------------------------------------------------------------------

# Describes each measurement field that can have legacy unitless data.
_UNIT_MIGRATION_FIELDS = [
    {
        "label": _("Feeding amount"),
        "model": models.Feeding,
        "value_field": "amount",
        "unit_field": "amount_unit",
        "choices": VOLUME_UNIT_CHOICES,
        "convert_fn": convert_volume,
        "unit_type": "volume",
    },
    {
        "label": _("Pumping amount"),
        "model": models.Pumping,
        "value_field": "amount",
        "unit_field": "amount_unit",
        "choices": VOLUME_UNIT_CHOICES,
        "convert_fn": convert_volume,
        "unit_type": "volume",
    },
    {
        "label": _("Weight"),
        "model": models.Weight,
        "value_field": "weight",
        "unit_field": "weight_unit",
        "choices": WEIGHT_UNIT_CHOICES,
        "convert_fn": convert_weight,
        "unit_type": "weight",
    },
    {
        "label": _("Height"),
        "model": models.Height,
        "value_field": "height",
        "unit_field": "unit",
        "choices": HEIGHT_UNIT_CHOICES,
        "convert_fn": convert_height,
        "unit_type": "height",
    },
    {
        "label": _("Head Circumference"),
        "model": models.HeadCircumference,
        "value_field": "head_circumference",
        "unit_field": "unit",
        "choices": HEIGHT_UNIT_CHOICES,
        "convert_fn": convert_height,
        "unit_type": "height",
    },
    {
        "label": _("Temperature"),
        "model": models.Temperature,
        "value_field": "temperature",
        "unit_field": "temperature_unit",
        "choices": TEMP_UNIT_CHOICES,
        "convert_fn": convert_temperature,
        "unit_type": "temperature",
    },
    {
        "label": _("Diaper change amount"),
        "model": models.DiaperChange,
        "value_field": "amount",
        "unit_field": "amount_unit",
        "choices": DIAPER_UNIT_CHOICES,
        "convert_fn": convert_diaper,
        "unit_type": "diaper",
    },
]


class _UnitMigrationRowForm(forms.Form):
    """One row in the migration form for a single measurement field."""

    enabled = forms.BooleanField(required=False)
    unit = forms.ChoiceField(required=False)
    convert = forms.BooleanField(
        required=False,
        label=_("Convert existing values to site default unit"),
        help_text=_(
            "If checked, stored numeric values will be multiplied/divided so they "
            "remain correct after the unit label is changed."
        ),
    )

    def __init__(self, *args, choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit"].choices = choices


class UnitMigrationProxy(db_models.Model):
    """Non-DB proxy used only to register the unit migration admin page."""

    class Meta:
        managed = False
        app_label = "core"
        verbose_name = _("Unit Migration")
        verbose_name_plural = _("Unit Migration")


@admin.register(UnitMigrationProxy)
class UnitMigrationAdmin(admin.ModelAdmin):
    def get_urls(self):
        return [
            path(
                "",
                self.admin_site.admin_view(self.migration_view),
                name="core_unitmigrationproxy_changelist",
            ),
        ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def migration_view(self, request):
        rows = []
        for spec in _UNIT_MIGRATION_FIELDS:
            blank_count = (
                spec["model"]
                .objects.filter(**{spec["unit_field"]: ""})
                .count()
            )
            form_prefix = spec["model"].__name__.lower() + "_" + spec["unit_field"]
            form = _UnitMigrationRowForm(
                request.POST if request.method == "POST" else None,
                prefix=form_prefix,
                choices=spec["choices"],
            )
            rows.append(
                {
                    "spec": spec,
                    "blank_count": blank_count,
                    "form": form,
                    "prefix": form_prefix,
                }
            )

        if request.method == "POST" and all(r["form"].is_valid() for r in rows):
            total_updated = 0
            for row in rows:
                data = row["form"].cleaned_data
                if not data.get("enabled"):
                    continue
                chosen_unit = data["unit"]
                if not chosen_unit:
                    continue
                spec = row["spec"]
                default_unit = get_default_unit(spec["unit_type"])
                should_convert = data.get("convert") and chosen_unit != default_unit

                qs = spec["model"].objects.filter(**{spec["unit_field"]: ""})
                if spec["value_field"] == "amount":
                    qs = qs.filter(amount__isnull=False)

                updated = 0
                for instance in qs:
                    if should_convert:
                        old_val = getattr(instance, spec["value_field"])
                        if old_val is not None:
                            new_val = spec["convert_fn"](old_val, chosen_unit, default_unit)
                            setattr(instance, spec["value_field"], new_val)
                    setattr(instance, spec["unit_field"], chosen_unit if not should_convert else default_unit)
                    instance.save(update_fields=[spec["value_field"], spec["unit_field"]] if should_convert else [spec["unit_field"]])
                    updated += 1

                # Also set unit for nullable-amount entries (no value conversion needed)
                if spec["value_field"] == "amount":
                    null_updated = (
                        spec["model"]
                        .objects.filter(**{spec["unit_field"]: ""})
                        .update(**{spec["unit_field"]: chosen_unit if not should_convert else default_unit})
                    )
                    updated += null_updated

                total_updated += updated

            messages.success(
                request,
                _("Migration complete. %(n)d entries updated.") % {"n": total_updated},
            )
            return redirect("admin:core_unitmigrationproxy_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": _("Migrate Legacy Unit Data"),
            "rows": rows,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/core/unit_migration.html",
            context,
        )
