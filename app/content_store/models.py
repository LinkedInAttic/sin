import logging, urllib2, json, datetime
import django.utils.log
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from utils import enum, totimestamp
from utils.enum import to_choices
from utils.template import load_template_source

from cluster.models import Group, Node, Membership
from files.models import File
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

def get_store_name_cache_key(name):
  return 'store_%s' % name

class ContentStoreQuerySet(models.query.QuerySet):
  def to_map_list(self, with_api_key=False):
    objs = list(self)
    nodes = Node.objects.filter(group__in=[o.group_id for o in objs]).values('group_id').annotate(host=Max('host'))
    node_map = dict([(o['group_id'], o['host']) for o in nodes])
    for obj in objs:
      obj.broker_host = node_map[obj.group_id]
    return [store.to_map(with_api_key) for store in objs]

  def get(self, *args, **kwargs):
    if (not args) and len(kwargs) == 1 and 'name' in kwargs:
      cache_key = get_store_name_cache_key(kwargs['name'])
      obj = cache.get(cache_key)
      if not obj:
        obj = super(ContentStoreQuerySet, self).get(*args, **kwargs)
        cache.set(cache_key, obj)
      return obj
    return super(ContentStoreQuerySet, self).get(*args, **kwargs)

class ContentStoreManager(models.Manager):
  def get_query_set(self):
    return ContentStoreQuerySet(model=self.model, using=self._db)

SUPPORTED_COLUMN_TYPES = set([
  'int', 'short', 'char', 'long', 'float', 'double', 'string', 'date', 'text'])
SUPPORTED_FACET_TYPES = set(['simple', 'path', 'range', 'multi', 'compact-multi', 'custom'])

class ContentStore(models.Model):
  _broker_host_cache = None

  sensei_port_base = 10000
  broker_port_base = 15000

  name = models.CharField(max_length=20, unique=True)
  api_key = models.CharField(max_length=40)
  description = models.CharField(max_length=1024)

  replica = models.IntegerField(default=2)
  partitions = models.IntegerField(default=2)

  # config = models.TextField(default=json.dumps(default_schema))

  created = models.DateTimeField(auto_now_add=True)

  status = models.SmallIntegerField(choices=to_choices(enum.STORE_STATUS),
    default=enum.STORE_STATUS['new'])

  group = models.ForeignKey(Group, related_name="stores", default=1)

  nodes = models.ManyToManyField(Node, through="cluster.Membership")

  collaborators = models.ManyToManyField(User, related_name="my_stores")

  objects = ContentStoreManager()

  def get_current_config(self):
    try:
      try:
        config = self.configs.get(active=True)
      except StoreConfig.DoesNotExist:
        config = self.configs.order_by('-id', '-last_activated')[:1].get()
    except StoreConfig.DoesNotExist:
      config = self.configs.create()

    return config

  current_config = property(get_current_config)

  def get_unique_name(self):
    return "%s_%s" % (self.name, long(totimestamp(self.created)*1000))

  unique_name = property(get_unique_name)

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
        res = json.loads(doc.encode('utf-8'))
        if res.get(u'clusterinfo') == []:
          logger.info("Clusterinfo is not available yet.  Try again...")
          time.sleep(2)
        else:
          break;
      except:
        # logging.exception(e)
        logger.info("Hit an exception. Try to get sysinfo again...")
        time.sleep(2)

    return res

  running_info = property(get_running_info)

  def to_map(self, with_api_key=False):
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
      'current_config': self.current_config.to_map(),
      'created': self.created,
      'running_info': self.running_info,
      'status': self.status,
      'status_display': unicode(enum.STORE_STATUS_DISPLAY[self.status]),
      'description' : self.description,
    }
    if with_api_key:
      obj['api_key'] = self.api_key
    return obj

@receiver(post_delete, sender=ContentStore)
def post_store_delete_handler(sender, **kwargs):
  instance = kwargs['instance']
  cache.delete(get_store_name_cache_key(instance.name))

@receiver(post_save, sender=ContentStore)
def post_store_save_handler(sender, **kwargs):
  instance = kwargs['instance']
  cache.delete(get_store_name_cache_key(instance.name))


class StoreConfig(models.Model):
  class Meta:
    ordering = ['-id', '-last_activated']

  name = models.CharField(max_length=20, blank=True)

  active = models.BooleanField(default=False)

  created = models.DateTimeField(auto_now_add=True)
  last_activated = models.DateTimeField(default=datetime.datetime.max)

  schema = models.TextField(default=json.dumps(default_schema))
  properties = models.TextField(default=load_template_source(
      'sensei-conf/sensei.properties')[0])
  custom_facets = models.TextField(default=load_template_source(
      'sensei-conf/custom-facets.xml')[0])
  plugins = models.TextField(default=load_template_source(
      'sensei-conf/plugins.xml')[0])

  extensions = models.ManyToManyField(File)

  store = models.ForeignKey(ContentStore, related_name='configs')

  def updated(self):
    if self.last_activated <= datetime.datetime.now():
      extensions = list(self.extensions.all())
      self.pk = None
      self.active = False
      self.last_activated = datetime.datetime.max
      # self.created = datetime.datetime.now()
      self.save()
      self.extensions = extensions
    else:
      self.save()

  def validate_schema(self):  #TODO: do more validation.
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
      schema = json.loads(self.schema)
      for facet in schema['facets']:
        valid, error = validate_facet(facet)
        if not valid:
          return (valid, error)
      valid, error = validate_table(schema['table'])
      if not valid:
        return (valid, error)

      self.schema = json.dumps(schema)
    except Exception as e:
      logging.exception(e)
      return (False, 'Configuration is not valid.')

    return (True, None)

  def validate_properties(self):  #TODO: do more validation.
    return (True, None)

  def validate_custom_facets(self):  #TODO: do more validation.
    return (True, None)

  def validate_plugins(self):  #TODO: do more validation.
    return (True, None)

  def to_map(self):
    obj = {
      'id': self.id,
      'name': self.name,
      'active': self.active,
      'created': self.created,
      'last_activated': self.last_activated,
      'schema': self.schema,
      'properties': self.properties,
      'custom_facets': self.custom_facets,
      'plugins': self.plugins,
      # 'extensions': [f.to_map() for f in self.extensions.all()],
    }
    return obj

