import logging, random, os, subprocess, json, shutil, urllib, urllib2, datetime
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.db import connection
from django.conf import settings
from django.contrib.auth.models import User
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import HttpResponseGone
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseServerError
import kafka

from decorators import login_required, api_key_required
from utils import enum, generate_api_key, get_local_pub_ip
from utils import ClusterLayout
from utils.ClusterLayout import Rectangle, Label, SvgPlotter
from utils import validator

from content_store.models import ContentStore, StoreConfig
from cluster.models import Group, Node, Membership

from senseiClient import SenseiClient
from senseiClient import SenseiRequest
from senseiClient import SenseiSelection

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

kafkaHost = settings.KAFKA_HOST
kafkaPort = int(settings.KAFKA_PORT)
kafkaProducer = kafka.KafkaProducer(kafkaHost, kafkaPort)
validators = {}

@login_required
def storeExists(request,store_name):
  resp = {
    'exists' : request.user.my_stores.filter(name=store_name).exists()
  }
  return HttpResponse(json.dumps(resp))

@api_key_required
def openStore(request,store_name):
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

@login_required
def newStore(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
    resp = {
      'ok' : False,
      'error' : 'store: %s already exists, please choose another name.' % store_name
    }
    return HttpResponse(json.dumps(resp))

  replica = int(request.POST.get('replica','2'))
  partitions = int(request.POST.get('partitions','2'))
  desc = request.POST.get('desc',"")

  num_nodes = Node.objects.count()

  # Check for nodes:
  if num_nodes == 0:
    n = Node.objects.create(host=get_local_pub_ip(), online=True, group=Group(pk=1))
    num_nodes = 1

  if replica > num_nodes:
    resp = {'ok': False, 'error':'Num of replicas is too big'}
    return HttpResponse(json.dumps(resp))

  store = ContentStore(
    name=store_name,
    api_key=generate_api_key(),
    replica=replica,
    partitions=partitions,
    description=desc
  )
  store.save()
  store.collaborators.add(request.user)

  setupCluster(store)

  resp = store.to_map(True)
  resp.update({
    'ok' : True,
    'kafkaHost' : kafkaHost,
    'kafkaPort' : kafkaPort,
  })
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def regenerate_api_key(request, store_name):
  try:
    store = request.user.my_stores.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'msg' : 'You do not own a store with the name "%s".' % store_name
    }
    return HttpResponse(json.dumps(resp))
  store.api_key = generate_api_key()
  store.save()
  resp = {
    'ok': True,
    'api_key': store.api_key,
  }
  return HttpResponse(json.dumps(resp))

@login_required
def deleteStore(request,store_name):
  try:
    try:
      store = request.user.my_stores.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'You do not own a store with the name "%s".' % store_name
      }
      return HttpResponse(json.dumps(resp))
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

@login_required
def purgeStore(request, store_name):
  try:
    try:
      store = request.user.my_stores.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'You do not own a store with the name "%s".' % store_name
      }
      return HttpResponse(json.dumps(resp))
    params = {}
    params["name"] = store_name

    members = store.membership_set.order_by("sensei_node_id")
    for member in members:
      output = urllib2.urlopen("http://%s:%d/%s" % (member.node.host,
                                                    member.node.agent_port,
                                                    "delete-store"),
                               urllib.urlencode(params))

    store.created = store.created + datetime.timedelta(milliseconds=1)
    store.save()

    return startStore(request, store_name)
  except Exception as e:
    logging.exception(e)
    resp = {
      'ok': False,
      'msg': str(e),
    }
  return HttpResponse(json.dumps(resp))

