import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils import enum
from utils.enum import to_choices
from utils import json

from cluster.models import Group

default_schema = {
  "facets": [
    {
      "depends": "",
      "dynamic": "",
      "name": "color",
      "params": [],
      "type": "simple"
    },
    {
      "depends": "",
      "dynamic": "",
      "name": "category",
      "params": [],
      "type": "simple"
    },
    {
      "depends": "",
      "dynamic": "",
      "name": "city",
      "params": [{
        "name": "separator",
        "value": "/"
      }],
      "type": "path"
    },
    {
      "depends": "",
      "dynamic": "",
      "name": "makemodel",
      "params": [],
      "type": "path"
    },
    {
      "depends": "",
      "dynamic": "",
      "name": "year",
      "params": [
        {
          "name": "range",
          "value": "1993-1994"
        },
        {
          "name": "range",
          "value": "1995-1996"
        },
        {
          "name": "range",
          "value": "1997-1998"
        },
        {
          "name": "range",
          "value": "1999-2000"
        },
        {
          "name": "range",
          "value": "2001-2002"
        }
      ],
      "type": "range"
    },
    {
      "depends": "",
      "dynamic": "",
      "name": "mileage",
      "params": [
        {
          "name": "range",
          "value": "*-12500"
        },
        {
          "name": "range",
          "value": "12501-15000"
        },
        {
          "name": "range",
          "value": "15001-17500"
        },
        {
          "name": "range",
          "value": "17501-*"
        }
      ],
      "type": "range"
    },
    {
      "depends": "",
      "dynamic": "",
      "name": "price",
      "params": [
        {
          "name": "range",
          "value": "*,6700"
        },
        {
          "name": "range",
          "value": "6800,9900"
        },
        {
          "name": "range",
          "value": "10000,13100"
        },
        {
          "name": "range",
          "value": "13200,17300"
        },
        {
          "name": "range",
          "value": "17400,*"
        }
      ],
      "type": "range"
    },
    #{
      #"depends": "",
      #"dynamic": "",
      #"name": "tags",
      #"params": [],
      #"type": "multi"
    #}
  ],
  "table": {
    "columns": [
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "color",
        "store": "",
        "termvector": "",
        "type": "string"
      },
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "category",
        "store": "",
        "termvector": "",
        "type": "string"
      },
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "city",
        "store": "",
        "termvector": "",
        "type": "string"
      },
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "makemodel",
        "store": "",
        "termvector": "",
        "type": "string"
      },
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "year",
        "store": "",
        "termvector": "",
        "type": "int"
      },
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "price",
        "store": "",
        "termvector": "",
        "type": "float"
      },
      {
        "from": "",
        "index": "",
        "multi": False,
        "name": "mileage",
        "store": "",
        "termvector": "",
        "type": "int"
      },
      {
        "delimiter": ",",
        "from": "",
        "index": "",
        "multi": True,
        "name": "tags",
        "store": "",
        "termvector": "",
        "type": "string"
      },
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
  name = models.CharField(max_length=20, unique=True)
  description = models.CharField(max_length=1024,unique=False)
  sensei_port = models.IntegerField(unique=True)
  broker_port = models.IntegerField(unique=True)

  partitions = models.IntegerField(default=10)

  config = models.TextField(default=json.json_encode(default_schema))

  created = models.DateTimeField(auto_now_add=True)

  status = models.SmallIntegerField(choices=to_choices(enum.STORE_STATUS),
    default=enum.STORE_STATUS['init'])

  group = models.ForeignKey(Group, related_name="stores", default=1)

