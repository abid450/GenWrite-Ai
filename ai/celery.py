import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai.settings')

app = Celery('ai')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Debug Task --------------------------------------------------------
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return f'Task executed successfully with id: {self.request.id}'



# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'apps.content.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {
            'expires': 3600,
        },
    },
    'reset-daily-limits': {
        'task': 'apps.accounts.tasks.reset_daily_limits',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },

    'send-daily-report': {
        'task': 'apps.accounts.tasks.send_daily_report',
        'schedule': crontab(hour=9, minute=0),  # Daily at 09:00
        'options': {
            'expires': 1800,  # 30 minutes
        }
    },

    'retry-failed-tasks': {
        'task': 'apps.content.tasks.retry_failed_tasks',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}


# Task routes (বিভিন্ন queue তে পাঠানোর জন্য)
app.conf.task_routes = {
    'apps.content.tasks.generate_content_task': {'queue': 'high_priority'},
    'apps.content.tasks.bulk_generate_content': {'queue': 'batch_queue'},
    'apps.accounts.tasks.send_email': {'queue': 'email_queue'},
}

# Task time limits
app.conf.task_time_limit = 120  # 2 minutes
app.conf.task_soft_time_limit = 90  # 1.5 minutes

# Task result expiry
app.conf.result_expires = 3600  # 1 hour

# Task compression
app.conf.task_compression = 'gzip'
app.conf.result_compression = 'gzip'
