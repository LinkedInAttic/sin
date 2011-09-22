from django import template
from django.conf import settings
from django.contrib.auth import login as dj_login, logout as dj_logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from django.shortcuts import render_to_response

from decorators import login_required
from utils import enum

@login_required
def mydash(request):
  return render_to_response('mydash.html', {
  }, context_instance=template.RequestContext(request))


def index(request):
  if request.method == 'POST':
    form = AuthenticationForm(request, request.POST)
    if form.is_valid():
      dj_login(request, form.get_user())
  else:
    request.session.set_test_cookie()
    form = AuthenticationForm(request)
    
  return render_to_response('index.html', {
    "form" : form
  }, context_instance=template.RequestContext(request))
  
def home(request):
  return render_to_response('home.html', {
  }, context_instance=template.RequestContext(request))

@login_required
def dashboard(request):
  return render_to_response('dashboard.html', {
  }, context_instance=template.RequestContext(request))

def downloads(request):
  return render_to_response('downloads.html', {
  }, context_instance=template.RequestContext(request))

def get_started(request):
  return render_to_response('get_started.html', {
  }, context_instance=template.RequestContext(request))

def documentation(request):
  return render_to_response('documentation.html', {
  }, context_instance=template.RequestContext(request))

def developers(request):
  return render_to_response('developers.html', {
  }, context_instance=template.RequestContext(request))

def team(request):
  return render_to_response('team.html', {
  }, context_instance=template.RequestContext(request))

def login(request):
  next = request.REQUEST.get('next', reverse('home'))

  if request.user.is_authenticated():
    return HttpResponseRedirect(next)

  if request.method == 'POST':
    form = AuthenticationForm(request, request.POST)
    if form.is_valid():
      dj_login(request, form.get_user())
      return HttpResponseRedirect(next)
  else:
    request.session.set_test_cookie()
    form = AuthenticationForm(request)

  return render_to_response('login.html', {
    'form': form,
    'next': next,
    }, context_instance=template.RequestContext(request))

def register(request):
  next = request.REQUEST.get('next', reverse('home'))

  if request.user.is_authenticated():
    return HttpResponseRedirect(next)

  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      auth_form = AuthenticationForm(request, {
        'username': request.POST.get('username'),
        'password': request.POST.get('password1'),
      })
      if auth_form.is_valid():  # Should always happen.
        dj_login(request, auth_form.get_user())
      return HttpResponseRedirect(next)
  else:
    request.session.set_test_cookie()
    form = UserCreationForm()

  return render_to_response('register.html', {
    'form': form,
    'next': next,
    }, context_instance=template.RequestContext(request))

def logout(request):
  dj_logout(request)
  return HttpResponseRedirect(reverse('index'))

