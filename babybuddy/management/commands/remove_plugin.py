# -*- coding: utf-8 -*-
"""
Management command for cleanly removing a Baby Buddy plugin.

Usage:
    python manage.py remove_plugin <app_label>

This command:
1. Rolls back all of the plugin's migrations (dropping its tables)
2. Removes its entries from django_migrations so no stale history remains

Run this BEFORE uninstalling the plugin package or removing it from
INSTALLED_APPS. After running it you can safely uninstall/remove the plugin
and restart Baby Buddy with a clean database state.

Example (removing the books plugin):
    python manage.py remove_plugin books
    pip uninstall django-babybuddy-books
"""
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Cleanly remove a Baby Buddy plugin: rolls back migrations and clears migration history."

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            help="The app_label of the plugin to remove (e.g. 'books').",
        )
        parser.add_argument(
            "--no-input",
            "--noinput",
            action="store_false",
            dest="interactive",
            help="Do not prompt for confirmation.",
        )

    def handle(self, *args, **options):
        app_label = options["app_label"]
        interactive = options["interactive"]

        # Confirm the app is actually installed
        from django.apps import apps

        if not apps.is_installed(app_label) and not self._has_migration_history(app_label):
            raise CommandError(
                f"No app with label '{app_label}' is installed and no migration "
                f"history found. Nothing to remove."
            )

        if interactive:
            self.stdout.write(
                self.style.WARNING(
                    f"\nThis will roll back ALL migrations for '{app_label}', "
                    f"permanently deleting its database tables and data.\n"
                )
            )
            confirm = input("Are you sure? Type the app label to confirm: ")
            if confirm.strip() != app_label:
                self.stdout.write("Aborted.")
                sys.exit(1)

        # Step 1: roll back all migrations (drops tables)
        if apps.is_installed(app_label):
            self.stdout.write(f"Rolling back migrations for '{app_label}'...")
            try:
                call_command("migrate", app_label, "zero", verbosity=1, interactive=False)
            except Exception as exc:
                raise CommandError(f"Migration rollback failed: {exc}") from exc
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"App '{app_label}' is not in INSTALLED_APPS — skipping migration "
                    f"rollback (tables may still exist in the database)."
                )
            )

        # Step 2: remove stale migration history entries
        removed = self._clear_migration_history(app_label)
        if removed:
            self.stdout.write(
                f"Removed {removed} migration history record(s) for '{app_label}'."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nPlugin '{app_label}' removed cleanly.\n"
                f"You can now uninstall the package and restart Baby Buddy."
            )
        )

    def _has_migration_history(self, app_label):
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations WHERE app = %s",
                    [app_label],
                )
                return cursor.fetchone()[0] > 0
            except Exception:
                return False

    def _clear_migration_history(self, app_label):
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "DELETE FROM django_migrations WHERE app = %s", [app_label]
                )
                return cursor.rowcount
            except Exception:
                return 0
