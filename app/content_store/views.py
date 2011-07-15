import random, os, subprocess, socket
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.http import Http404

import kafka

from content_store.models import ContentStore
from cluster.models import Group, Node

from utils import enum, json

from django.utils import simplejson
import shutil
import urllib, urllib2

from senseiClient import SenseiClient
from senseiClient import SenseiRequest
from senseiClient import SenseiSelection

kafkaHost = settings.KAFKA_HOST
kafkaPort = int(settings.KAFKA_PORT)
kafkaProducer = kafka.KafkaProducer(kafkaHost, kafkaPort)

def storeExists(request,store_name):
  resp = {
    'exists' : ContentStore.objects.filter(name=store_name).exists()
  }
  return HttpResponse(json.json_encode(resp))

def openStore(request,store_name):
  store = ContentStore.objects.get(name=store_name)
  if not store:
    resp = {
      'ok' : False,
      'error' : 'store: %s does not exist.' % store_name
    }
    return HttpResponse(json.json_encode(resp))

  resp = store.to_map();

  resp.update({
    'ok' : True,
    'kafkaHost' : kafkaHost,
    'kafkaPort' : kafkaPort,
  })
  return HttpResponse(json.json_encode(resp))

def newStore(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
    resp = {
      'ok' : False,
      'error' : 'store: %s already exists.' % store_name
    }
    return HttpResponse(json.json_encode(resp))

  replica = int(request.POST.get('replica','2'))
  partitions = int(request.POST.get('partitions','10'))
  desc = request.POST.get('desc',"")

  # Check for nodes:
  if Node.objects.count() == 0:
    n = Node.objects.create(host=socket.gethostname(), group=Group(pk=1))

  store = ContentStore(
    name=store_name,
    replica=replica,
    partitions=partitions,
    description=desc
  )
  store.save()
  resp = store.to_map()
  resp.update({
    'ok' : True,
    'kafkaHost' : kafkaHost,
    'kafkaPort' : kafkaPort,
  })
  return HttpResponse(json.json_encode(resp))

def deleteStore(request,store_name):
  if not ContentStore.objects.filter(name=store_name).exists():
    resp = {
      'ok' : False,
      'msg' : 'store: %s does not exist.' % store_name
    }
    return HttpResponse(json.json_encode(resp))
  stopStore(request, store_name)

  store_data_dir = os.path.join(settings.STORE_HOME, store_name)
  try:
    shutil.rmtree(store_data_dir)
  except:
    pass
  ContentStore.objects.filter(name=store_name).delete()
  resp = {
    'ok' : True,
    'msg' : 'store: %s successfully deleted.' % store_name
  }
  return HttpResponse(json.json_encode(resp))

def updateConfig(request, store_name):
  config = request.POST.get('config');
  resp = {
    'ok': False,
  }
  if config:
    # TODO: valid configuration.
    ContentStore.objects.filter(name=store_name).update(config=config);
    resp['ok'] = True
  else:
    resp['error'] = 'No config provided.'

  return HttpResponse(json.json_encode(resp))

def addDoc(request,store_name):
  doc = request.POST.get('doc');
  
  if not doc:
    resp = {'ok':False,'error':'no doc posted'}
  else:
    try:
      jsonDoc = simplejson.loads(doc.encode('utf-8'))
      kafkaProducer.send([json.json_encode(jsonDoc)], store_name.encode('utf-8'))
      resp = {'ok': True,'numPosted':1}
    except ValueError:
      resp = {'ok':False,'error':'invalid json: %s' % doc}
    except Exception as e:
      resp = {'ok':False,'error':e}
  
  return HttpResponse(json.json_encode(resp))

def addDocs(request,store_name):
  docs = request.POST.get('docs');  
  if not docs:
    resp = {'ok':False,'error':'no docs posted'}
  else:
    try:
      jsonArray = simplejson.loads(docs.encode('utf-8'))
      messages = []
      for obj in jsonArray:
        str = json.json_encode(obj).encode('utf-8')
        messages.append(str)
      kafkaProducer.send(messages, store_name.encode('utf-8'))
      resp = {'ok':True,'numPosted':len(messages)}
    except ValueError:
      resp = {'ok':False,'error':'invalid json: %s' % docs}
    except Exception as e:
      resp = {'ok':False,'error':e}
  return HttpResponse(json.json_encode(resp))

def startStore(request, store_name):
  try:
    store = ContentStore.objects.get(name=store_name)
    webapp = os.path.join(settings.SENSEI_HOME,'src/main/webapp')
    store_home = os.path.join(settings.STORE_HOME, store_name)
    index = os.path.join(store_home, 'index')

    sensei_custom_facets = loader.render_to_string(
      'sensei-conf/custom-facets.xml', {
        })
    sensei_plugins = loader.render_to_string(
      'sensei-conf/plugins.xml', {
        })

    params = {}
    params["name"] = store_name
    params["sensei_port"] = store.sensei_port
    params["broker_host"] = store.broker_host
    params["broker_port"] = store.broker_port
    params["sensei_custom_facets"] = sensei_custom_facets
    params["sensei_plugins"] = sensei_plugins
    params["schema"] = store.config
  
    nodes = store.group.nodes.all()
    nodeInfos = allocateResource(store)
    for i in range(len(nodeInfos)):
      nodeInfo = nodeInfos[i]
      node = nodes[i]
      sensei_properties = loader.render_to_string(
        'sensei-conf/sensei.properties',
        {'node_id': nodeInfo["id"],
         'node_partitions': ','.join(str(x) for x in nodeInfo["parts"]),
         'max_partition_id': store.partitions - 1,
         'store': store,
         'index': index,
         'webapp': webapp,
         })
      params["sensei_properties"] = sensei_properties
      output = urllib2.urlopen("http://%s:%d/%s" % (node.host, node.agent_port, "start-store"),
                               urllib.urlencode(params))

    store.status = enum.STORE_STATUS['running']
    store.save()
    resp = store.to_map()
    resp.update({
      "ok":True,
    })
    return HttpResponse(json.json_encode(resp))
  except Exception as e:
    return HttpResponse(json.json_encode({'ok':False,'error':e}))

def stopStore(request, store_name):
  try:
    store = ContentStore.objects.get(name=store_name)

    params = {}
    params["name"] = store_name

    nodes = store.group.nodes.all()
    for node in nodes:
      output = urllib2.urlopen("http://%s:%d/%s" % (node.host, node.agent_port, "stop-store"),
                               urllib.urlencode(params))
    store.status = enum.STORE_STATUS['stopped']
    store.save()
    resp = store.to_map()
    resp.update({
      "ok":True,
    })
    return HttpResponse(json.json_encode(resp))
  except Exception as e:
    return HttpResponse(json.json_encode({'ok':False,'error':e}))

def restartStore(request, store_name):
  stopStore(request, store_name)
  return startStore(request, store_name)

def getSize(request,store_name):
  store = ContentStore.objects.get(name=store_name)
  if not store:
    resp = {'ok' : False,'error' : 'store: %s does not exist.' % store_name}
    return HttpResponse(json.json_encode(resp))
  senseiHost = store.broker_host
  senseiPort = store.broker_port
  senseiClient = SenseiClient(senseiHost,senseiPort)
  req = SenseiRequest()
  req.count = 0
  res = senseiClient.doQuery(req)
  resp = {'store':store_name,"size":res.totalDocs}
  return HttpResponse(json.json_encode(resp))
  
def getDoc(request,store_name,id):
  uid = long(id)
  store = ContentStore.objects.get(name=store_name)
  if not store:
    resp = {'ok' : False,'error' : 'store: %s does not exist.' % store_name}
    return HttpResponse(json.json_encode(resp))
  senseiHost = store.broker_host
  senseiPort = store.broker_port
  senseiClient = SenseiClient(senseiHost,senseiPort)
  req = SenseiRequest()
  sel = SenseiSelection("uid")
  sel.addSelection(id)
  req.count = 1
  req.selections = [sel]
  res = senseiClient.doQuery(req)
  doc = None
  if res.numHits > 0:
    if res.hits and len(res.hits) > 0:
      hit = res.hits[0]
      doc = hit.srcData
  resp = {'store':store_name,"uid":uid,"doc":doc}
  return HttpResponse(json.json_encode(resp))

def available(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
    resp = {'ok':True,'store':store_name,"available":True}
  else:
    resp = {'ok':False,'error':'store: %s does not exist.' % store_name}
  return HttpResponse(json.json_encode(resp))

def stores(request):
  objs = ContentStore.objects.order_by('-created')
  #TODO: remove multiple calls to get broker_host.
  resp = [store.to_map() for store in objs]
  return HttpResponse(json.json_encode(resp))

def allocateResource(store):
  """
  Given a store and its replica and partition requirement, figure out
  the cluster layout.  Return a list of nodes with partition information.
  """
  nodes = store.group.nodes.all()
  totalNodes = len(nodes)
  numNodesPerReplica = totalNodes / store.replica
  actualTotalNodes = numNodesPerReplica * store.replica
  numPartsPerNode = store.partitions / numNodesPerReplica

  nodeInfos = []
  for i in range(store.replica):
    for j in range(numNodesPerReplica):
      nodeDict = {}
      nodeId = i * numNodesPerReplica + j + 1
      nodeDict["id"] = nodeId
      nodeDict["name"] = nodes[nodeId - 1].host
      parts = []
      for k in range(numPartsPerNode):
        parts.append(j * numPartsPerNode + k)
      nodeDict["parts"] = parts
      nodeInfos.append(nodeDict)

  return nodeInfos
