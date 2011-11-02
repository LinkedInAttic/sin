/**
 * 
 */
package org.projectsin.client.api;

import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * @author ruslan
 *
 */
public class SinSearchQuery
{
  private String    _query;
  
  private int       _start  = 0;
  private int       _length = 10;
  
  private Map<String,String> _facetMap = new HashMap<String,String>();
  private Set<String>        _countSet = new HashSet<String>();
  
  public String getQuery()
  {
    return _query;
  }
  
  public SinSearchQuery setQuery(String query)
  {
    _query = query;
    return this;
  }
  
  public int getStart()
  {
    return _start;
  }
  
  public SinSearchQuery setStart(int start)
  {
    _start = start;
    return this;
  }
  
  public int getLength()
  {
    return _length;
  }
  
  public SinSearchQuery setLength(int length)
  {
    _length = length;
    return this;
  }
  
  public SinSearchQuery addFacet(String facet, String value)
  {
    _facetMap.put(facet, value);
    return this;
  }
  
  public SinSearchQuery addFacetCount(String facet)
  {
    _countSet.add(facet);
    return this;
  }

  public Map<String, String> getFacetMap()
  {
    return Collections.unmodifiableMap(_facetMap);
  }

  public Set<String> getCountSet()
  {
    return Collections.unmodifiableSet(_countSet);
  }
  
}
