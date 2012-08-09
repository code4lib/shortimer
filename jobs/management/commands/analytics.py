from django.conf import settings
from django.core.management.base import BaseCommand

from shortimer.jobs import analytics

class Command(BaseCommand):
    """Updates web analytics stats using Google Analytics API.
    """

    def handle(self, *args, **options):
        analytics.update()

