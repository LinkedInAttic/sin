#!/usr/bin/env python

"""Python client library for Sin
"""

class Sindex:
	host = None
	port = None
	name = None
	def __init__(self,name,host='localhost',port=6666):
		self.name = name
		self.host = host
		self.port = port
	
	def isStarted(self):
		return True
	
	def addDoc(self,doc):
		print "indexed"
		
	def getSize(self):
		print "0"
	
	def search(self,q):
		print 'found'

class SinClient:
	host = None
	port = None
	
	def __init__(self,host='localhost',port=6666):
		self.host = host
		self.port = port
	
	def newIndex(self,name):
		sindex = Sindex(name,self.host,self.port)
		while not sindex.isStarted():
			time.sleep(0.5)
		
		print "%s added" %name
		return sindex
	
	
	
