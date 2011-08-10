import time, base64, hashlib, random

def totimestamp(dt):
  return time.mktime(dt.timetuple()) + dt.microsecond/1e6

def generate_api_key():
  return base64.b64encode(hashlib.sha256( str(random.getrandbits(256)) ).digest(),
    random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')

