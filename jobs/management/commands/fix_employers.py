from django.db.models import Count
from django.core.management.base import BaseCommand

from shortimer.jobs.models import Employer

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        slugs = Employer.objects.values("slug").annotate(Count("id"))
        for slug in slugs.order_by('id__count'):
            if slug['id__count'] == 1:
                continue

            employers = list(Employer.objects.filter(slug=slug['slug']))
            with_freebase_id = []
            without_freebase_id = []
            
            for employer in employers:
                if employer.freebase_id:
                    with_freebase_id.append(employer)
                else:
                    without_freebase_id.append(employer)

            if len(with_freebase_id) != 1:
                print "uncertain %s - %s" % (slug['slug'], with_freebase_id)
                continue

            e1 = with_freebase_id[0]
            for e2 in without_freebase_id:
                for job in e2.jobs.all():
                    print job
                    job.employer = e1
                    job.save()
                e2.delete()

            
