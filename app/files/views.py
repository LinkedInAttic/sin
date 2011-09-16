import os, logging, json, uuid
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse

from decorators import login_required
from utils import enum

from files.models import File

# @login_required
def upload(request):
  resp = []

  for f in request.FILES.values():
    name = os.path.basename(f.name)
    name_on_storage = '%s.%s' % (uuid.uuid1().hex, name)
    file_model = File(name=name, path='', size=f.size)
    file_model.the_file.save(name_on_storage, f)
    resp.append(file_model.to_map())

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))
