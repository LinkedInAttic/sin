# Create your views here.
from django.http import HttpResponse
from utils import json

def newIndex(request,index_name):
	resp = {'store':index_name,'sensei-host':'localhost','sensei-port':8080,'sensei-path':'sensei'}
	return HttpResponse(json.json_encode(resp))

def getSize(request,index_name):
	resp = {'store':index_name,"size":0}
	return HttpResponse(json.json_encode(resp))
	
def getDoc(request,index_name,id):
	uid = long(id)
	doc = {'id':uid}
	resp = {'store':index_name,'doc':doc}
	return HttpResponse(json.json_encode(resp))

def addDoc(request,index_name,id):
	uid = long(id)
	doc = {'id':uid}
	resp = {'store':index_name,'doc':doc}
	return HttpResponse(json.json_encode(resp))

def available(request,index_name):
	resp = {'store':index_name,"available":True}
	return HttpResponse(json.json_encode(resp))
