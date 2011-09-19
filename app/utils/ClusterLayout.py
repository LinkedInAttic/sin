#!/usr/bin/env python

from xml.sax.saxutils import escape
import os, io

DEFAULT_LABEL_SIZE = 10

NODE_WIDTH  = 80
NODE_HEIGHT = 80
NODE_DISTANCE_X = NODE_WIDTH + 20
NODE_DISTANCE_Y = NODE_HEIGHT + 40

class ClusterLayout:
  """A class to draw the layout of a Sin store in SVG format.

  This is a collections of shapes (rectangles and labels) that represent
  a cluster layout for a Sin store.  It can be used by a SvgPlotter to
  convert the cluster layout to SVG format.

  """

  def __init__(self, width=640, height=400,
               online_color='lightblue', offline_color='red',
               node_id_color='black', node_comment_color='black',
               max_host_len=15):
    self.shapes = []
    self.width = width
    self.height = height
    self.online_color = online_color
    self.offline_color = offline_color
    self.node_id_color = node_id_color
    self.node_comment_color = node_comment_color
    self.max_host_len = max_host_len

  def addShape(self, shape):
    self.shapes.append(shape)

  def addNode(self, x, y, node_id, online, host, parts):
    """Add a Sensei node in the layout."""

    node_color = self.online_color
    if not online:
      node_color = self.offline_color

    # Node box
    self.addShape(Rectangle(x, y, x + NODE_WIDTH, y + NODE_HEIGHT,
                            color='black',
                            fillcolor=node_color))
    if not online:
      self.addShape(Line(x + 3, y + 3, x + NODE_WIDTH - 3, y + NODE_HEIGHT - 3,
                         color='black'))
      self.addShape(Line(x + 3, y + NODE_HEIGHT - 3, x + NODE_WIDTH - 3, y + 3,
                         color='black'))

    # Node Id
    self.addShape(Label(x + NODE_WIDTH / 2, y + NODE_HEIGHT / 2,
                        'Node %d' % node_id,
                        font_size=DEFAULT_LABEL_SIZE + 2,
                        bold=True,
                        color=self.node_id_color,
                        alignment_baseline='middle',
                        alignment='middle'))
    new_y = y + NODE_HEIGHT + 15

    # Host name
    self.addShape(Label(x + NODE_WIDTH / 2, new_y,
                        shortened_host(host, self.max_host_len),
                        color=self.node_comment_color,
                        alignment='middle'))
    new_y += DEFAULT_LABEL_SIZE + 2

    # Partitions
    self.addShape(Label(x + NODE_WIDTH / 2, new_y,
                        'Parts: %s' % parts,
                        color=self.node_comment_color,
                        alignment='middle'))

  def setSize(self, width, height):
    self.width = width
    self.height = height


def shortened_host(host, max_len):
  """Return a shortened host name."""

  if len(host) <= max_len:
    return host
  tmp = host[:max_len + 1]      # Keep one more in case the next char is '.'
  if '.' not in tmp:
    return tmp[:max_len]
  for i in range(max_len, 0, -1):
    if tmp[i] == '.':
      break
  return tmp[:i]


class Line:
  """A line shape."""
  
  def __init__(self, x1, y1, x2, y2,
               color="black", line_width=1):
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    self.color = color
    self.line_width = line_width


class Rectangle:
  """A rectangle shape."""

  def __init__(self, x1, y1, x2, y2,
               color='black',
               fillcolor='lightblue',
               round=5):
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    self.color = color
    self.fillcolor = fillcolor
    self.round = round

class Label:
  """A label shape."""

  def __init__(self, x, y, text,
               font_size=DEFAULT_LABEL_SIZE,
               bold=False,
               color='black',
               alignment_baseline='auto',
               alignment='start'):
    self.x = x
    self.y = y
    self.text = text
    self.font_size = font_size
    self.bold = bold
    self.color = color
    self.alignment_baseline = alignment_baseline
    self.alignment = alignment

