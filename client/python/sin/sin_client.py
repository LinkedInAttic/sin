#!/usr/bin/env python

"""Python client library for Sin
"""

import cookielib
import json
import sys
import time
import urllib
import urllib2

from sensei import BQLRequest, SenseiClientError, SenseiFacet, SenseiSelection,\
                   SenseiSort, SenseiFacetInitParams, SenseiFacetInfo,\
                   SenseiNodeInfo, SenseiSystemInfo, SenseiRequest, SenseiHit,\
                   SenseiResultFacet, SenseiResult, SenseiClient

from optparse import OptionParser
import getpass

store_map = {}

class Sindex:
  opener = None
  name = None
  senseiClient = None
  baseurl = None
  config = None
  created = None
  description = None
  status = None
  
  def __init__(self, id, name, api_key, description, created, url, config, senseiClient, status, cookie_jar):
    self.id = id
    self.name = name
    self.api_key = api_key
    self.created = created
    self.description = description
    self.senseiClient = senseiClient
    self.cookie_jar = cookie_jar
    self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
    self.opener.addheaders = [('X-Sin-Api-Key', api_key)]
    self.baseurl = url
    self.config = config
    self.status = status
  
  def available(self):
    """Check if the store is available."""
    url = '%s/%s/%s' % (self.baseurl,'available',self.name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('available',False)

  def start(self):
    """Start the store."""
    url = '%s/%s/%s' % (self.baseurl,'start-store',self.name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))

  def stop(self):
    """Stop the store."""
    url = '%s/%s/%s' % (self.baseurl,'stop-store',self.name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
  
  def addDoc(self,doc):
    """Add a document to the store."""
    return self.addDocs([doc])

  def addDocs(self,docs):
    """Add a list of documents."""
    if not docs:
      raise Exception('no docs supplied')
    url = '%s/%s/%s' % (self.baseurl,'add-docs',self.name)

    params = urllib.urlencode({'docs': json.dumps(docs)})
    urlReq = urllib2.Request(url,params)
    res = self.opener.open(urlReq)

    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('numPosted',0)

  def updateDoc(self,doc):
    """Update a document."""
    if not doc:
      raise Exception('no doc supplied')
    url = '%s/%s/%s' % (self.baseurl,'update-doc',self.name)

    params = urllib.urlencode({'doc': json.dumps(doc)})
    urlReq = urllib2.Request(url,params)
    res = self.opener.open(urlReq)

    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('numPosted',0)
    
  def importFile(self,dataFile,batchSize=100):
    batch = []
    fd = open(dataFile,'r+')
    for line in fd:
      jsonObj = dict(json.loads(line))
      batch.append(jsonObj)
      if batch.length >= batchSize:
        self.addDocs(batch)
        batch = []
    fd.close()
    if batch.length > 0:
      self.addDocs(batch)

    
  def getDoc(self, id):
    """Retrieve a document based its document ID."""
    if not id:
      return None

    req = SenseiRequest()
    sel = SenseiSelection("uid")
    sel.addSelection(str(id))
    req.count = 1
    req.fetch_stored = True
    req.selections = [sel]
    res = self.senseiClient.doQuery(req)
    doc = None
    if res.numHits > 0:
      if res.hits and len(res.hits) > 0:
        hit = res.hits[0]
        doc = hit.srcData
    if doc:
      return doc
    else:
      return None

  def delDoc(self,id):
    """Delete a document based on the document ID.

    Return 1 if the document is deleted successfully; 0 otherwise.
    
    """
    return self.delDocs([id])

  def delDocs(self, idList):
    """Delete multiple documents based on a list of document IDs.

    Return the number of documents deleted successfully.

    """
    if not idList or len(idList)==0:
      return 0

    url = '%s/%s/%s' % (self.baseurl,'delete-docs',self.name)
    params = urllib.urlencode({"ids": idList})
    urlReq = urllib2.Request(url, params)
    res = self.opener.open(urlReq)

    jsonObj = json.loads(res.read())
    if not jsonObj["ok"]:
      raise Exception("error: %s" % jsonObj.get("error", "unknown error"))
    return jsonObj.get("numDeleted", 0)

  def getSize(self):
    req = SenseiRequest()
    req.count = 0
    res = self.senseiClient.doQuery(req)
    return res.totalDocs
  
  def getSenseiClient(self):
    return self.senseiClient

class SinClient:
  """Sin Client."""

  def __init__(self, host='localhost', port=8666):
    self.host = host
    self.port = port
    self.stores = None
    self.store_map = {}
    self.cookie_jar = cookielib.CookieJar()
    self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))

  def login(self, username, password):
    url = 'http://%s:%s/login_api' % (self.host, self.port)
    res = self.opener.open(url, json.dumps({'username': username, 'password': password}))
    obj = json.loads(res.read())
    if not obj.get('ok'):
      raise Exception(obj.get('msg', 'Login failed'))

    # Get info of all stores
    baseurl = 'http://%s:%d/%s' % (self.host, self.port, 'store')
    urlReq = urllib2.Request(baseurl + "/stores")
    stores = self.opener.open(urlReq).read()
    self.stores = json.loads(stores)
    for store in self.stores:
      self.store_map[store.get("name")] = store
    return True

  def logout(self):
    url = 'http://%s:%s/logout_api' % (self.host, self.port)
    res = self.opener.open(url)
    obj = json.loads(res.read())
    if not obj.get('ok'):
      raise Exception(obj.get('msg', 'Logout failed'))
    return True

  def show_stores(self):
    """Execute SHOW STORES command."""

    keys = ["name", "description"]
    max_lens = None

    def get_max_lens(keys):
      max_lens = {}
      for key in keys:
        max_lens[key] = len(key)
      for store in self.stores:
        for key in keys:
          tmp_len = len(store.get(key))
          if tmp_len > max_lens[key]:
            max_lens[key] = tmp_len
      return max_lens

    def print_line(keys, max_lens, char='-', sep_char='+'):
      sys.stdout.write(sep_char)
      for key in keys:
        sys.stdout.write(char * (max_lens[key] + 2) + sep_char)
      sys.stdout.write('\n')

    def print_header(keys, max_lens):
      print_line(keys, max_lens, '-', '+')
      sys.stdout.write('|')
      for key in keys:
        sys.stdout.write(' %s%s |' % (key, ' ' * (max_lens[key] - len(key))))
      sys.stdout.write('\n')
      print_line(keys, max_lens, '-', '+')

    def print_footer(keys, max_lens):
      print_line(keys, max_lens, '-', '+')

    max_lens = get_max_lens(keys)
    print_header(keys, max_lens)
    for store in self.stores:
      sys.stdout.write('|')
      for key in keys:
        val = store.get(key)
        sys.stdout.write(' %s%s |' % (val, ' ' * (max_lens[key] - len(val))))
      sys.stdout.write('\n')
    print_footer(keys, max_lens)
  
  def openStore(self, name, api_key):
    baseurl = 'http://%s:%d/%s' % (self.host, self.port, 'store')
    url = '%s/%s/%s' % (baseurl,'open-store',name)
    urlReq = urllib2.Request(url)
    self.opener.addheaders = [('X-Sin-Api-Key', api_key)]
    res = self.opener.open(urlReq)
    jsonObj = json.loads(res.read())
    
    if not jsonObj['ok']:
      errorMsg = "error: %s" % jsonObj.get('error','unknown error')
      raise Exception(errorMsg)
    
    brokerPort = jsonObj['broker_port']
    senseiPort = jsonObj['sensei_port']
    storeId = jsonObj['id']
    storeConfig = jsonObj.get('config')
    storeCreated = jsonObj['created']
    storeStatus = jsonObj['status']
    description = jsonObj.get('description',None)
    status = jsonObj['status_display']
    
    senseiClient = SenseiClient(self.host, brokerPort)
    sindex = Sindex(storeId,name,api_key,description,storeCreated,baseurl,storeConfig,senseiClient,status,self.cookie_jar)
    while not sindex.available():
      time.sleep(0.5)
    
    return sindex

  #def newStore(self,name,rep=1,parts=10,description=""):
    #baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    #url = '%s/%s/%s' % (baseurl,'new-store',name)
    #params = urllib.urlencode(dict(replica=rep,partitions=parts,desc=description))
    #urlReq = urllib2.Request(url)
    #res = self.opener.open(urlReq,params)
    #jsonObj = dict(json.loads(res.read()))
    
    #if not jsonObj['ok']:
      #errorMsg = "error: %s" % jsonObj.get('error','unknown error')
      #raise Exception(errorMsg)
    
    #brokerPort = jsonObj['broker_port']
    #senseiPort = jsonObj['sensei_port']
    #storeId = jsonObj['id']
    #storeConfig = jsonObj.get('config')
    #storeCreated = jsonObj['created']
    #storeStatus = jsonObj['status']
    #kafkaHost = jsonObj['kafkaHost']
    #kafkaPort = jsonObj['kafkaPort']
    #description = jsonObj.get('description',None)
    #status = jsonObj['status_display']
    
    #senseiClient = SenseiClient(self.host,brokerPort)
    #return Sindex(storeId,name,description,storeCreated,baseurl,storeConfig,senseiClient,status,self.cookie_jar)

  #def storeExists(self,name):
    #baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    #url = '%s/%s/%s' % (baseurl,'exists',name)
    #urlReq = urllib2.Request(url)
    #res = self.opener.open(urlReq)
    #jsonObj = dict(json.loads(res.read()))
    #return jsonObj['exists']
    
  #def deleteStore(self,name):
    #baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    #url = '%s/%s/%s' % (baseurl,'delete-store',name)
    #urlReq = urllib2.Request(url)
    #res = self.opener.open(urlReq)
    #jsonObj = dict(json.loads(res.read()))
    #if not jsonObj['ok']:
      #errorMsg = "error: %s" % jsonObj.get('msg','unknown error')
      #raise Exception(errorMsg)

