#!/usr/bin/env python

"""Python client library for Sin
"""

from senseiClient import SenseiClient
from senseiClient import SenseiRequest

import urllib
import urllib2
import json

class Sindex:
	senseiHost = None
	senseiPort = None
	senseiPath = None
	name = None
	senseiClient = None
	
	def __init__(self,name,host,port,path):
		self.name = name
		self.senseiHost = host
		self.senseiPort = port
		self.senseiPath = path
		self.senseiClient = SenseiClient(host,port,path)
	
	def available(self):
		return True
	
	def addDoc(self,uid,doc):
		print "indexed"
		
	def getDoc(self,uid):
		print "getdoc"
		
	def getSize(self):
		return 0
	
	def search(self,req=None):
		if not req:
			req = SenseiRequest()
		self.senseiClient.doQuery(req)
		print 'found'

class SinClient:
	host = None
	port = None
	
	def __init__(self,host='localhost',port=6666):
		self.host = host
		self.port = port
	
	def newIndex(self,name):
		sindex = Sindex(name,'localhost',8080,'sensei')
		while not sindex.isStarted():
			time.sleep(0.5)
		
		print "%s added" %name
		return sindex

if __name__ == '__main__':
	client = SinClient()
	idx = client.newIndex('test')
	idx.search()
	