import logging
import time
import zookeeper, threading, sys
from optparse import OptionParser

DEFAULT_TIMEOUT = 30000
ZOO_OPEN_ACL_UNSAFE = {"perms":0x1f, "scheme":"world", "id" :"anyone"}

class SinClusterClientError(Exception):
  """Exception raised for all errors related to SinClusterClient."""

  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class Node:
  """A node in a Sin cluster.

  A node in a Sin cluster consists of three parts:

    1. node Id
    2. host
    3. port

  Node Id is a none-negative integer uniquely assigned to each node.
  "host:port" is also called the url of this node, which should also be
  unique in a Sin cluster.

  """

  def __init__(self, node_id, host, port):
    self.node_id = node_id
    self.host = host
    self.port = port

  def __init__(self, node_id, url):
    parts = url.split(":")
    if len(parts) != 2:
      raise SinClusterClientError("Url for a node is bad: %s" % url)
    else:
      self.node_id = int(node_id)
      self.host = parts[0]
      self.port = int(parts[1])

  def __str__(self):
    return "%d:%s:%d" % (self.node_id, self.host, self.port)

  def get_id(self):
    return self.node_id

  def get_host(self):
    return self.host

  def get_port(self):
    return self.port

  def get_url(self):
    return "%s:%s" % (self.host, self.port)


class SinClusterClient:
  """Sin cluster client class."""

  def __init__(self, service_name, connect_string, timeout=DEFAULT_TIMEOUT, default_port=6664):
    self.SERVICE_NODE = "/" + service_name
    self.AVAILABILITY_NODE = self.SERVICE_NODE + "/available"
    self.MEMBERSHIP_NODE = self.SERVICE_NODE + "/members"
    self.connected = False
    self.timeout = timeout
    self.default_port = default_port
    self.conn_cv = threading.Condition()
    self.conn_cv.acquire()
    self.handle = zookeeper.init(connect_string, self.connection_watcher, timeout)
    self.conn_cv.wait(timeout / 1000)
    self.conn_cv.release()
    self.watcher_lock = threading.Lock()
    self.logger = logging.getLogger("sincc")

    if not self.connected:
      raise SinClusterClientError("Unable to connect to %s" % connect_string)

    for path in [self.SERVICE_NODE, self.AVAILABILITY_NODE, self.MEMBERSHIP_NODE]:
      if not zookeeper.exists(self.handle, path):
        zookeeper.create(self.handle, path, "", [ZOO_OPEN_ACL_UNSAFE], 0)
    self.listeners = []
    # Start to watch both /members and /available
    zookeeper.get_children(self.handle, self.MEMBERSHIP_NODE, self.watcher)
    available = zookeeper.get_children(self.handle, self.AVAILABILITY_NODE, self.watcher)
    self.available_nodes = {}
    for node_id in available:
      self.available_nodes[int(node_id)] = Node(int(node_id),
                                                zookeeper.get(self.handle, self.AVAILABILITY_NODE + "/" + node_id)[0])

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
      listener(self.available_nodes)

  def watcher(self, handle, event, state, path):
    """Watching node changes."""

    self.watcher_lock.acquire()
    self.logger.debug("Watcher called: handle=%d event=%d state=%d path=%s" %
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
    self.available_nodes.clear()
    for node_id in members:
      if node_id in available:
        self.available_nodes[int(node_id)] = Node(int(node_id),
                                                  zookeeper.get(self.handle, self.AVAILABILITY_NODE + "/" + node_id)[0])
    self.notify_all()
    
  def handle_availability_changed(self):
    available = zookeeper.get_children(self.handle, self.AVAILABILITY_NODE, self.watcher)
    self.available_nodes.clear()
    for node_id in available:
      self.available_nodes[int(node_id)] = Node(int(node_id),
                                                zookeeper.get(self.handle, self.AVAILABILITY_NODE + "/" + node_id)[0])
    self.notify_all()

  def register_node(self, node_id, host, port=0):
    """Register a node to the cluster."""

    path = self.MEMBERSHIP_NODE + "/" + str(node_id)
    if port <= 0:
      port = self.default_port
    try:
      data = host + ":" + str(port)
      zookeeper.create(self.handle, path, data, [ZOO_OPEN_ACL_UNSAFE], 0)
      self.logger.info("Node %d: %s is registered" % (node_id, data))
    except zookeeper.NodeExistsException:
      self.logger.warn("%s already exists" % path)

  def remove_node(self, node_id):
    """Remove a node from the cluster."""

    path = self.MEMBERSHIP_NODE + "/" + str(node_id)
    try:
      zookeeper.delete(self.handle, path)
      self.logger.info("Node %d is removed" % node_id)
    except zookeeper.NoNodeException:
      self.logger.warn("%s does not exist" % path)

  def get_registered_nodes(self):
    """Get all registered nodes."""

    nodes = {}
    try:
      members = zookeeper.get_children(self.handle, self.MEMBERSHIP_NODE)
      for node_id in members:
        nodes[int(node_id)] = Node(int(node_id),
                                   zookeeper.get(self.handle, self.MEMBERSHIP_NODE + "/" + node_id)[0])
    except:
      pass
    return nodes

  def mark_node_available(self, node_id, data=""):
    """Mark a node available."""

    path = self.AVAILABILITY_NODE + "/" + str(node_id)
    try:
      zookeeper.create(self.handle, path, data, [ZOO_OPEN_ACL_UNSAFE], zookeeper.EPHEMERAL)
      self.logger.info("Node %d: %s is now available" % (node_id, data))
    except zookeeper.NodeExistsException:
      self.logger.warn("%s already exists" % path)

  def mark_node_unavailable(self, node_id):
    """Mark a node unavailable."""

    path = self.AVAILABILITY_NODE + "/" + str(node_id)
    try:
      data = zookeeper.get(self.handle, path)[0]
      zookeeper.delete(self.handle, path)
      self.logger.info("Node %d: %s is now unavailable" % (node_id, data))
    except zookeeper.NoNodeException:
      self.logger.warn("Tried to mark node %s unavailable, but it did not exist" % path)

  def reset(self):
    """Reset both MEMBERSHIP_NODE and AVAILABILITY_NODE to empty nodes."""

    nodes = zookeeper.get_children(self.handle, self.MEMBERSHIP_NODE)
    for node_id in nodes:
      path = self.MEMBERSHIP_NODE + "/" + node_id
      try:
        zookeeper.delete(self.handle, path)
        self.logger.info("Node %s is removed (because of reset)" % node_id)
      except zookeeper.NoNodeException:
        self.logger.warn("%s does not exist" % path)

  def shutdown(self):
    """Shut down the cluster client."""

    self.logger.info("Shutting down zookeeper session: %d" % self.handle)
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

  cc = SinClusterClient("sin", options.servers, options.timeout)
  cc.add_listener(SinClusterListener())

  cc.logger.setLevel(logging.DEBUG)
  formatter = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d - %(message)s")
  stream_handler = logging.StreamHandler()
  stream_handler.setFormatter(formatter)
  cc.logger.addHandler(stream_handler)

  if (options.test_node >= 0):
    cc.register_node(options.test_node)
    cc.mark_node_available(options.test_node)
    time.sleep(10)
    sys.exit()

  # Watcher may not be called if there is no delay
  cc.register_node(0); time.sleep(1)
  cc.register_node(1); time.sleep(1)
  cc.register_node(2); time.sleep(1)

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
