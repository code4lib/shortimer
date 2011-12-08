# Create your views here.

from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse

from jobs import models

def home(request):
    jobs = models.Job.objects.all().order_by('-post_date')
    return render(request, 'home.html', {'jobs': jobs})

def job(request, id):
    j = get_object_or_404(models.Job, id=id)
    return render(request, "job.html", {"job": j})

def matcher(request):
    return render(request, "matcher.html", {"keywords": _kw()})

def matcher_table(request):
    return render(request, "matcher_table.html", {"keywords": _kw()})

def keyword(request, id):
    k = get_object_or_404(models.Keyword, id=id)
    if request.method == 'POST':
        if request.POST.get('ignore'):
            k.ignore = True
        elif request.POST.get('unlink'):
            k.subject = None
        k.save()
    return render(request, "keyword.html", {"keyword": k})

def subjects(request):

    # adding a new subject
    if request.method == "POST":
        s, created = models.Subject.objects.get_or_create(
            name=request.POST.get('subjectName')
        )
        s.type=request.POST.get('subjectTypeName')
        s.freebase_id=request.POST.get('subjectId')
        s.freebase_type_id=request.POST.get('subjectTypeId')

        kw = models.Keyword.objects.get(id=request.POST.get('keywordId'))
        s.keywords.add(kw)
        s.save()
        return redirect(reverse('subject', args=[s.slug]))

    subjects = models.Subject.objects.all()
    return render(request, "subjects.html", {"subjects": subjects})

def subject(request, slug):
    s = get_object_or_404(models.Subject, slug=slug)
    j = models.Job.objects.filter(keywords__subject=s)
    j = j.order_by('-post_date')
    return render(request, "subject.html", {"subject": s, "jobs": j})

def _kw():
    kw = models.Keyword.objects.all()
    kw = kw.annotate(num_jobs=Count("jobs"))
    kw = kw.filter(num_jobs__gt=1, ignore=False)
    return kw.order_by("-num_jobs")
