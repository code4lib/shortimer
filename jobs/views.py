import re
import json
import smtplib
import datetime

from django.http import Http404
from django.contrib import auth
from django.conf import settings
from django.db.models import Count
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.template import RequestContext
from django.core.paginator import EmptyPage
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseGone, HttpResponseNotFound
from django.shortcuts import render, render_to_response, get_object_or_404, redirect


from shortimer.jobs import models
from shortimer.miner import autotag
from shortimer.paginator import DiggPaginator
from shortimer.jobs.decorators import AllowJSONPCallback

def about(request):
    return render(request, 'about.html')

def login(request):
    if request.user.is_authenticated():
        logout(request)
    next = request.GET.get('next', '')
    return render(request, 'login.html', {'next': next})

def logout(request):
    auth.logout(request)
    return redirect('/')

def jobs(request, subject_slug=None):
    jobs = models.Job.objects.filter(published__isnull=False, deleted__isnull=True)
    jobs = jobs.order_by('-published')

    # filter by subject if we were given one
    if subject_slug:
        subject = get_object_or_404(models.Subject, slug=subject_slug)
        jobs = jobs.filter(subjects__in=[subject])
        feed_url = "http://" + request.META['HTTP_HOST'] + reverse('feed_tag', args=[subject.slug])
        feed_title = 'code4lib jobs feed - %s' % subject.name
    else: 
        feed_url = "http://" + request.META['HTTP_HOST'] + reverse('feed')
        feed_title = 'code4lib jobs feed'
        subject = None

    paginator = DiggPaginator(jobs, 20, body=8)
    try:
        page = paginator.page(int(request.GET.get("page", 1)))
    except ValueError:
        raise Http404
    except EmptyPage:
        raise Http404 

    context = {
        'jobs': page.object_list,
        'page': page,
        'paginator': paginator,
        'subject': subject,
        'feed_url': feed_url, 
        'feed_title': feed_title
    }
    return render(request, 'jobs.html', context)

def feed(request, tag=None, page=1):
    jobs = models.Job.objects.filter(published__isnull=False, deleted__isnull=True)
    title = "code4lib jobs feed"
    feed_url = "http://" + request.META['HTTP_HOST'] + reverse('feed')
    subject = None
    if tag:
        subject = get_object_or_404(models.Subject, slug=tag)
        jobs = jobs.filter(subjects__in=[subject])
        title = "code4lib jobs feed - %s" % subject.name 
        feed_url = "http://" + request.META['HTTP_HOST'] + reverse('feed_tag', args=[tag])

    jobs = jobs.order_by('-published')
    if jobs.count() == 0: raise Http404
    updated = jobs[0].updated

    paginator = DiggPaginator(jobs, 50, body=8)
    try: 
        page = paginator.page(page)
    except EmptyPage:
        raise Http404

    return render_to_response('feed.xml', 
                              {
                                  "subject": subject,
                                  "page": page, 
                                  "updated": updated, 
                              }, 
                              mimetype="application/atom+xml",
                              context_instance=RequestContext(request))

def job(request, id):
    j = get_object_or_404(models.Job, id=id)
    if j.deleted: 
        return HttpResponseGone("Sorry, this job has been deleted.")
    return render(request, "job.html", {"job": j})

@login_required
def job_edit(request, id=None):
    if id:
        j = get_object_or_404(models.Job, id=id)
    else:
        j = models.Job(creator=request.user)

    can_edit_description = _can_edit_description(request.user, j)

    if request.method == "GET":
        context = {"job": j, 
                   "curate_next": request.path == "/curate/employers/",
                   "can_edit_description": can_edit_description, 
                   "error": request.session.pop("error", None),
                   "job_types": models.JOB_TYPES,
                   "google_api_key": settings.GOOGLE_API_KEY}
        return render(request, "job_edit.html", context)

    form = request.POST
    if form.get("action") == "view" and j.id:
        return redirect(reverse('job', args=[j.id]))

    _update_job(j, form, request.user)

    if form.get("action") == "autotag":
        autotag(j)

    if form.get("action") == "delete" and not j.published:
        j.deleted = datetime.datetime.now()
        j.save()

    if form.get("action") == "publish":
        publishable, msg = j.publishable()
        if not publishable:
            request.session['error'] = 'Cannot publish yet: %s' % msg
        else:
            j.publish(request.user)

    if request.path.startswith("/curate/"):
        return redirect(request.path)

    if j and not j.deleted:
        return redirect(reverse('job_edit', args=[j.id]))

    return redirect("/") # job was deleted

