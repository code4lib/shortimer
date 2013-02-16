# -*- coding: utf-8 -*-

import re
import datetime
import json
import urllib

from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify

from social_auth.signals import pre_update
from social_auth.backends.facebook import FacebookBackend
from social_auth.backends.twitter import TwitterBackend

import tweepy
import bitlyapi
import html2text

JOB_TYPES = (
    (u'ft', 'full-time'), 
    (u'pt', 'part-time'), 
    (u'co', 'contract'),
    (u'tm', 'temporary'), 
    (u'in', 'internship'),
    (u'rp', 'rfp'),
)

# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
url_pattern = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')

class FreebaseEntity(object):

    def freebase_image_url(self):
        url = "https://usercontent.googleapis.com/freebase/v1/image" 
        url += self.freebase_id
        url += "?maxwidth=400&maxheight=200"
        return url

    def freebase_url(self):
        return "http://www.freebase.com/view" + self.freebase_id

    def freebase_json_url(self):
        return "http://www.freebase.com/experimental/topic/standard" + self.freebase_id

    def freebase_data(self):
        try:
            data = json.load(urllib.urlopen(self.freebase_json_url()))
            return data
        except ValueError:
            return {}

    def freebase_rdf_url(self):
        id = self.freebase_id
        id = id.lstrip("/")
        id = id.replace("/", ".")
        return "http://rdf.freebase.com/rdf/" + id

class Job(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.DateTimeField(null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    url = models.CharField(max_length=1024)
    origin_url = models.CharField(max_length=1024, null=True)
    post_date = models.DateTimeField(null=True)
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
    published = models.DateTimeField(null=True)
    published_by = models.ForeignKey(User, related_name='published_jobs', null=True)
    tweet_date = models.DateTimeField(null=True)
    page_views = models.IntegerField(null=True)

    def __str__(self):
        return self.title.encode('ascii', 'ignore')

    @models.permalink
    def get_absolute_url(self):
        return ('job', [str(self.id)])

    def publish(self, user):
        self.published = datetime.datetime.now()
        self.published_by = user
        self.tweet()
        self.email()
        self.save()

    def publishable(self):
        if self.published:
            return False, "already published"
        if not self.title:
            return False, "need to assign a title"
        if not self.employer:
            return False, "need to assign an employer"
        if self.subjects.all().count() == 0:
            return False, "please assign some tags"
        return True, "ok"

    def tweet(self):
        if self.tweet_date or not settings.CODE4LIB_TWITTER_OAUTH_CONSUMER_KEY:
            return 

        url = self.short_url()

        # construct tweet message
        msg = "Job: " + self.title
        if self.employer:
            msg = msg + " at " + self.employer.name
        msg += ' ' + url

        # can't tweet if it won't fit
        if len(msg) > 140:
            return 

        # tweet it
        auth = tweepy.OAuthHandler(settings.CODE4LIB_TWITTER_OAUTH_CONSUMER_KEY,
                                   settings.CODE4LIB_TWITTER_OAUTH_CONSUMER_SECRET)
        auth.set_access_token(settings.CODE4LIB_TWITTER_OAUTH_ACCESS_TOKEN_KEY,
                              settings.CODE4LIB_TWITTER_OAUTH_ACCESS_TOKEN_SECRET)

        twitter = tweepy.API(auth)
        twitter.update_status(msg)
        self.tweet_date = datetime.datetime.now()
        self.save()

    def email(self):
        if self.post_date or not settings.EMAIL_HOST_PASSWORD:
            return

        url = "http://jobs.code4lib.org/job/%s/" % self.id
        body = html2text.html2text(self.description)
        body += "\r\n\r\nBrought to you by code4lib jobs: " + url
        body = re.sub('&[^ ]+;', '', body)

        if self.employer:
            subject = "Job: " + self.title + " at " + self.employer.name
        else:
            subject = "Job: " + self.title

        send_mail(subject, body, settings.EMAIL_HOST_USER, settings.EMAIL_ANNOUNCE)
        self.post_date = datetime.datetime.now()
        self.save()

    def short_url(self):
        long_url = "http://jobs.code4lib.org/job/%s/" % self.id
        bitly = bitlyapi.BitLy(settings.BITLY_USERNAME, settings.BITLY_PASSWORD)
        response = bitly.shorten(longUrl=long_url)
        return response['url']

    class Meta:
        ordering = ['-post_date']

class JobEdit(models.Model):
    user = models.ForeignKey(User, related_name="edits")
    job = models.ForeignKey(Job, related_name="edits")
    created = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ['-created']

class Employer(models.Model, FreebaseEntity):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, null=True)
    freebase_id = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    domain = models.CharField(max_length=50)

    def __str__(self):
        return "%s - %s <%s>" % (self.name, self.slug, self.freebase_id)

class Keyword(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    ignore = models.BooleanField(default=False)
    subject = models.ForeignKey('Subject', related_name='keywords', null=True)

class Subject(models.Model, FreebaseEntity):
    name = models.CharField(max_length=500)
    slug = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=100)
    freebase_id = models.CharField(max_length=100)
    freebase_type_id = models.CharField(max_length=100)
    jobs = models.ManyToManyField('Job', related_name='subjects', null=True)

    class Meta: 
        ordering = ['name']

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.freebase_id) 

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
        providers = set(["twitter", "facebook", "github", "linkedin", "google"])
        linked = set(self.linked_providers())
        return list(providers - linked)

