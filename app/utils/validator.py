import types
from types import *
from decimal import *
from django.utils import simplejson as json

class DocValidator(object):
  columns = {}
  uid_column = "uid"

  def __init__(self, schema):
    if isinstance(schema, basestring):
      schema = json.loads(schema)
    for col in schema["table"]["columns"]:
      self.columns[col["name"]] = col

    if "uid" in schema["table"]:
      self.uid_column = schema["table"]["uid"]

  def validate(self, doc):
    """
    Validate if a document (in JSON format) is compliant with the
    schema requirement.  Return the first error if some error is detected.
    """
    if self.uid_column not in doc:
      return (False, "Required column %s is missing" % self.uid_column)

    for (key, value) in doc.iteritems():
      if key == self.uid_column:
        defined_type = "long"
      else:
        if key not in self.columns:
          return (False, "Column %s is not declared in schema" % key)
        defined_type = self.columns[key]["type"]
  
      actual_type = type(value)

      if defined_type == "string" and actual_type is not StringType:
        return (False, "Column %s is not a string type" % key)
      elif defined_type == "int" and actual_type is not IntType:
        return (False, "Column %s is not an int type" % key)
      elif defined_type == "long" and actual_type is not LongType and actual_type is not IntType:
        return (False, "Column %s is not a long type" % key)
      elif defined_type == "short" and actual_type is not IntType:
        return (False, "Column %s is not a short type" % key)
      elif defined_type == "float" and actual_type is not FloatType:
        return (False, "Column %s is not a float type" % key)
      elif defined_type == "double" and actual_type is not FloatType:
        return (False, "Column %s is not a double type" % key)
      elif defined_type == "text" and actual_type is not StringType:
        return (False, "Column %s is not a text type" % key)
  
    return (True, None)

if __name__ == "__main__":

  # "true" is not defined here
  # print json.dumps({"table": {"uid": "id", "src-data-field": "src_data", "src-data-store": "lucene", "delete-field": "isDeleted", "compress-src-data": true, "columns": [{"index": "", "multi": "false", "from": "", "name": "authorname", "termvector": "", "delimiter": "", "parentModel": {}, "type": "string", "store": ""}, {"index": "", "multi": "false", "from": "", "name": "time", "termvector": "", "delimiter": "", "parentModel": {}, "type": "long", "store": ""}, {"index": "ANALYZED", "multi": "false", "from": "", "name": "text", "termvector": "NO", "delimiter": "", "parentModel": {}, "type": "text", "store": "NO"}]}, "facets": [{"name": "authorname", "dynamic": "false", "depends": "", "parentModel": {}, "params": [], "type": "simple"}, {"name": "time", "dynamic": "false", "depends": "", "parentModel": {}, "params": [], "type": "simple"}]},
  #                  indent=2)

  # print json.dumps(json.loads(schema), indent=2)

  schema = """
{
  "table": {
    "uid": "id", 
    "src-data-field": "src_data", 
    "src-data-store": "lucene", 
    "delete-field": "isDeleted", 
    "compress-src-data": true, 
    "columns": [
      {
        "index": "", 
        "multi": "false", 
        "from": "", 
        "name": "authorname", 
        "termvector": "", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "string", 
        "store": ""
      }, 
      {
        "index": "", 
        "multi": "false", 
        "from": "", 
        "name": "time", 
        "termvector": "", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "long", 
        "store": ""
      }, 
      {
        "index": "ANALYZED", 
        "multi": "false", 
        "from": "", 
        "name": "text", 
        "termvector": "NO", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "text", 
        "store": "NO"
      },
      {
        "index": "ANALYZED", 
        "multi": "false", 
        "from": "", 
        "name": "price", 
        "termvector": "NO", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "float", 
        "store": "NO"
      },
      {
        "index": "ANALYZED", 
        "multi": "false", 
        "from": "", 
        "name": "age", 
        "termvector": "NO", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "int", 
        "store": "NO"
      }
    ]
  }, 
  "facets": [
    {
      "name": "authorname", 
      "dynamic": "false", 
      "depends": "", 
      "parentModel": {}, 
      "params": [], 
      "type": "simple"
    }, 
    {
      "name": "time", 
      "dynamic": "false", 
      "depends": "", 
      "parentModel": {}, 
      "params": [], 
      "type": "simple"
    }
  ]
}
"""

  validator = DocValidator(schema)

  doc = json.loads(json.dumps({'profileimg': u'http://a1.twimg.com/profile_images/1447971116/20110716110709-1_normal.jpg', 'text': u'Oh no no no white grape apple juice *licks lips* yum!! ^_^', 'authorname': u'ShanTaughtUwell', 'authorid': 258899646L, 'time': 1311083873L, 'createdtime': u'Tue, 19 Jul 2011 05:57:53 +0000', 'id': 93197849340293120L},
                              indent=2))

  print validator.validate({"not-defined-col":123})
  print validator.validate({"id": 123, "not-defined-col":123})
  print validator.validate({"id": 123, "time":123}) # Good one
  print validator.validate({"id": 123, "time":123, "authorname":123})
  print validator.validate({"id": 123, "time":123, "age":12345678901234567890})
  print validator.validate({"id": 123, "time":123, "price":123})

  # XXX check "isPublic":true

