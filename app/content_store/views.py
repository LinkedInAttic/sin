import random
from django.http import HttpResponse

from content_store.models import ContentStore

from utils import json

def newStore(request,index_name):
  store = ContentStore(name=index_name, sensei_port=random.randint(10000, 15000), brocker_port=random.randint(15000, 20000))
  store.save()
  resp = {
    'id': store.id,
    'name': store.name,
    'sensei_port': store.sensei_port,
    'brocker_port': store.brocker_port,
    'config': store.config,
    'created': store.created,
    'status': store.status,
  }
  return HttpResponse(json.json_encode(resp))

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
      'brocker_port': store.brocker_port,
      'config': store.config,
      'created': store.created,
      'status': store.status,
    }
    for store in objs]
  return HttpResponse(json.json_encode(resp))

