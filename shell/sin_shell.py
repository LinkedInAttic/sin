#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Sin Shell
"""
import sys
import datetime
import logging

from sin.sin_client import SinClient

logger = logging.getLogger("sin_client")


def main(argv):
  print "Welcome to Sin Shell"
  from optparse import OptionParser
  usage = "usage: %prog [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("-w", "--column-width", dest="max_col_width",default=100, help="Set the max column width")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose",default=False, help="Turn on verbose mode")
  (options, args) = parser.parse_args()
  
  if options.verbose:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  formatter = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d - %(message)s")
  stream_handler = logging.StreamHandler()
  stream_handler.setFormatter(formatter)
  logger.addHandler(stream_handler)

  host = 'localhost'  
  port = 8666
  if len(args) > 1:
    host = args[0]
    port = int(args[1])
    logger.debug("Url specified, host: %s, port: %d" % (host,port))
    print "Url specified, host: %s, port: %d" % (host,port)
    #client = SenseiClient(host, port, 'sensei')

    
  print "using host=%s, port=%d" %(host,port)
  import readline
  readline.parse_and_bind("tab: complete")
  
  sinClient = SinClient(host,port)
  
  while 1:
    try:
      stmt = raw_input('> ')
      if stmt == "exit":
        break
      else:
        pass
    except EOFError:
      break
    
  
if __name__ == "__main__":
  main(sys.argv)
