import datetime, json, logging, os, threading
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils import enum, jolokia
from utils.enum import to_choices

class Group(models.Model):
  name = models.CharField(max_length=20)

class Node(models.Model):
  class Meta:
    unique_together = ("host", "agent_port")

  host         = models.CharField(max_length=40)
  agent_port   = models.IntegerField(default=6664)
  group        = models.ForeignKey(Group, related_name="nodes", null=True)
  online       = models.BooleanField(default=False)

  def __unicode__(self):
    return u"%s:%s:%s" % (self.group.name, self.host, self.agent_port)

class Membership(models.Model):
  node           = models.ForeignKey(Node, related_name="members")
  store          = models.ForeignKey("content_store.ContentStore", related_name="members")
  replica        = models.IntegerField(default=0)
  parts          = models.CommaSeparatedIntegerField(max_length=1024)
  bootstrapped   = models.DateTimeField(default=datetime.datetime.min)

  def load_index(self, uri=None):
    if not uri:
      uri = self.store.bootstrap_uri
    if not uri:
      return False, u'uri cannot be empty.'
    if self.store.status < enum.STORE_STATUS['running']:
      return False, 'Store "%s" is not running.' % self.store.name
    if not self.node.online:
      return False, u'Node "%s" is offline.' % self.node

    client = jolokia.Client('http://%s:%d/admin/jmx' % (self.node.host, self.store.broker_port))
    errors = []
    for part in json.loads(self.parts):
      res = client.request({
        "type"        : "exec",
        "mbean"       : "com.senseidb:zoie-name=pair-admin-%s-%s" % (self.node_id, part),
        "operation"   : "loadIndex",
        "arguments"   : [os.path.join(uri, str(part))]
      })
      if not (res and res.get('value')):
        errors.append(u'Loading index failed for node "%s" partition "%s": %s' % (self.node, part, json.dumps(res)))
        logging.error(errors[-1])

    if errors:
      return False, '\n'.join(errors)

    self.bootstrapped = datetime.datetime.now()
    self.save()
    return True, None

  def load_index_threaded(self, uri=None):
    if not uri:
      uri = self.store.bootstrap_uri
    if not uri:
      return False, u'uri cannot be empty.'
    if self.store.status < enum.STORE_STATUS['running']:
      return False, 'Store "%s" is not running.' % self.store.name
    if not self.node.online:
      return False, u'Node "%s" is offline.' % self.node

    client = jolokia.Client('http://%s:%d/admin/jmx' % (self.node.host, self.store.broker_port))
    errors = []
    parts = json.loads(self.parts)
    threads = []

    class RequestThread(threading.Thread):
      def __init__(self, member, part, *args, **kwargs):
        super(RequestThread, self).__init__(*args, **kwargs)
        self.member = member
        self.part = part

      def run(self):
        res = client.request({
          "type"        : "exec",
          "mbean"       : "com.senseidb:zoie-name=pair-admin-%s-%s" % (self.member.node_id, self.part),
          "operation"   : "loadIndex",
          "arguments"   : [os.path.join(uri, str(self.part))]
        })
        if not (res and res.get('value')):
          errors.append(u'Loading index failed for node "%s" partition "%s": %s' % (self.member.node, self.part, json.dumps(res)))
          logging.error(errors[-1])

    for part in parts:
      t = RequestThread(self, part)
      t.setDaemon(True)
      if (len(parts) - len(threads)) > 1:
        threads.append(t)
        t.start()
      else:
        t.run()

    for t in threads:
      t.join()

    if errors:
      return False, '\n'.join(errors)

    self.bootstrapped = datetime.datetime.now()
    self.save()
    return True, None

