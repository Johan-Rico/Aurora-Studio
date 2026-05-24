from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aurora_studio.settings')

try:
	from celery import Celery

	app = Celery('aurora_studio')
	app.config_from_object('django.conf:settings', namespace='CELERY')
	app.autodiscover_tasks()
except Exception:  # pragma: no cover - celery may be missing in minimal env
	app = None

__all__ = ('app',)
