import json
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.http import urlquote

from content_store.models import ContentStore

def login_required(function=None):
  def wrapped(request, *args, **kwargs):
    if request.user.is_anonymous():
      path = urlquote(request.get_full_path())
      url = reverse('login') + "?next=%s" % path
      return HttpResponseRedirect(url)
    return function(request, *args, **kwargs)
  return wrapped

def api_key_required(function=None):
  def wrapped(request, store_name, *args, **kwargs):
    try:
      store = ContentStore.objects.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'store: %s does not exist.' % store_name
      }
      return HttpResponse(json.dumps(resp))
    if store.api_key != request.META.get('HTTP_X_SIN_API_KEY'):
      resp = {
        'ok' : False,
        'msg' : 'Invalid api key.'
      }
      return HttpResponse(json.dumps(resp))
    return function(request, store_name, *args, **kwargs)
  return wrapped