@login_required
def updateSchema(request, store_name, config_id):
  schema = request.POST.get('schema');
  resp = {
    'ok': False,
  }
  
  if schema:
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.schema = schema
    valid, error = config.validate_schema()
    if valid:
      config.updated()
      validator.erase_validator(store_name)
      resp['ok'] = True
      resp.update(config.to_map())
    else:
      resp['error'] = error
  else:
    resp['error'] = 'No schema provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def updateProperties(request, store_name, config_id):
  properties = request.POST.get('properties');
  resp = {
    'ok': False,
  }
  
  if properties:
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.properties = properties
    valid, error = config.validate_properties()
    if valid:
      config.updated()
      resp['ok'] = True
      resp.update(config.to_map())
    else:
      resp['error'] = error
  else:
    resp['error'] = 'No properties provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def updateCustomFacets(request, store_name, config_id):
  custom_facets = request.POST.get('custom_facets');
  resp = {
    'ok': False,
  }
  
  if custom_facets:
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.custom_facets = custom_facets
    valid, error = config.validate_custom_facets()
    if valid:
      config.updated()
      resp['ok'] = True
      resp.update(config.to_map())
    else:
      resp['error'] = error
  else:
    resp['error'] = 'No custom_facets provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def updatePlugins(request, store_name, config_id):
  plugins = request.POST.get('plugins');
  resp = {
    'ok': False,
  }
  
  if plugins:
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.plugins = plugins
    valid, error = config.validate_plugins()
    if valid:
      config.updated()
      resp['ok'] = True
      resp.update(config.to_map())
    else:
      resp['error'] = error
  else:
    resp['error'] = 'No plugins provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def updateVMArgs(request, store_name, config_id):
  vm_args = request.POST.get('vm_args');
  resp = {
    'ok': False,
  }
  
  if vm_args:
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.vm_args = vm_args
    valid, error = config.validate_vm_args()
    if valid:
      config.updated()
      resp['ok'] = True
      resp.update(config.to_map())
    else:
      resp['error'] = error
  else:
    resp['error'] = 'No vm_args provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def updateName(request, store_name, config_id):
  name = request.POST.get('name');
  resp = {
    'ok': False,
  }
  
  if name is not None:
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.name = name
    config.save()
    resp['ok'] = True
    resp.update(config.to_map())
  else:
    resp['error'] = 'No name provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def configExtensions(request, store_name, config_id):
  try:
    config = StoreConfig.objects.filter(
      store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
  except StoreConfig.DoesNotExist:
    resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
    return HttpResponse(json.dumps(resp))

  resp = [f.to_map() for f in config.extensions.all()]
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def updateExtensions(request, store_name, config_id):
  extensions = request.POST.get('extensions');
  resp = {
    'ok': False,
  }
  
  if extensions:
    extensions = json.loads(extensions.encode('utf-8'))
    try:
      config = StoreConfig.objects.filter(
        store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
    except StoreConfig.DoesNotExist:
      resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
      return HttpResponse(json.dumps(resp))

    config.updated()
    config.extensions = extensions
    resp['ok'] = True
    resp.update(config.to_map())
  else:
    resp['error'] = 'No extensions provided.'

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def deleteConfig(request, store_name, config_id):
  resp = {
    'ok': False,
  }
  try:
    config = StoreConfig.objects.filter(
      store=ContentStore.objects.filter(name=store_name, collaborators=request.user)).get(id=config_id)
  except StoreConfig.DoesNotExist:
    resp['error'] = 'You do not own a config with the store name "%s" and config id "%s".' % (store_name, config_id)
    return HttpResponse(json.dumps(resp))

  if config.last_activated <= datetime.datetime.now():
    resp['error'] = 'Active config cannot be deleted.'
  else:
    config.delete()
    resp['ok'] = True

  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@api_key_required
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

@api_key_required
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

@login_required
def startStore(request, store_name, config_id=None, restart=False):
  try:
    try:
      store = request.user.my_stores.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'You do not own a store with the name "%s".' % store_name
      }
      return HttpResponse(json.dumps(resp))

    if config_id:
      current_config = store.configs.get(id=config_id)
    else:
      current_config = store.current_config

    webapp = os.path.join(settings.SENSEI_HOME,'sensei-core/src/main/webapp')
    store_home = os.path.join(settings.STORE_HOME, store_name)
    index = os.path.join(store_home, 'index')
    extensions = []
    for ext in current_config.extensions.all():
      url = ext.the_file.url
      if not url.startswith('http:'):
        url = request.build_absolute_uri(url)
      extensions.append(url)

    params = {
      'name': store_name,
      'vm_args': current_config.vm_args,
      'sensei_port': store.sensei_port,
      'broker_host': store.broker_host,
      'broker_port': store.broker_port,
      'extensions': json.dumps(extensions),
      'schema': store.current_config.schema,
    }
  
    members = store.membership_set.order_by("sensei_node_id")
    for member in members:
      context = RequestContext(request, {
         'node_id': member.sensei_node_id,
         'node_partitions': member.parts[1:len(member.parts)-1],
         'max_partition_id': store.partitions - 1,
         'store': store,
         'index': index,
         'webapp': webapp,
         'kafka_host': kafkaHost,
         'kafka_port': kafkaPort,
         'zookeeper_url': settings.ZOOKEEPER_URL,
        })

      sensei_custom_facets = loader.get_template_from_string(current_config.custom_facets)
      params["sensei_custom_facets"] = sensei_custom_facets.render(context)

      sensei_plugins = loader.get_template_from_string(current_config.plugins)
      params["sensei_plugins"] = sensei_plugins.render(context)

      sensei_properties = loader.get_template_from_string(current_config.properties)
      params["sensei_properties"] = sensei_properties.render(context)

      logger.info("Sending request: http://%s:%d/%s" % (member.node.host, member.node.agent_port,
                                                not restart and "start-store" or "restart-store"))
      output = urllib2.urlopen("http://%s:%d/%s"
                               % (member.node.host, member.node.agent_port,
                                  not restart and "start-store" or "restart-store"),
                               urllib.urlencode(params))

    store.configs.filter(active=True).update(active=False)
    current_config.active = True
    current_config.last_activated = datetime.datetime.now();
    current_config.save()
    store.status = enum.STORE_STATUS['running']
    store.save()
    resp = store.to_map(True, True)
    resp.update({
      "ok":True,
    })
    return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))
  except Exception as e:
    logging.exception(e)   
    return HttpResponseServerError(json.dumps({'ok':False,'error':e.message}))

