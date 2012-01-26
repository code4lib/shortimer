from django.contrib.sitemaps import Sitemap
from shortimer.jobs.models import Job

class JobSitemap(Sitemap):
    changefreq = "always"
    priority = 0.9

    def items(self):
        jobs = Job.objects.filter(published__isnull=False)
        return jobs.order_by('-updated')

    def lastmod(self, obj):
        return obj.updated
