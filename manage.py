#!/usr/bin/env python
import os
import sys
import uuid

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rpg.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Test")
    os.environ.setdefault("DJANGO_SECRET_KEY", str(uuid.uuid4()))
    try:
        # from django.core.management import execute_from_command_line
        from configurations.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
