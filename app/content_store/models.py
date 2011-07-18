import logging, urllib2
import django.utils.log
from django.db import models
from django.db.models import Max
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from utils import enum
from utils.enum import to_choices
from utils import json

from cluster.models import Group, Node
import time
import socket

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

default_schema = {
  "facets": [
  ],
  "table": {
    "columns": [
      {
        "from": "",
        "index": "ANALYZED",
        "multi": False,
        "name": "contents",
        "store": "NO",
        "termvector": "NO",
        "type": "text"
      }
    ],
    "compress-src-data": True,
    "delete-field": "isDeleted",
    "src-data-store": "lucene",
    "src-data-field": "src_data",
    "uid": "id"
  }
}

class ContentStoreQuerySet(models.query.QuerySet):
  def to_map_list(self):
    objs = list(self)
    nodes = Node.objects.filter(group__in=[o.group_id for o in objs]).values('group_id').annotate(host=Max('host'))
    node_map = dict([(o['group_id'], o['host']) for o in nodes])
    for obj in objs:
      obj.broker_host = node_map[obj.group_id]
    return [store.to_map() for store in objs]

class ContentStoreManager(models.Manager):
  def get_query_set(self):
    return ContentStoreQuerySet(model=self.model, using=self._db)

SUPPORTED_COLUMN_TYPES = set([
  'int', 'short', 'char', 'long', 'float', 'double', 'string', 'date', 'text'])
SUPPORTED_FACET_TYPES = set(['simple', 'path', 'range', 'multi', 'compact-multi'])

class ContentStore(models.Model):
  _broker_host_cache = None

  sensei_port_base = 10000
  broker_port_base = 15000

  name = models.CharField(max_length=20, unique=True)
  description = models.CharField(max_length=1024,unique=False)

  replica = models.IntegerField(default=2)
  partitions = models.IntegerField(default=10)

  config = models.TextField(default=json.json_encode(default_schema))

  created = models.DateTimeField(auto_now_add=True)

  status = models.SmallIntegerField(choices=to_choices(enum.STORE_STATUS),
    default=enum.STORE_STATUS['new'])

  group = models.ForeignKey(Group, related_name="stores", default=1)

  objects = ContentStoreManager()

  def get_sensei_port(self):
    return self.sensei_port_base + self.pk

  sensei_port = property(get_sensei_port)

  def get_broker_port(self):
    return self.broker_port_base + self.pk

  broker_port = property(get_broker_port)

  def get_broker_host(self):
    if not self._broker_host_cache:
      self._broker_host_cache = self.group.nodes.order_by('?')[0].host

    return self._broker_host_cache

  def set_broker_host(self, broker_host):
    self._broker_host_cache = broker_host

  broker_host = property(get_broker_host, set_broker_host)

  def get_running_info(self):
    if self.status != enum.STORE_STATUS['running']:
      return {}

    res = {}
    retry = 20
    while retry > 0:
      retry -= 1
      try:
        url = 'http://%s:%s/sensei/sysinfo' % (socket.gethostbyname(self.broker_host), self.broker_port)
        doc = urllib2.urlopen(url).read()
        res = simplejson.loads(doc.encode('utf-8'))
        if res.get(u'clusterinfo') == []:
          logger.info("Clusterinfo is not available yet.  Try again...")
          time.sleep(1)
        else:
          break;
      except:
        # logging.exception(e)
        logger.info("Hit an exception. Try to get sysinfo again...")
        time.sleep(1)

    return res

  running_info = property(get_running_info)

  def validate_config(self):  #TODO: do more validation.
    def validate_facet(obj):
      if not obj.get('name'):
        return (False, 'Facet name is required.')
      if obj.get('type') not in SUPPORTED_FACET_TYPES:
        return (False, 'Facet type %s is not valid, supported types are %s.' % (obj.get('type'), SUPPORTED_FACET_TYPES))
      return (True, None)

    def validate_column(obj):
      if not obj.get('name'):
        return (False, 'Column name is required.')
      if obj.get('type') not in SUPPORTED_COLUMN_TYPES:
        return (False, 'Column type %s is not valid, supported types are %s.' % (obj.get('type'), SUPPORTED_COLUMN_TYPES))
      return (True, None)

    def validate_table(obj):
      for column in obj['columns']:
        valid, error = validate_column(column)
        if not valid:
          return (valid, error)

      # TODO: remove hard coded delete-field.
      obj['delete-field'] = 'isDeleted'

      return (True, None)

    try:
      config = simplejson.loads(self.config)
      for facet in config['facets']:
        valid, error = validate_facet(facet)
        if not valid:
          return (valid, error)
      valid, error = validate_table(config['table'])
      if not valid:
        return (valid, error)

      self.config = json.json_encode(config)
    except Exception as e:
      logging.exception(e)
      return (False, 'Configuration is not valid.')

    return (True, None)

  def to_map(self):
    """
    Do not use this method if you are getting a list of maps of this,
    use ContentStoreQuerySet.to_map_list instead.
    """
    obj = {
      'id': self.id,
      'name': self.name,
      'replica': self.replica,
      'partitions': self.partitions,
      'sensei_port': self.sensei_port,
      'broker_host': self.broker_host,
      'broker_port': self.broker_port,
      'config': self.config,
      'created': self.created,
      'running_info': self.running_info,
      'status': self.status,
      'status_display': unicode(enum.STORE_STATUS_DISPLAY[self.status]),
      'description' : self.description,
    }
    return obj

