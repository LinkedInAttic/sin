from django.db import models

from utils import enum, totimestamp
from utils.enum import to_choices

class File(models.Model):
  name = models.CharField(max_length=255)
  size = models.IntegerField()
  the_file = models.FileField(upload_to='generic/%Y/%m/%d')
  created = models.DateTimeField(auto_now_add=True)
  src_type = models.SmallIntegerField(choices=to_choices(enum.FILE_SRC_TYPES), default=enum.FILE_SRC_TYPES['upload'])
  src_url = models.URLField(verify_exists=False, max_length=1024, blank=True)

  def to_map(self):
    obj = {
      'id': self.id,
      'name': self.name,
      'size': self.size,
      'url': self.the_file.url,
      'created': self.created,
      'src_type': self.get_src_type_display(),
      'src_url': self.src_url,
    }
    return obj