class SvgPlotter:
  """SVG Plotter.

  This plotter takes a Sin cluster layout, visits all of its shapes, and
  generates the SVG content.

  """

  def __init__(self, stream, scale=1, line_width=1, unit='',
               foreground=(0,0,0), background=(255,255,255), fillcolor=(0,0,0)):
    self.stream = stream
    self.scale = scale
    self.unit = unit
    self.line_width = line_width
    self.foreground = foreground
    self.background = background
    self.fillcolor = fillcolor
    self.indent = ''

  def _num(self, number):
    return '%d%s' % (number*self.scale, self.unit)

  def _numDistance(self, x2, x1):
    # The following is needed just to make sure that rectangle
    # corners are aligned with lines correctly.
    x2 = int(x2 * self.scale)
    x1 = int(x1 * self.scale)
    return '%d%s' % (x2 - x1, self.unit)

  def _unit(self, number):
    return '%d%s' % (number, self.unit)

  def _color(self, color):
    r,g,b = color
    return '#%02x%02x%02x' % (r,g,b)
    
  def visitImage(self, layout, xmlHeader=True):
    self.layout = layout
    self.width = layout.width
    self.height = layout.height
    if xmlHeader:
      self.stream.write(u"""\
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<svg width="%s" height="%s" version="1.1"
  xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink">

""" % (self._num(self.width),
       self._num(self.height)))
    else:
      self.stream.write(u"""<svg width="%s" height="%s" version="1.1" xmlns="http://www.w3.org/2000/svg">\n""" % (
          self._num(self.width),
          self._num(self.height)
          ))
    self.visitShapes(layout.shapes)
    self.stream.write(u'</svg>\n')
    self.stream.flush()
  
  def visitShapes(self, shapes):
    for shape in shapes:
      shapeName = shape.__class__.__name__
      visitorName = 'visit%s' % shapeName
      if hasattr(self, visitorName):
        getattr(self, visitorName)(shape)
      else:
        print "Error: don't know how to plot shape %r" % shape

  def _rectangle(self, x1, y1, x2, y2, round, color, style='', fillcolor='white'):
    """Draw a rectangle shape."""

    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1

    self.stream.write(u"""\
%s<rect x="%s" y="%s" rx="%d" ry="%d" width="%s" height="%s" style="stroke:%s; fill:%s; stroke-width:%s; %s" />
""" % (self.indent,
       self._num(x1), self._num(y1),
       round, round,
       self._numDistance(x2, x1), self._numDistance(y2, y1),
       color,
       fillcolor,
       self._unit(self.line_width),
       style
       ))

  def visitLine(self, line):
    """Handle a line."""

    self.stream.write(u"""%s<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke:%s;stroke-width:%s"/>
"""
                      % (self.indent,
                         self._num(line.x1), self._num(line.y1),
                         self._num(line.x2), self._num(line.y2),
                         line.color,
                         line.line_width))

  def visitRectangle(self, rectangle):
    """Handle a rectangle."""

    self._rectangle(rectangle.x1, rectangle.y1,
                    rectangle.x2, rectangle.y2,
                    rectangle.round,
                    rectangle.color,
                    fillcolor=rectangle.fillcolor)

  def visitLabel(self, label):
    """Handle a label."""

    self.stream.write(u"""\
%s<text x="%s" y="%s" font-family="Arial,sans-serif" font-size="%s" %s %s %s style="fill:%s" >
%s
%s</text>
""" % (self.indent,
       self._num(label.x), self._num(label.y),
       self._num(label.font_size),
       (label.bold and 'font-weight="bold"' or ''),
       (label.alignment_baseline == 'auto' and '' or
        'alignment-baseline="%s"' % label.alignment_baseline),
       (label.alignment == 'start' and '' or
        'text-anchor="%s"' % label.alignment),
       label.color,
       escape(label.text.encode('utf8')),
       self.indent
       ))


if __name__ == "__main__":

  print shortened_host('aaa.bbb.ccc', 11)
  print shortened_host('aaa.bbb.ccc', 10)
  print shortened_host('aaa.bbb.ccc', 7)
  print shortened_host('aaa.bbb.ccc', 5)
  print shortened_host('aaa.bbb.ccc', 3)
  print shortened_host('aaa.bbb.ccc', 2)

  layout = ClusterLayout()
  
  xOffset = 80
  yOffset = 10
  legend = 40
  replicas = 3
  numNodesPerReplica = 5
  numPartsPerNode = 2

  for i in range(replicas):
    y1 = yOffset + i * NODE_DISTANCE_Y
    layout.addShape(Label(10, y1 + NODE_HEIGHT / 2, "Replica " + str(i+1),
                          font_size=12, bold=True, color="darkblue", alignment_baseline="middle"))
    for j in range(numNodesPerReplica):
      x1 = xOffset + j * NODE_DISTANCE_X
      layout.addNode(x1, y1,
                     node_id=i * numNodesPerReplica + j + 1,
                     online=True,
                     host='host' + str(i * numNodesPerReplica + j + 1),
                     parts='%s-%s' % (j * numPartsPerNode, (j+1) * numPartsPerNode - 1))

  layout.setSize(xOffset + numNodesPerReplica * NODE_DISTANCE_X,
                 yOffset + replicas * NODE_DISTANCE_Y)

  layout.addShape(Rectangle(1, 1,
                            xOffset + numNodesPerReplica * NODE_DISTANCE_X - 1,
                            yOffset + replicas * NODE_DISTANCE_Y - 1,
                            fillcolor='none'))

  plotter = SvgPlotter(io.StringIO())
  plotter.visitImage(layout, False)
  svg = plotter.stream.getvalue()

  plotter = SvgPlotter(file('/tmp/test.svg', 'w+'))
  plotter.visitImage(layout)
  
  print 'Done.'
