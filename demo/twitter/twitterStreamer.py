import json
import urllib
import urllib2

import time
from dateutil.parser import *

from sinClient.sinClient import *

sinHost = "localhost"
sinPort = 8666
sinStore = "tweets"
sinApiKey = "O87D1PRQv65wSsjSVJgqovq5hbVpSeRThXUJUIzAMg0"
queryString = "apple"
batchsize = 100
baseurl = 'http://search.twitter.com/search.json'

def searchTwitter(opener,queryString,since_id):
  params = {'q':queryString,'result_type':'recent','rpp':batchsize}
  if since_id:
    params['since_id']=since_id
  urlReq = urllib2.Request(baseurl,urllib.urlencode(params))
  res = opener.open(urlReq)
  return dict(json.loads(res.read()))
  
def extract(tweetHit):
  indexable = {}
  indexable['id'] = long(tweetHit['id_str'])
  indexable['authorid'] = long(tweetHit['from_user_id'])
  indexable['authorname'] = tweetHit['from_user']
  indexable['profileimg'] = tweetHit.get('profile_image_url')
  indexable['text'] = tweetHit.get('text')
  timeString = tweetHit['created_at']
  indexable['createdtime'] = timeString
  if timeString:
    try:
      dt = parse(timeString)
      ts = long(time.mktime(dt.timetuple()))
      indexable['time'] = ts
    except Exception as e:
      print e
  return indexable
  
if __name__ == '__main__':

  sinClient = SinClient(sinHost,sinPort)
  tweetStore = sinClient.openStore(sinStore, sinApiKey)
  since_id = None
  opener = urllib2.build_opener()
  opener.addheaders = [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30')]
  
  while True:
    print "fetching more data from twitter..."
    jsonObj = searchTwitter(opener,queryString,since_id)
  
    since_id = jsonObj["max_id"]
    results = jsonObj["results"]
    for result in results:
      indexable = extract(result)
      print indexable
      print tweetStore.addDoc(indexable)
    time.sleep(4)

  
