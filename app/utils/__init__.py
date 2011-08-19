import time, base64, hashlib, random, socket

def totimestamp(dt):
  return time.mktime(dt.timetuple()) + dt.microsecond/1e6

def generate_api_key():
  return base64.b64encode(hashlib.sha256( str(random.getrandbits(256)) ).digest(),
    random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')

def get_local_pub_ip():
  """Get local public ip address.

  By creating a udp socket and assigning a DUMMY public ip address and a
  DUMMY port, and getting the local sock name.
  """
  skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    skt.connect(('74.125.224.0', 80))
    return skt.getsockname()[0]
  finally:
    skt.close()

