import random, os, subprocess, socket, json
from django.db import connection
from django.conf import settings
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse
from django.template import loader
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import HttpResponseGone
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseServerError
import kafka

from content_store.models import ContentStore
from cluster.models import Group, Node, Membership
import logging
from utils import enum
from utils import ClusterLayout
from utils.ClusterLayout import Rectangle, Label, SvgPlotter
from utils import validator

import shutil
import urllib, urllib2

from senseiClient import SenseiClient
from senseiClient import SenseiRequest
from senseiClient import SenseiSelection

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

kafkaHost = settings.KAFKA_HOST
kafkaPort = int(settings.KAFKA_PORT)
kafkaProducer = kafka.KafkaProducer(kafkaHost, kafkaPort)
validators = {}

def storeExists(request,store_name):
  resp = {
    'exists' : ContentStore.objects.filter(name=store_name).exists()
  }
  return HttpResponse(json.dumps(resp))

def openStore(request,store_name):
  store = None
  try:
    store = ContentStore.objects.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'store: %s does not exist.' % store_name
    }
    return HttpResponseNotFound(json.dumps(resp))

  resp = store.to_map();

  resp.update({
    'ok' : True,
    'kafkaHost' : kafkaHost,
    'kafkaPort' : kafkaPort,
  })
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

def newStore(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
    resp = {
      'ok' : False,
      'error' : 'store: %s already exists.' % store_name
    }
    return HttpResponseNotAllowed(json.dumps(resp))

  replica = int(request.POST.get('replica','2'))
  partitions = int(request.POST.get('partitions','2'))
  desc = request.POST.get('desc',"")

  num_nodes = Node.objects.count()

  # Check for nodes:
  if num_nodes == 0:
    def _get_local_pub_ip():
      """Get local public ip address.

      By creating a udp socket and assigning a DUMMY public ip address and a
      DUMMY port, and getting the local sock name.
      """
      skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      try:
        skt.connect(('74.125.224.0', 80))
        return skt.getsockname()[0]
      finally:
        skt.close()

    n = Node.objects.create(host=_get_local_pub_ip(), group=Group(pk=1))
    num_nodes = 1

  if replica > num_nodes:
    resp = {'ok': False, 'error':'Num of replicas is too big'}
    return HttpResponseBadRequest(json.dumps(resp))

  store = ContentStore(
    name=store_name,
    replica=replica,
    partitions=partitions,
    description=desc
  )
  store.save()

  setupCluster(store)

  resp = store.to_map()
  resp.update({
    'ok' : True,
    'kafkaHost' : kafkaHost,
    'kafkaPort' : kafkaPort,
  })
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

def deleteStore(request,store_name):
  try:
    store = None
    try:
      store = ContentStore.objects.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'store: %s does not exist.' % store_name
      }
      return HttpResponseNotFound(json.dumps(resp))
    params = {}
    params["name"] = store_name

    members = store.membership_set.order_by("sensei_node_id")
    for member in members:
      output = urllib2.urlopen("http://%s:%d/%s" % (member.node.host,
                                                    member.node.agent_port,
                                                    "delete-store"),
                               urllib.urlencode(params))

    store.delete()
    resp = {
      'ok': True,
    }
  except Exception as e:
    logging.exception(e)
    resp = {
      'ok': False,
      'msg': str(e),
    }
  return HttpResponse(json.dumps(resp))

def updateConfig(request, store_name):
  config = request.POST.get('config');
  resp = {
    'ok': False,
  }
  
  if config:
    store = None
    try:
      store = ContentStore.objects.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp['error'] = "store %s does not exist." % store_name
      return HttpResponse(json.dumps(resp))

    store.config = config
    valid, error = store.validate_config()
    if valid:
      store.save()
      validator.erase_validator(store_name)
      resp['ok'] = True
    else:
      resp['error'] = error
  else:
    resp['error'] = 'No config provided.'

  return HttpResponse(json.dumps(resp))

