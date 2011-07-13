#!/usr/bin/env python

"""Python client library for Sin
"""

from senseiClient import SenseiClient
from senseiClient import SenseiRequest

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
	kafkaProducer = None
	description = None
	
	def __init__(self,id,name,description,created,url,config,senseiClient,kafkaHost,kafkaPort):
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
		self.kafkaProducer = kafka.KafkaProducer(kafkaHost, kafkaPort)
	
	def available(self):
		url = '%s/%s/%s' % (self.baseurl,'available',self.name)
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
		if not jsonObj['ok']:
			print "error: %s" % jsonObj.get('error','unknown error')
			return False
		return jsonObj.get('available',False)
	
	def addDoc(self,doc):
		if not doc:
			return None
		uid = long(doc['id'])
		jsonObj = json.JSONEncoder().encode(doc)
		print jsonObj
		jsonString = json.dumps(jsonObj)
		print jsonString
		self.kafkaProducer.send([jsonString],self.name.encode('utf-8'))
		return doc
		
	def addDocs(self,docs):
		if not docs:
			return 0
		messages = []
		for doc in docs:
			uid = long(doc['id'])
			jsonObj = json.JSONEncoder().encode(doc)
			jsonString = json.dumps(jsonObj)
			messages.append(jsonString)
		self.kafkaProducer.send(messages, self.name.encode('utf-8'))
		return len(messages)
		
	def importFile(self,dataFile):
		fd = open(dataFile,'r+')
		for line in fd:
			print line
			self.kafkaProducer.send([line], self.name.encode('utf-8'))
		fd.close()
		
	def getDoc(self,uid):
		url = '%s/%s/%d/%s' % (self.baseurl,'get-doc',uid,self.name)
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
		return jsonObj.get('doc')
		
	def getSize(self):
		url = '%s/%s/%s' % (self.baseurl,'get-size',self.name)
		print url
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
		print jsonObj
		return jsonObj.get('size',0)
	
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
		kafkaHost = jsonObj['kafkaHost']
		kafkaPort = jsonObj['kafkaPort']
		description = jsonObj.get('description',None)
		
		senseiClient = SenseiClient(self.host,brokerPort,name)
		sindex = Sindex(storeId,name,description,storeCreated,baseurl,storeConfig,senseiClient,kafkaHost,kafkaPort)
		while not sindex.available():
			time.sleep(0.5)
		
		return sindex

	def newStore(self,name):
		baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
		url = '%s/%s/%s' % (baseurl,'new-store',name)
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
		kafkaHost = jsonObj['kafkaHost']
		kafkaPort = jsonObj['kafkaPort']
		description = jsonObj.get('description',None)
		
		senseiClient = SenseiClient(self.host,brokerPort,name)
		sindex = Sindex(storeId,name,description,storeCreated,baseurl,storeConfig,senseiClient,kafkaHost,kafkaPort)
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
	
	"""senseiClient = store.getSenseiClient()
	result = senseiClient.doQuery()"""

