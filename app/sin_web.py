#!/usr/bin/env python
import os, sys, logging, signal

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '../..'))

APP_HOME = os.path.join(SIN_HOME, 'app')

appsettings = 'settings'
apppath = APP_HOME

os.environ['DJANGO_SETTINGS_MODULE'] = appsettings
if apppath:
  sys.path.insert(0, apppath)

from twisted.internet import task, reactor
from twisted.python import log, threadpool
from twisted.web import server, resource, wsgi, static

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

from content_store.models import ContentStore 

class Root(resource.Resource):
  def __init__(self, WSGI):
    resource.Resource.__init__(self)
    self.WSGI = WSGI

  def getChild(self, path, request):
    request.prepath.pop()
    request.postpath.insert(0, path)
    request.content.seek(0, 0)
    return self.WSGI

pool = threadpool.ThreadPool()

def handle_signal(signum,stackframe):
  if signum in [signal.SIGINT, signal.SIGTERM]:
    ### Cleanup ###
    pool.stop()
    reactor.stop()

signal.signal(signal.SIGHUP, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def main(argv):
  logging.basicConfig(format='[%(asctime)s]%(levelname)-8s"%(message)s"', datefmt='%Y-%m-%d %a %H:%M:%S')
  
  verbose = True
  if '-q' in sys.argv:
    verbose = False
  
  if verbose:
    logging.getLogger().setLevel(logging.NOTSET)
  
  static_files = static.File(os.path.join(os.path.join(SIN_HOME, 'admin')))
  WSGI = wsgi.WSGIResource(reactor, pool, WSGIHandler())
  root = Root(WSGI)
  root.putChild('static', static_files)
  
  log.startLogging(sys.stdout)
  site = server.Site(root)
  reactor.listenTCP(settings.SIN_LISTEN, site)
  pool.start()
  reactor.run(installSignalHandlers=False)

def target(*args):
  return main, None

if __name__ == '__main__':
  main(sys.argv)
