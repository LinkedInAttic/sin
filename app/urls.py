from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'sinApp.views.home', name='home'),
    # url(r'^sinApp/', include('sinApp.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
	(r'^store/new-store/(?P<store_name>[^/]+)/?$','content_store.views.newStore'),
	(r'^store/delete-store/(?P<store_name>[^/]+)/?$','content_store.views.deleteStore'),
	(r'^store/update-config/(?P<store_name>[^/]+)/?$','content_store.views.updateConfig'),
	(r'^store/start-store/(?P<store_name>[^/]+)/?$','content_store.views.startStore'),
	(r'^store/restart-store/(?P<store_name>[^/]+)/?$','content_store.views.restartStore'),
	(r'^store/get-size/(?P<store_name>[^/]+)/?$','content_store.views.getSize'),
	(r'^store/get-doc/(?P<id>\d+)/(?P<store_name>[^/]+)/?$','content_store.views.getDoc'),
	(r'^store/add-doc/(?P<id>\d+)/(?P<store_name>[^/]+)/?$','content_store.views.addDoc'),
	(r'^store/available/(?P<store_name>[^/]+)/?$','content_store.views.available'),
	(r'^store/stores/$','content_store.views.stores'),
)
