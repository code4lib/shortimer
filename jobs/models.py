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
    (u'ct', 'contest'),
)

# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
url_pattern = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')

clean_xml_utf8 = re.compile(r'[^\x09\x0A\x0D\x20-\xD7FF\xE000-\xFFFD\U10000-\U10FFFF]')

class FreebaseValue(object):

    @classmethod 
    def make_values(klass, property_data, prop):
        values = []
        p = property_data.get(prop, {})
        valuetype = p.get("valuetype")
        for v in p.get("values", []):
            values.append(FreebaseValue(valuetype, v))
        return values
   
    def __init__(self, valuetype, obj={}):
        self.valuetype = valuetype
        self.text = obj.get("text")
        self.lang = obj.get("lang")
        self.id = obj.get("id")
        self.creator = obj.get("creator")
        self.timestamp = obj.get("timestamp")
        self.value = obj.get("value")
        self.property = obj.get("property", {})

    def get_values(self, prop):
        return FreebaseValue.make_values(self.property, prop)

    def get_value(self, prop):
        values = self.get_values(prop)
        if len(values) > 0:
            return values[0]

class FreebaseEntity(object):

    def freebase_image_url(self):
        url = "https://usercontent.googleapis.com/freebase/v1/image" 
        url += self.freebase_id
        url += "?maxwidth=400&maxheight=200"
        return url

    def freebase_url(self):
        return "http://www.freebase.com/view" + self.freebase_id

    def freebase_json_url(self):
        return "https://www.googleapis.com/freebase/v1/topic" + self.freebase_id + "?key=" + settings.GOOGLE_API_KEY

    def freebase_json_url_no_key(self):
        return "https://www.googleapis.com/freebase/v1/topic" + self.freebase_id

    def freebase_data(self):
        if hasattr(self, '_fb_data'):
            return self._fb_data
        try:
            resp = urllib.urlopen(self.freebase_json_url())
            data = json.load(resp)
            self._fb_data = data
            return data
        except ValueError:
            return {}

    def freebase_values(self, prop):
        data = self.freebase_data()
        if not data or not data.has_key("property"):
            return []
        return FreebaseValue.make_values(data["property"], prop)

    def freebase_value(self, prop):
        values = self.freebase_values(prop)
        if len(values) > 0:
            return values[0].value
        return None
        
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
    location = models.ForeignKey('Location', related_name='jobs', null=True)

    def __str__(self):
        return self.title.encode('ascii', 'ignore')

    @models.permalink
    def get_absolute_url(self):
        return ('job', [str(self.id)])

    @property
    def description_for_xml(self):
        # returns utf-8, minus any characters that can't be used in xml
        return re.sub(clean_xml_utf8, '', self.description.encode('utf8'));

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
        if not self.location and not self.telecommute:
            return False, "need to assign a location, or make it telecommute (whee)"
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
        body = self.title + "\r\n"
        body += self.employer.name + "\r\n"
        body += self.location.name + "\r\n\r\n"
        body += html2text.html2text(self.description)
        body += "\r\n\r\nBrought to you by code4lib jobs: " + url
        body += "\r\nTo post a new job please visit http://jobs.code4lib.org/"
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

    def display_location(self):
        if self.location and self.location.name == self.employer.city:
            return self.employer.display_location()
        elif self.location:
            return self.location.name
        elif self.employer.city and self.employer.state:
            return "%s, %s" % (self.employer.city, self.employer.state)
        elif self.employer.city:
            return self.employer.city
        else:
            return ""

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
    country = models.CharField(max_length=100)
    domain = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=25)
    description = models.TextField(null=True)

    @models.permalink
    def get_absolute_url(self):
        return ('employer', [self.slug])

    def save(self, *args, **kwargs):
        # try to grab some stuff from freebase if it is not defined already
        if self.freebase_id and not self.country:
            self.load_freebase_data()
        super(Employer, self).save(*args, **kwargs)

    def load_freebase_data(self):
        values = self.freebase_values("/organization/organization/headquarters")
        values.extend(self.freebase_values("/location/location/street_address"))
        self.description = self.freebase_value("/common/topic/description")
        for addr in values:
            city = addr.get_value("/location/mailing_address/citytown")
            state = addr.get_value("/location/mailing_address/state_province_region")
            country = addr.get_value("/location/mailing_address/country")
            postal_code = addr.get_value("/location/mailing_address/postal_code")
            address = addr.get_value("/location/mailing_address/street_address")

            if city:
                self.city = city.text
                if state:
                    self.state = state.text
                if country:
                    self.country = country.text
                if postal_code:
                    self.postal_code = postal_code.text
                if address:
                    self.address = address.text

                return

    def guess_location(self):
        if not self.freebase_id: return None

        # look for city in a few places
        values = self.freebase_values('/organization/organization/headquarters')
        values.extend(self.freebase_values('/location/location/street_address'))

        for addr in values:
            city = addr.get_value("/location/mailing_address/citytown")
            if city: 
                try:
                    locs = Location.objects.filter(freebase_id=city.id)
                    if len(locs) > 0:
                        return locs[0]
                except Location.DoesNotExist:
                    l = Location()
                    l.name = city.text
                    l.freebase_id = city.id
                return l
        return None

    def display_location(self):
        if self.city and self.state:
            return "%s, %s" % (self.city, self.state)
        elif self.city:
            return self.city
        else:
            return ""

    def __str__(self):
        return "%s - %s [%s] [%s, %s, %s %s]" % (self.name, self.slug, self.freebase_id, self.city, self.state, self.country, self.postal_code)

class Location(models.Model, FreebaseEntity):
    name = models.CharField(max_length=255)
    freebase_id = models.CharField(max_length=100)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)

    def save(self, *args, **kwargs):
        if not self.latitude:
           self.load_freebase_data()
        super(Location, self).save(*args, **kwargs)

    def load_freebase_data(self):
        for value in self.freebase_values("/location/location/geolocation"):
            lat = value.get_value("/location/geocode/latitude")
            lon = value.get_value("/location/geocode/longitude")
            if lat and lon:
                self.latitude = lat.value
                self.longitude = lon.value
                return

    def __str__(self):
        return "%s (%s, %s) [%s]" % (self.name, self.latitude, self.longitude, self.freebase_id)

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
    description = models.TextField(null=True)

    def save(self, *args, **kwargs):
        # try to grab some stuff from freebase if it is not defined already
        if self.freebase_id and not self.description:
            self.load_freebase_data()
        super(Subject, self).save(*args, **kwargs)

    def load_freebase_data(self):
        self.description = self.freebase_value('/common/topic/description')

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

pre_save.connect(make_slug, sender=Subject)
pre_save.connect(make_slug, sender=Employer)
pre_update.connect(facebook_extra_values, sender=FacebookBackend)
pre_update.connect(twitter_extra_values, sender=TwitterBackend)
post_save.connect(create_user_profile, sender=User)
