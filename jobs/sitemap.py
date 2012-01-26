from django.contrib.sitemaps import Sitemap
from shortimer.jobs.models import Job

class JobSitemap(Sitemap):
    changefreq = "never"
    priority = 0.9

    def items(self):
        return Job.objects.filter(published__isnull=False)

    def lastmod(self, obj):
        return obj.published
