from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('tweets.views',
  (r'^search/?$','search'),
)
