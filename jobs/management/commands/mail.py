import re
import logging
import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from shortimer.jobs.models import Job

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "send an email digest of new jobs"

    def handle(self, *args, **options):

        # get all jobs that have been published are not deleted
        # and have not been emailed

        jobs = Job.objects.filter(published__isnull=False,
                                  deleted__isnull=True,
                                  post_date__isnull=True)

        if len(jobs) == 0:
            return

        lines = []
        a = lines.append
        for job in jobs:
            a(job.title.strip())
            a("  " + job.employer.name.strip())
            a("  " + job.display_location())
            a("  " + ', '.join([s.name for s in job.subjects.all()]))
            a("  " + "http://jobs.code4lib.org/job/%s" % job.id)
            a("")

        a("To post a new job please visit http://jobs.code4lib.org/")
        body = "\r\n".join(lines)

        today = datetime.date.today().strftime("%Y-%m-%d")

        if len(jobs) == 1:
            subject = "JOBS: %s new job for %s" % (len(jobs), today)
        else:
            subject = "JOBS: %s new jobs for %s" % (len(jobs), today)

        send_mail(subject, body, settings.EMAIL_HOST_USER, settings.EMAIL_ANNOUNCE)

        # if everything went well we can mark the jobs as having been emailed
        for job in jobs:
            job.post_date = datetime.datetime.now()
            job.save()
