/**
 * 
 */
package org.projectsin.client.api;

import java.util.List;
import java.util.Map;

/**
 * @author ruslan
 *
 */
public interface SinSearchResult
{
  public int getNumHits();
  
  public List<Long> getIds();
  
  public Map<String,Map<String,Integer>> getFacetCounts();
}
