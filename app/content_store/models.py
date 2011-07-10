import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils import enum
from utils.enum import to_choices

class ContentStore(models.Model):
  name = models.CharField(max_length=20, unique=True)
  sensei_port = models.IntegerField(unique=True)
  broker_port = models.IntegerField(unique=True)

  config = models.TextField(default="{}")

  created = models.DateTimeField(auto_now_add=True)

  status = models.SmallIntegerField(choices=to_choices(enum.STORE_STATUS), default=enum.STORE_STATUS['init'])

