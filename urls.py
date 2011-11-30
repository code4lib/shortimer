from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('jobs4lib.jobs.views',
    # Examples:
    # url(r'^$', 'jobs4lib.views.home', name='home'),
    # url(r'^jobs4lib/', include('jobs4lib.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    url(r'^jobs/$', 'jobs', name='jobs'),
    url(r'^jobs/(?P<id>\d+)/$', 'job', name='job'),

    url(r'^keywords/matcher/$', 'matcher', name='matcher'),
    url(r'^keywords/matcher/table/$', 'matcher_table', name='matcher_table'),

    url(r'^keywords/(?P<id>\d+)/$', 'keyword', name='keyword'),

    url(r'^subjects/$', 'subjects', name='subjects'),
    url(r'^subjects/(?P<slug>.+)/', 'subject', name='subject')
)
