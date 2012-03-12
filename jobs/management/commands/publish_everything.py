from datetime import datetime

from django.core.management.base import BaseCommand

from shortimer.jobs.models import Job

class Command(BaseCommand):

    def handle(self, *args, **options):
        for job in Job.objects.all():
            if not job.published:
                job.published = datetime.now()
                job.save()

