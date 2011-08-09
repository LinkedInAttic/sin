from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlquote

def login_required(function=None):
  def wrapped(request, *args, **kwargs):
    if request.user.is_anonymous():
      path = urlquote(request.get_full_path())
      url = reverse('login') + "?next=%s" % path
      return HttpResponseRedirect(url)
    return function(request, *args, **kwargs)
  return wrapped

