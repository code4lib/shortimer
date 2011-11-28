# Create your views here.

from django.db.models import Count
from django.shortcuts import render, get_object_or_404

from jobs import models

def keywords(request):
    return render(request, "keywords.html", {"keywords": _kw()})

def keywords_table(request):
    return render(request, "keywords_table.html", {"keywords": _kw()})

def keyword(request, id):
    k = get_object_or_404(models.Keyword, id=id)
    if request.method == 'POST':
        k.ignore = True
        k.save()
    return render(request, "keyword.html", {"keyword": k})

def tags(request):
    if request.method == "POST":
        pass
    tags = models.Tag.objects.all()
    return render(request, "tags.html", {"tags": tags})

def tag(request, id):
    t = get_object_or_404(models.Tag, slug=slug)
    return render(request, "tag.html", {"tag": tag})

def _kw():
    k = models.Keyword.objects.all()
    k = k.annotate(num_jobs=Count("jobs"))
    k = k.filter(num_jobs__gt=1, ignore=False)
    return k.order_by("-num_jobs")

