# -*- coding: utf-8 -*-
"""
Global enums defined here.
"""
from django.utils.translation import ugettext_lazy as _

def to_choices(d):
  return map(lambda x: (x[1], x[0]), d.items())

STORE_STATUS_BASE = (
  ('new', 0, _(u'New')),
  ('disabled', 5, _(u'Disabled')),
  ('stopped', 10, _(u'Stopped')),
  ('running', 15, _(u'Running')),
)
STORE_STATUS = dict([(x[0], x[1]) for x in STORE_STATUS_BASE])
STORE_STATUS_DISPLAY = dict([(x[1], x[2]) for x in STORE_STATUS_BASE])

