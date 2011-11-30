import re

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.template.defaultfilters import slugify

JOB_TYPES = (
    ('ft', 'full-time'), 
    ('pt', 'part-time'), 
    ('co', 'contract'),
    ('tm', 'temporary'), 
    ('in', 'internship'),
)

class Job(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    url = models.CharField(max_length=1024)
    post_date = models.DateTimeField()
    close_date = models.DateTimeField(null=True)
    contact_name = models.CharField(max_length=255)
    contact_email = models.CharField(max_length=255)
    telecommute = models.BooleanField(default=False)
    salary_start = models.IntegerField(null=True)
    salary_end = models.IntegerField(null=True)
    email_message_id = models.CharField(max_length=1024, null=True)
    job_type = models.CharField(max_length=2, choices=JOB_TYPES, default='ft')
    employer = models.ForeignKey('Employer', related_name='jobs', null=True)
    creator = models.ForeignKey(User, related_name='jobs', null=True)

    @property 
    def description_html(self):
        # add paragraphs
        html = "<p>" + self.description + "</p>"
        html = html.replace("\n\n", "</p>\n\n<p>")

        # hyperlinks known subjects
        for keyword in self.keywords.all():
            if keyword.subject:
                def subject_link(m):
                    url = reverse('subject', args=[keyword.subject.slug])
                    return '<a href="' + url + '">' + m.group(1) + '</a>'

                pattern = re.compile("(" + keyword.name +")", re.IGNORECASE)
                html = re.sub(pattern, subject_link, html)

        return html

    def __str__(self):
        return self.title

class Employer(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    domain = models.CharField(max_length=50)

class Keyword(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    jobs = models.ManyToManyField('Job', related_name='keywords')
    ignore = models.BooleanField(default=False)
    subject = models.ForeignKey('Subject', related_name='keywords', null=True)

class Subject(models.Model):
    name = models.CharField(max_length=500)
    slug = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    freebase_id = models.CharField(max_length=100)
    freebase_type_id = models.CharField(max_length=100)

    def freebase_image_url(self):
        url = "https://usercontent.googleapis.com/freebase/v1/image" 
        url += self.freebase_id
        url += "?maxwidth=400&maxheight=200"
        return url

    def freebase_url(self):
        base = "http://www.freebase.com/view"
        if self.freebase_id.startswith("/en"):
            return base + self.freebase_id
        else:
            return base + "/en" + self.freebase_id

    def freebase_type_url(self):
        return "http://www.freebase.com/view" + self.freebase_type_id



def make_slug(sender, **kwargs):
    i = kwargs['instance']
    i.slug = slugify(i.name)

pre_save.connect(make_slug, sender=Subject)
