import json, urllib2

class Client:
  def __init__(self, endpoint):
    self.endpoint = endpoint

  def request(self, data):
    req = urllib2.Request(self.endpoint)
    req.add_header('Content-Type', 'text/json')

    res = urllib2.urlopen(req, json.dumps(data))
    doc = res.read()
    return json.loads(doc)
