from django.views.generic.simple import direct_to_template
from django.conf.urls.defaults import patterns, include, url

from shortimer.jobs.sitemap import JobSitemap

urlpatterns = patterns('shortimer.jobs.views',
    url(r'^$', 'jobs', name='home'),
    url(r'^feed/$', 'feed', name='feed'),
    url(r'^feed/(?P<page>\d+)/$', 'feed', name='feed_page'),
    url(r'^feed/tag/(?P<tag>.+)/(?P<page>\d+)/$', 'feed', name='feed_tag_page'),
    url(r'^feed/tag/(?P<tag>.+)/$', 'feed', name='feed_tag'),
    url(r'^about/$', 'about', name='about'),
    url(r'^jobs/(?P<subject_slug>.+)/$', 'jobs', name='jobs_by_subject'),
    url(r'^job/(?P<id>\d+)/$', 'job', name='job'),
    url(r'^job/(?P<id>\d+)/edit/$', 'job_edit', name='job_edit'),
    url(r'^job/new/$', 'job_edit', name='job_new'),
    url(r'^keywords/matcher/$', 'matcher', name='matcher'),
    url(r'^keywords/matcher/table/$', 'matcher_table', name='matcher_table'),
    url(r'^keywords/(?P<id>\d+)/$', 'keyword', name='keyword'),
    url(r'^tags/$', 'tags', name='tags'),
    url(r'^employers/$', 'employers', name='employers'),
    url(r'^employer/(?P<employer_slug>.+)/$', 'employer', name='employer'),
    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^user/(?P<username>.+)/$', 'user', name='user'),
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^users/$', 'users', name='users'),
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^curate/$', 'curate', name='curate'),
    url(r'^curate/employers/$', 'curate_employers', name='curate_employers'),
    url(r'^curate/drafts/$', 'curate_drafts', name='curate_drafts'),
    url(r'^api/v1/guess_location', 'guess_location', name='guess_location'),
    url(r'^api/v1/recent_jobs$', 'recent_jobs', name='recent_jobs'),
    url(r'^map/$', 'map_jobs', name='map_jobs'),
    url(r'^map/more/(?P<count>\d+)/$','more_map_data', name="more_maps_data"),
    url(r'', include('social_auth.urls')),
)

sitemaps = {'jobs': JobSitemap}
urlpatterns += patterns('',
    url(r'^robots\.txt$', direct_to_template, {'template': 'robots.txt', 'mimetype': 'text/plain'}),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)
