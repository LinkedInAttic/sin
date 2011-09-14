from django.conf.urls.defaults import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('views',
  # Examples:
  # url(r'^$', 'sinApp.views.home', name='home'),
  # url(r'^sinApp/', include('sinApp.foo.urls')),

  url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
  url(r'^admin/', include(admin.site.urls)),

  url(r'^index/?$', 'index', name='index'),
  url(r'^$', 'home', name='home'),
  url(r'^dashboard/?$', 'dashboard', name='dashboard'),
  url(r'^downloads/?$', 'downloads', name='downloads'),
  url(r'^get-started/?$', 'get_started', name='get_started'),
  url(r'^documentation/?$', 'documentation', name='documentation'),
  url(r'^developers/?$', 'developers', name='developers'),
  url(r'^team/?$', 'team', name='team'),

  url(r'^login/?$', 'login', name='login'),
  url(r'^register/?$', 'register', name='register'),
  url(r'^logout/?$', 'logout', name='logout'),

  url(r'^cluster/', include('cluster.urls')),
  url(r'^store/', include('content_store.urls')),
  url(r'^files/', include('files.urls')),
)
