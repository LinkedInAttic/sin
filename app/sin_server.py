#!/usr/bin/env python
import os, sys, logging, signal, time, traceback

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '../..'))

APP_HOME = os.path.join(SIN_HOME, 'app')

app_settings = 'settings'
app_path = APP_HOME

os.environ['DJANGO_SETTINGS_MODULE'] = app_settings
if app_path:
  sys.path.insert(0, app_path)

from twisted.internet import task, reactor
from twisted.python import log, threadpool
from twisted.web import server, resource, wsgi, static

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.handlers.wsgi import WSGIHandler

from optparse import OptionParser
import zookeeper
from sincc import SinClusterClient

from utils import enum

from content_store.models import ContentStore 
from content_store.views import do_start_store, find_doc, samples, samples_lock
from cluster.models import Group, Node
from sin_site.models import SinSite

logger = logging.getLogger("sin_server")

def initialize():
  current_site = Site.objects.get_current()
  try:
    sinsite = current_site.sinsite
  except SinSite.DoesNotExist:
    sinsite = SinSite.objects.create(name=current_site.name,
                                     domain=current_site.domain,
                                     site_ptr=current_site)
  sinsite.initialize()

class Root(resource.Resource):
  def __init__(self, WSGI):
    resource.Resource.__init__(self)
    self.WSGI = WSGI

  def getChild(self, path, request):
    request.prepath.pop()
    request.postpath.insert(0, path)
    request.content.seek(0, 0)
    return self.WSGI

pool = threadpool.ThreadPool(minthreads=settings.SIN_MIN_THREAD, maxthreads=settings.SIN_MAX_THREAD)

monitor_running = True
def monitoring():
  first_try = {}

  while monitor_running:
    with samples_lock:
      items = list(samples.items())

    for name, my_samples in items:
      with samples_lock:
        ids = list(my_samples)
      if ids:
        try:
          store = ContentStore.objects.get(name=name)
          doc = find_doc(store, ids[0])
          if doc:
            with samples_lock:
              my_samples.pop(0)
            try:
              del first_try[name]
            except: pass
          else:
            begin = first_try.get(name)
            if begin:
              if time.time() - begin > 30:
                # Timeout
                logger.critical("Problems with store %s, indexing delay is more than 30 seconds with UID %s" % (name, ids[0]))
                with samples_lock:
                  my_samples.pop(0)
                del first_try[name]
            else:
              first_try[name] = time.time()
        except Exception as e:
          logger.exception(e)

    time.sleep(5)

cluster_client = None

def handle_signal(signum, stackframe):
  if signum in [signal.SIGINT, signal.SIGTERM]:
    ### Cleanup ###
    pool.stop()
    reactor.stop()

    global monitor_running
    monitor_running = False

    if cluster_client:
      cluster_client.shutdown()
  elif signum in [signal.SIGUSR1, signal.SIGUSR2]:
    print 'Signal received.\nTraceback:\n' + ''.join(traceback.format_stack(stackframe))
    if signum == signal.SIGUSR2:
      import pdb
      pdb.set_trace()

class SinClusterListener(object):

  def __call__(self, nodes):
    # Get all available nodes from ZooKeeper and update the node status in DB
    logger.info("Current nodes = %s", [(key, node.get_url()) for key, node in nodes.iteritems()])
    for db_node in Node.objects.all():
      node = nodes.get(db_node.id)
      if node and node.get_host() == db_node.host:
        if not db_node.online:
          db_node.online = True
          db_node.save()

          logger.info('Node "%s: %s:%s" is now online, try to start all stores served by this node...' % (db_node.id,
                                                                                                          db_node.host,
                                                                                                          db_node.agent_port))
          for store in db_node.stores.filter(status=enum.STORE_STATUS['running']):
            try:
              do_start_store(None, store, node=db_node, with_running_info=False)
            except Exception as e:
              logger.exception(e);
      else:
        if db_node.online:
          logger.info('Node "%s: %s:%s" went offline.' % (db_node.id, db_node.host, db_node.agent_port))
          db_node.online = False
          db_node.save()

signal.signal(signal.SIGHUP,  handle_signal)
signal.signal(signal.SIGUSR1, handle_signal)
signal.signal(signal.SIGUSR2, handle_signal)
signal.signal(signal.SIGINT,  handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def main(argv):
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("-f", "--force", action="store_true", dest="force", help="Overwrite existing Sensei node info")
  parser.add_option("-c", "--reset", action="store_true", dest="reset", help="Remove all registered nodes and then exit")
  parser.add_option("-i", "--init", action="store_true", dest="init", help="Initialize nodes")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Verbose mode")
  (options, args) = parser.parse_args()

  logging.basicConfig(format='[%(asctime)s] %(levelname)-8s"%(message)s"', datefmt='%Y-%m-%d %a %H:%M:%S')
  
  if options.verbose:
    logger.setLevel(logging.NOTSET)

  initialize()

  zookeeper.set_log_stream(open("/dev/null"))
  global cluster_client
  cluster_client = SinClusterClient(settings.SIN_SERVICE_NAME, settings.ZOOKEEPER_URL, settings.ZOOKEEPER_TIMEOUT)
  cluster_client.logger.setLevel(logging.INFO)
  cluster_client.logger.addHandler(logging.StreamHandler())
  cluster_client.add_listener(SinClusterListener())

  if options.force or options.reset:
    cluster_client.reset()
    Node.objects.all().delete()
    logger.info("Removed all registered nodes from the system.")
    logger.info("You may want to shut down all the agents.")
    if options.reset:
      return

  for node in settings.SIN_NODES["nodes"]:
    if not Node.objects.filter(id=node["node_id"]).exists():
      Node.objects.create(id=node["node_id"], host=node["host"], agent_port=node["port"],
                          online=False, group=Group(pk=1))
    cluster_client.register_node(node["node_id"], node["host"], port=node["port"])

  if options.init:
    return

  # Reset online status.  Some node(s) might have gone offline while Sin
  # server was down, therefore the server did not get notified and still
  # keeps the old "online" status for the node(s).  If the node(s) are
  # still online, we will send the start-store commands to them anyway.
  # If a store is already running on a node, the start-store command
  # will simply become a no-op.
  Node.objects.filter(online=True).update(online=False)


  static_files = static.File(os.path.join(os.path.join(SIN_HOME, 'admin')))
  WSGI = wsgi.WSGIResource(reactor, pool, WSGIHandler())
  root = Root(WSGI)
  root.putChild('static', static_files)
  
  log.startLogging(sys.stdout)
  site = server.Site(root)
  reactor.listenTCP(settings.SIN_LISTEN, site)
  pool.start()

  def post_initialization():
    cluster_client.notify_all()

  reactor.callInThread(post_initialization)

  reactor.callInThread(monitoring)

  reactor.run(installSignalHandlers=False)

def target(*args):
  return main, None

if __name__ == '__main__':
  main(sys.argv)
