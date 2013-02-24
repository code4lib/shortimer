import sys
import email
import json
import logging
import unittest

from jobs.models import Employer, Job, Keyword, Subject, Location

import miner

class JobsTests(unittest.TestCase):

    def setUp(self):
        Job.objects.all().delete()

    def test_email_to_job(self):
        # need a keyword/subject mapping to test auto-tagging
        kw = Keyword.objects.create(name="drupal")
        su = Subject.objects.create(name="Drupal")
        su.keywords.add(kw)
        su.save()

        msg = email.message_from_file(open("test-data/job-email"))
        j = miner.email_to_job(msg)
        self.assertTrue(type(j), Job)
        self.assertEqual(j.contact_name, 'Cheryl A. Gowing')
        self.assertEqual(j.contact_email, "cgowing@miami.edu")
        self.assertEqual(j.title, 'Job Posting: Head of Web &  Emerging Technologies, University of Miami - revised')
        self.assertTrue('collaborates' in j.description)
        self.assertTrue(j.email_message_id, '<7933CD19EEFCC94392323A994F6F1EDF01DBB52AE8@MBX03.cgcent.miami.edu>')

        subjects = [s.name for s in j.subjects.all()]
        self.assertTrue('Drupal' in subjects)
    
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

class FreebaseTests(unittest.TestCase):

    def test_get_json_url(self):
        emp = Employer.objects.get(pk=1)
        self.assertEqual(emp.freebase_json_url(), "https://www.googleapis.com/freebase/v1/topic/en/stanford_university")

    def test_employer_save(self):
        e = Employer(name="Stanford University",
                     freebase_id="/en/stanford_university")
        e.save()
        self.assertEqual(e.city, 'Stanford')
        self.assertEqual(e.state, 'California')
        self.assertEqual(e.country, 'United States of America')
        self.assertEqual(e.postal_code, '94305')

        e = Employer(name="University of Chicago",
                     freebase_id="/en/university_of_chicago")
        e.save()
        self.assertEqual(e.city, 'Chicago')
        self.assertEqual(e.state, 'Illinois')
        self.assertEqual(e.country, '')
        self.assertEqual(e.postal_code, '60637')

    def test_employer_save_no_freebase_id(self):
        e = Employer(name="Haha College")
        e.save()
        self.assertEqual(e.city, '')
        self.assertEqual(e.state, '')
        self.assertEqual(e.country, '')

    def test_location_save(self):
        l = Location(name="Stanford", freebase_id="/en/stanford")
        l.save()
        self.assertEqual(l.latitude, 37.4225)
        self.assertEqual(l.longitude, -122.165277778)

    def test_freebase_values(self):
        l = Location(name="Stanford", freebase_id="/en/stanford")
        geos = l.freebase_values("/location/location/geolocation")
        self.assertEqual(len(geos), 1)
        g = geos[0]
        self.assertEqual(g.text, "37.4225 - -122.165277778 - Freebase Geodata Team - Geocode")
        self.assertEqual(g.lang, "en")
        self.assertEqual(g.creator, "/user/merge_bot")
        self.assertEqual(g.value, None)
        self.assertTrue(g.timestamp)

        lats = g.get_values("/location/geocode/latitude")
        self.assertEqual(len(lats), 1)
        l = lats[0]
        self.assertEqual(l.text, "37.4225")
        self.assertEqual(l.lang, "en")
        self.assertEqual(l.value, 37.4225)
        self.assertEqual(l.creator, "/user/geo_bot")
        self.assertTrue(l.timestamp)

        lat = g.get_value("/location/geocode/latitude")
        self.assertEqual(lat.text, "37.4225")
        self.assertEqual(lat.lang, "en")
        self.assertEqual(lat.value, 37.4225)
        self.assertEqual(lat.creator, "/user/geo_bot")
        self.assertTrue(lat.timestamp)

    def test_guess_location(self):
        e = Employer(name="Stanford University",
                     freebase_id="/en/stanford_university")
        l = e.guess_location()
        self.assertEqual(l.name, "Stanford")
        self.assertEqual(l.freebase_id, "/m/01zqy6t")

    def test_london(self):
        e = Employer(name="British Library",
                     freebase_id="/en/british_library")
        e.save()
        l = e.guess_location()
        self.assertTrue(l)
        self.assertEqual(l.name, "London")
        l.save()
        self.assertEqual(l.longitude, -0.106196)
        self.assertEqual(l.latitude, 51.517124)


