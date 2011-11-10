/**
 * 
 */
package org.projectsin.client.api;

import java.util.Map;

import org.json.JSONObject;

/**
 * @author ruslan
 *
 */
public interface SinIndexableFactory
{
  /**
   * @param jsonObj
   * @return
   */
  public SinIndexable fromJSON(JSONObject jsonObj);
  
  /**
   * @param valMap
   * @return
   */
  public SinIndexable fromMap(Map<String,Object> valMap);
}
