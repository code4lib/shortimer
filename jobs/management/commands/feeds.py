import re
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
import feedparser

from shortimer.miner import autotag
from shortimer.jobs.models import Job

log = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        for feed_url in settings.JOB_FEEDS:
            self.fetch(feed_url)

    def fetch(self, url):
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            description = entry.summary.replace("\n", " ")
            description = re.sub(r"[ \t]+", " ", description)
            url = entry.link

            if Job.objects.filter(origin_url=url).count() != 0:
                continue
            job = Job(title=title, description=description, origin_url=url, url=url)
            job.save()
            autotag(job)
            log.info("added job for review: %s" % job)
