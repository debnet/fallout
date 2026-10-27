# coding: utf-8
"""Django management entry point, importable before the project's Celery setup."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rpg.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Test")
    from configurations.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
