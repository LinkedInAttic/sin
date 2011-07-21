'''
Created on Jul 20, 2011

@author: sguo
'''
import unittest

from utils.validator import DocValidator


class TestValidator(unittest.TestCase):

  def setUp(self):
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
    self.schema = schema
    self.validator = DocValidator(schema)

# Invalid ones

  def testUIDExistence(self):
    testresult = self.validator.validate({"not-defined-col":123})
    self.assertEqual(False, testresult[0], "UID not defined");
    
  def testUIDNegative(self):
    testresult = self.validator.validate({"id": -123})
    self.assertEqual(False, testresult[0], "negative id");  
    
  def testUIDString(self):
    testresult = self.validator.validate({"id": "abc"})
    self.assertEqual(False, testresult[0], "string id");  
    
  def testUIDNotLong(self):
    testresult = self.validator.validate({"id": 123.345})
    self.assertEqual(False, testresult[0], "not a long id");              

  def testLongValue(self):
    testresult = self.validator.validate({"id": 123, "time":123, "age":12345678901234567890})
    self.assertEqual(False, testresult[0], "age has a long value");

  def testMultiValueHasString(self):
    testresult = self.validator.validate({"id": 123, "skills":123})
    self.assertEqual(False, testresult[0], "Multi-value column skills should have a string value");    

  def testInvalidValuesA(self):
    testresult = self.validator.validate({"id": 123, "skills":"123,aaa"})
    self.assertEqual(False, testresult[0], "skills contains invalid values");
    
  def testInvalidValuesB(self):
    testresult = self.validator.validate({"id": 123, "age": [1,2,3]})
    self.assertEqual(False, testresult[0], "age does not have an integer value");  
    
  def testInvalidValuesC(self):
    testresult = self.validator.validate({"id": 123, "price": "xyz"})
    self.assertEqual(False, testresult[0], "invalid value");               

  def testOutOfRangeA(self):
    testresult = self.validator.validate({"id": 123, "skills":"99999999999"})
    self.assertEqual(False, testresult[0], "Out of range"); 
    
  def testOutOfRangeB(self):
    testresult = self.validator.validate({"id": 123, "age": -2147483648888})
    self.assertEqual(False, testresult[0], "Out of range");            
    
  def testOutOfRangeC(self):
    testresult = self.validator.validate({"id": 123, "age": 2147483648888})
    self.assertEqual(False, testresult[0], "Out of range");  
    
  def testOutOfRangeD(self):
    testresult = self.validator.validate({"id": 123, "age": -10})
    self.assertEqual(False, testresult[0], "Out of range (negative)");  
    
  def testOutOfRangeE(self):
    testresult = self.validator.validate({"id": 123, "price": -10.50})
    self.assertEqual(False, testresult[0], "Out of range (negative)");    
    
  def testDelimiter(self):
    testresult = self.validator.validate({"id": 123, "scores":"  60.5, 95.5  "})
    self.assertEqual(False, testresult[0], "Delimiter should be ';'");    
    
    
# Valid ones
    
  def __checkValid(self, doc):
    testresult = self.validator.validate(doc)
    self.assertEqual(True, testresult[0], "should be valid one");    
 
  def testValid_1(self):
    self.__checkValid({"id": 123, "time":123, "authorname":123}); 

  def testValid_2(self):
    self.__checkValid({"id": 123, "not-defined-col":123});  
  
  def testValid_3(self):
    self.__checkValid({"id": "123", "time":123});  
    
  def testValid_4(self):
    self.__checkValid({"id": 123, "time":123});     
    
  def testValid_5(self):
    self.__checkValid({"id": 123, "time":123, "price":123});  
  
  def testValid_6(self):
    self.__checkValid({"id": 123, "time":123, "price":123, "isPublic":True});  
    
  def testValid_7(self):
    self.__checkValid({"id": 123, "skills":"123"});   
    
  def testValid_8(self):
    self.__checkValid({"id": 123, "skills":"  123,   456,   789  "});  
  
  def testValid_9(self):
    self.__checkValid({"id": 123, "scores":"  60.5; ;; 95.5  "});  
    
  def testValid_10(self):
    self.__checkValid({"id": 123, "price":"  25.678 "});                        




if __name__ == "__main__":
    unittest.main()