from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opportunity_project.settings')

app = Celery('opportunity_project')
app.conf.enable_utc = False
app.conf.update(timezone='UTC')

app.config_from_object(settings, namespace='CELERY')