def addDocs(request,store_name):
  """Add a list of documents."""
  try:
    store = ContentStore.objects.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'msg' : 'store: %s does not exist.' % store_name
    }
    return HttpResponseNotFound(json.dumps(resp))
  docs = request.POST.get('docs');
  if not docs:
    resp = {'ok':False,'error':'no docs posted'}
    return HttpResponseBadRequest(json.dumps(resp))
  else:
    my_validator, error = validator.get_validator(store_name)
    if not my_validator:
      resp = {
        'ok': False,
        'msg': error,
      }
      return HttpResponse(json.dumps(resp))

    try:
      jsonDocs = json.loads(docs.encode('utf-8'))
      messages = []
      for doc in jsonDocs:
        (valid, error) = my_validator.validate(doc)
        if not valid:
          logger.warn("Found an invalid doc for store %s when adding docs" % store_name)
          resp = {'ok': False,'numPosted':0, 'error':error}
          return HttpResponseBadRequest(json.dumps(resp))
        str = json.dumps(doc).encode('utf-8')
        messages.append(str)
      if messages:
        kafkaProducer.send(messages, store.unique_name.encode('utf-8'))
      resp = {'ok':True,'numPosted':len(messages)}
      return HttpResponse(json.dumps(resp))
    except ValueError:
      resp = {'ok':False,'error':'invalid json: %s' % docs}
      return HttpResponseBadRequest(json.dumps(resp))
    except Exception as e:
      logger.error(e.messages)
      resp = {'ok':False,'error':e.message}
      return HttpResponseServerError(json.dumps(resp))

def updateDoc(request,store_name):
  try:
    store = None
    try:
      store = ContentStore.objects.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'store: %s does not exist.' % store_name
      }
      return HttpResponseNotFound(json.dumps(resp))

    doc = request.POST.get('doc');

    if not doc:
      resp = {'ok':False,'error':'no doc posted'}
      return HttpResponseBadRequest(json.dumps(resp))
    else:
      jsonDoc = json.loads(doc.encode('utf-8'))

      my_validator, error = validator.get_validator(store_name)
      if not my_validator:
        resp = {
          'ok': False,
          'msg': error,
        }
        return HttpResponse(json.dumps(resp))

      (valid, error) = my_validator.validate(jsonDoc)
      if not valid:
        logger.warn("Found an invalid doc for store %s when updating a doc" % store_name)
        resp = {'ok': False,'numPosted':0, 'error':error}
        return HttpResponseBadRequest(json.dumps(resp))

      uid = long(jsonDoc['id'])
      existingDocString = findDoc(store,uid)

      if not existingDocString:
        resp = {'ok':False,'error':'doc: %d does not exist' % uid}
        return HttpResponseBadRequest(json.dumps(resp))

      existingDoc = json.loads(existingDocString)
      print existingDoc
      for k,v in jsonDoc.items():
        existingDoc[k]=v
      
      kafkaProducer.send([json.dumps(existingDoc).encode('utf-8')], store.unique_name.encode('utf-8'))
      resp = {'ok': True,'numPosted':1}
      return HttpResponse(json.dumps(resp))
  except ValueError:
    resp = {'ok':False,'error':'invalid json: %s' % doc}
    return HttpResponseBadRequest(json.dumps(resp))
  except Exception as e:
    resp = {'ok':False,'error':e.message}
  return HttpResponseServerError(json.dumps(resp))

def startStore(request, store_name, restart=False):
  try:
    store = None
    try:
      store = ContentStore.objects.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'store: %s does not exist.' % store_name
      }
      return HttpResponseNotFound(json.dumps(resp))

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
  
    members = store.membership_set.order_by("sensei_node_id")
    for member in members:
      sensei_properties = loader.render_to_string(
        'sensei-conf/sensei.properties',
        {'node_id': member.sensei_node_id,
         'node_partitions': member.parts[1:len(member.parts)-1],
         'max_partition_id': store.partitions - 1,
         'store': store,
         'index': index,
         'webapp': webapp,
         'kafka_host': kafkaHost,
         'kafka_port': kafkaPort,
         'zookeeper_url': settings.ZOOKEEPER_URL,
         })
      params["sensei_properties"] = sensei_properties

      logger.info("Sending request: http://%s:%d/%s" % (member.node.host, member.node.agent_port,
                                                not restart and "start-store" or "restart-store"))
      output = urllib2.urlopen("http://%s:%d/%s"
                               % (member.node.host, member.node.agent_port,
                                  not restart and "start-store" or "restart-store"),
                               urllib.urlencode(params))

    store.status = enum.STORE_STATUS['running']
    store.save()
    resp = store.to_map()
    resp.update({
      "ok":True,
    })
    return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))
  except Exception as e:
    logging.exception(e)   
    return HttpResponseServerError(json.dumps({'ok':False,'error':e.message}))

