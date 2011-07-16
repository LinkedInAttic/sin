from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('views',
  # Examples:
  # url(r'^$', 'sinApp.views.home', name='home'),
  # url(r'^sinApp/', include('sinApp.foo.urls')),

  url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
  url(r'^admin/', include(admin.site.urls)),

  url(r'^$', 'home', name='home'),

  url(r'^cluster/', include('cluster.urls')),
  url(r'^store/', include('content_store.urls')),
)
