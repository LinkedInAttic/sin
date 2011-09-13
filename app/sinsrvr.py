#!/usr/bin/env python
import os, sys, logging, signal
import json
import time

appsettings = 'settings'
os.environ['DJANGO_SETTINGS_MODULE'] = appsettings

from optparse import OptionParser
from cluster.models import Group, Node
import zookeeper
from sincc import SinClusterClient
from django.conf import settings

SIN_HOME = os.path.normpath(os.path.join(os.path.normpath(__file__), '../..'))
APP_HOME = os.path.join(SIN_HOME, 'app')

apppath = APP_HOME

if apppath:
  sys.path.insert(0, apppath)

class SinClusterListener(object):

  def __call__(self, nodes):
    for node in Node.objects.all():
      if nodes.get(node.id) == node.host:
        node.online = True
      else:
        node.online = False
      node.save()

if __name__ == '__main__':
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("-f", action="store_true", dest="force", help="Overwrite Sensei node info in database")
  (options, args) = parser.parse_args()

  zookeeper.set_log_stream(open("/dev/null"))
  cc = SinClusterClient(settings.SIN_SERVICE_NAME, settings.ZOOKEEPER_URL, settings.ZOOKEEPER_TIMEOUT)
  cc.add_listener(SinClusterListener())

  if options.force:
    for node in Node.objects.all():
      node.delete()

  for node in settings.SENSEI_NODES["nodes"]:
    if not Node.objects.filter(id=node["node_id"]).exists():
      Node.objects.create(id=node["node_id"], host=node["host"], agent_port=node["port"],
                          online=False, group=Group(pk=1))

  while True:
    time.sleep(1)
