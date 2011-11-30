package org.projectsin.client.test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.HashSet;
import java.util.Set;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.projectsin.client.api.SinSearchResult;
import org.projectsin.client.impl.SinSearchResultParser;
import org.projectsin.client.impl.SinSearchResultParserImpl;

public class TestResultParser
{
  static File _rf1 = new File("src/test/resources/output1.txt");
  
  /**
   * @throws java.lang.Exception
   */
  @BeforeClass
  public static void setUpBeforeClass()
    throws Exception
  {
    if(!_rf1.exists())
      throw new Exception("No input test resource file found:" + _rf1.getAbsolutePath());
  }

  /**
   * @throws java.lang.Exception
   */
  @AfterClass
  public static void tearDownAfterClass()
    throws Exception
  {
  }

  /**
   * @throws java.lang.Exception
   */
  @Before
  public void setUp()
    throws Exception
  {
  }

  /**
   * @throws java.lang.Exception
   */
  @After
  public void tearDown()
    throws Exception
  {
  }

  @Test
  public void testResultParser()
    throws IOException
  {
    InputStream is = null;
    
    try
    {
      is = new FileInputStream(_rf1);
      SinSearchResultParser srp = new SinSearchResultParserImpl("id");
      
      Set<String> fvs = new HashSet<String>();
      fvs.add("anets");
              
      SinSearchResult result = srp.parseResult(is, fvs, null);
      assertNotNull(result);
      
      assertEquals(36, result.getNumHits());
      
      assertNotNull(result.getFieldValues());
      assertEquals(true, result.getFieldValues().containsKey("anets"));
      assertEquals(true, result.getFieldValues().get("anets").containsKey(70l));
      assertEquals(true, result.getFieldValues().get("anets").get(70l).contains("123922"));
    }
    finally {
      if(is != null)
        is.close();
    }
  }
}
