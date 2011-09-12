import logging
import time
import zookeeper, threading, sys
from optparse import OptionParser

DEFAULT_TIMEOUT = 30000
ZOO_OPEN_ACL_UNSAFE = {"perms":0x1f, "scheme":"world", "id" :"anyone"}

logger = logging.getLogger()

class SinClusterClientError(Exception):

  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class SinClusterClient(object):

  def __init__(self, service_name, connect_string, timeout = DEFAULT_TIMEOUT):
    self.SERVICE_NODE = "/" + service_name
    self.AVAILABILITY_NODE = self.SERVICE_NODE + "/available"
    self.MEMBERSHIP_NODE = self.SERVICE_NODE + "/members"
    self.connected = False
    self.timeout = timeout
    self.conn_cv = threading.Condition()
    self.conn_cv.acquire()
    self.handle = zookeeper.init(connect_string, self.connection_watcher, timeout)
    self.conn_cv.wait(timeout / 1000)
    self.conn_cv.release()
    self.watcher_lock = threading.Lock()

    if not self.connected:
      raise SinClusterClientError("Unable to connect to %s" % connect_string)

    for path in [self.SERVICE_NODE, self.AVAILABILITY_NODE, self.MEMBERSHIP_NODE]:
      if (not zookeeper.exists(self.handle, path)):
        zookeeper.create(self.handle, path, "", [ZOO_OPEN_ACL_UNSAFE], 0)
    self.listeners = []
    # Start to watch both /members and /available
    zookeeper.get_children(self.handle, self.MEMBERSHIP_NODE, self.watcher)
    available = zookeeper.get_children(self.handle, self.AVAILABILITY_NODE, self.watcher)
    self.current_nodes = {}
    for node_id in available:
      self.current_nodes[int(node_id)] = zookeeper.get(self.handle, self.AVAILABILITY_NODE + "/" + node_id)[0]

  def connection_watcher(self, handle, event, state, path):
    self.handle = handle
    self.conn_cv.acquire()
    self.connected = True
    self.conn_cv.notifyAll()
    self.conn_cv.release()

  def add_listener(self, callback):
    self.listeners.append(callback)

  def notify_all(self):
    for listener in self.listeners:
      listener(self.current_nodes)

  def watcher(self, handle, event, state, path):
    """Watching node changes."""

    self.watcher_lock.acquire()
    logger.debug("Watcher called: handle=%d event=%d state=%d path=%s" %
                 (handle, event, state, path))

    if event == zookeeper.CHILD_EVENT:
      if path == self.AVAILABILITY_NODE:
        self.handle_availability_changed()
      elif path == self.MEMBERSHIP_NODE:
        self.handle_membership_changed()
    self.watcher_lock.release()


  def handle_membership_changed(self):
    members = zookeeper.get_children(self.handle, self.MEMBERSHIP_NODE, self.watcher)
    # No need to watch /available here.
    available = zookeeper.get_children(self.handle, self.AVAILABILITY_NODE)
    self.current_nodes.clear()
    for member in members:
      if member in available:
        self.current_nodes[int(member)] = zookeeper.get(self.handle, self.AVAILABILITY_NODE + "/" + member)[0]
    self.notify_all()
    
  def handle_availability_changed(self):
    available = zookeeper.get_children(self.handle, self.AVAILABILITY_NODE, self.watcher)
    self.current_nodes.clear()
    for node_id in available:
      self.current_nodes[int(node_id)] = zookeeper.get(self.handle, self.AVAILABILITY_NODE + "/" + node_id)[0]
    self.notify_all()

  def add_node(self, node_id, data=""):
    """Add a node to the clusters."""

    path = self.MEMBERSHIP_NODE + "/" + str(node_id)
    try:
      zookeeper.create(self.handle, path, data, [ZOO_OPEN_ACL_UNSAFE], 0)
    except zookeeper.NodeExistsException:
      logger.warn("%s already exists" % path)

  def remove_node(self, node_id):
    """Remove a node from the cluster."""

    path = self.MEMBERSHIP_NODE + "/" + str(node_id)
    try:
      zookeeper.delete(self.handle, path)
    except zookeeper.NoNodeException:
      logger.warn("%s does not exist" % path)

  def mark_node_available(self, node_id, data=""):
    """Mark a node available."""

    path = self.AVAILABILITY_NODE + "/" + str(node_id)
    try:
      zookeeper.create(self.handle, path, data, [ZOO_OPEN_ACL_UNSAFE], zookeeper.EPHEMERAL)
    except zookeeper.NodeExistsException:
      logger.warn("%s already exists" % path)

  def mark_node_unavailable(self, node_id):
    """Mark a node unavailable."""

    path = self.AVAILABILITY_NODE + "/" + str(node_id)
    try:
      zookeeper.delete(self.handle, path)
    except zookeeper.NoNodeException:
      logger.warn("%s does not exist" % path)

  def shutdown(self):
    """Shut down the cluster client."""

    logger.info("Shutting down zookeeper session: %d" % self.handle)
    zookeeper.close(self.handle)


if __name__ == '__main__':
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("", "--connect-string", dest="servers",
                    default="localhost:2181", help="comma separated list of host:port (default localhost:2181)")
  parser.add_option("", "--timeout", dest="timeout", type="int",
                    default=5000, help="session timeout in milliseconds (default 5000)")
  parser.add_option("-t", "--test", dest="test_node",type="int",
                    default=-1, help="testing node number (default -1)")
  (options, args) = parser.parse_args()
  
  zookeeper.set_log_stream(open("/dev/null"))

  logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d - %(message)s")
  stream_handler = logging.StreamHandler()
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)

  cc = SinClusterClient("sin", options.servers, options.timeout)
  cc.add_listener(SinClusterListener())

  if (options.test_node >= 0):
    cc.add_node(options.test_node)
    cc.mark_node_available(options.test_node)
    time.sleep(10)
    sys.exit()

  # Watcher may not be called if there is no delay
  cc.add_node(0); time.sleep(1)
  cc.add_node(1); time.sleep(1)
  cc.add_node(2); time.sleep(1)

  cc.mark_node_available(0); time.sleep(1)
  cc.mark_node_available(1); time.sleep(1)
  cc.mark_node_available(2); time.sleep(1)

  cc.mark_node_unavailable(0); time.sleep(1)
  cc.mark_node_unavailable(1); time.sleep(1)
  cc.mark_node_unavailable(2); time.sleep(1)
  cc.mark_node_unavailable(3); time.sleep(1)
  cc.mark_node_unavailable(4); time.sleep(1)

  cc.remove_node(0); time.sleep(1)
  cc.remove_node(1); time.sleep(1)
  cc.remove_node(2); time.sleep(1)

  cc.shutdown()

  time.sleep(10000)
