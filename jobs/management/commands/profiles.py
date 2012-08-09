import json

from django.conf import settings
from django.core.management.base import BaseCommand

from shortimer.jobs import analytics

class Command(BaseCommand):
    """prints out Google Analytics website profile names and ids to help you
    decide which profile ID to include in your settings file for collecting
    site stats.
    """

    def handle(self, *args, **options):
        for profile in analytics.profiles():
            print profile['name'], "ga:" + profile['id']