def stopStore(request, store_name):
  try:
    store = None
    try:
      store = ContentStore.objects.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'store: %s does not exist.' % store_name
      }
      return HttpResponseNotFound(json.dumps(resp))
    params = {}
    params["name"] = store_name

    members = store.membership_set.order_by("sensei_node_id")
    for member in members:
      output = urllib2.urlopen("http://%s:%d/%s" % (member.node.host,
                                                    member.node.agent_port,
                                                    "stop-store"),
                               urllib.urlencode(params))

    store.status = enum.STORE_STATUS['stopped']
    store.save()
    resp = store.to_map()
    resp.update({
      "ok":True,
    })
    return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))
  except Exception as e:
    return HttpResponseServerError(json.dumps({'ok':False,'error':e.message}))

def restartStore(request, store_name):
  return startStore(request, store_name, restart=True)

def getSize(request,store_name):
  store = None
  try:
    store = ContentStore.objects.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {'ok' : False,'error' : 'store: %s does not exist.' % store_name}
    return HttpResponseNotFound(json.dumps(resp))
  senseiHost = store.broker_host
  senseiPort = store.broker_port
  senseiClient = SenseiClient(senseiHost,senseiPort)
  req = SenseiRequest()
  req.count = 0
  res = senseiClient.doQuery(req)
  resp = {'store':store_name,"size":res.totalDocs}
  return HttpResponse(json.dumps(resp))

def findDoc(store,id):
  senseiHost = store.broker_host
  senseiPort = store.broker_port
  senseiClient = SenseiClient(senseiHost,senseiPort)
  req = SenseiRequest()
  sel = SenseiSelection("uid")
  sel.addSelection(str(id))
  req.count = 1
  req.fetch = True
  req.selections = [sel]
  res = senseiClient.doQuery(req)
  doc = None
  if res.numHits > 0:
    if res.hits and len(res.hits) > 0:
      hit = res.hits[0]
      doc = hit.srcData
  return doc

def getDoc(request,store_name,id):
  uid = long(id)
  if uid<0:
    resp = {'ok':False,'error':'negative uid'}
    return HttpResponseBadRequest(json.dumps(resp))
  try:
    store = ContentStore.objects.get(name=store_name)
    doc = findDoc(store,uid)
    resp = {'store':store_name,"uid":uid,"doc":doc}
    return HttpResponse(json.dumps(resp))
  except ContentStore.DoesNotExist:
    resp = {'ok':False,'error':"store %s does not exist."}
    return HttpResponseNotFound(json.dumps(resp))
  except Exception as e:
    logging.exception(e)
    resp = {'ok':False,'error':e.message}
    return HttpResponseServerError(json.dumps(resp))

def delDocs(request, store_name):
  ids = request.POST.get('ids')

  if not ids or len(ids) == 0:
    resp = {'ok': True,'numDeleted':0}
    return HttpResponse(json.dumps(resp))

  try:
    store = ContentStore.objects.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {'ok' : False,'error' : 'store: %s does not exist.' % store_name}
    return HttpResponseNotFound(json.dumps(resp))

  try:
    delObjs = []
    for id in ids:
      delDoc = {'id':id,'isDeleted':True}
      delObjs.append(json.dumps(delDoc).encode('utf-8'))
    kafkaProducer.send(delObjs,store.unique_name.encode('utf-8'))
    resp = {'ok': True,'numDeleted':len(delObjs)}
    return HttpResponse(json.dumps(resp))
  except Exception as e:
    logging.exception(e)
    resp = {'ok':False,'error':e.message}
    return HttpResponseServerError(json.dumps(resp))

