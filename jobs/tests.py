import sys
import email
import json
import logging
import unittest

from jobs.models import Employer, Job, Keyword, Subject

import miner

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

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

class FreebaseTests(unittest.TestCase):

    def setUp(self):
        pass
        
    def test_get_json_url(self):
        emp = Employer.objects.get(pk=1)
        self.assertEqual('http://www.freebase.com/experimental/topic/standard/en/stanford_university', emp.freebase_json_url())

    def test_get_freebase_data(self):
        emp = Employer.objects.get(pk=1)
        data = emp.freebase_data()
        self.assertTrue('/api/status/ok', data['code'])

    def test_get_freebase_data_bad_url(self):
        emp = Employer.objects.get(pk=3) 
        data = emp.freebase_data()
        self.assertEqual('/api/status/error', data['code'])
        self.assertEqual('400 Bad Request', data['status'])

    def test_get_location_exists(self):
        from jobs.models import get_freebase_location
        raw = """
        {
            "status": "200 OK",
            "code": "/api/status/ok",
            "result": {
                "properties": {
                    "/organization/organization/headquarters": {
                        "text": "Headquarters",
                        "expected_type": {
                            "text": "Address",
                            "id": "/location/mailing_address"
                        },
                        "values": [
                            {
                                "text": "450 Serra Mall, Stanford, California, United States of America 94305",
                                "address": {
                                    "city": {
                                        "url": "http://www.freebase.com/view/en/stanford",
                                        "text": "Stanford",
                                        "id": "/en/stanford"
                                    },
                                    "region": {
                                        "url": "http://www.freebase.com/view/en/california",
                                        "text": "California",
                                        "id": "/en/california"
                                    },
                                    "street": [
                                        "450 Serra Mall"
                                    ],
                                    "postal_code": "94305",
                                    "country": {
                                        "url": "http://www.freebase.com/view/en/united_states",
                                        "text": "United States of America",
                                        "id": "/en/united_states"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        """
        data = json.loads(raw)
        location = get_freebase_location(data)
        self.assertEqual('Stanford', location.get('city'))
        self.assertEqual('California', location.get('state'))
        self.assertEqual('United States of America', location.get('country'))

    def test_get_location_not_exists(self):
        from jobs.models import get_freebase_location
        raw = """
        {
            "status": "200 OK",
            "code": "/api/status/ok",
            "result": {
                "properties": {
                }
            }
        }
        """
        data = json.loads(raw)
        location = get_freebase_location(data)
        self.assertEqual(None, location.get('city'))
        self.assertEqual(None, location.get('state'))
        self.assertEqual(None, location.get('country'))

    def test_get_location_partial(self):
        from jobs.models import get_freebase_location
        raw = """
        {
            "status": "200 OK",
            "code": "/api/status/ok",
            "result": {
                "properties": {
                    "/organization/organization/headquarters": {
                        "text": "Headquarters",
                        "expected_type": {
                            "text": "Address",
                            "id": "/location/mailing_address"
                        },
                        "values": [
                            {
                                "text": "450 Serra Mall, Stanford, California, United States of America 94305",
                                "address": {
                                    "country": {
                                        "url": "http://www.freebase.com/view/en/united_states",
                                        "text": "United States of America",
                                        "id": "/en/united_states"
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        """
        data = json.loads(raw)
        location = get_freebase_location(data)
        self.assertEqual(None, location.get('city'))
        self.assertEqual(None, location.get('state'))
        self.assertEqual('United States of America', location.get('country'))


    def test_get_location_dc(self):
        from jobs.models import get_freebase_location
        raw = """
        {
            "status": "200 OK",
            "code": "/api/status/ok",
            "result": {
                "properties": {
                    "/organization/organization/headquarters": {
                        "expected_type": {
                            "id": "/location/mailing_address",
                            "text": "Address"
                        },
                        "text": "Headquarters",
                        "values": [
                            {
                                "address": {
                                    "city": {
                                        "id": "/en/washington_united_states",
                                        "text": "Washington, D.C.",
                                        "url": "http://www.freebase.com/view/en/washington_united_states"
                                    },
                                    "country": {
                                        "id": "/en/united_states",
                                        "text": "United States of America",
                                        "url": "http://www.freebase.com/view/en/united_states"
                                    },
                                    "postal_code": "20052",
                                    "region": {
                                        "id": "/en/washington_united_states",
                                        "text": "Washington, D.C.",
                                        "url": "http://www.freebase.com/view/en/washington_united_states"
                                    },
                                    "street": [
                                        "2121 I Street, NW"
                                    ]
                                },
                                "text": "2121 I Street, NW, Washington, D.C., Washington, D.C., United States of America 20052"
                            }
                        ]
                    }
                }
            }
        }
        """
        data = json.loads(raw)
        location = get_freebase_location(data)
        self.assertEqual("Washington, D.C.", location.get('city'))
        self.assertEqual(None, location.get('state'))
        self.assertEqual('United States of America', location.get('country'))