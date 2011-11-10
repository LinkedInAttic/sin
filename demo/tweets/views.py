from django import template
from django.shortcuts import render_to_response
from django.conf import settings
from django import forms
from sinClient.senseiClient import *
from sinClient.sinClient import *


from django.http import HttpResponseServerError
from django.http import HttpResponse
import logging
import json

sinClient = SinClient(settings.SIN_HOST,settings.SIN_PORT)
store = sinClient.openStore(settings.SIN_STORE, settings.SIN_API_KEY)
searcher = store.getSenseiClient()

req = SenseiRequest()
req.fetch_stored = True
req.count = 10
facetSpec = SenseiFacet()
facetSpec.expand = True
facetSpec.maxCounts = 5

sort = SenseiSort('time',True)
req.sorts = [sort]
req.facets={'authorname':facetSpec}

sel = SenseiSelection('authorname')
req.selections['authorname'] = sel

def search(request):
  q = request.GET.get('query')
  
  if not q or len(q)==0:
    req.query = None
  else:
    req.query = "text:%s" %q
  authorname = request.GET.get('authorname')
  authorSelected = request.GET.get('selected')
  
  if authorSelected=="true":
    if not authorname in sel.values:
      sel.values.append(authorname)
  else:
    if authorname in sel.values:
      sel.values.remove(authorname)
  
  try:
    res = searcher.doQuery(req);
    hits = []
    facetList = []
    if res.hits:
      for senseiHit in res.hits:
        hits.append(senseiHit['srcdata'])
    if res.facetMap:
      authorFacetList = res.facetMap.get('authorname')
      if authorFacetList:
        for authorFacet in authorFacetList:
          obj = {'value':authorFacet.value,'count':authorFacet.count,'selected':authorFacet.selected}
          facetList.append(obj)
    resp = {'ok':True,'numHits':res.numHits,'totalDocs':res.totalDocs,'hits':hits,'authornamefacet':facetList}
    return HttpResponse(json.dumps(resp))
  except Exception as e:
    logging.exception(e)
    resp = {'ok':False,'error':e.message}
    return HttpResponseServerError(json.dumps(resp))
