package org.projectsin.client.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.projectsin.client.api.SinSearchResult;

public class SinSearchResultBuilder
{
  private int         _numHits = 0;
  private List<Long>  _ids = new ArrayList<Long>();
  private double      _score = 0.0;
  
  private Map<String, Map<String, Integer>>     _facetCounts = new HashMap<String, Map<String, Integer>>();
  private Map<String, Map<Long, List<String>>>  _fieldValues = new HashMap<String, Map<Long, List<String>>>();
  
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
  
  public SinSearchResultBuilder setScore(double score)
  {
    _score = score;
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
  
  public SinSearchResultBuilder addFields(Set<String> fields)
  {
    for (String f: fields)
    {
      final Map<Long, List<String>> valMap = new HashMap<Long, List<String>>();
      _fieldValues.put(f, valMap);
    }
    return this;
  }
  
  public SinSearchResultBuilder addFieldValue(String field, long id, String value)
  {
    final Map<Long, List<String>> valMap = _fieldValues.get(field);
    if(valMap != null)
    {
      List<String> values = valMap.get(id);
      if(values == null)
      {
        values = new ArrayList<String>();
        valMap.put(id, values);
      }
      values.add(value);
    }
    return this;
  }

  public SinSearchResult build()
  {
    SinSearchResult result = new SinSearchResult();
    
    result.setNumHits(_numHits);
    result.setIds(new ArrayList<Long>(_ids));
    result.setScore(_score);
    
    // TODO MED makes this immutable compeltely
    result.setFacetCounts(new HashMap<String, Map<String, Integer>>   (_facetCounts));
    result.setFieldValues(new HashMap<String, Map<Long, List<String>>>(_fieldValues));
    
    return result;
  }
}
