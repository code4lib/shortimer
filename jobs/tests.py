import email
import unittest

from jobs.models import JobEmail

import miner

class JobsTests(unittest.TestCase):

    def setUp(self):
        JobEmail.objects.all().delete()

    def test_email(self):
        msg = email.message_from_file(open("test-data/job-email"))
        e = JobEmail.new_from_msg(msg)
        self.assertEqual(e.from_address, "cgowing@miami.edu")
        self.assertEqual(e.from_domain, 'miami.edu')
        self.assertEqual(e.from_name, 'Cheryl A. Gowing')
        self.assertEqual(e.subject, 'Job Posting: Head of Web &  Emerging Technologies, University of Miami - revised')
        self.assertTrue('collaborates' in e.body)
        self.assertTrue(e.message_id, '<7933CD19EEFCC94392323A994F6F1EDF01DBB52AE8@MBX03.cgcent.miami.edu>')
        keywords = [kw.name for kw in e.keywords.all()]
        self.assertTrue('drupal' in keywords)

    def test_multipart_email(self):
        msg = email.message_from_file(open("test-data/job-multipart-email"))
        e = JobEmail.new_from_msg(msg)
        self.assertEqual(e.subject, "Library System Administrator Position")

class MinerTests(unittest.TestCase):
    text = "Experience in web application, web services development, and XM.  Experience with Flash, AJAX, or other highly interactive web user interface development, digital video, and audio formats, and technologies and/or digital repositories (e.g., Fedora). Combinations of related education and experience will be considered."

    def test_nouns(self):
        self.assertTrue("AJAX" in miner.nouns(MinerTest.text))

    def test_tags(self):
        self.assertTrue(("Flash", "NNP") in miner.tags(MinerTest.text))

    def test_wikipedia_categories(self):
        self.assertTrue("Dynamic programming languages" in miner.wikipedia_categories("Perl"))
