import os
import sys


def bootstrap():
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(), '..'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admapp.settings")

    import django
    django.setup()