def make_slug(sender, **kwargs):
    i = kwargs['instance']
    if not i.slug:
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
    class Meta:
        ordering = ['-post_date']

class JobEdit(models.Model):
    user = models.ForeignKey(User, related_name="edits")
    job = models.ForeignKey(Job, related_name="edits")
    created = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ['-created']

class Employer(models.Model, FreebaseEntity):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, null=True)
    freebase_id = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    domain = models.CharField(max_length=50)

    def __str__(self):
        return "%s - %s <%s>" % (self.name, self.slug, self.freebase_id)

class Keyword(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    ignore = models.BooleanField(default=False)
    subject = models.ForeignKey('Subject', related_name='keywords', null=True)

class Subject(models.Model, FreebaseEntity):
    name = models.CharField(max_length=500)
    slug = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=100)
    freebase_id = models.CharField(max_length=100)
    freebase_type_id = models.CharField(max_length=100)
    jobs = models.ManyToManyField('Job', related_name='subjects', null=True)

    class Meta: 
        ordering = ['name']

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.freebase_id) 

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
        providers = set(["twitter", "facebook", "github", "linkedin", "google"])
        linked = set(self.linked_providers())
        return list(providers - linked)

def make_slug(sender, **kwargs):
    i = kwargs['instance']
    if not i.slug:
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

    class Meta:
        ordering = ['-post_date']

class JobEdit(models.Model):
    user = models.ForeignKey(User, related_name="edits")
    job = models.ForeignKey(Job, related_name="edits")
    created = models.DateTimeField(auto_now_add=True)

    class Meta: 
        ordering = ['-created']

class Employer(models.Model, FreebaseEntity):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, null=True)
    freebase_id = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    domain = models.CharField(max_length=50)

    def __str__(self):
        return "%s - %s <%s>" % (self.name, self.slug, self.freebase_id)

class Keyword(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    ignore = models.BooleanField(default=False)
    subject = models.ForeignKey('Subject', related_name='keywords', null=True)

class Subject(models.Model, FreebaseEntity):
    name = models.CharField(max_length=500)
    slug = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=100)
    freebase_id = models.CharField(max_length=100)
    freebase_type_id = models.CharField(max_length=100)
    jobs = models.ManyToManyField('Job', related_name='subjects', null=True)

    class Meta: 
        ordering = ['name']

    def __unicode__(self):
        return "%s [%s]" % (self.name, self.freebase_id) 

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
        providers = set(["twitter", "facebook", "github", "linkedin", "google"])
        linked = set(self.linked_providers())
        return list(providers - linked)

def make_slug(sender, **kwargs):
    i = kwargs['instance']
    if not i.slug:
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


def add_employer_location(sender, **kwargs):
    job = kwargs.get('instance')
    employer = job.employer
    #Add employer location data if not available already.
    if not employer.city:
        fb = employer.freebase_data()
        fb_properties = fb.get('result', {}).get('properties', {})
        if fb_properties:
            hq_values = fb_properties.get('/organization/organization/headquarters', {}).get('values', {})
            if hq_values:
                for val in hq_values:
                    addr = val.get('address')
                    if addr:
                        city = addr.get('city', {}).get('text', {})
                        if city:
                            employer.city = city
                        state = addr.get('region', {}).get('text', {})
                        if state:
                            #DC appears twice in the Freebase data, as city and state.
                            if state != 'Washington, D.C.':
                                employer.state = state
                        country = addr.get('country', {}).get('text', {})
                        if country:
                            employer.country = country
                        employer.save()
                        #Let's work with the first available address only. 
                        return


pre_save.connect(make_slug, sender=Subject)
pre_save.connect(make_slug, sender=Employer)
pre_update.connect(facebook_extra_values, sender=FacebookBackend)
pre_update.connect(twitter_extra_values, sender=TwitterBackend)
post_save.connect(create_user_profile, sender=User)
post_save.connect(add_employer_location, sender=Job)
