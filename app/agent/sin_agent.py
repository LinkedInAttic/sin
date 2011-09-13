import re, sys, json, shutil, errno, platform
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
from sincc import SinClusterClient
from optparse import OptionParser
import socket

appsettings = 'settings'
os.environ['DJANGO_SETTINGS_MODULE'] = appsettings

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '../../..'))
APP_HOME = os.path.join(SIN_HOME, 'app')
apppath = APP_HOME

if apppath:
  sys.path.insert(0, apppath)

from django.conf import settings

SENSEI_HOME = '/tmp/sensei/'
STORE_HOME = '/tmp/store/'
CALL_BACK_LATER = 'CallBackLater'

SIN_AGENT_PORT = 6664

#
# The dict for all running Sensei processes
#
running = {}

#
# Main server resource
#
class Root(Resource):

  def render_GET(self, request):
    """
    get response method for the root resource
    localhost:8000/
    """
    return 'Welcome to the REST API'

  def getChild(self, name, request):
    """
    We overrite the get child function so that we can handle invalid
    requests
    """
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
    """
    Start a Sensei store.
    """
    try:
      name = request.args["name"][0]
      vm_args = request.args["vm_args"][0]
      sensei_port = request.args["sensei_port"][0]
      broker_port = request.args["broker_port"][0]
      sensei_properties = request.args["sensei_properties"][0]
      sensei_custom_facets = request.args["sensei_custom_facets"][0]
      sensei_plugins = request.args["sensei_plugins"][0]
      schema = request.args["schema"][0]
      extensions = json.loads(request.args["extensions"][0].encode('utf-8'))
      log.msg("Starting store %s" % name)
      d = doStartStore(name, vm_args, sensei_port, broker_port,
                       sensei_properties, sensei_custom_facets,
                       sensei_plugins, schema, extensions)

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
    """
    Restart a Sensei store.
    """
    try:
      name = request.args["name"][0]
      vm_args = request.args["vm_args"][0]
      res, msg = doStopStore(name)
      if msg == CALL_BACK_LATER:
        reactor.callLater(1, self.render_GET, request, True)
        return NOT_DONE_YET

      sensei_port = request.args["sensei_port"][0]
      broker_port = request.args["broker_port"][0]
      sensei_properties = request.args["sensei_properties"][0]
      sensei_custom_facets = request.args["sensei_custom_facets"][0]
      sensei_plugins = request.args["sensei_plugins"][0]
      schema = request.args["schema"][0]
      extensions = json.loads(request.args["extensions"][0].encode('utf-8'))

      if res:
        log.msg("Restarting store %s" % name)
        d = doStartStore(name, vm_args, sensei_port, broker_port,
                         sensei_properties, sensei_custom_facets,
                         sensei_plugins, schema, extensions)
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
                 sensei_plugins, schema, extensions):
  """
  Do the real work to get a Sensei server started for a store.
  """
  store_home = os.path.join(STORE_HOME, name)
  index = os.path.join(store_home, 'index')
  try:
    os.makedirs(index)
  except:
    pass

  conf = os.path.join(store_home, 'conf')
  try:
    os.makedirs(conf)
  except:
    pass

  ext_dir = os.path.join(store_home, 'ext')
  try:
    shutil.rmtree(ext_dir)
  except:
    pass
  try:
    os.makedirs(ext_dir)
  except:
    pass

  logs = os.path.join(store_home, 'logs')
  try:
    os.makedirs(logs)
  except:
    pass

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

  custom_sensei = False

  if not vm_args:
    vm_args = '-Xmx1g -Xms1g -XX:NewSize=256m'

  def start_sensei():
    outFile = open(os.path.join(logs, "std-output"), "w+")
    errFile = open(os.path.join(logs, "std-error"), "w+")

    if custom_sensei:
      log4jclasspath = os.path.join(SENSEI_HOME,'resources')
      extension_classpath = os.path.join(ext_dir, '*')

      classpath = "%s:%s" % (log4jclasspath,extension_classpath)
    else:
      classpath1 = os.path.join(SENSEI_HOME, 'sensei-core/target/*')
      classpath2 = os.path.join(SENSEI_HOME, 'sensei-core/target/lib/*')
      log4jclasspath = os.path.join(SENSEI_HOME,'resources')
      extension_classpath = os.path.join(ext_dir, '*')

      classpath = "%s:%s:%s:%s" % (classpath1,classpath2,log4jclasspath,extension_classpath)

    architecture = "-d%s" % platform.architecture()[0][:2]

    cmd = ["nohup", "java", "-server", architecture, vm_args, "-classpath", classpath, "-Dlog.home=%s" % logs, "com.sensei.search.nodes.SenseiServer", conf, "&"]
    print ' '.join(cmd)
    p = subprocess.Popen(cmd, cwd=SENSEI_HOME, stdout=outFile, stderr=errFile)
    running[name] = p.pid

  if extensions:
    d = defer.Deferred()
    ext_set = set(extensions)

    def cbDownloaded(res, ext):
      print "%s downloaded" % ext
      ext_set.remove(ext)
      if not ext_set: # The last one.
        start_sensei()
        d.callback(json.dumps({
          'ok': True,
        }))

    def cbErrorDownload(res, ext):
      print "Error download '%s': %s" % (ext, res)
      d.callback(json.dumps({
        'ok': False,
        'msg': "Error download '%s': %s" % (ext, res),
      }))

    for ext in extensions:
      if re.match(r'[^\.]+\.sensei-.*\.jar', ext):
        custom_sensei = True
      downloadPage(ext.encode('utf-8'), os.path.join(ext_dir, os.path.basename(ext))).addCallbacks(
          cbDownloaded, cbErrorDownload, callbackArgs=[ext], errbackArgs=[ext])

    return d

  start_sensei()
  return defer.succeed(json.dumps({'ok': True}))

