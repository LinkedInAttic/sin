import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils import enum
from utils.enum import to_choices

class Group(models.Model):
  name = models.CharField(max_length=20)

class Node(models.Model):
  class Meta:
    unique_together = ("host", "agent_port")

  host = models.CharField(max_length=40)
  agent_port = models.IntegerField(default=6664)
  group = models.ForeignKey(Group, related_name="nodes", null=True)
  online = models.BooleanField(default=False)

  def __unicode__(self):
    return u"%s:%s:%s" % (self.group.name, self.host, self.agent_port)

class Membership(models.Model):
  node = models.ForeignKey(Node)
  store = models.ForeignKey("content_store.ContentStore")
  replica = models.IntegerField(default=0)
  sensei_node_id = models.IntegerField()
  parts = models.CommaSeparatedIntegerField(max_length=1024)