@login_required
def stopStore(request, store_name):
  try:
    try:
      store = request.user.my_stores.get(name=store_name)
    except ContentStore.DoesNotExist:
      resp = {
        'ok' : False,
        'msg' : 'You do not own a store with the name "%s".' % store_name
      }
      return HttpResponse(json.dumps(resp))
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

@login_required
def restartStore(request, store_name, config_id=None):
  return startStore(request, store_name, config_id, restart=True)

@api_key_required
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

@api_key_required
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

@api_key_required
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
    ids = json.loads(ids.encode('utf-8'))
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

@api_key_required
def available(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
    resp = {'ok':True,'store':store_name,"available":True}
  else:
    resp = {'ok':False,'error':'store: %s does not exist.' % store_name}
  return HttpResponse(json.dumps(resp))

@login_required
def stores(request):
  objs = request.user.my_stores.order_by('-created')
  resp = objs.to_map_list(True)
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def collaborators(request, store_name):
  try:
    store = ContentStore.objects.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'store: %s does not exist.' % store_name
    }
    return HttpResponseNotFound(json.dumps(resp))
  resp = [{
      'id': c.id,
      'username': c.username,
    } for c in store.collaborators.all()]
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def configs(request, store_name):
  try:
    store = ContentStore.objects.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'store: %s does not exist.' % store_name
    }
    return HttpResponseNotFound(json.dumps(resp))
  resp = [c.to_map() for c in store.configs.all()]
  if not resp:
    resp = [store.current_config.to_map()]
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

