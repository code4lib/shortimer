from django.conf import settings
from django.core.management.base import BaseCommand

from shortimer.jobs import analytics

class Command(BaseCommand):

    def handle(self, *args, **options):
        analytics.update()

