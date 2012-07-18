import re
import datetime

from django.conf import settings
import requests

from shortimer.jobs.models import Job

class AnalyticsClient:

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
        url = "https://www.google.com/" + path
        return requests.get(url, params=params, headers=headers).json

    def account_json(self):
        return self.get_json("/analytics/feeds/accounts/default?alt=json")

    def data_json(self, query):
        return self.get_json("/analytics/feeds/data?alt=json", params=query)

def websites():
    c = AnalyticsClient(settings.GA_USERNAME, settings.GA_PASSWORD)
    for a in c.account_json()['feed']['entry']:
        print a['title']['$t'], a['dxp$tableId']['$t']

def update():
    c = AnalyticsClient(settings.GA_USERNAME, settings.GA_PASSWORD)
    end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    result = c.data_json({
        "ids": "ga:54634246", 
        "dimensions": "ga:pagePath",
        "metrics": "ga:pageViews", 
        "start-date": "2010-01-01", 
        "end-date": end_date
    })

    for row in result['feed']['entry']:
        page = row['dxp$dimension'][0]['value']
        views = row['dxp$metric'][0]['value']
        m = re.match("^/job/(\d+)/$", page)
        if not m:
            continue
        try:
            job = Job.objects.get(id=int(m.group(1)))
            job.page_views = views
            job.save()
        except Job.DoesNotExist:
            pass # deleted