"""
if __name__ == '__main__':
  client = SinClient()
  store = client.openStore('tweets')
  searcher = store.getSenseiClient()
  req = SenseiRequest()

  req.fetch_stored = True
  req.count = 5
  res = searcher.doQuery(req)

  for hit in res.hits:
    print hit.uid
    srcdata = hit.srcData
    if srcdata:
      print srcdata.get('author-name')
    else:
      print 'none'

if __name__ == '__main__':
  storeName = 'test'
  client = SinClient()
  if client.storeExists(storeName):
    store = client.openStore(storeName)
  else:
    store = client.newStore(storeName)
  print store.available()
  print store.getSize()
  print store.getDoc(123)
  obj = {'id':1,'color':'red'}
  print store.addDoc(obj)
  print store.addDocs([obj,obj])
  store.importFile("test.json")
  
  senseiClient = store.getSenseiClient()
  result = senseiClient.doQuery()"""


def main(argv):
  usage = "Usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("-n", "--host", dest="host",
                    default="localhost", help="Host name of Sin server")
  parser.add_option("-o", "--port", dest="port",
                    default=8666, help="Port of Sin server")
  parser.add_option("-u", "--user", dest="user",
                    help="Sin user name (login id)")
  parser.add_option("-p", "--password", dest="password",
                    help="Sin user password")

  (options, args) = parser.parse_args()
  if options.password == None:
    options.password = getpass.getpass()

  my_client = SinClient(options.host, options.port)
  my_client.login(options.user, options.password)

  import logging  
  logger = logging.getLogger("sin_client")  
  logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d - %(message)s")
  stream_handler = logging.StreamHandler()
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)

  def cleanup():
    """ clean up when the user exit the command line
    """

  def getStoreName(stmt):
    if stmt.startswith("use "):
      args = stmt.split()
      return args[1]
    else:
      return ""
    
  def testStore(store, api_key):
    try:
        sinClient_test = SinClient()
        sinClient_test.openStore(store, api_key)
        return True
    except:
      return False

  def execute_bql(stmt):
    req = SenseiRequest(stmt)
    store = my_client.store_map.get(req.index)
    if not store:
      print "Store %s does not exist!" % req.index
      return

    client = SenseiClient(store["broker_host"], store["broker_port"])
    if req.stmt_type == "select":
      res = client.doQuery(req)
      res.display(req.get_columns(), 1000)
    elif req.stmt_type == "desc":
      sysinfo = client.getSystemInfo()
      sysinfo.display()
    else:
      print "Wrong command: %s" % stmt

  import readline
  store = ""
  readline.parse_and_bind("tab: complete")
  print "Sin Commandline version 0.1;"
  print "Type 'exit' to end this program."
  while 1:
    try:
      stmt = raw_input('> ')
      parts = stmt.split()
      if (len(parts) == 1 and
          parts[0].lower() == "exit"):
        cleanup()
        break;
      elif (len(parts) == 2 and
            parts[0].lower() == "show" and
            parts[1].lower() in ["stores", "tables"]):
        my_client.show_stores()
      else:
        execute_bql(stmt)
    except EOFError:
      print "EOF error"
      break
    except Exception as e:
      print e.message

if __name__ == '__main__':
    main(sys.argv)
