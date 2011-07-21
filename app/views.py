from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.http import Http404

from utils import enum

def home(request):
  return HttpResponseRedirect('/static/index.html')

