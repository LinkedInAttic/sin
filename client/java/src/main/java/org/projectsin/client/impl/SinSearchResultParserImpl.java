/**
 * 
 */
package org.projectsin.client.impl;

import java.io.IOException;
import java.io.InputStream;
import java.io.StringWriter;
import java.util.Set;

import org.apache.commons.io.IOUtils;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.projectsin.client.api.SinSearchHit;
import org.projectsin.client.api.SinSearchResult;

/**
 * @author ruslan
 *
 */
public class SinSearchResultParserImpl implements SinSearchResultParser
{
  private final String      _idField;
  
  public SinSearchResultParserImpl(String idField)
  {
    _idField  =  idField;
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.impl.SinSearchResultParser#parseResult(java.io.InputStream)
   */
  @Override
  public SinSearchResult parseResult(InputStream is, Set<String> fieldSet, Set<String> countSet)
    throws IOException
  {
    final SinSearchResultBuilder rb = new SinSearchResultBuilder();

    try
    {
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
              SinSearchHit sh = new SinSearchHit();
              
              long id = 0;
              String idVal = (String)((JSONArray)jsonHit.get(_idField)).get(0);
              if(idVal == null)
                idVal = jsonHit.getString("uid");
              
              if(idVal != null)
              {
                id = Long.valueOf(idVal);
                sh.setId(id);

                double score = jsonHit.getDouble("score");
                sh.setScore(score);
                
                String srcData = jsonHit.getString("srcdata");
                sh.setSrcData(srcData);
                
                long docId = jsonHit.getLong("docid");
                sh.setDocid(docId);
                
                int grouphitscount = jsonHit.getInt("grouphitscount");
                sh.setGrouphitscount(grouphitscount);
              }
              else
              {
                continue;
              }
              
              if(fieldSet != null && !fieldSet.isEmpty())
              {
                for (String f: fieldSet)
                {
                  JSONArray valArr = (JSONArray)jsonHit.get(f);
                  if(valArr != null)
                  {
                    for(int ti = 0; ti < valArr.length(); ti++)
                    {
                      String val = (String)valArr.get(ti);
                      sh.addFieldValue(f, val);
                    }/*for*/
                  }/*valArr != null*/
                }/*for*/
              }/*if*/
              rb.addHit(sh);
            }/*jsonHit != null*/
          }/*for*/
        }/*hitsArr*/
        
        int numHits = jsonObj.getInt("numhits");
        rb.setNumHits(numHits);
        
        if(countSet != null && !countSet.isEmpty())
        {
          JSONObject facetsObj = (JSONObject)jsonObj.get("facets");
          if(facetsObj != null)
          {
            for(String s: countSet)
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
              }/*facetArr != null*/
            }/*for*/
          }/*facetObj != null*/
        }/*countFacets != null && !countFacets.isEmpty()*/
      }/*jsonObj != null*/
    }
    catch (JSONException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    return rb.build();
  }

}
