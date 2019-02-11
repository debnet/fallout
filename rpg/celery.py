# coding: utf-8
import celery
import os
from configurations import importer


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rpg.settings')
os.environ.setdefault("DJANGO_CONFIGURATION", 'Prod')

# Load environment configuration
importer.install()

# Initialize Celery application
app = celery.Celery('fallout')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
