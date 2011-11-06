/**
 * 
 */
package org.projectsin.client.api;

import java.io.Serializable;
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
  private List<Long>  _ids;
  private Map<String, Map<String, Integer>> _facetCounts;
  
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
  
  public void setIds(List<Long> ids)
  {
    _ids = ids;
  }
  
  public Map<String, Map<String, Integer>> getFacetCounts()
  {
    return _facetCounts;
  }
  
  public void setFacetCounts(Map<String, Map<String, Integer>> facetCounts)
  {
    _facetCounts = facetCounts;
  }

}
