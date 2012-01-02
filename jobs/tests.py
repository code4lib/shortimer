import sys
import email
import logging
import unittest

from jobs.models import Job

import miner

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class JobsTests(unittest.TestCase):

    def setUp(self):
        Job.objects.all().delete()

    def test_email_to_job(self):
        msg = email.message_from_file(open("test-data/job-email"))
        j = miner.email_to_job(msg)
        self.assertTrue(type(j), Job)
        self.assertEqual(j.contact_name, 'Cheryl A. Gowing')
        self.assertEqual(j.contact_email, "cgowing@miami.edu")
        self.assertEqual(j.title, 'Job Posting: Head of Web &  Emerging Technologies, University of Miami - revised')
        self.assertTrue('collaborates' in j.description)
        self.assertTrue(j.email_message_id, '<7933CD19EEFCC94392323A994F6F1EDF01DBB52AE8@MBX03.cgcent.miami.edu>')
        keywords = [kw.name for kw in j.keywords.all()]
        self.assertTrue('drupal' in keywords)
    
        # test employer
        #self.assertEqual(j.from_domain, 'miami.edu')

    def test_multipart(self):
        msg = email.message_from_file(open("test-data/job-multipart-email"))
        j = miner.email_to_job(msg)
        self.assertEqual(j.title, "Library System Administrator Position")

    def test_missing_charset(self):
        msg = email.message_from_file(open("test-data/job-email-missing-charset"))
        self.assertTrue(msg)
        self.assertTrue(miner.is_job_email(msg))
        j = miner.email_to_job(msg)
        self.assertTrue(j)
        self.assertEqual(j.title, "Job Posting: Programmer/Analyst 2, The University of Chicago Library")

class MinerTests(unittest.TestCase):
    text = "Experience in web application, web services development, and XM.  Experience with Flash, AJAX, or other highly interactive web user interface development, digital video, and audio formats, and technologies and/or digital repositories (e.g., Fedora). Combinations of related education and experience will be considered."

    def test_nouns(self):
        self.assertTrue("AJAX" in miner.nouns(MinerTests.text))

    def test_tags(self):
        self.assertTrue(("Flash", "NNP") in miner.tags(MinerTests.text))

    def test_wikipedia_categories(self):
        self.assertTrue("Dynamic programming languages" in miner.wikipedia_categories("Perl"))