def _update_job(j, form, user):
    j.title = form.get("title")
    j.url = form.get("url")
    j.contact_name = form.get("contact_name")
    j.contact_email = form.get("contact_email")
    j.job_type = form.get("job_type")
    j.telecommute = True if form.get("telecommute") == "yes" else False

    # set employer: when an employer is first added this save triggers
    # a lookup to Freebase to get hq address information
    if form.get("employer", None):
        e, created = models.Employer.objects.get_or_create(
            name=form.get("employer"),
            freebase_id=form.get("employer_freebase_id"))
        j.employer = e

    # set location: when a location is first added this save triggers
    # a lookup to Freebase to get geo-coordinates
    if form.get("location", None):
        l, created = models.Location.objects.get_or_create(
            name=form.get("location"),
            freebase_id=form.get("location_freebase_id"))
        j.location = l

    # only people flagged as staff can edit the job text
    if _can_edit_description(user, j):
        j.description = form.get('description')

    j.save()

    # update subjects
    j.subjects.clear()
    for k in form.keys():
        m = re.match('^subject_(\d+)$', k)
        if not m: continue

        name = form.get(k)
        if not name: continue

        fb_id = form.get("subject_freebase_id_" + m.group(1))
        slug = slugify(name)

        try:
            s = models.Subject.objects.get(slug=slug)
        except models.Subject.DoesNotExist:
            s = models.Subject.objects.create(name=name, freebase_id=fb_id, slug=slug)
        finally:
            j.subjects.add(s)

    # record the edit
    models.JobEdit.objects.create(job=j, user=user)

def user(request, username):
    user = get_object_or_404(auth.models.User, username=username)
    can_edit = request.user.is_authenticated() and user == request.user
    recent_edits = user.edits.all()[0:15]
    return render(request, "user.html", {"user": user, "can_edit": can_edit,
                                         "recent_edits": recent_edits})

def users(request):
    users = auth.models.User.objects.all()
    users = users.annotate(count=Count('edits'))
    users = users.order_by('-count')

    paginator = DiggPaginator(users, 25, body=8)
    try:
        page = paginator.page(int(request.GET.get("page", 1)))
    except ValueError:
        raise Http404
    except EmptyPage:
        raise Http404 
    page = paginator.page(request.GET.get("page", 1))
    return render(request, "users.html", 
            {"paginator": paginator, "page": page})

@login_required
def profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        user.username = request.POST.get("username", user.username)
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.profile.home_url = request.POST.get("home_url")
        user.save()
        user.profile.save()
        return redirect(reverse('user', args=[user.username]))

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

def tags(request):
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

    subjects = models.Subject.objects.filter(jobs__deleted__isnull=True)
    subjects = subjects.annotate(num_jobs=Count("jobs"))
    subjects = subjects.filter(num_jobs__gt=0)
    subjects = subjects.order_by("-num_jobs")
    paginator = DiggPaginator(subjects, 25, body=8)
    try:
        page = paginator.page(int(request.GET.get("page", 1)))
    except ValueError:
        raise Http404
    except EmptyPage:
        raise Http404
    context = {
        "paginator": paginator,
        "page": page
        }
    return render(request, "tags.html", context)

def employers(request):
    employers = models.Employer.objects.all()
    employers = employers.annotate(num_jobs=Count("jobs"))
    employers = employers.filter(num_jobs__gt=0)
    employers = employers.order_by("-num_jobs")
    paginator = DiggPaginator(employers, 25, body=8)
    try:
        page = paginator.page(int(request.GET.get("page", 1)))
    except ValueError:
        raise Http404
    except EmptyPage:
        raise Http404
    context = {
        "paginator": paginator,
        "page": page,
    }
    return render(request, "employers.html", context)

def employer(request, employer_slug):
    employer = get_object_or_404(models.Employer, slug=employer_slug)
    return render(request, "employer.html", {"employer": employer})

def curate(request):
    need_employer = models.Job.objects.filter(employer__isnull=True, deleted__isnull=True).count()
    need_publish = models.Job.objects.filter(published__isnull=True, deleted__isnull=True).count()
    return render(request, "curate.html", {"need_employer": need_employer,
                                           "need_publish": need_publish})

@login_required
def curate_employers(request):
    if request.method == "POST":
        return job_edit(request, request.POST.get('job_id'))

    # get latest job that lacks an employer
    jobs = models.Job.objects.filter(employer__isnull=True, deleted__isnull=True)
    jobs = jobs.order_by('-post_date')
    if jobs.count() == 0:
        return redirect(reverse('curate'))
    job = jobs[0]
    return job_edit(request, job.id)

