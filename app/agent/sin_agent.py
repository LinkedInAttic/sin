#!/usr/bin/env python
import sys, json, shutil, errno, platform, signal, commands
import random, os, subprocess
from twisted.internet import defer, reactor
from twisted.web import server, resource
from twisted.web.client import downloadPage
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.python import log
from datetime import datetime
import time
from twisted.web.server import NOT_DONE_YET
import zookeeper
import threading
import logging
from optparse import OptionParser
import socket

app_settings = 'settings'
os.environ['DJANGO_SETTINGS_MODULE'] = app_settings

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '../../..'))
APP_HOME = os.path.join(SIN_HOME, 'app')
app_path = APP_HOME

if app_path:
  sys.path.insert(0, app_path)

from sincc import SinClusterClient
from django.conf import settings

from utils import is_current_host

CALL_BACK_LATER = 'CallBackLater'

#
# The dict for all running Sensei processes
#
running = {}

#
# Main server resource
#
class Root(Resource):

  def render_GET(self, request):
    """Get response method for the root resource localhost:8000/"""

    return 'Welcome to the REST API'

  def getChild(self, name, request):
    """Overwrite the get child function so that we can handle invalid requests."""

    if name == '':
      return self
    else:
      if name in VIEWS.keys():
        return Resource.getChild(self, name, request)
      else:
        return PageNotFoundError()


class PageNotFoundError(Resource):

  def render_GET(self, request):
    return 'Page Not Found!'


class StartStore(Resource):

  def render_GET(self, request):
    """Start a Sensei store."""

    global running
    try:
      name = request.args["name"][0]
      p = running.get(name)
      if p:
        return json.dumps({
          'ok':  False,
          'msg': 'store "%s" already started.' % name,
        })

      vm_args              = request.args["vm_args"][0]
      sensei_port          = request.args["sensei_port"][0]
      broker_port          = request.args["broker_port"][0]
      sensei_properties    = request.args["sensei_properties"][0]
      sensei_custom_facets = request.args["sensei_custom_facets"][0]
      sensei_plugins       = request.args["sensei_plugins"][0]
      schema               = request.args["schema"][0]
      webapps              = json.loads(request.args["webapps"][0].encode('utf-8'))
      resources            = json.loads(request.args["resources"][0].encode('utf-8'))
      libs                 = json.loads(request.args["libs"][0].encode('utf-8'))

      log.msg("Starting store %s" % name)
      d = doStartStore(name, vm_args, sensei_port, broker_port,
                       sensei_properties, sensei_custom_facets,
                       sensei_plugins, schema, webapps, resources,
                       libs)

      def cbStartFinished(res):
        request.write(res)
        request.finish()
      d.addCallback(cbStartFinished)
      return NOT_DONE_YET
    except Exception as e:
      log.err()
      return json.dumps({
        'ok': False,
        'msg': str(e),
      })

  def render_POST(self, request):
    return self.render_GET(request)


class RestartStore(Resource):

  def render_GET(self, request, isCallback=False):
    """Restart a Sensei store."""

    try:
      name    = request.args["name"][0]
      vm_args = request.args["vm_args"][0]

      res, msg = doStopStore(name)
      if msg == CALL_BACK_LATER:
        reactor.callLater(1, self.render_GET, request, True)
        return NOT_DONE_YET

      sensei_port          = request.args["sensei_port"][0]
      broker_port          = request.args["broker_port"][0]
      sensei_properties    = request.args["sensei_properties"][0]
      sensei_custom_facets = request.args["sensei_custom_facets"][0]
      sensei_plugins       = request.args["sensei_plugins"][0]
      schema               = request.args["schema"][0]
      webapps              = json.loads(request.args["webapps"][0].encode('utf-8'))
      resources            = json.loads(request.args["resources"][0].encode('utf-8'))
      libs                 = json.loads(request.args["libs"][0].encode('utf-8'))

      if res:
        log.msg("Restarting store %s" % name)
        d = doStartStore(name, vm_args, sensei_port, broker_port,
                         sensei_properties, sensei_custom_facets,
                         sensei_plugins, schema, webapps, resources,
                         libs)
        def cbStartFinished(res):
          request.write(res)
          request.finish()
        d.addCallback(cbStartFinished)
        return NOT_DONE_YET

      resp = {
        'ok': res,
        'msg': msg,
        }
      if isCallback:
        request.write(json.dumps(resp))
        request.finish()
      else:
        return json.dumps(resp)
    except Exception as e:
      log.err()
      resp = {
        'ok': False,
        'msg': str(e),
      }
      if isCallback:
        request.write(json.dumps(resp))
        request.finish()
      else:
        return json.dumps(resp)

  def render_POST(self, request):
    return self.render_GET(request)


