/**
 * 
 */
package org.projectsin.client.impl;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.net.MalformedURLException;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

import org.apache.commons.io.IOUtils;
import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URIUtils;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.impl.conn.tsccm.ThreadSafeClientConnManager;
import org.apache.http.message.BasicNameValuePair;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.projectsin.client.api.InvalidSinConfigurationException;
import org.projectsin.client.api.SinConfig;
import org.projectsin.client.api.SinIndexable;
import org.projectsin.client.api.SinIndexableFactory;
import org.projectsin.client.api.SinSearchQuery;
import org.projectsin.client.api.SinSearchResult;
import org.projectsin.client.api.SinStore;
import org.projectsin.client.api.SinStoreConfig;

/**
 * @author ruslan
 *
 */
public class SinStoreImpl implements SinStore
{

  private final HttpClient  _httpClient = new DefaultHttpClient(new ThreadSafeClientConnManager());
  
  private final SinStoreConfig  _storeConfig;
  private final SinConfig         _sinConfig;
  
  private final String  _sinBaseUrl;
  private final String  _addDocsUrl;
  private final String  _updDocsUrl;
  private final String  _delDocsUrl;
  
  private final SinIndexableFactory _indexableFactory;
  
  public SinStoreImpl(SinConfig sinConfig, SinStoreConfig storeConfig)
    throws InvalidSinConfigurationException
  {
    _sinConfig = sinConfig;
    _storeConfig = storeConfig;
    
    try
    {
      _sinBaseUrl = new URL("http://" + _sinConfig.getHost() + ":" + _sinConfig.getPort() + "/store").toString();
      _addDocsUrl = new URL(_sinBaseUrl + "/add-docs/"    + _storeConfig.getName()).toString();
      _updDocsUrl = new URL(_sinBaseUrl + "/update-doc/"  + _storeConfig.getName()).toString();
      _delDocsUrl = new URL(_sinBaseUrl + "/delete-docs/" + _storeConfig.getName()).toString();
    }
    catch (MalformedURLException e)
    {
      throw new InvalidSinConfigurationException(e);
    }
    
    _indexableFactory = new SinIndexableFactoryImpl(_storeConfig);
  }
  
  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#submit(org.projectsin.client.api.SinIndexable)
   */
  @Override
  public void submit(SinIndexable doc)
  {
    Collection<SinIndexable> docs = new ArrayList<SinIndexable>(1);
    docs.add(doc);
    
    submit(docs);
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#submit(java.util.Collection)
   */
  @Override
  public void submit(Collection<SinIndexable> docs)
  {
    if(docs != null && !docs.isEmpty())
    {
      final JSONArray jsonMsgs = new JSONArray();

      for(SinIndexable doc: docs)
      {
        try
        {
          JSONObject jsonObj = new JSONObject(doc.getAsJSONString());
          jsonMsgs.put(jsonObj);
        }
        catch (JSONException e)
        {
          // TODO Auto-generated catch block
          e.printStackTrace();
        }
      }/*for*/
      
      if(jsonMsgs.length() > 0)
      {
        post(_addDocsUrl, "docs", jsonMsgs.toString());
      }
    }
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#update(org.projectsin.client.api.SinIndexable)
   */
  @Override
  public void update(SinIndexable doc)
  {
    try
    {
      JSONObject jsonObj = new JSONObject(doc.getAsJSONString());

      jsonObj.put(_storeConfig.getIdField(),
                  doc.getId());

      post(_updDocsUrl, "doc", jsonObj.toString());
    }
    catch (JSONException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#remove(long)
   */
  @Override
  public void remove(long id)
  {
    Collection<Long> ids = new ArrayList<Long>(1);
    ids.add(id);
    
    remove(ids);
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#remove(java.util.Collection)
   */
  @Override
  public void remove(Collection<Long> ids)
  {
    if(ids != null && !ids.isEmpty())
    {
      JSONArray jsonMsgs = new JSONArray();
      
      for(Long id: ids)
      {
        jsonMsgs.put(id);
      }
    
      post(_delDocsUrl, "ids", jsonMsgs.toString());
    }
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#search(org.projectsin.client.api.SinSearchQuery)
   */
  @Override
  public SinSearchResult search(SinSearchQuery query)
  {
    final SinSearchResultBuilder rb = new SinSearchResultBuilder();
    
    if(query == null)
      return rb.build();
    
    List<NameValuePair> nvp = new ArrayList<NameValuePair>();
    
    if(query.getHasQuery())
      nvp.add(new BasicNameValuePair("q", query.getQuery()));
    
    if(query.getHasFacetSet())
    {
      
      for(Map.Entry<String, String> e: query.getFacetMap().entrySet())
      {
        nvp.add(new BasicNameValuePair("select." + e.getKey() + ".val", e.getValue()));
      }
    }
    
    if(query.getHasFieldSet())
    {
      rb.addFields(query.getFieldSet());
    }
    
    if(query.getHasCountSet())
    {
      for(String s: query.getCountSet())
      {
        String facetParam = "facet." + s;
        
        nvp.add(new BasicNameValuePair(facetParam + ".expand", "true"));
        nvp.add(new BasicNameValuePair(facetParam + ".minhit", "0" ));
        nvp.add(new BasicNameValuePair(facetParam + ".max"   , Integer.toString(query.getMaxFacetCountHits())));
        nvp.add(new BasicNameValuePair(facetParam + ".order" , "hits"));
      }
    }
    
    nvp.add(new BasicNameValuePair("start", Integer.toString(query.getStart ())));
    nvp.add(new BasicNameValuePair("rows" , Integer.toString(query.getLength())));
    
    nvp.add(new BasicNameValuePair("sort" , "date:desc"));
    
    URI uri;
    try
    {
      uri = URIUtils.createURI(_storeConfig.getSenseiUrl().getProtocol(),
                               _storeConfig.getSenseiUrl().getHost(),
                               _storeConfig.getSenseiUrl().getPort(),
                               _storeConfig.getSenseiUrl().getPath(),
                               URLEncodedUtils.format(nvp, "UTF-8"),
                               null);
      
      HttpGet get = new HttpGet(uri);
      
      System.out.println("query=" + uri.toString());
      
      get.addHeader("X-Sin-Api-Key", _storeConfig.getApiKey());
      
      HttpResponse res = _httpClient.execute(get);
      
      InputStream is = null;
      
      try
      {
        is = res.getEntity().getContent();
        
        StringWriter sw = new StringWriter();
        IOUtils.copy(is, sw, "UTF-8");
        
        String respData = sw.toString();
        
        JSONObject jsonObj = new JSONObject(respData);
        
        if(jsonObj != null)
        {
          JSONArray hitsArr = (JSONArray)jsonObj.get("hits");
          if(hitsArr != null)
          {
            for(int i = 0; i < hitsArr.length(); i++)
            {
              JSONObject jsonHit = (JSONObject)hitsArr.get(i);
              if(jsonHit != null)
              {
                long id = 0;
                String idVal = (String)((JSONArray)jsonHit.get(_storeConfig.getIdField())).get(0);
                if(idVal != null)
                {
                  id = Long.valueOf(idVal);
                  rb.addId(id);
                }
                else
                {
                  continue;
                }
                
                if(query.getHasFieldSet())
                {
                  for (String f: query.getFieldSet())
                  {
                    JSONArray valArr = (JSONArray)jsonHit.get(f);
                    if(valArr != null)
                    {
                      for(int ti = 0; ti < valArr.length(); ti++)
                      {
                        String val = (String)valArr.get(ti);
                        rb.addFieldValue(f, id, val);
                      }/*for*/
                    }/*valArr != null*/

                  }
                }
              }
            }/*hitsArr*/
            
            int numHits = jsonObj.getInt("numhits");
            rb.setNumHits(numHits);
            
            double score = jsonObj.getDouble("score");
            rb.setScore(score);
            
            if(query.getHasCountSet())
            {
              JSONObject facetsObj = (JSONObject)jsonObj.get("facets");
              if(facetsObj != null)
              {
                for(String s: query.getCountSet())
                {
                  JSONArray facetArr = (JSONArray)facetsObj.get(s);
                  if(facetArr != null)
                  {
                    for(int fi = 0; fi < facetArr.length(); fi++)
                    {
                      JSONObject facetObj = (JSONObject)facetArr.get(fi);
                      if(facetObj != null)
                      {
                        Long   countVal = (Long)facetObj.get("count");
                        String facetVal = (String)facetObj.get("value");
                        
                        if(countVal != null && facetVal != null)
                        {
                          rb.addFacetCount(s, facetVal, countVal.intValue());
                        }
                      }
                    }/*for*/
                  }
                }/*for*/
              }/*facetObj != null*/
            }/*countFacets != null && !countFacets.isEmpty()*/
          }
        }/*jsonObj != null*/
      }
      catch (JSONException e)
      {
        // TODO Auto-generated catch block
        e.printStackTrace();
      }
      finally   {
        if(is != null)
          is.close();
      }
    }
    catch (URISyntaxException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    catch (ClientProtocolException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    catch (IOException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }

    return rb.build();
  }

  private void post(String url, final String param, final String postData)
  {
    HttpPost post = new HttpPost(url);
    
    List<NameValuePair> nvp = new ArrayList<NameValuePair>();
    nvp.add(new BasicNameValuePair(param, postData));
    
    try
    {
      UrlEncodedFormEntity entity = new UrlEncodedFormEntity(nvp);
      post.setEntity(entity);
      post.addHeader("X-Sin-Api-Key", _storeConfig.getApiKey());

      HttpResponse res = _httpClient.execute(post);
      InputStream is = null;
      
      try
      {
        is = res.getEntity().getContent();
        while (is.skip(10000) > 0);
      }
      finally   {
        if(is != null)
          is.close();
      }
    }
    catch(UnsupportedEncodingException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    catch (ClientProtocolException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    catch (IOException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#getIndexableFactory()
   */
  @Override
  public SinIndexableFactory getIndexableFactory()
  {
    return _indexableFactory;
  }

}
