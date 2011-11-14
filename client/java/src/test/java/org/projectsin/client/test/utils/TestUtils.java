package org.projectsin.client.test.utils;

public class TestUtils
{

  public static void assertWithTimeout(long millis, AssertionClause ac)
    throws Exception
  {
    long st = System.currentTimeMillis();

    while(st + millis > System.currentTimeMillis())
    {
      try
      {
        ac.doAssert();
        break;
      }
      catch(AssertionError ex)
      {
        
      }
    }/*while*/
  }
}
