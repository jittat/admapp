#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admapp.settings")

    # Run management commands (createsuperuser, migrate, ...) in English by
    # default. Commands that exercise the served site keep its own default
    # language (LANGUAGE_CODE): the dev servers and the test runner are excluded
    # here, and production serves via wsgi.py which never sets this. Override for
    # a single run with ADMAPP_LANGUAGE_CODE=th.
    if not {"runserver", "testserver", "test"}.intersection(sys.argv):
        os.environ.setdefault("ADMAPP_LANGUAGE_CODE", "en")

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
