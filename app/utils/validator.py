import types
from types import *
from decimal import *
from django.utils import simplejson as json
import re

MIN_SHORT = 0                   # Not -32768
MAX_SHORT = 32767
MIN_INT = 0                     # Not -2147483648
MAX_INT = 2147483647

class DocValidator(object):
  """Document validator for Sin.

  This class builds a document validator based on a schema (in JSON
  format), and is used to detect if a document contains valid data
  before it is indexed by Sin.

  """
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
    """Validate if a document is valid.

    Given a document in JSON format, validate if its data is compliant
    with the schema requirement.  Return the first error once it is
    detected.

    """
    if self.uid_column not in doc:
      return (False, "Required column %s is missing" % self.uid_column)

    for (key, value) in doc.iteritems():
      is_multi = False
      if key == self.uid_column:
        defined_type = "long"
      else:
        if key not in self.columns:
          return (False, "Column %s is not declared in schema" % key)
        defined_type = self.columns[key]["type"]
        if (self.columns[key].get("multi") == "true"):
          is_multi = True

      if is_multi:
        #
        # Multi-value column.
        #
        # All multi-value columns should have the values wrapped into a string.
        #
        if not isinstance(value, basestring):
          return (False, "Multi-value column %s does not have a string value" % key)
        delimiter = self.columns[key].get("delimiter")
        if delimiter and len(delimiter) > 0:
          delimiter = delimiter[:1]
        else:
          delimiter = ","
        val_strs = re.split(r"[%s\s]+" % delimiter, value.strip())
        # print val_strs
        try:
          if defined_type == "int":
            for val_str in val_strs:
              val = int(val_str)
              if val < MIN_INT or val > MAX_INT:
                return (False, "Multi-value column %s contains some out-of-range value(s)" % key)
          elif defined_type == "long":
            for val_str in val_strs:
              val = long(val_str)
              if val < 0:
                return (False, "Multi-value column %s contains some out-of-range value(s)" % key)
          elif defined_type == "short":
            for val_str in val_strs:
              val = int(val_str)
              if val < MIN_SHORT or val > MAX_SHORT:
                return (False, "Multi-value column %s contains some out-of-range value(s)" % key)
          elif defined_type == "float" or defined_type == "double":
            for val_str in val_strs:
              val = float(val_str)
              if val < 0:
                return (False, "Multi-value column %s contains some out-of-range value(s)" % key)
        except:
          return (False, "Multi-value columns %s contains some invalid value(s)" % key)
      else:
        #
        # Single-value column
        #
        if defined_type == "string" and not isinstance(value, (basestring, bool)):
          return (False, "Column %s does not have a string value" % key)
        elif defined_type == "int":
          if not isinstance(value, int):
            return (False, "Column %s does not have an int value" % key)
          elif value < MIN_INT or value > MAX_INT:
            return (False, "Column %s has an out-of-range value" % key)
        elif defined_type == "long" and not isinstance(value, (int, long)):
          return (False, "Column %s does not have a long value" % key)
        elif defined_type == "short":
          if not isinstance(value, int):
            return (False, "Column %s does not have a short value" % key)
          elif value < MIN_SHORT or value > MAX_SHORT:
            return (False, "Column %s has an out-of-range value" % key)
        elif defined_type == "float" or defined_type == "double":
          if not isinstance(value, (int, long, float)):
            return (False, "Column %s does not have a float/double value" % key)
          elif value < 0:
            return (False, "Column %s has an out-of-range value" % key)
        elif defined_type == "text" and not isinstance(value, basestring):
          return (False, "Column %s does not have a text value" % key)
  
    return (True, None)

if __name__ == "__main__":

  # Testing...

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
        "name": "isPublic", 
        "termvector": "NO", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "string", 
        "store": "NO"
      },
      {
        "index": "ANALYZED", 
        "multi": "true", 
        "from": "", 
        "name": "skills", 
        "termvector": "NO", 
        "delimiter": "", 
        "parentModel": {}, 
        "type": "short", 
        "store": "NO"
      },
      {
        "index": "ANALYZED", 
        "multi": "true", 
        "from": "", 
        "name": "scores", 
        "termvector": "NO", 
        "delimiter": ";", 
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

  # Invalid ones
  print validator.validate({"not-defined-col":123})                # Required uid field is missing
  print validator.validate({"id": 123, "time":123, "age":12345678901234567890}) # age has a long value
  print validator.validate({"id": 123, "skills":123})              # Multi-value column skills should have a string value
  print validator.validate({"id": 123, "skills":"123,aaa"})        # skills contains invalid values
  print validator.validate({"id": 123, "skills":"99999999999"})    # Out of range
  print validator.validate({"id": 123, "scores":"  60.5, 95.5  "}) # Delimiter should be ';'
  print validator.validate({"id": 123, "age": -2147483648888})     # Out of range
  print validator.validate({"id": 123, "age": 2147483648888})      # Out of range
  print validator.validate({"id": 123, "age": [1,2,3]})            # age does not have an integer value
  print validator.validate({"id": 123, "age": -10})                # Out of range (negative)
  print validator.validate({"id": 123, "price": -10.50})           # 
  print validator.validate({"id": -123})                           #negative id
  print validator.validate({"id": "abc"})                          #not valid id
  print validator.validate({"id": 123.345})                        #id out of range

  print "-------------------------------------------------------------"

  # Valid ones
  
  print validator.validate({"id": 123, "time":123, "authorname":123})
  print validator.validate({"id": 123, "not-defined-col":123})     
  print validator.validate({"id": "123", "time":123})
  print validator.validate({"id": 123, "time":123})
  print validator.validate({"id": 123, "time":123, "price":123})
  print validator.validate({"id": 123, "time":123, "price":123, "isPublic":True}) # Boolean value is OK for string
  print validator.validate({"id": 123, "skills":"123"})
  print validator.validate({"id": 123, "skills":"  123,   456,   789  "})
  print validator.validate({"id": 123, "scores":"  60.5; ;; 95.5  "})
