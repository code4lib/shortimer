import re

import nltk

"""
Functions for doing text munging on job text.
"""

def is_job(msg):
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
    return False

def proper_nouns(text):
    """returns proper nouns from a chunk of text
    """
    nouns = []
    for tag in tags(text):
        word = tag[0]
        is_proper_noun = tag[1] == "NNP"
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
    try:
        hits = json.loads(urllib.urlopen(url).read())
    except ValueError, e:
        logging.error("wikipedia returned bad JSON for %s", term)
        return False
    except Exception, e:
        logging.exception("unable to lookup %s at wikipedia", term)
    for hit in hits[1]:
        if hit.lower() == word.lower():
            return True
    return False
