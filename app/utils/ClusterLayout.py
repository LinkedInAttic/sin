#!/usr/bin/env python

from xml.sax.saxutils import escape
import os, io

DEFAULT_LABEL_SIZE = 11

NODE_WIDTH  = 60
NODE_HEIGHT = 60
NODE_DISTANCE_X = NODE_WIDTH + 20
NODE_DISTANCE_Y = NODE_HEIGHT + 40
NODE_LABEL_INDENT = 10

class ClusterLayout:
  """
  This is a collections of shapes (rectangles and labels) that represent
  a cluster layout for a Sin store.  It can be used by a SvgPlotter to
  convert the cluster layout to SVG format.
  """
  def __init__(self, width=640, height=400):
    self.shapes = []
    self.width = width
    self.height = height

  def addShape(self, shape):
    self.shapes.append(shape)

  def setSize(self, width, height):
    self.width = width
    self.height = height

class Rectangle:
  def __init__(self, x1, y1, x2, y2, fillcolor="lightblue", round=5):
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2
    self.fillcolor = fillcolor
    self.round = round

class Label:
  def __init__(self, x, y, text, fontSize=DEFAULT_LABEL_SIZE, bold=False, color="black", alignment="start"):
    self.x = x
    self.y = y
    self.text = text
    self.fontSize = fontSize
    self.bold = bold
    self.color = color
    self.alignment = alignment

class SvgPlotter:
  def __init__(self, stream, scale = 1, lineWidth=1, unit='',
               foreground=(0,0,0), background=(255,255,255), fillcolor=(0,0,0)
               ):
    self.stream = stream
    self.scale = scale
    self.unit = unit
    self.lineWidth = lineWidth
    self.foreground = foreground
    self.background = background
    self.fillcolor = fillcolor
    self.indent = ''

  def _num(self, number):
    return "%d%s" % (number*self.scale, self.unit)

  def _numDistance(self, x2, x1):
    # The following is needed just to make sure that rectangle
    # corners are aligned with lines correctly.
    x2 = int(x2 * self.scale)
    x1 = int(x1 * self.scale)
    return "%d%s" % (x2 - x1, self.unit)

  def _unit(self, number):
    return "%d%s" % (number, self.unit)

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
    self.stream.write(u"</svg>\n")
    self.stream.flush()
  
  def visitShapes(self, shapes):
    for shape in shapes:
      shapeName = shape.__class__.__name__
      visitorName = 'visit%s' % shapeName
      if hasattr(self, visitorName):
        getattr(self, visitorName)(shape)
      else:
        print "Error: don't know how to plot shape %r" % shape

  def _rectangle(self, x1, y1, x2, y2, round, style='', fillcolor="white"):
    """
    Draw a rectangle shape.
    """
    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1

    self.stream.write(u"""\
%s<rect x="%s" y="%s" rx="%d" ry="%d" width="%s" height="%s" style="stroke:%s; fill:%s; stroke-width:%s; %s" />
""" % (self.indent,
       self._num(x1), self._num(y1),
       round, round,
       self._numDistance(x2, x1), self._numDistance(y2, y1),
       self._color(self.fillcolor),
       fillcolor,
       self._unit(self.lineWidth),
       style
       ))

  def visitLabel(self, label):
    """
    Handle a label.
    """
    self.stream.write(u"""\
%s<text x="%s" y="%s" font-family="Arial,sans-serif" font-size="%s" %s text-anchor="%s" style="fill:%s" >
%s
%s</text>
""" % (self.indent,
       self._num(label.x), self._num(label.y-0.3),
       self._num(label.fontSize),
       (label.bold and 'font-weight="bold"' or ''),
       label.alignment,
       label.color,
       escape(label.text.encode('utf8')),
       self.indent
       ))

  def visitRectangle(self, rectangle):
    """
    Handle a rectangle.
    """
    self._rectangle(rectangle.x1, rectangle.y1,
                    rectangle.x2, rectangle.y2,
                    rectangle.round,
                    fillcolor=rectangle.fillcolor)

if __name__ == "__main__":

  layout = ClusterLayout()
  
  xOffset = 80
  yOffset = 10
  legend = 40
  replicas = 3
  numNodesPerReplica = 5
  numPartsPerNode = 2

  for i in range(replicas):
    y1 = yOffset + i * NODE_DISTANCE_Y
    layout.addShape(Label(10, y1 + NODE_HEIGHT/2 + 2, "Replica " + str(i+1), fontSize=12, bold=True, color="darkblue"))
    for j in range(numNodesPerReplica):
      x1 = xOffset + j * NODE_DISTANCE_X
      layout.addShape(Rectangle(x1, y1, x1 + NODE_WIDTH, y1 + NODE_HEIGHT))
      layout.addShape(Label(x1 + NODE_WIDTH/2, y1 + NODE_HEIGHT + 15,
                            "Node %s" % str(i * numNodesPerReplica + j + 1),
                            bold=True,
                            alignment="middle"))
      layout.addShape(Label(x1 + NODE_WIDTH/2, y1 + NODE_HEIGHT + 15 + DEFAULT_LABEL_SIZE + 1,
                            "Parts: %s-%s" % (j * numPartsPerNode, (j+1) * numPartsPerNode - 1),
                            alignment="middle"))

  layout.setSize(xOffset + numNodesPerReplica * NODE_DISTANCE_X,
                 yOffset + replicas * NODE_DISTANCE_Y)

  plotter = SvgPlotter(io.StringIO())
  plotter.visitImage(layout, False)
  svg = plotter.stream.getvalue()

  plotter = SvgPlotter(file("/tmp/test.svg", "w+"))
  plotter.visitImage(layout)
  
  print "Done."
