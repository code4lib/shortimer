# -*- coding: utf-8 -*-

import re
import json
import time
import codecs
import rfc822
import urllib
import logging
import datetime
import StringIO

import nltk

from shortimer.jobs.models import Job, Keyword, Subject

"""
Functions for doing text munging on job text.
"""

NOUN_CODES = ["NNP"]

# http://daringfireball.net/2010/07/improved_regex_for_matching_urls
URL_PATTERN = re.compile(r'''(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')


def email_to_job(msg):
    logging.info("looking at email with subject: %s", msg['subject'])

    if not is_job_email(msg):
        return None

    if Job.objects.filter(email_message_id=msg['message-id']).count() == 1:
        return None

    logging.info("parsing job email %s", msg['message-id'])

    j = Job()
    j.contact_name, j.contact_email = rfc822.parseaddr(msg['from'])
    j.contact_name = normalize_name(j.contact_name)
    j.contact_email = j.contact_email.lower()

    # get the employer
    #j.from_domain = j.from_address.split('@')[1]

    j.title = re.sub("^\[CODE4LIB\] ", "", msg['subject'])
    j.title = re.sub("[\n\r]", "", j.title)
    j.email_message_id = msg['message-id']
    j.description = get_html(get_body(msg))

    t = time.mktime(rfc822.parsedate(msg['date']))
    j.post_date = datetime.datetime.fromtimestamp(t)

    if not j.description:
        logging.warn("missing body")
        return None

    if 'http://jobs.code4lib.org' in j.description:
        logging.warn("not loading a job that shortimer posted")
        return None

    j.save()
    autotag(j)
    j.save()
    return j

def autotag(job):
    for n in nouns(job.description):
        n = n.lower()
        for subject in Subject.objects.filter(keywords__name=n):
            job.subjects.add(subject)

def normalize_name(name):
    if ',' in name:
        parts = name.split(',')
        parts = [p.strip() for p in parts]
        first_name = parts.pop()
        parts.insert(0, first_name)
        name = ' '.join(parts)
    return name

def get_html(text):
    if text is not None:
        html = "<p>" + text + "</p>"
        html = html.replace("\n\n", "</p>\n\n<p>")
        return re.sub(URL_PATTERN, r'<a href="\1">\1</a>', html)
    else:
        return None

def get_body(msg):
    # pull out first text part to a multipart message
    # not going to get in the business of extracting text from word, pdf, etc
    if msg.is_multipart():
        text_part = None
        for m in msg.get_payload():
            print m['content-type']
            if m['content-type'].lower().startswith('text'):
                text_part = m
                break
        if not text_part:
            return None
        else:
            msg = text_part

    charset = msg.get_content_charset()
    if not charset: 
        logging.warn("no charset assuming utf8")
        charset = "utf8"

    try:
        codec = codecs.getreader(charset)
    except LookupError: 
        logging.warn("no codec for %s", charset)
        return None

    payload = StringIO.StringIO(msg.get_payload(decode=True))
    reader = codec(payload)
    body = ''.join(reader.readlines())
    return body

def is_job_email(msg):
    """takes an email message and returns a boolean indicating whether the 
    message looks like a job ad.
    """
    if not msg['subject']:
        return False
    subject = msg['subject'].lower()
    if re.search('^re:', subject):
        return False
    if re.search('job', subject):
        return True
    if re.search('position', subject):
        return True
    if re.search('employment', subject):
        return True
    return False

def nouns(text):
    """returns proper nouns from a chunk of text
    """
    nouns = []
    for tag in tags(text):
        word = tag[0]
        is_proper_noun = tag[1] in NOUN_CODES
        is_word = re.match("^[a-z]+$", tag[0], re.IGNORECASE)

        if is_proper_noun and is_word:
            nouns.append(tag[0])
        elif len(nouns) > 0:
            yield " ".join(nouns)
            nouns = []

def tags(text):
    """returns some text with part of speech tagging
    """
    words = nltk.word_tokenize(text)
    return nltk.pos_tag(words)

def wikipedia_term(term):
    """Pass in a term or phrase and get it back true if it is on wikipedia, or
    False if it is not.
    """
    url = "http://en.wikipedia.org/w/api.php?action=opensearch&search=%s" % term
    hits = _get_json(url)
    if hits:
        for hit in hits[1]:
            if hit.lower() == word.lower():
                return True
    return False

def wikipedia_categories(term):
    """Pass wikipedia term and get back the categories it belongs to.
    """
    url = "http://en.wikipedia.org/w/api.php?action=query&prop=categories&titles=%s&format=json&cllimit=50" % term
    results = _get_json(url)
    page_id = results['query']['pages'].keys()[0]

    categories = []
    for c in results['query']['pages'][page_id].get('categories', []):
        categories.append(re.sub('^Category:', '', c['title']))
    return categories

def _get_json(url):
    """utility to fetch and decode json
    """
    try:
        return json.loads(urllib.urlopen(url).read())
    except ValueError, e:
        logging.exception("bad JSON from %s", url)
    except Exception, e:
        logging.exception("unable to get %s", url)
    return None