class DeleteStore(Resource):
  def render_GET(self, request, isCallback=False):
    """Delete a Sensei store."""
    log.msg("in DeleteStore...")
    try:
      name = request.args["name"][0]
      res, msg = doStopStore(name)
      if msg == CALL_BACK_LATER:
        reactor.callLater(1, self.render_GET, request, True)
        return NOT_DONE_YET

      if res:
        store_home = os.path.join(STORE_HOME, name)
        try:
          shutil.rmtree(store_home)
        except OSError as ose:
          if ose.errno == errno.ENOENT:
            log.msg("store home for %s does not exist." % name)
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
    log.msg("in StopStore...")
    try:
      name = request.args["name"][0]

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


def doStopStore(name):
  """Stop a Sensei store."""
  global running
  try:
    pid = running.get(name)
    if pid:
      log.msg("Stopping existing process %d for store %s" % (pid, name))
      os.kill(pid, 15)
      psOutput = ''
      ps = subprocess.Popen("ps ax|grep -e '^%d.*%s'" % (pid, name),
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
        print "Waiting for process %d to die" % pid
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
    log.msg("Current nodes = ", nodes)

if __name__ == '__main__':
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("", "--node", dest="node",
                    help="node id")
  (options, args) = parser.parse_args()

  root = Root()
  for viewName, className in VIEWS.items():
    # Add the view to the web service
    root.putChild(viewName, className)
  log.startLogging(sys.stdout)
  log.msg("Starting server: %s" % str(datetime.now()))

  cc = SinClusterClient(settings.SIN_SERVICE_NAME, settings.ZOOKEEPER_URL, settings.ZOOKEEPER_TIMEOUT)
  cc.add_listener(SinClusterListener())
  # XXX add validation here
  cc.add_node(options.node); time.sleep(1)
  cc.mark_node_available(options.node, socket.gethostname()); time.sleep(1)

  server = server.Site(root)
  reactor.listenTCP(SIN_AGENT_PORT, server)
  reactor.run()