@login_required
def add_collab(request, store_name):
  try:
    store = request.user.my_stores.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'You do not own a store with the name "%s".' % store_name
    }
    return HttpResponse(json.dumps(resp))

  username = request.REQUEST.get('username', '')
  try:
    user = User.objects.get(username=username)
  except User.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'Unknown user: "%s".' % username
    }
    return HttpResponse(json.dumps(resp))

  # Not checking if user alread in collabs, just adding
  store.collaborators.add(user)
  resp = {
    'ok' : True,
    'id': user.id,
    'username': user.username,
  }
  return HttpResponse(json.dumps(resp))

@login_required
def remove_collab(request, store_name):
  try:
    store = request.user.my_stores.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'You do not own a store with the name "%s".' % store_name
    }
    return HttpResponse(json.dumps(resp))

  username = request.REQUEST.get('username', '')
  try:
    user = store.collaborators.get(username=username)
  except User.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'User "%s" is not a collaborator of store "%s".' % (username, store_name)
    }
    return HttpResponse(json.dumps(resp))
  if request.user == user:
    resp = {
      'ok' : False,
      'error' : 'You cannot remove your self.'
    }
    return HttpResponse(json.dumps(resp))

  store.collaborators.remove(user)
  resp = {
    'ok' : True,
    'id': user.id,
    'username': user.username,
  }
  return HttpResponse(json.dumps(resp))

@login_required
def cluster_svg(request, store_name):
  resp = {
    'ok' : True,
  }
  try:
    store = request.user.my_stores.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'You do not own a store with the name "%s".' % store_name
    }
    return HttpResponse(json.dumps(resp))

  s = StringIO()
  buildClusterSVG(store, s, False)
  resp['cluster'] = s.getvalue()
  s.close()
  return HttpResponse(json.dumps(resp))

@login_required
def with_running_info(request, store_name):
  resp = {
    'ok' : True,
  }
  try:
    store = request.user.my_stores.get(name=store_name)
  except ContentStore.DoesNotExist:
    resp = {
      'ok' : False,
      'error' : 'You do not own a store with the name "%s".' % store_name
    }
    return HttpResponse(json.dumps(resp))

  resp.update(store.to_map(True, True))
  return HttpResponse(json.dumps(resp, ensure_ascii=False, cls=DateTimeAwareJSONEncoder))

def setupCluster(store):
  """Set up the cluster for a given store.

  Set up the cluster for a store based on currently available
  Sensei nodes.  The cluster layout is determined by the store's number
  of replicas and number of partitions.
  """
  nodes = store.group.nodes.filter(online=True)
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
      nodeId = i * numNodesPerReplica + j
      parts = []
      for k in range(numPartsPerNode):
        parts.append(j * numPartsPerNode + k)
      if remainingParts > 0 and j < remainingParts:
        parts.append(store.partitions - remainingParts + j)
      Membership.objects.create(node = nodes[nodeId],
                                store = store,
                                replica = i,
                                sensei_node_id = nodeId,
                                parts = parts)

def buildClusterSVG(store, stream, xml_header=True):
  """Given a store, generate the SVG for its cluster layout.
  
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
      current_node = members[i * numNodesPerReplica + j].node
      x1 = xOffset + j * ClusterLayout.NODE_DISTANCE_X
      layout.addNode(x1, y1,
                     node_id = i * numNodesPerReplica + j,
                     online = current_node.online,
                     host = current_node.host,
                     parts = members[i * numNodesPerReplica + j].parts)

  layout.setSize(xOffset + numNodesPerReplica * ClusterLayout.NODE_DISTANCE_X,
                 yOffset + (store.replica + extraRow) * ClusterLayout.NODE_DISTANCE_Y)

  plotter = SvgPlotter(stream)
  plotter.visitImage(layout, xml_header)
  return stream


def testSetupCluster():
  """Testing cluster setup for stores."""

  # Create some nodes

  nodes = []
  for i in range(10):
    nodes.append(Node.objects.create(host="ela4-be80%d" % i, online=True, group=Group(pk=1)))

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

  # Remove one node, and redraw cluster layout for store 1
  nodes[4].online = False
  nodes[4].save()
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

  # Delete all the testing nodes and stores
  for node in nodes:
    node.delete()
  store1.delete()
  store2.delete()
