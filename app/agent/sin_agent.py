import sys, json
import random, os, subprocess
from twisted.internet import reactor
from twisted.web import server, resource
from twisted.web.resource import Resource
from twisted.web.static import File
from twisted.python import log
from datetime import datetime

SENSEI_HOME = '/tmp/sensei/'
STORE_HOME = '/tmp/store/'

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
      sensei_port = request.args["sensei_port"][0]
      broker_port = request.args["broker_port"][0]
      sensei_properties = request.args["sensei_properties"][0]
      sensei_custom_facets = request.args["sensei_custom_facets"][0]
      sensei_plugins = request.args["sensei_plugins"][0]
      schema = request.args["schema"][0]
      log.msg("Starting store %" % name)
      return doStartStore(name, sensei_port, broker_port,
                          sensei_properties, sensei_custom_facets,
                          sensei_plugins, schema)
    except:
      log.err()
      return "Error"

  def render_POST(self, request):
    return self.render_GET(request)


class RestartStore(Resource):

  def render_GET(self, request):
    """
    Restart a Sensei store.
    """
    global running
    try:
      name = request.args["name"][0]
      sensei_port = request.args["sensei_port"][0]
      broker_port = request.args["broker_port"][0]
      sensei_properties = request.args["sensei_properties"][0]
      sensei_custom_facets = request.args["sensei_custom_facets"][0]
      sensei_plugins = request.args["sensei_plugins"][0]
      schema = request.args["schema"][0]

      pid = running.get(name)
      if pid:
        log.msg("Stopping existing process for store %s" % name)
        os.system("kill %s" % pid)
        del running[name]
      else:
        log.err("Store %s is not running" % name)

      log.msg("Restarting store %s" % name)
      return doStartStore(name, sensei_port, broker_port,
                          sensei_properties, sensei_custom_facets,
                          sensei_plugins, schema)
    except:
      log.err()
      return "Error"

  def render_POST(self, request):
    return self.render_GET(request)


def doStartStore(name, sensei_port, broker_port,
                 sensei_properties, sensei_custom_facets,
                 sensei_plugins, schema):
  """
  Do the real work to get a Sensei server started for a store.
  """
  classpath1 = os.path.join(SENSEI_HOME, 'target/*')
  classpath2 = os.path.join(SENSEI_HOME, 'target/lib/*')
  log4jclasspath = os.path.join(SENSEI_HOME,'resources')

  classpath = "%s:%s:%s" % (classpath1,classpath2,log4jclasspath)

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

  outFile = open(os.path.join(logs, "std-output"), "w+")
  errFile = open(os.path.join(logs, "std-error"), "w+")

  cmd = ["nohup", "java", "-server", "-d64", "-Xmx1g", "-Xms1g", "-XX:NewSize=256m", "-classpath", classpath, "-Dlog.home=%s" % logs, "com.sensei.search.nodes.SenseiServer", conf, "&"]
  print ' '.join(cmd)
  p = subprocess.Popen(cmd, cwd=SENSEI_HOME, stdout=outFile, stderr=errFile)
  running[name] = p.pid
  return "Ok"


class StopStore(Resource):
  def render_GET(self, request):
    """
    Stop a Sensei store.
    """
    log.msg("in StopStore...")
    global running
    try:
      name = request.args["name"][0]
      pid = running.get(name)
      if pid:
        os.system("kill %s" % pid)
        del running[name]
      return "Stopped %s" % pid
    except:
      log.err()
      return "Error"

  def render_POST(self, request):
    return self.render_GET(request)

VIEWS = {
  "start-store": StartStore(),
  "stop-store": StopStore(),
  "restart-store": RestartStore()
}

if __name__ == '__main__':
  root = Root()
  for viewName, className in VIEWS.items():
    # Add the view to the web service
    root.putChild(viewName, className)
  log.startLogging(sys.stdout)
  log.msg("Starting server: %s" % str(datetime.now()))
  server = server.Site(root)
  reactor.listenTCP(SIN_AGENT_PORT, server)
  reactor.run()
