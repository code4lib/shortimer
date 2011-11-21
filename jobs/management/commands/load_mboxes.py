import os
import re
import urllib
import logging
import mailbox

from django.conf import settings
from django.core.management.base import BaseCommand

from jobs.models import JobEmail

mbox_dir = os.path.join(settings.PROJECT_DIR, "mboxes")

log = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        for mbox in mboxes():
            for msg in mailbox.mbox(mbox):
                email = JobEmail.new_from_msg(msg)
                if email:
                    log.info("loaded %s", email)

def mboxes():
    if not os.path.isdir(mbox_dir):
        os.mkdir(mbox_dir)
        download_mboxes()
    for filename in os.listdir(mbox_dir):
        if filename.endswith("mbox"):
            yield os.path.join(mbox_dir, filename)

def download_mboxes():
    print "downloading code4lib mboxes"
    opener = urllib.URLopener()
    url = "http://serials.infomotions.com/code4lib/etc/mboxes/code4lib-%s.mbox"
    for year in range(2004, 2012):
        mbox_url = url % year
        mbox_file = os.path.join(mbox_dir, "code4lib-%s.mbox" % year)
        print "saving %s as %s" % (mbox_url, mbox_file)
        opener.retrieve(mbox_url, mbox_file)

