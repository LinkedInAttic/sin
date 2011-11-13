/**
 * 
 */
package org.projectsin.client.test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

import java.net.URL;
import java.util.HashMap;
import java.util.Map;

import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.projectsin.client.DefaultSinClientFactory;
import org.projectsin.client.api.SinClient;
import org.projectsin.client.api.SinClientFactory;
import org.projectsin.client.api.SinConfig;
import org.projectsin.client.api.SinIndexableFactory;
import org.projectsin.client.api.SinSearchQuery;
import org.projectsin.client.api.SinSearchResult;
import org.projectsin.client.api.SinStore;
import org.projectsin.client.api.SinStoreConfig;
import org.projectsin.client.test.utils.AssertionClause;
import org.projectsin.client.test.utils.TestUtils;

/**
 * @author ruslan
 *
 */
public class TestRemoteQuery
{
  /**
   * @throws java.lang.Exception
   */
  @BeforeClass
  public static void setUpBeforeClass()
    throws Exception
  {
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
  public void testHappyPath()
    throws Exception
  {
    SinConfig sinConfig = new SinConfig().setHost(System.getProperty("testSinHost", "eat1-app55.corp"))
                                         .setPort(Integer.parseInt(System.getProperty("testSinPort", "8666")) );
    
    SinStoreConfig storeConfig = new SinStoreConfig().setName("tests")
                                                     .setApiKey(System.getProperty("testSinAPIKey", "aOLueRW1vyaeQrrsyinGTbXaj1DHaWIXOXpR2qh3qYU"))
                                                     .setSenseiUrl(new URL(System.getProperty("testSenseiUrl", "http://172.18.158.51:15017/sensei")));
    
    SinClientFactory cf = DefaultSinClientFactory.getInstance();
    
    assertNotNull(cf);
    
    SinClient sc = cf.createClient(sinConfig);
    assertNotNull(sc);
    
    final SinStore ss = sc.openStore(storeConfig);
    
    // #1 empty result
    
    SinSearchResult searchResult = ss.search(new SinSearchQuery());
    assertNotNull(searchResult);
    assertEquals(0, searchResult.getNumHits());
    
    // #2 submit 2 documents
    Map<String,Object> doc1 = new HashMap<String,Object>();
    doc1.put("id"  , new Long(1));
    doc1.put("tags", "java,python");
    doc1.put("contents", "document 1");
    
    Map<String,Object> doc2 = new HashMap<String,Object>();
    doc2.put("id"  , new Long(2));
    doc2.put("tags", "ruby,groovy");
    doc2.put("contents", "document 2");

    SinIndexableFactory sindf = ss.getIndexableFactory();
    
    ss.submit(sindf.fromMap(doc1));
    ss.submit(sindf.fromMap(doc2));
                                             
    TestUtils.assertWithTimeout(2000, new AssertionClause()
    {
      @Override
      public void doAssert() throws Exception
      {
        SinSearchResult searchResult = ss.search(new SinSearchQuery());
        assertNotNull(searchResult);
        assertEquals(2, searchResult.getNumHits());
      }
    });
    
    ss.remove(1);
    ss.remove(2);
  }

}