def doStartStore(name, vm_args, sensei_port, broker_port,
                 sensei_properties, sensei_custom_facets,
                 sensei_plugins, schema, webapps, resources,
                 libs):
  """Do the real work to get a Sensei server started for a store."""

  store_home = os.path.join(settings.STORE_HOME, name)
  def _ensure_dir(d):
    try:
      os.makedirs(d)
    except:
      pass

  def _refresh_dir(d):
    try:
      shutil.rmtree(d)
    except:
      pass
    _ensure_dir(d)

  index = os.path.join(store_home, 'index')
  _ensure_dir(index)

  conf = os.path.join(store_home, 'conf')
  _ensure_dir(conf)

  webapp_dir = os.path.join(store_home, 'webapp')
  _refresh_dir(webapp_dir)

  resource_dir = os.path.join(store_home, 'resource')
  _refresh_dir(resource_dir)

  lib_dir = os.path.join(store_home, 'lib')
  _refresh_dir(lib_dir)

  logs = os.path.join(store_home, 'logs')
  _ensure_dir(logs)

  out_file = open(os.path.join(conf, 'sensei.properties'), 'w+')
  try:
    out_file.write(sensei_properties)
    out_file.flush()
  finally:
    out_file.close()

  out_file = open(os.path.join(conf, 'custom-facets.xml'), 'w+')
  try:
    out_file.write(sensei_custom_facets)
    out_file.flush()
  finally:
    out_file.close()

  out_file = open(os.path.join(conf, 'plugins.xml'), 'w+')
  try:
    out_file.write(sensei_plugins)
    out_file.flush()
  finally:
    out_file.close()

  out_file = open(os.path.join(conf, 'schema.json'), 'w+')
  try:
    out_file.write(schema)
    out_file.flush()
  finally:
    out_file.close()

  if not vm_args:
    vm_args = ['-Xmx1g', '-Xms1g', '-XX:NewSize=256m']
  else:
    vm_args = vm_args.split()

  def start_sensei():
    outFile = open(os.path.join(logs, "std-output"), "w+")
    errFile = open(os.path.join(logs, "std-error"), "w+")

    classpath = "%s:%s" % (resource_dir, os.path.join(lib_dir, '*'))

    architecture = "-d%s" % platform.architecture()[0][:2]

    cmd = ["nohup", "java", "-server", architecture] + vm_args +["-classpath", classpath,
           "-Dlog.home=%s" % logs, "com.senseidb.search.node.SenseiServer", conf, "&"]
    print ' '.join(cmd)
    p = subprocess.Popen(cmd, cwd=store_home, stdout=outFile, stderr=errFile)
    running[name] = p

  d = defer.Deferred()
  ongoing_set = set([f['url'] for f in webapps])
  ongoing_set.update([f['url'] for f in resources])
  ongoing_set.update([f['url'] for f in libs])

  def cbDownloaded(res, base, ongoing):
    print "%s downloaded" % ongoing
    ongoing_set.remove(ongoing['url'])
    if not ongoing_set: # The last one.
      start_sensei()
      d.callback(json.dumps({
        'ok': True,
      }))

  def cbErrorDownload(res, base, ongoing):
    retry = ongoing.get('retry', 0)
    if retry < 20:
      print "Error download '%s': %s (retring)" % (ongoing, res)
      reactor.callLater(1, _download, base, ongoing)
    else:
      print "Error download '%s': %s" % (ongoing, res)
      d.callback(json.dumps({
        'ok': False,
        'msg': "Error download '%s': %s" % (ongoing, res),
      }))

  def _download(base, ongoing):
    path = os.path.join(base, ongoing['path'])
    _ensure_dir(path)

    fullname = os.path.join(path, ongoing['name']).encode('utf-8')
    url      = ongoing['url'].encode('utf-8')

    downloadPage(url, fullname).addCallbacks(
        cbDownloaded, cbErrorDownload, callbackArgs=[base, ongoing], errbackArgs=[base, ongoing])

  for ongoing in webapps:
    _download(webapp_dir, ongoing)

  for ongoing in resources:
    _download(resource_dir, ongoing)

  for ongoing in libs:
    _download(lib_dir, ongoing)

  return d

class DeleteStore(Resource):
  def render_GET(self, request, isCallback=False):
    """Delete a Sensei store."""

    try:
      name = request.args["name"][0]
      log.msg('Delete store %s' % name)
      res, msg = doStopStore(name, True)
      if msg == CALL_BACK_LATER:
        reactor.callLater(1, self.render_GET, request, True)
        return NOT_DONE_YET

      if res:
        store_home = os.path.join(settings.STORE_HOME, name)
        try:
          shutil.rmtree(store_home)
        except OSError as ose:
          if ose.errno == errno.ENOENT:
            log.msg("Store home for %s does not exist." % name)
          else:
            raise
        resp = {
          'ok': True,
        }
      else:
        resp = {
          'ok': res,
          'msg': msg,
        }
      
      if isCallback:
        request.write(json.dumps(resp))
        request.finish()
      else:
        return json.dumps(resp)
    except Exception as e:
      log.err()
      resp = {
        'ok': False,
        'msg': str(e),
      }
      return json.dumps(resp)

  def render_POST(self, request):
    return self.render_GET(request)

