from django.core.management.base import BaseCommand

from shortimer.jobs import models

class Command(BaseCommand):

    def handle(self, *args, **options):
        for job in models.Job.objects.all():
            for kw in job.keywords.all():
                if kw.subject:
                    print job.title, " -> ", kw.subject
                    job.subjects.add(kw.subject)
            job.save()


