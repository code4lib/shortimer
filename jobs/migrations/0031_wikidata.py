# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import time
import urllib
import datetime

from south.db import db
from south.v2 import DataMigration
from django.db import models

import requests

wikidata = requests.Session()
google = requests.Session()

def sparql(q):
    time.sleep(1)
    resp = wikidata.get(
      "https://query.wikidata.org/bigdata/namespace/wdq/sparql",
      params={"query": q}, 
      headers={"Accept": "application/json"}
    )
    if resp.status_code == 200:
        return resp.json
    return None

def first(r):
    if r == None:
        return None
    try:
        name = r['head']['vars'][0]
        if 'results' in r and len(r['results']['bindings']) > 0:
            return r["results"]["bindings"][0][name]["value"]
    except KeyError as e:
        print("KeyError: %s" % json.dumps(r))
    return None

def lookup_freebase_id(freebase_id):
    q = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        SELECT ?subject WHERE {
          ?subject wdt:P646 "%s" .
        }
        """ % freebase_id
    return first(sparql(q))

def lookup_name(name):
    q = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?subject
        WHERE {
          ?subject rdfs:label "%s"@en .
        }
        LIMIT 1
        """ % name
    return first(sparql(q))

def lookup_wikipedia_url(name):
    # hack to figure out canonical URL for a wikipedia article
    url = "https://en.wikipedia.org/wiki/" + urllib.quote(name)
    resp = requests.get(url)
    if resp.status_code != 200:
        return None
    m = re.search('<link rel="canonical" href="(.+?)"/>', resp.content)
    if not m:
        return None
    url = m.group(1)

    print("looking up %s" % url)
    q = """
        PREFIX schema: <http://schema.org/>
        SELECT ?o WHERE {
          <%s> schema:about ?o .
        }
        LIMIT 1
        """ % url
    return first(sparql(q))

def add_wikidata_id(e):
    if not e.freebase_id:
        return None
    if e.wikidata_id:
        return e.wikidata_id

    e.wikidata_id = lookup_freebase_id(e.freebase_id) \
        or lookup_wikipedia_url(e.name) \
        or lookup_name(e.name)

    print("%s (%s) -> %s" % (e.name, e.freebase_id, e.wikidata_id))
    if e.wikidata_id:
        e.save()

    return e.wikidata_id

class Migration(DataMigration):

    def forwards(self, orm):
        map(add_wikidata_id, orm['jobs.Subject'].objects.all())
        map(add_wikidata_id, orm['jobs.Employer'].objects.all())
        map(add_wikidata_id, orm['jobs.Location'].objects.all())

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'jobs.employer': {
            'Meta': {'object_name': 'Employer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'freebase_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'wikidata_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        u'jobs.job': {
            'Meta': {'ordering': "['-post_date']", 'object_name': 'Job'},
            'close_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'contact_email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'contact_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'deleted': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'email_message_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'employer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'to': u"orm['jobs.Employer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'default': "'ft'", 'max_length': '2'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'to': u"orm['jobs.Location']"}),
            'origin_url': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'page_views': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'post_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'published_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'published_jobs'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'salary_end': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'salary_start': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'telecommute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tweet_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'jobs.jobedit': {
            'Meta': {'ordering': "['-created']", 'object_name': 'JobEdit'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edits'", 'to': u"orm['jobs.Job']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'edits'", 'to': u"orm['auth.User']"})
        },
        u'jobs.keyword': {
            'Meta': {'object_name': 'Keyword'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keywords'", 'null': 'True', 'to': u"orm['jobs.Subject']"})
        },
        u'jobs.location': {
            'Meta': {'object_name': 'Location'},
            'freebase_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'wikidata_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        u'jobs.subject': {
            'Meta': {'ordering': "['name']", 'object_name': 'Subject'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'freebase_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'freebase_type_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jobs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subjects'", 'null': 'True', 'to': u"orm['jobs.Job']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'wikidata_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'})
        },
        u'jobs.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'github_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'home_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'linkedin_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pic_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'twitter_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['jobs']
    symmetrical = True
