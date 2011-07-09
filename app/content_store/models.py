import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContentStore(models.Model):
  name = models.CharField(max_length=20, unique=True)
  brocker_port = models.IntegerField(unique=True)

