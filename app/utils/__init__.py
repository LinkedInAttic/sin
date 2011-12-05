import commands, base64, hashlib, kafka, random, re, socket, time

from django.conf import settings

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

def is_current_host(host, me=None):
  if not me:
    me = socket.gethostbyaddr(socket.gethostname())[0]

  hosts_a = set(socket.gethostbyname_ex(host)[2])
  hosts_b = set(socket.gethostbyname_ex(me)[2])
  if not [h for h in hosts_b if not h.startswith('127.')]:
    hosts_b.update([h for h in [c.split()[1][5:] for c in commands.getoutput("ifconfig").split("\n") if re.match(r'\s*inet.*', c)] if h])
  if hosts_a.intersection(hosts_b):
    return True
  else:
    return False

kafka_producer = None
def kafka_send(*args, **kwargs):
  global kafka_producer
  if kafka_producer is None:
    kafka_producer = kafka.KafkaProducer(settings.KAFKA_HOST, int(settings.KAFKA_PORT))

  kafka_producer.send(*args, **kwargs)

