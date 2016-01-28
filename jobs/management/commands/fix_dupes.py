from django.db.models import Count
from django.core.management.base import BaseCommand

from shortimer.jobs.models import Employer, Subject

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for klass in (Employer, Subject):
            fix(klass)

def fix(klass):
    slugs = klass.objects.values("slug").annotate(Count("id"))
    for slug in slugs.order_by('id__count'):
        if slug['id__count'] == 1:
            continue

        slug = slug['slug']

        objects = list(klass.objects.filter(slug=slug))
        guess = None
        for o in objects:
            jobs = o.jobs.all()
            print ("%s [%s] %s" % (o.name, o.id, jobs.count())).encode('utf8')
            if guess is None or jobs.count() > guess.jobs.all().count():
                guess = o

        print ("guess: %s [%s]" % (guess.name, guess.id)).encode('utf8')
        choice = raw_input("rewire? [y/n] ")
        if choice.lower() == "y" or choice == "":
            for o in objects:
                if o == guess:
                    continue

                for job in o.jobs.all():
                    if klass == Employer:
                        job.employer = guess
                        job.save()
                    elif klass == Subject:
                        job.subjects.remove(o)
                        job.subjects.add(guess)
                        job.save()
                    print ("rewrote %s [%s]" % (job.title, job.id)).encode('utf8')

                klass.objects.get(id=o.id).delete()
                print ("deleted %s [%s]" % (o.name, o.id))

        print