def available(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
    resp = {'ok':True,'store':store_name,"available":True}
  else:
    resp = {'ok':False,'error':'store: %s does not exist.' % store_name}
  return HttpResponse(json.dumps(resp))

def stores(request):
  objs = ContentStore.objects.order_by('-created')
  resp = objs.to_map_list()
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

def setupCluster(store):
  """
  Set up the cluster for a given store based on currently available
  Sensei nodes.  The cluster layout is determined by the store's number
  of replicas and number of partitions.
  """
  nodes = store.group.nodes.all()
  totalNodes = len(nodes)
  numNodesPerReplica = totalNodes / store.replica
  remainingNodes = totalNodes % store.replica
  numPartsPerNode = store.partitions / numNodesPerReplica
  remainingParts = store.partitions % numNodesPerReplica
  extraRow = remainingNodes > 0 and 1 or 0

  for i in range(store.replica + extraRow):
    numNodes = numNodesPerReplica
    if i == store.replica:
      # The replica row for extra nodes
      numNodes = remainingNodes
    for j in range(numNodes):
      nodeId = i * numNodesPerReplica + j + 1
      parts = []
      for k in range(numPartsPerNode):
        parts.append(j * numPartsPerNode + k)
      if remainingParts > 0 and j < remainingParts:
        parts.append(store.partitions - remainingParts + j)
      Membership.objects.create(node = nodes[nodeId - 1],
                                store = store,
                                replica = i,
                                sensei_node_id = nodeId,
                                parts = parts)

def buildClusterSVG(store, stream, xml_header=True):
  """
  Given a store, generate the SVG for its cluster layout.
  The output is written to a file-like stream.  If ``xml_header'' is
  True, the XML file header will be included in the output (this is
  useful for generating an SVG file).
  """
  layout = ClusterLayout.ClusterLayout()

  xOffset = 80
  yOffset = 10
  legend = 40
  replicas = store.replica
  members = store.membership_set.order_by("sensei_node_id")
  totalNodes = len(members)
  numNodesPerReplica = totalNodes / store.replica
  remainingNodes = totalNodes % store.replica
  numPartsPerNode = store.partitions / numNodesPerReplica
  remainingParts = store.partitions % numNodesPerReplica
  extraRow = remainingNodes > 0 and 1 or 0

  for i in range(store.replica + extraRow):
    y1 = yOffset + i * ClusterLayout.NODE_DISTANCE_Y
    layout.addShape(Label(10, y1 + ClusterLayout.NODE_HEIGHT/2 + 2,
                          "Replica " + str(i+1),
                          fontSize=12, bold=True, color="darkblue"))
    numNodes = numNodesPerReplica
    if i == store.replica:
      # The replica row for extra nodes
      numNodes = remainingNodes
    for j in range(numNodes):
      x1 = xOffset + j * ClusterLayout.NODE_DISTANCE_X
      layout.addShape(Rectangle(x1, y1, x1 + ClusterLayout.NODE_WIDTH, y1 + ClusterLayout.NODE_HEIGHT))
      layout.addShape(Label(x1 + ClusterLayout.NODE_WIDTH/2, y1 + ClusterLayout.NODE_HEIGHT + 15,
                            "Node %s" % str(i * numNodesPerReplica + j + 1),
                            bold=True,
                            alignment="middle"))
      layout.addShape(Label(x1 + ClusterLayout.NODE_WIDTH/2,
                            y1 + ClusterLayout.NODE_HEIGHT + 15 + ClusterLayout.DEFAULT_LABEL_SIZE + 1,
                            "Parts: %s" % members[i * numNodesPerReplica + j].parts,
                            alignment="middle"))

  layout.setSize(xOffset + numNodesPerReplica * ClusterLayout.NODE_DISTANCE_X,
                 yOffset + (store.replica + extraRow) * ClusterLayout.NODE_DISTANCE_Y)

  plotter = SvgPlotter(stream)
  plotter.visitImage(layout, xml_header)
  return stream


def testSetupCluster():

  # Create some nodes

  n1 = Node.objects.create(host="node-1", group=Group(pk=1))
  n2 = Node.objects.create(host="node-2", group=Group(pk=1))
  n3 = Node.objects.create(host="node-3", group=Group(pk=1))
  n4 = Node.objects.create(host="node-4", group=Group(pk=1))
  n5 = Node.objects.create(host="node-5", group=Group(pk=1))
  n6 = Node.objects.create(host="node-6", group=Group(pk=1))
  n7 = Node.objects.create(host="node-7", group=Group(pk=1))
  n8 = Node.objects.create(host="node-8", group=Group(pk=1))
  n9 = Node.objects.create(host="node-9", group=Group(pk=1))
  n10 = Node.objects.create(host="node-10", group=Group(pk=1))

  # Create test store 1

  print "==== [ Test Store 1] ======================================"
  store1 = ContentStore(name = "test-store1",
                       replica = 3,
                       partitions = 10,
                       description = "This is test store one")
  store1.save()
  setupCluster(store1)

  for node in store1.nodes.all():
    print node.host

  for member in store1.membership_set.order_by("sensei_node_id"):
    print member.node.host, member.replica, member.parts

  buildClusterSVG(store1, file("/tmp/%s.svg" % store1.name, "w+"), True)


  # Create test store 2

  print "==== [ Test Store 2] ======================================"
  store2 = ContentStore(name = "test-store2",
                       replica = 2,
                       partitions = 5,
                       description = "This is test store two")
  store2.save()
  setupCluster(store2)

  for node in store2.nodes.all():
    print node.host

  for member in store2.membership_set.order_by("sensei_node_id"):
    print member.node.host, member.replica, member.parts

  buildClusterSVG(store2, file("/tmp/%s.svg" % store2.name, "w+"), True)

