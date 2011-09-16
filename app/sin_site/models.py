import logging, os, uuid
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.files import File as DJFile
from django.db import models
from django.utils.translation import ugettext_lazy as _

from files.models import File

from utils import totimestamp

class SinSite(Site):
  default_webapps = models.ManyToManyField(File, related_name='sites_of_this_webapp')
  default_libs = models.ManyToManyField(File, related_name='sites_of_this_lib')
  default_resources = models.ManyToManyField(File, related_name='sites_of_this_resource')

  def initialize(self):
    self.load_webapps()
    self.load_libs()
    self.load_resources()

  def load_webapps(self):
    base = os.path.join(settings.SIN_HOME, 'app/defaults/webapp')
    webapps, changed = self._load_files(base, list(self.default_webapps.all()))
    if changed:
      self.default_webapps = webapps

  def load_libs(self):
    base = os.path.join(settings.SIN_HOME, 'app/defaults/lib')
    libs, changed = self._load_files(base, list(self.default_libs.all()))
    if changed:
      self.default_libs = libs

  def load_resources(self):
    base = os.path.join(settings.SIN_HOME, 'app/defaults/resource')
    resources, changed = self._load_files(base, list(self.default_resources.all()))
    if changed:
      self.default_resources = resources

  def _load_files(self, base, old=[]):
    old_map = dict([(os.path.join(f.path, f.name), f) for f in old])
    new, changed = [], False

    for root, dirs, files in os.walk(base):
      for name in files:
        fullname = os.path.join(root, name)
        name_on_storage = '%s.%s' % (uuid.uuid1().hex, name)
        path = os.path.dirname(os.path.relpath(fullname, base))

        new_file = old_map.get(os.path.join(path, name))
        if new_file:
          # Check if it's new enough.
          old_modified = int(totimestamp(new_file.the_file.storage.modified_time(new_file.the_file.name)))
          new_modified = int(os.stat(fullname).st_mtime)
          if new_modified > old_modified:
            f = DJFile(open(fullname))
            new_file = File(name=name, path=path, size=f.size)
            new_file.the_file.save(name_on_storage, f)
            changed = True
          else:
            new_file.reuse = True
        else:
          f = DJFile(open(fullname))
          new_file = File(name=name, path=path, size=f.size)
          new_file.the_file.save(name_on_storage, f)
          changed = True

        new.append(new_file)

    if len(old) != len(new):
      changed = True

    for f in old:
      if not getattr(f, 'reuse', False):
        f.the_file.delete()
        f.delete()

    return new, changed

