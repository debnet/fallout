# coding: utf-8
# flake8: noqa
__all__ = []
__version__ = '2018.12.18'

try:
    # Get celery configuration
    from rpg.celery import app as celery_app
    __all__ = ['celery_app']
    # Apply monkey patchs
    import rpg.patch
except ImportError:
    # ImportError will only occurs when fetching version outside Django scope
    pass
