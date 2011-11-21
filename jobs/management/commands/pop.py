import os
import email
import poplib
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from jobs.models import JobEmail

log = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **options):
        log.info("checking for new emails")
        gmail = poplib.POP3_SSL(settings.POP_SERVER, settings.POP_PORT)
        gmail.user(settings.POP_USER)
        gmail.pass_(settings.POP_PASSWORD)

        num_messages = len(gmail.list()[1])
        for i in range(num_messages):
            email_txt = '\n'.join(gmail.retr(i+1)[1])
            msg = email.message_from_string(email_txt)
            e = JobEmail.new_from_msg(msg)
            if e:
                log.info("found a new job email: %s", e)
