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
            with_city = []
            without_city = []
            
            for employer in employers:

                if employer.freebase_id.startswith("/en/"):
                    with_freebase_id.append(employer)
                else:
                    without_freebase_id.append(employer)

                if employer.city:
                    with_city.append(employer)
                else:
                    without_city.append(employer)

            if len(with_freebase_id) > 1 and len(with_city) == 1:
                fix(with_city[0], without_city)

            elif len(with_freebase_id) == 1:
                fix(with_freebase_id[0], without_freebase_id)

def fix(good_employer, bad_employers):
    for bad_employer in bad_employers:
        for job in bad_employer.jobs.all():
            print  "rewiring %s to %s" % (job, good_employer)
            job.employer = good_employer
            job.save()
        bad_employer.delete()
        print "deleting: %s" % bad_employer


            
