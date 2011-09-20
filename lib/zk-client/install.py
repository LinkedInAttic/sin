#! /usr/bin/env python

import platform
import os

#
# This script installs the ZooKeeper Python client extension module and
# required dynamic libraries to a machine.
#
# To run, just type in:
#
#   $ cd sin/lib/zk-client/
#   $ sudo install.py
#

ZOOKEEPER_LIB_ROOT = os.path.normpath(os.path.join(os.path.normpath(__file__), '..'))

v1, v2, _ = platform.python_version_tuple()
python_ver = "%s.%s" % (v1, v2)
system = platform.system()
arch = platform.architecture()[0][:2]
site_pkg_path = None
src_lib_dir = None

if system == "Darwin":
  site_pkg_path = "/Library/Python/%s/site-packages/" % python_ver
  src_lib_dir = ZOOKEEPER_LIB_ROOT + "/mac-os"
  os.system("cp -f %s/ZooKeeper-0.4-py2.6.egg-info %s" % (src_lib_dir, site_pkg_path))
elif system == "Linux":
  site_pkg_path = "/usr/lib%s/python%s/site-packages/" % (arch, python_ver)
  if arch == 64:
    src_lib_dir = ZOOKEEPER_LIB_ROOT + "/linux-x86_64-2.6"
  else:
    src_lib_dir = ZOOKEEPER_LIB_ROOT + "/linux-i686-2.6"
else:
  print "%s is not supported yet!" % system
  sys.exit()

os.system("mkdir -p /usr/local/lib")
os.system("cp -fR %s/libzookeeper_* /usr/local/lib" % src_lib_dir)
os.system("cp -f %s/zookeeper.so %s" % (src_lib_dir, site_pkg_path))
