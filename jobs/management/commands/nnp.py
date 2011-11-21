from django.core.management.base import BaseCommand

from jobs.models import JobEmail

class Command(BaseCommand):

    def handle(self, *args, **options):
        for email in JobEmail.objects.all():
            for n in email.proper_nouns():
                print n.lower().encode('utf-8')
