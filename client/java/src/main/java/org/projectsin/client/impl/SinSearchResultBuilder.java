package org.projectsin.client.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.projectsin.client.api.SinSearchResult;

public class SinSearchResultBuilder
{
  private int         _numHits = 0;
  private List<Long>  _ids = new ArrayList<Long>();
  
  private Map<String, Map<String, Integer>> _facetCounts = new HashMap<String, Map<String, Integer>>();
  
  public SinSearchResultBuilder addId(long id)
  {
    _ids.add(id);
    return this;
  }

  public SinSearchResultBuilder setNumHits(int numHits)
  {
    _numHits = numHits;
    return this;
  }
  
  public SinSearchResultBuilder addFacetCount(String type, String value, int count)
  {
    Map<String,Integer> facetCount = _facetCounts.get(type);
    if(facetCount == null)
    {
      facetCount = new HashMap<String,Integer>();
      _facetCounts.put(type, facetCount);
    }
    facetCount.put(value, count);
    return this;
  }

  public SinSearchResult build()
  {
    SinSearchResult result = new SinSearchResult();
    
    result.setNumHits(_numHits);
    result.setIds(new ArrayList<Long>(_ids));
    
    // TODO MED makes this immutable compeltely
    result.setFacetCounts(new HashMap<String, Map<String, Integer>>(_facetCounts));
    
    return result;
  }
}
