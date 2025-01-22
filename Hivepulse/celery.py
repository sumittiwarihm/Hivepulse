from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hivepulse.settings')
# Create the Celery app
app = Celery('Hivepulse')

# Load configuration from Django settings with the 'CELERY_' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in installed apps
app.autodiscover_tasks()

# Worker-specific configurations
app.conf.update(
    broker_url='amqp://guest:guest@127.0.0.1:5672//',
    # this warning i got because of that i added this
    broker_connection_retry_on_startup = True,
    worker_pool='threads',
    worker_concurrency=4,  # Number of worker processes
    worker_prefetch_multiplier=1,  # Number of tasks a worker can prefetch
    task_acks_late=True,  # Acknowledge tasks after completion
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Import and register tasks explicitly (optional, for clarity)
# from platforms.task import factorial_task, fibonacci , fetch_flipkart_reviews
