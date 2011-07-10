import random, os, subprocess
from django.conf import settings
from django.http import HttpResponse

from content_store.models import ContentStore

from utils import json

running = {
}

def newStore(request,store_name):
  store = ContentStore(name=store_name, sensei_port=random.randint(10000, 15000), broker_port=random.randint(15000, 20000))
  store.save()
  resp = {
    'id': store.id,
    'name': store.name,
    'sensei_port': store.sensei_port,
    'broker_port': store.broker_port,
    'config': store.config,
    'created': store.created,
    'status': store.status,
  }
  return HttpResponse(json.json_encode(resp))

def stopStore(request, store_name):
  global running

  pid = running.get(store_name)
  if pid:
    os.system('kill %s' % pid)
    del running[store_name]

  return HttpResponse(json.json_encode({}))

def startStore(request, store_name):
  global running

  store = ContentStore.objects.get(name=store_name)

  classpath = os.path.join(settings.SENSEI_HOME, '*')

  store_home = os.path.join(settings.STORE_HOME, store_name)
  index = os.path.join(store_home, 'index')
  conf = os.path.join(store_home, 'conf')
  logs = os.path.join(store_home, 'logs')

  # TODO:wonlay: generate conf

  cmd = ["java", "-server", "-d64", "-Xmx1g", "-Xms1g", "-XX:NewSize=256m", "-classpath", classpath, "-Dlog.home=%s" % logs, "com.sensei.search.nodes.SenseiServer", conf]

  p = subprocess.Popen(cmd, cwd=settings.SENSEI_HOME)
  running[store_name] = p.pid

  return HttpResponse(json.json_encode({}))

def restartStore(request, store_name):
  stopStore(request, store_name)
  return startStore(request, store_name)


def getSize(request,store_name):
  resp = {'store':store_name,"size":0}
  return HttpResponse(json.json_encode(resp))
  
def getDoc(request,store_name,id):
  uid = long(id)
  doc = {'id':uid}
  resp = {'store':store_name,'doc':doc}
  return HttpResponse(json.json_encode(resp))

def addDoc(request,store_name,id):
  uid = long(id)
  doc = {'id':uid}
  resp = {'store':store_name,'doc':doc}
  return HttpResponse(json.json_encode(resp))

def available(request,store_name):
  resp = {'store':store_name,"available":True}
  return HttpResponse(json.json_encode(resp))

def stores(request):
  objs = ContentStore.objects.all()
  resp = [{
      'id': store.id,
      'name': store.name,
      'sensei_port': store.sensei_port,
      'broker_port': store.broker_port,
      'config': store.config,
      'created': store.created,
      'status': store.status,
    }
    for store in objs]
  return HttpResponse(json.json_encode(resp))

