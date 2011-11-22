import re
import time
import codecs
import rfc822
import logging
import datetime
import StringIO

from django.db import models

import miner

class EmailKeyword(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    emails = models.ManyToManyField('JobEmail', related_name='keywords')
    on_wikipedia = models.BooleanField()

class JobEmail(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    from_name = models.CharField(max_length=255)
    from_address = models.CharField(max_length=255)
    from_domain = models.CharField(max_length=255)
    subject = models.TextField()
    body = models.TextField()
    sent_time = models.DateTimeField()
    message_id = models.CharField(max_length=1024)

    def __str__(self):
        return "%s -%s" % (self.from_address, self.subject)

    @classmethod
    def new_from_msg(klass, msg):
        if not miner.is_job(msg):
            return None

        if JobEmail.objects.filter(message_id=msg['message-id']).count() == 1:
            return None

        logging.info("parsing email %s", msg['message-id'])

        e = JobEmail()
        e.from_name, e.from_address = rfc822.parseaddr(msg['from'])
        e.from_name = normalize_name(e.from_name)
        e.from_address = e.from_address.lower()
        e.from_domain = e.from_address.split('@')[1]
        e.subject = msg['subject']
        e.message_id = msg['message-id']
        e.body = get_body(msg)

        t = time.mktime(rfc822.parsedate(msg['date']))
        e.sent_time = datetime.datetime.fromtimestamp(t)

        if not e.body:
            logging.warn("missing body")
            return None

        e.save()

        # add keywords
        for n in miner.proper_nouns(e.body):
            n = n.lower()
            try:
                kw = EmailKeyword.objects.get(name=n)
                kw.emails.add(e)
                kw.save()
            except EmailKeyword.DoesNotExist:
                kw = EmailKeyword.objects.create(name=n)
                kw.emails.add(e)
                kw.save()

        return e

def normalize_name(name):
    if ',' in name:
        parts = name.split(',')
        parts = [p.strip() for p in parts]
        first_name = parts.pop()
        parts.insert(0, first_name)
        name = ' '.join(parts)
    return name

def get_body(msg):
    charset = msg.get_content_charset()

    if not charset: 
        logging.warn("no charset for")
        return None

    try:
        codec = codecs.getreader(charset)
    except LookupError: 
        logging.warn("no codec for %s", charset)
        return None

    payload = StringIO.StringIO(msg.get_payload())
    reader = codec(payload)
    body = "\n".join(reader.readlines())
    return body
