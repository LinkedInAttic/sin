#!/usr/bin/env python

"""Python client library for Sin
"""

from senseiClient import SenseiClient
from senseiClient import SenseiRequest

import urllib
import urllib2
import json
import time
import kafka

class Sindex:
	opener = None
	name = None
	senseiClient = None
	baseurl = None
	config = None
	created = None
	
	def __init__(self,id,name,created,url,config,senseiClient):
		self.id = id
		self.name = name
		self.created = created
		self.senseiClient = senseiClient
		self.opener = urllib2.build_opener()
		self.opener.addheaders = [('User-agent', 'Python-urllib/2.5')]
		self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30')]
		self.baseurl = url
		self.config = config
	
	def available(self):
		url = '%s/%s/%s' % (self.baseurl,'available',self.name)
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
		if not jsonObj['ok']:
			print "error: %s" % jsonObj.get('error','unknown error')
			return False
		return jsonObj.get('available',False)
	
	def addDoc(self,uid,doc):
		url = '%s/%s/%d/%s' % (self.baseurl,'add-doc',uid,self.name)
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
		return jsonObj.get('doc')
		
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
	
	def search(self,req=None):
		if not req:
			req = SenseiRequest()
		self.senseiClient.doQuery(req)

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
	
	def newStore(self,name):
		baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
		url = '%s/%s/%s' % (baseurl,'new-store',name)
		print url
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
		
		senseiClient = SenseiClient(self.host,brokerPort,'sensei')
		sindex = Sindex(storeId,name,storeCreated,baseurl,storeConfig,senseiClient)
		while not sindex.available():
			time.sleep(0.5)
		
		print "%s added" %name
		return sindex
		
	def deleteStore(self,name):
		baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
		url = '%s/%s/%s' % (baseurl,'delete-store',name)
		if not jsonObj['ok']:
			errorMsg = "error: %s" % jsonObj.get('msg','unknown error')
			raise Exception(errorMsg)

if __name__ == '__main__':
	client = SinClient()
	idx = client.newStore('test')
	print idx.available()
	print idx.getSize()
	print idx.getDoc(123)
	print idx.addDoc(123,None)
	idx.search()
	