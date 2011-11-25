/**
 * 
 */
package org.projectsin.client.api;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @author ruslan
 *
 */
public class SinSearchResult
  implements Serializable
{
  private static final long serialVersionUID = 1L;

  private int         _numHits;

  private Map<String, Map<String, Integer>>    _facetCounts;
  private Map<String, Map<Long, List<String>>>  _fieldValues;
  
  private List<Long>  _ids;
  private List<SinSearchHit>    _searchHits;

  public int getNumHits()
  {
    return _numHits;
  }
  
  public void setNumHits(int numHits)
  {
    _numHits = numHits;
  }
  
  public List<Long> getIds()
  {
    return _ids;
  }
  
  public void setSearchHits(List<SinSearchHit> searchHits)
  {
    _searchHits = searchHits;
    if(_searchHits != null)
    {
      _ids = new ArrayList<Long>(_searchHits.size());
      _fieldValues = new HashMap<String, Map<Long, List<String>>>();

      for(SinSearchHit hit: _searchHits)
      {
        _ids.add(hit.getId());
        Map<String,List<String>> fvMap = hit.getFieldValues();
        if(fvMap != null)
        {
          for(Map.Entry<String, List<String>> e: fvMap.entrySet())
          {
            Map<Long,List<String>> id2ValuesMap = _fieldValues.get(e.getKey());
            if(id2ValuesMap == null)
            {
              id2ValuesMap = new HashMap<Long,List<String>>();
              _fieldValues.put(e.getKey(), id2ValuesMap);
            }
            id2ValuesMap.put(hit.getId(), e.getValue());
          }
        }
      }/*for*/
    }
    else
    {
      _ids = null;
      _fieldValues = null;
    }
  }
  
  public List<SinSearchHit> getSearchHits()
  {
    return _searchHits;
  }

  public Map<String, Map<String, Integer>> getFacetCounts()
  {
    return _facetCounts;
  }
  
  public void setFacetCounts(Map<String, Map<String, Integer>> facetCounts)
  {
    _facetCounts = facetCounts;
  }

  public Map<String, Map<Long, List<String>>> getFieldValues()
  {
    return _fieldValues;
  }

}
