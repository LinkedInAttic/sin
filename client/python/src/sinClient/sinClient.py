#!/usr/bin/env python

"""Python client library for Sin
"""

from senseiClient import *

import urllib
import urllib2
import time
import kafka

import json

class Sindex:
  opener = None
  name = None
  senseiClient = None
  baseurl = None
  config = None
  created = None
  description = None
  status = None
  
  def __init__(self,id,name,description,created,url,config,senseiClient,status):
    self.id = id
    self.name = name
    self.created = created
    self.description = description
    self.senseiClient = senseiClient
    self.opener = urllib2.build_opener()
    self.opener.addheaders = [('User-agent', 'Python-urllib/2.5')]
    self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30')]
    self.baseurl = url
    self.config = config
    self.status = status
  
  def available(self):
    url = '%s/%s/%s' % (self.baseurl,'available',self.name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('available',False)

  def start(self):
    url = '%s/%s/%s' % (self.baseurl,'start-store',self.name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))

  def start(self):
    url = '%s/%s/%s' % (self.baseurl,'stop-store',self.name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
  
  def addDoc(self,doc):
    if not doc:
      raise Exception('no doc supplied')
    url = '%s/%s/%s' % (self.baseurl,'add-doc',self.name)
    
    params = urllib.urlencode({'doc': doc})
    urlReq = urllib2.Request(url,params)
    res = self.opener.open(urlReq)

    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('numPosted',0)
    
  def addDocs(self,docs):
    if not docs:
      raise Exception('no docs supplied')
    url = '%s/%s/%s' % (self.baseurl,'add-docs',self.name)

    params = urllib.urlencode({'docs': docs})
    urlReq = urllib2.Request(url,params)
    res = self.opener.open(urlReq)

    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('numPosted',0)

  def updateDoc(self,doc):
    if not doc:
        raise Exception('no doc supplied')
    url = '%s/%s/%s' % (self.baseurl,'update-doc',self.name)

    params = urllib.urlencode({'doc': doc})
    urlReq = urllib2.Request(url,params)
    res = self.opener.open(urlReq)

    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      raise Exception("error: %s" % jsonObj.get('error','unknown error'))
    return jsonObj.get('numPosted',0)
    
  def importFile(self,dataFile):
    fd = open(dataFile,'r+')
    for line in fd:
      print line
      self.kafkaProducer.send([line], self.name.encode('utf-8'))
    fd.close()
    
  def getDoc(self,uid):
    req = SenseiRequest()
    sel = SenseiSelection("uid")
    sel.addSelection(str(uid))
    req.count = 1
    req.fetch = True
    req.selections = [sel]
    res = self.senseiClient.doQuery(req)
    doc = None
    if res.numHits > 0:
      if res.hits and len(res.hits) > 0:
        hit = res.hits[0]
        doc = hit.srcData
    if doc:
      return json.loads(doc)
    else:
    return None

  def delDoc(self,id):
    if not id:
      return 0
    uid = long(id)
    url = '%s/%s/%s' % (self.baseurl,'delete-doc',self.name)
    doc = {'id':uid,'isDeleted':True}
    jsonObj = json.JSONEncoder().encode(doc)
    jsonString = json.dumps(jsonObj)
    self.kafkaProducer.send([jsonString.encode('utf-8')],self.name.encode('utf-8'))
    return 1

  def delDocs(self,idList):
    if not idList or len(idList)==0:
      return 0
    delObjs = []
    for id in idList:
      delDoc = {'id':id,'isDeleted':True}
      jsonObj = json.JSONEncoder().encode(delDoc)
      jsonString = json.dumps(jsonObj)
      delObjs.append(jsonString.encode('utf-8'))
    self.kafkaProducer.send(delObjs,self.name.encode('utf-8'))
    return len(idList)

  def getSize(self):
    req = SenseiRequest()
    req.count = 0
    res = self.senseiClient.doQuery(req)
    return res.totalDocs
  
  def getSenseiClient(self):
    return self.senseiClient

class SinClient:
  host = None
  port = None
  opener = None
  path = 'store'
  
  def __init__(self,host='localhost',port=8000):
    self.host = host
    self.port = port
    self.opener = urllib2.build_opener()
    self.opener.addheaders = [('User-agent', 'Python-urllib/2.5')]
    self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30')]
  
  def openStore(self,name):
    baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    url = '%s/%s/%s' % (baseurl,'open-store',name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    
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
    
    senseiClient = SenseiClient(self.host,brokerPort)
    sindex = Sindex(storeId,name,description,storeCreated,baseurl,storeConfig,senseiClient,status)
    while not sindex.available():
      time.sleep(0.5)
    
    return sindex

  def newStore(self,name,rep=2,parts=10,description=""):
    baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    url = '%s/%s/%s' % (baseurl,'new-store',name)
    params = urllib.urlencode(dict(replica=rep,partitions=parts,desc=description))
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq,params)
    jsonObj = dict(json.loads(res.read()))
    
    if not jsonObj['ok']:
      errorMsg = "error: %s" % jsonObj.get('error','unknown error')
      raise Exception(errorMsg)
    
    brokerPort = jsonObj['broker_port']
    senseiPort = jsonObj['sensei_port']
    storeId = jsonObj['id']
    storeConfig = jsonObj.get('config')
    storeCreated = jsonObj['created']
    storeStatus = jsonObj['status']
    kafkaHost = jsonObj['kafkaHost']
    kafkaPort = jsonObj['kafkaPort']
    description = jsonObj.get('description',None)
    status = jsonObj['status_display']
    
    senseiClient = SenseiClient(self.host,brokerPort)
    sindex = Sindex(storeId,name,description,storeCreated,baseurl,storeConfig,senseiClient,kafkaHost,kafkaPort,status)
    while not sindex.available():
      time.sleep(0.5)
    
    print "%s added" %name
    return sindex
  
  def storeExists(self,name):
    baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    url = '%s/%s/%s' % (baseurl,'exists',name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    return jsonObj['exists']
    
  def deleteStore(self,name):
    baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
    url = '%s/%s/%s' % (baseurl,'delete-store',name)
    urlReq = urllib2.Request(url)
    res = self.opener.open(urlReq)
    jsonObj = dict(json.loads(res.read()))
    if not jsonObj['ok']:
      errorMsg = "error: %s" % jsonObj.get('msg','unknown error')
      raise Exception(errorMsg)

if __name__ == '__main__':
  client = SinClient()
  store = client.openStore('tweets')
  searcher = store.getSenseiClient()
  req = SenseiRequest()

  req.fetch = True
  req.count = 5
  res = searcher.doQuery(req)

  for hit in res.hits:
    print hit.uid
    srcdata = hit.srcData
    if srcdata:
      print srcdata.get('author-name')
    else:
      print 'none'
"""
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

