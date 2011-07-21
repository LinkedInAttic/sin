import os, json
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.http import Http404

from cluster.models import Group, Node

from utils import enum


def nodes(request, group_id):
  group_id = int(group_id)

  objs = Node.objects.filter(group__pk=group_id)
  resp = [{
    'id': node.pk,
    'host': node.host,
    'agent_port': node.agent_port,
    'group': node.group_id,
  } for node in objs]
  return HttpResponse(json.dumps(resp))

def nodes_count(request, group_id):
  group_id = int(group_id)

  objs = Node.objects.filter(group__pk=group_id)
  resp = {
    'count': objs.count(),
  }
  return HttpResponse(json.dumps(resp))
