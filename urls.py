from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('jobs4lib.jobs.views',
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', 'home', name='home'),
    url(r'^jobs/(?P<id>\d+)/$', 'job', name='job'),

    url(r'^keywords/matcher/$', 'matcher', name='matcher'),
    url(r'^keywords/matcher/table/$', 'matcher_table', name='matcher_table'),

    url(r'^keywords/(?P<id>\d+)/$', 'keyword', name='keyword'),

    url(r'^subjects/$', 'subjects', name='subjects'),
    url(r'^subjects/(?P<slug>.+)/', 'subject', name='subject')
)
