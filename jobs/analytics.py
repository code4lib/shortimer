import re
import json
import datetime
import urlparse

from django.conf import settings
import requests

from shortimer.jobs.models import Job

class AnalyticsClient:
    """
    It's kind of sad that it was easier to roll my own code to talk 
    to Google Analytics than it was to understand Google's gdata 
    Python library...
    """

    def __init__(self, username, password, source="jobs.code4lib.org"):
        self.username = username
        self.password = password
        self.source = source
        self.login()

    def login(self):
        form = {
                "Email": self.username,
                "Passwd": self.password,
                "accountType": "GOOGLE",
                "source": self.source,
                "service": "analytics"
               }
        r = requests.post("https://www.google.com/accounts/ClientLogin", form)
        self.auth = "GoogleLogin " + re.search("(Auth=.+)$", r.content).group(1)

    def get_json(self, path, params=None):
        headers = {"Authorization": self.auth, "GData-Version": "2"}
        url = urlparse.urljoin("https://www.googleapis.com", path)
        return requests.get(url, params=params, headers=headers).json

    def account_json(self):
        return self.get_json("/analytics/v3/management/accounts?alt=json")

    def data_json(self, query):
        return self.get_json("/analytics/v3/data/ga?alt=json", params=query)

def profiles():
    c = AnalyticsClient(settings.GA_USERNAME, settings.GA_PASSWORD)
    for account in c.account_json()['items']:
        for prop in c.get_json(account['childLink']['href'])['items']:
            for profile in c.get_json(prop['childLink']['href'])['items']:
                yield profile

def update():
    c = AnalyticsClient(settings.GA_USERNAME, settings.GA_PASSWORD)
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    result = c.data_json({
        "ids": settings.GA_PROFILE_ID,
        "dimensions": "ga:pagePath",
        "metrics": "ga:pageViews", 
        "start-date": "2010-01-01", 
        "end-date": end_date
    })

    for page, views in result['rows']:
        m = re.match("^/job/(\d+)/$", page)
        if not m:
            continue
        try:
            job = Job.objects.get(id=int(m.group(1)))
            job.page_views = views
            job.save()
        except Job.DoesNotExist:
            pass # deleted
