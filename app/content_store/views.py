import random, os, subprocess
from django.http import HttpResponse

from content_store.models import ContentStore

from utils import json

running = {
}

def newStore(request,index_name):
  store = ContentStore(name=index_name, sensei_port=random.randint(10000, 15000), broker_port=random.randint(15000, 20000))
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

def stopStore(request, index_name):
  global running

  pid = running.get(index_name)
  if pid:
    os.system('kill %s' % pid)
    del running[index_name]

  return HttpResponse(json.json_encode({}))

def startStore(request, index_name):
  global running

  pid = subprocess.Popen(["java", ""]).pid
  running[index_name] = pid

  return HttpResponse(json.json_encode({}))

def restartStore(request, index_name):
  stopStore(request, index_name)
  return startStore(request, index_name)


def getSize(request,index_name):
  resp = {'store':index_name,"size":0}
  return HttpResponse(json.json_encode(resp))
  
def getDoc(request,index_name,id):
  uid = long(id)
  doc = {'id':uid}
  resp = {'store':index_name,'doc':doc}
  return HttpResponse(json.json_encode(resp))

def addDoc(request,index_name,id):
  uid = long(id)
  doc = {'id':uid}
  resp = {'store':index_name,'doc':doc}
  return HttpResponse(json.json_encode(resp))

def available(request,index_name):
  resp = {'store':index_name,"available":True}
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

