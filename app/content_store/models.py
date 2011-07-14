import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils import enum
from utils.enum import to_choices
from utils import json

from cluster.models import Group

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
    "delete-field": "",
    "src-data-store": "src_data",
    "uid": "id"
  }
}

class ContentStore(models.Model):
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

  def get_sensei_port(self):
    return self.sensei_port_base + self.pk

  sensei_port = property(get_sensei_port)

  def get_broker_port(self):
    return self.broker_port_base + self.pk

  broker_port = property(get_broker_port)

  def get_broker_host(self):
    return self.group.nodes.order_by('?')[0].host

  broker_host = property(get_broker_host)

