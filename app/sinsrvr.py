#!/usr/bin/env python
import os, sys, logging, signal
import json
import time

appsettings = 'settings'
os.environ['DJANGO_SETTINGS_MODULE'] = appsettings

from optparse import OptionParser
from cluster.models import Group, Node
import zookeeper
import threading
from sincc import SinClusterClient

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '../..'))
APP_HOME = os.path.join(SIN_HOME, 'app')

apppath = APP_HOME

if apppath:
  sys.path.insert(0, apppath)

class SinClusterListener(object):

  def __init__(self):
    self.mutex = threading.Lock()

  def __call__(self, nodes):
    self.mutex.acquire()
    print "===== Current nodes = ", nodes
    for node in Node.objects.all():
      if nodes.get(node.id) == node.host:
        node.online = True
      else:
        node.online = False
      node.save()
    self.mutex.release()

if __name__ == '__main__':
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("", "--connect-string", dest="servers",
                    default="localhost:2181", help="comma separated list of host:port (default localhost:2181)")
  parser.add_option("", "--timeout", dest="timeout", type="int",
                    default=5000, help="session timeout in milliseconds (default 5000)")
  parser.add_option("", "--nodes", dest="nodes",
                    help="JSON file contains all the nodes")
  (options, args) = parser.parse_args()
  
  zookeeper.set_log_stream(open("/dev/null"))
  cc = SinClusterClient("sin", options.servers, options.timeout)
  cc.add_listener(SinClusterListener())

  nodes = json.load(open(options.nodes))
  for node in nodes["nodes"]:
    Node.objects.create(id=node["node_id"]+100000, host=node["host"], agent_port=node["port"],
                        online=True, group=Group(pk=1))

  while True:
    time.sleep(1)