class StopStore(Resource):
  def render_GET(self, request, isCallback=False):
    """Stop a Sensei store."""

    try:
      name = request.args["name"][0]
      log.msg('Stopping store %s' % name)

      res, msg = doStopStore(name)
      if msg == CALL_BACK_LATER:
        reactor.callLater(1, self.render_GET, request, True)
        return NOT_DONE_YET

      resp = {
        'ok': res,
        'msg': msg,
      }

      if isCallback:
        request.write(json.dumps(resp))
        request.finish()
      else:
        return json.dumps(resp)
    except:
      log.err()
      request.write("Error")
      request.finish()

  def render_POST(self, request):
    return self.render_GET(request)


def doStopStore(name, kill=False):
  """Stop a Sensei store."""
  global running
  try:
    p = running.get(name)
    if p:
      log.msg("Stopping existing process %d for store %s" % (p.pid, name))
      if kill:
        p.kill()
      else:
        p.terminate()
      psOutput = ''
      ps = subprocess.Popen("ps ax|grep -e '^%d.*%s'" % (p.pid, name),
                                  shell=True, stdout=subprocess.PIPE)
      while True:
        try:
          psOutput += ps.stdout.read()
          break
        except IOError as ioe:
          if ioe.errno == errno.EINTR:
            pass
          else:
            raise

      if len(psOutput) > 0:
        print "Waiting for process %d to die" % p.pid
        return False, CALL_BACK_LATER

      del running[name]
    else:
      log.err("Store %s is not running" % name)
    return True, None
  except Exception as e:
    log.err()
    return False, str(e)


VIEWS = {
  "start-store": StartStore(),
  "stop-store": StopStore(),
  "restart-store": RestartStore(),
  "delete-store": DeleteStore(),
}

class SinClusterListener(object):

  def __call__(self, nodes):
    log.msg("Current nodes =", [(key, node.get_url()) for key, node in nodes.iteritems()])


cluster_client = None

def handle_signal(signum, stackframe):
  if signum in [signal.SIGINT, signal.SIGTERM]:
    ### Cleanup ###
    log.msg('Do some cleanups before shutdown...')

    reactor.stop()
    if cluster_client:
      cluster_client.mark_node_unavailable(node_id)

    processes = running.values()
    for p in processes:
      p.terminate()

    log.msg('Waiting for all store processes to terminate (will force to kill them after 300 seconds).')
    beginning = time.time()
    while True:
      all_dead = True
      for p in processes:
        if p.poll() is None:
          all_dead = False
          break
      if all_dead:
        break
      passed = time.time() - beginning
      if passed > 300:
        for p in processes:
          if p.poll() is None:
            p.kill()
        break
      time.sleep(0.1)
    if cluster_client:
      cluster_client.shutdown()

signal.signal(signal.SIGHUP, handle_signal)
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

if __name__ == '__main__':
  usage = "usage: %prog [options] node_id"
  parser = OptionParser(usage=usage)
  parser.add_option("", "--host", dest="host",
                    default="", help="Host name of this node (used for overriding default one)")
  (options, args) = parser.parse_args()

  if len(args) != 1:
    print "Required argument, node_id, is missing"
    print usage
    sys.exit(1)

  node_id = int(args[0])

  root = Root()
  for viewName, className in VIEWS.items():
    # Add the view to the web service
    root.putChild(viewName, className)
  log.startLogging(sys.stdout)
  log.msg("Starting server: %s" % str(datetime.now()))

  server = server.Site(root)
  
  cluster_client = SinClusterClient(settings.SIN_SERVICE_NAME, settings.ZOOKEEPER_URL, settings.ZOOKEEPER_TIMEOUT)
  cluster_client.logger.setLevel(logging.DEBUG)
  cluster_client.logger.addHandler(logging.StreamHandler())
  cluster_client.add_listener(SinClusterListener())

  nodes = cluster_client.get_registered_nodes()
  if nodes.get(node_id):
    node = nodes[node_id]
    host = None
    if options.host != "":
      host = options.host
    if settings.DISABLE_HOST_CHECK or is_current_host(node.get_host(), host):
      # Force this node to be offline first.  (In the case where
      # sin_agent is stopped and then immediately restarted, the
      # ephemeral node created in the last session may still be there
      # when sin_agent is restarted.)
      cluster_client.mark_node_unavailable(node_id)
      reactor.listenTCP(node.get_port(), server)
      log.msg("Mark %s available" % node.get_url())
      cluster_client.mark_node_available(node_id, node.get_url())
    else:
      log.err("Hostname, %s, might not have been registered!" % host)
      sys.exit(1)
  else:
    log.err("Node id %d is not registered!" % node_id)
    sys.exit(1)

  reactor.run(installSignalHandlers=False)
