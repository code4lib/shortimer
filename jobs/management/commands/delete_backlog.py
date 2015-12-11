from django.utils import timezone
from django.core.management.base import BaseCommand

from shortimer.jobs import models

class Command(BaseCommand):

    def handle(self, *args, **options):
        jobs = models.Job.objects.filter(
            published__isnull=True, 
            deleted__isnull=True
        )
        for job in jobs:
            a = raw_input("%s: %s - Delete? [Y/n] " % (job.created, job.title))
            if a.lower() == "y" or a == "":
                job.deleted = timezone.now()
                job.save()

            
