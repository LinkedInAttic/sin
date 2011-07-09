#!/usr/bin/env python

"""Python client library for Sin
"""

from senseiClient import SenseiClient
from senseiClient import SenseiRequest

import urllib
import urllib2
import json
import time

class Sindex:
	opener = None
	name = None
	senseiClient = None
	baseurl = None
	
	def __init__(self,name,url,senseiClient):
		self.name = name
		self.senseiClient = senseiClient
		self.opener = urllib2.build_opener()
		self.opener.addheaders = [('User-agent', 'Python-urllib/2.5')]
		self.opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30')]
		self.baseurl = url
	
	def available(self):
		url = '%s/%s/%s' % (self.baseurl,'available',self.name)
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
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
	
	def newIndex(self,name):
		baseurl = 'http://%s:%d/%s' % (self.host,self.port,'store')
		url = '%s/%s/%s' % (baseurl,'new-index',name)
		print url
		urlReq = urllib2.Request(url)
		res = self.opener.open(urlReq)
		jsonObj = dict(json.loads(res.read()))
		
		senseiHost = jsonObj['sensei-host']
		senseiPort = jsonObj['sensei-port']
		senseiPath = jsonObj['sensei-path']
		
		senseiClient = SenseiClient(senseiHost,senseiPort,senseiPath)
		sindex = Sindex(name,baseurl,senseiClient)
		while not sindex.available():
			time.sleep(0.5)
		
		print "%s added" %name
		return sindex

if __name__ == '__main__':
	client = SinClient()
	idx = client.newIndex('test')
	print idx.available()
	print idx.getSize()
	print idx.getDoc(123)
	print idx.addDoc(123,None)
	idx.search()
	