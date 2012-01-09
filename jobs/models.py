# -*- coding: utf-8 -*-

import re

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify

from social_auth.signals import pre_update
from social_auth.backends.facebook import FacebookBackend
from social_auth.backends.twitter import TwitterBackend


JOB_TYPES = (
    ('ft', 'full-time'), 
    ('pt', 'part-time'), 
    ('co', 'contract'),
    ('tm', 'temporary'), 
    ('in', 'internship'),
)

# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
url_pattern = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')

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
        html = "<p>" + self.description + "</p>"
        html = html.replace("\n\n", "</p>\n\n<p>")
        html = re.sub(url_pattern, r'<a href="\1">\1</a>', html)
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
    ignore = models.BooleanField(default=False)
    subject = models.ForeignKey('Subject', related_name='keywords', null=True)

class Subject(models.Model):
    name = models.CharField(max_length=500)
    slug = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    freebase_id = models.CharField(max_length=100)
    freebase_type_id = models.CharField(max_length=100)
    jobs = models.ManyToManyField('Job', related_name='subjects', null=True)

    class Meta: 
        ordering = ['name']

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.freebase_id) 

    def freebase_image_url(self):
        url = "https://usercontent.googleapis.com/freebase/v1/image" 
        url += self.freebase_id
        url += "?maxwidth=400&maxheight=200"
        return url

    def freebase_url(self):
        return "http://www.freebase.com/view" + self.freebase_id
        base = "http://www.freebase.com/view"
        if self.freebase_id.startswith("/en"):
            return base + self.freebase_id
        else:
            return base + "/en" + self.freebase_id

    def freebase_type_url(self):
        return "http://www.freebase.com/view" + self.freebase_type_id

class UserProfile(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, related_name='profile')
    pic_url = models.URLField(blank=True)
    home_url = models.URLField(blank=True)
    twitter_id = models.CharField(max_length=100, blank=True)
    facebook_id = models.CharField(max_length=100, blank=True)
    linkedin_id= models.CharField(max_length=100, blank=True)
    github_id = models.CharField(max_length=100, blank=True)

    def linked_providers(self):
        return [s.provider for s in self.user.social_auth.all()]
    
    def unlinked_providers(self):
        providers = set(["twitter", "facebook", "github", "linkedin"])
        linked = set(self.linked_providers())
        return list(providers - linked)

def make_slug(sender, **kwargs):
    i = kwargs['instance']
    i.slug = slugify(i.name)

def facebook_extra_values(sender, user, response, details, **kwargs):
    facebook_id = response.get('id')
    user.profile.facebook_id = facebook_id
    user.profile.pic_url = 'http://graph.facebook.com/' + facebook_id + '/picture'
    user.profile.save()

def twitter_extra_values(sender, user, response, details, **kwargs):
    twitter_id = response.get('screen_name')
    user.profile.twitter_id = twitter_id
    user.profile.pic_url = user.social_auth.get(provider='twitter').extra_data['profile_image_url']
    user.profile.save()

def create_user_profile(sender, created, instance, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

pre_save.connect(make_slug, sender=Subject)
pre_update.connect(facebook_extra_values, sender=FacebookBackend)
pre_update.connect(twitter_extra_values, sender=TwitterBackend)
post_save.connect(create_user_profile, sender=User)
