from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('files.views',
  (r'^upload/?$', 'upload'),
)

