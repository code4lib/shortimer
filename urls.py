from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('shortimer.jobs.views',
    #url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'jobs', name='home'),
    url(r'^about/$', 'about', name='about'),
    url(r'^jobs/(?P<subject_slug>.+)/$', 'jobs', name='jobs_by_subject'),
    url(r'^job/(?P<id>\d+)/$', 'job', name='job'),
    url(r'^job/(?P<id>\d+)/edit/$', 'job_edit', name='job_edit'),

    url(r'^keywords/matcher/$', 'matcher', name='matcher'),
    url(r'^keywords/matcher/table/$', 'matcher_table', name='matcher_table'),

    url(r'^keywords/(?P<id>\d+)/$', 'keyword', name='keyword'),

    url(r'^tags/$', 'tags', name='tags'),

    url(r'^login/$', 'login', name='login'),
    url(r'^logout/$', 'logout', name='logout'),
    url(r'^user/(?P<username>.+)/$', 'user', name='user'),
    url(r'^profile/$', 'profile', name='profile'),
    url(r'^users/$', 'users', name='users'),
    url(r'^reports/$', 'reports', name='reports'),
    url(r'^curate/$', 'curate', name='curate'),
    url(r'^curate/employers/$', 'curate_employers', name='curate_employers'),

    url(r'', include('social_auth.urls')),

)