@login_required
def curate_drafts(request):
    if request.method == "POST":
        return job_edit(request, request.POST.get('job_id'))

    # get latest un-published job
    jobs = models.Job.objects.filter(published__isnull=True, deleted__isnull=True)
    jobs = jobs.order_by('-post_date')
    if jobs.count() == 0:
        return redirect(reverse('curate'))
    job = jobs[0]
    return job_edit(request, job.id)

def reports(request):
    now = datetime.datetime.now()
    m = now - datetime.timedelta(days=31)
    w = now - datetime.timedelta(days=7)
    y = now - datetime.timedelta(days=365)

    hotjobs_m = models.Job.objects.filter(post_date__gte=m, deleted__isnull=True)
    hotjobs_m = hotjobs_m.order_by('-page_views')[0:10]

    hotjobs_w = models.Job.objects.filter(post_date__gte=w, deleted__isnull=True)
    hotjobs_w = hotjobs_w.order_by('-page_views')[0:10]

    subjects_m = models.Subject.objects.filter(jobs__post_date__gte=m, jobs__deleted__isnull=True)
    subjects_m = subjects_m.annotate(num_jobs=Count("jobs"))
    subjects_m = subjects_m.order_by("-num_jobs")
    subjects_m = subjects_m[0:10]

    subjects_y = models.Subject.objects.filter(jobs__post_date__gte=y, jobs__deleted__isnull=True)
    subjects_y = subjects_y.annotate(num_jobs=Count("jobs"))
    subjects_y = subjects_y.order_by("-num_jobs")
    subjects_y = subjects_y[0:10]

    employers_m = models.Employer.objects.filter(jobs__post_date__gte=m, jobs__deleted__isnull=True)
    employers_m = employers_m.annotate(num_jobs=Count("jobs"))
    employers_m = employers_m.order_by("-num_jobs")
    employers_m = employers_m[0:10]

    employers_y = models.Employer.objects.filter(jobs__post_date__gte=y, jobs__deleted__isnull=True)
    employers_y = employers_y.annotate(num_jobs=Count("jobs"))
    employers_y = employers_y.order_by("-num_jobs")
    employers_y = employers_y[0:10]

    return render(request, 'reports.html', {"subjects_m": subjects_m,
                                            "subjects_y": subjects_y,
                                            "employers_m": employers_m,
                                            "employers_y": employers_y,
                                            "hotjobs_w": hotjobs_w,
                                            "hotjobs_m": hotjobs_m})

# bits of an API as needed, might be nice to rationalize this at some point

@AllowJSONPCallback
def guess_location(request):
    """guess location of the job based on the employer's headquarters
    """
    freebase_id = request.GET.get("freebase_id", None)
    employer = models.Employer(freebase_id=freebase_id)
    location = employer.guess_location()
    if location:
        result = {"name": location.name, "freebase_id": location.freebase_id}
    else:
        result = None
    return HttpResponse(json.dumps(result), mimetype="application/json")

@AllowJSONPCallback
def recent_jobs(request):
    freebase_id = request.GET.get("freebase_id", None)
    jobs = models.Job.objects.filter(published__isnull=False).order_by('-created')
    result = {'jobs': []}
    if freebase_id:
        jobs = jobs.filter(employer__freebase_id=freebase_id)

    for job in jobs[0:10]:
        result['jobs'].append({
            'title': job.title,
            'created': job.created.strftime('%Y-%m-%d'),
            'employer': job.employer.name,
            'url': _add_host(request, job.get_absolute_url())
        })

    return HttpResponse(json.dumps(result), mimetype="application/json")

def _can_edit_description(user, job):
    # only staff or the creator of a job posting can edit the text of the 
    # job description once it is posted
    if user.is_staff:
        return True
    elif job.creator == user:
        return True
    elif not job.published:
        return True
    else:
        return False

def map_jobs(request):
    return render(request, 'map_jobs.html')


@cache_control(max_age=60 * 60 * 24)
def map_data(request):
    # maybe this will be too expensive some day?
    geojson = {
        "type": "FeatureCollection",
        "features": [
        ]
    }
    for j in models.Job.objects.filter(location__latitude__isnull=False, location__longitude__isnull=False, post_date__isnull=False):
        feature = {
            "id": _add_host(request, j.get_absolute_url()),
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [j.location.longitude, j.location.latitude],
            },
            "properties": {
                "title": j.title,
                "employer": j.employer.name,
                "employer_url": _add_host(request, j.employer.get_absolute_url()),
                "created": j.post_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
        geojson['features'].append(feature)
    return HttpResponse(json.dumps(geojson), mimetype="application/json")


def search(request):
    return render_to_response('search.html')

def _add_host(request, url):
    return 'http://' + request.META['HTTP_HOST'] + url

