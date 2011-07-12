import random, os, subprocess
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.http import Http404

from content_store.models import ContentStore

from utils import json
import shutil

running = {
}


def storeExists(request,store_name):
	resp = {
		'exists' : ContentStore.objects.filter(name=store_name).exists()
	}
	return HttpResponse(json.json_encode(resp))

def newStore(request,store_name):
  if ContentStore.objects.filter(name=store_name).exists():
	resp = {
		'ok' : False,
		'error' : 'store: %s already exists.' % store_name
	}
	return HttpResponse(json.json_encode(resp))

  store = ContentStore(name=store_name, sensei_port=random.randint(10000, 15000), broker_port=random.randint(15000, 20000))
  store.save()

  pid = startNewStore(store_name)

  resp = {
	'ok' : True,
    'id': store.id,
    'name': store.name,
    'sensei_port': store.sensei_port,
    'broker_port': store.broker_port,
    'config': store.config,
    'created': store.created,
    'status': store.status,
	'pid' : pid,
  }
  print "req completed"
  return HttpResponse(json.json_encode(resp))

def deleteStore(request,store_name):
	if not ContentStore.objects.filter(name=store_name).exists():
		resp = {
			'ok' : False,
			'msg' : 'store: %s does not exist.' % store_name
		}
		return HttpResponse(json.json_encode(resp))
	killStore(store_name)
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

def killStore(store_name):
	global running

	pid = running.get(store_name)
	if pid:
		os.system('kill %s' % pid)
		del running[store_name]
		
	store_home = os.path.join(settings.STORE_HOME, store_name)
	try:
		shutil.rmtree(store_home)
	except:
		pass
	
def stopStore(request, store_name):
  killStore(store_name)
  return HttpResponse(json.json_encode({'ok': True}))


def startStore(request, store_name):
	pid = startNewStore(store_name)
	return HttpResponse(json.json_encode({'ok': True,'pid':pid}))
	
def startNewStore(store_name):
  global running

  pid = running.get(store_name)
  if pid:
	print("%s is already started." % store_name)
	return pid

  store = ContentStore.objects.get(name=store_name)

  classpath1 = os.path.join(settings.SENSEI_HOME, 'target/*')
  classpath2 = os.path.join(settings.SENSEI_HOME, 'target/lib/*')
  log4jclasspath = os.path.join(settings.SENSEI_HOME,'resources')

  classpath = "%s:%s:%s" % (classpath1,classpath2,log4jclasspath)

  store_home = os.path.join(settings.STORE_HOME, store_name)
  index = os.path.join(store_home, 'index')
  try:
    os.makedirs(index)
  except:
    pass
  conf = os.path.join(store_home, 'conf')
  try:
    os.makedirs(conf)
  except:
    pass
  logs = os.path.join(store_home, 'logs')
  try:
    os.makedirs(logs)
  except:
    pass

  sensei_properties = loader.render_to_string(
    'sensei-conf/sensei.properties', {
      'store': store,
      'index': index,
    })
  sensei_custom_facets = loader.render_to_string(
    'sensei-conf/custom-facets.xml', {
    })
  sensei_plugins = loader.render_to_string(
    'sensei-conf/plugins.xml', {
    })

  out_file = open(os.path.join(conf, 'sensei.properties'), 'w+')
  try:
    out_file.write(sensei_properties)
    out_file.flush()
  finally:
    out_file.close()

  out_file = open(os.path.join(conf, 'custom-facets.xml'), 'w+')
  try:
    out_file.write(sensei_custom_facets)
    out_file.flush()
  finally:
    out_file.close()

  out_file = open(os.path.join(conf, 'schema.json'), 'w+')
  try:
    out_file.write(store.config)
    out_file.flush()
  finally:
    out_file.close()

  out_file = open(os.path.join(conf, 'plugins.xml'), 'w+')
  try:
    out_file.write(sensei_plugins)
    out_file.flush()
  finally:
    out_file.close()

  cmd = ["java", "-server", "-d64", "-Xmx1g", "-Xms1g", "-XX:NewSize=256m", "-classpath", classpath, "-Dlog.home=%s" % logs, "com.sensei.search.nodes.SenseiServer", conf]

  print ' '.join(cmd)

  p = subprocess.Popen(cmd, cwd=settings.SENSEI_HOME)
  running[store_name] = p.pid
  return p.pid

  

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
  if ContentStore.objects.filter(name=store_name).exists():
  	resp = {'ok':True,'store':store_name,"available":True}
  else:
	resp = {'ok':False,'error':'store: %s does not exist.' % store_name}
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

