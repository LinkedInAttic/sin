/**
 * 
 */
package org.projectsin.client.api;

import java.io.Serializable;
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
  private List<Long>  _ids;
  private double      _score;

  private Map<String, Map<String, Integer>>    _facetCounts;
  private Map<String, Map<Long, List<String>>>  _fieldValues;

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
  
  public double getScore()
  {
    return _score;
  }

  public void setScore(double score)
  {
    _score = score;
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

  public void setFieldValues(Map<String, Map<Long, List<String>>> fieldValues)
  {
    _fieldValues = fieldValues;
  }

}
