from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('jobs4lib.jobs.views',
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'jobs', name='home'),
    url(r'^jobs/(?P<subject_slug>.+)/$', 'jobs', name='jobs_by_subject'),
    url(r'^job/(?P<id>\d+)/$', 'job', name='job'),

    url(r'^keywords/matcher/$', 'matcher', name='matcher'),
    url(r'^keywords/matcher/table/$', 'matcher_table', name='matcher_table'),

    url(r'^keywords/(?P<id>\d+)/$', 'keyword', name='keyword'),

    url(r'^subjects/$', 'subjects', name='subjects'),
    url(r'^subjects/(?P<slug>.+)/$', 'subject', name='subject'),

    url(r'login/$', 'login', name='login'),
    url(r'logout/$', 'logout', name='logout'),
    url(r'user/(?P<username>.+)/$', 'user', name='user'),
    url(r'profile/', 'profile', name='profile'),

    url(r'', include('social_auth.urls')),

)
