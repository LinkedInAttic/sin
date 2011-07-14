from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('cluster.views',
  (r'^(?P<group_id>[^/]+)/nodes/?$','nodes'),
  (r'^(?P<group_id>[^/]+)/nodes/count/?$','nodes_count'),
)
