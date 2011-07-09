# Create your views here.
from django.http import HttpResponse
        
def newIndex(request,index_name):
	return HttpResponse("index %s created" %index_name)

def getSize(request,index_name):
	return HttpResponse("size %d" % 0)
	
def getDoc(request,id):
	return HttpResponse("uid: %d" % int(id))

def addDoc(request,id):
	return HttpResponse("uid: %d" % int(id))

def available(request,index_name):
	return HttpResponse("index %s created" %index_name)
