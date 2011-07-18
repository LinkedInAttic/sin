from django import template
from django.shortcuts import render_to_response

from django import forms
from sinClient.senseiClient import *
from sinClient.sinClient import *


storeName = 'tweets'
sinClient = SinClient('localhost',8000)
store = sinClient.openStore(storeName)
searcher = store.getSenseiClient()

req = SenseiRequest()
req.fetch = True
req.count = 10
facetSpec = SenseiFacet()
facetSpec.expand = True
facetSpec.maxCounts = 5

sort = SenseiSort('time',True)
req.sorts = [sort]
req.facets={'authorname':facetSpec}

def search(request):
  q = request.POST.get('query')
  if not q or len(q)==0:
    req.query = None
  else:
    req.query = "text:%s" %q
  result = searcher.doQuery(req)
  return render_to_response('search.html',{
    "result": result,
    },context_instance=template.RequestContext(request))

  