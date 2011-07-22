import time

def totimestamp(dt):
  return time.mktime(dt.timetuple()) + dt.microsecond/1e6
