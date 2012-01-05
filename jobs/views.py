# Create your views here.

from django.db.models import Count
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect

from jobs4lib.jobs import models
from jobs4lib.paginator import DiggPaginator

def login(request):
    return render(request, 'login.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

def jobs(request, subject_slug=None):
    jobs = models.Job.objects.all().order_by('-post_date')

    # filter by subject if we were given one
    if subject_slug:
        subject = get_object_or_404(models.Subject, slug=subject_slug)
        jobs = jobs.filter(subjects__in=[subject])
    else: 
        subject = None

    paginator = DiggPaginator(jobs, 20, body=8)
    page = paginator.page(request.GET.get("page", 1))

    context = {
        'jobs': page.object_list,
        'page': page,
        'paginator': paginator,
        'subject': subject,
    }
    return render(request, 'jobs.html', context)

def job(request, id):
    j = get_object_or_404(models.Job, id=id)
    return render(request, "job.html", {"job": j})

def user(request, username):
    user = get_object_or_404(auth.models.User, username=username)
    return render(request, "user.html", {"user": user})

@login_required
def profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.profile.home_url = request.POST.get("home_url")
        user.save()
        user.profile.save()
        return redirect(reverse('profile'))

    return render(request, "profile.html", {"user": user, "profile": profile})

def matcher(request):
    keywords = models.Keyword.objects.all()
    keywords = keywords.annotate(num_jobs=Count("jobs"))
    keywords = keywords.filter(num_jobs__gt=2, ignore=False, subject__isnull=True)
    keywords = keywords.order_by("-num_jobs")

    paginator = DiggPaginator(keywords, 25, body=8)
    page = paginator.page(request.GET.get("page", 1))
    if request.is_ajax():
        template = "matcher_table.html"
    else:
        template = "matcher.html"
    return render(request, template, {"page": page, "paginator": paginator})

def matcher_table(request):
    keywords = _kw()
    paginator = DiggPaginator(keywords, 25, body=8)
    page = paginator.page(request.GET.get("page", 1))
    return render(request, "matcher_table.html", {"page": page})

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
    # add a new subject
    if request.method == "POST":
        s, created = models.Subject.objects.get_or_create(
            name=request.POST.get('subjectName'))
        s.type=request.POST.get('subjectTypeName')
        s.freebase_id=request.POST.get('subjectId')
        s.freebase_type_id=request.POST.get('subjectTypeId')

        kw = models.Keyword.objects.get(id=request.POST.get('keywordId'))
        s.keywords.add(kw)
        s.save()
        return redirect(reverse('subject', args=[s.slug]))

    subjects = models.Subject.objects.all()
    paginator = DiggPaginator(subjects, 25, body=8)
    page = paginator.page(request.GET.get("page", 1))
    context = {
        "paginator": paginator,
        "page": page
        }
    return render(request, "subjects.html", context)

def subject(request, slug):
    s = get_object_or_404(models.Subject, slug=slug)
    j = models.Job.objects.filter(subjects__in=[s]).distinct()
    j = j.order_by('-post_date')
    return render(request, "subject.html", {"subject": s, "jobs": j})

