import email
import unittest

from jobs.models import JobEmail

class JobsTests(unittest.TestCase):

    def setUp(self):
        JobEmail.objects.all().delete()

    def test_email(self):
        msg = email.message_from_file(open("test-data/job-email"))
        e = JobEmail.new_from_msg(msg)
        self.assertEqual(e.from_address, "cgowing@miami.edu")
        self.assertEqual(e.from_domain, 'miami.edu')
        self.assertEqual(e.from_name, 'Cheryl A. Gowing')
        self.assertEqual(e.subject, '[CODE4LIB] Job Posting: Head of Web &  Emerging Technologies, University of Miami - revised')
        self.assertTrue('collaborates' in e.body)
        self.assertTrue(e.message_id, '<7933CD19EEFCC94392323A994F6F1EDF01DBB52AE8@MBX03.cgcent.miami.edu>')
        keywords = [kw.name for kw in e.keywords.all()]
        self.assertTrue('drupal' in keywords)

class MinerTest(unittest.TestCase):

    def test_proper_nouns(self):
        pass

    def test_tags(self):
        pass
