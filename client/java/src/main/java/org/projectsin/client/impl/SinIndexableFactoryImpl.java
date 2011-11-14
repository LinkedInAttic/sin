/**
 * 
 */
package org.projectsin.client.impl;

import java.util.Map;

import org.json.JSONException;
import org.json.JSONObject;
import org.projectsin.client.api.SinIndexable;
import org.projectsin.client.api.SinIndexableFactory;
import org.projectsin.client.api.SinStoreConfig;

/**
 * @author ruslan
 *
 */
public class SinIndexableFactoryImpl implements SinIndexableFactory
{
  private final SinStoreConfig  _storeConfig;
  
  public SinIndexableFactoryImpl(SinStoreConfig storeConfig)
  {
    _storeConfig = storeConfig;
  }
  
  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinIndexableFactory#fromJSON(org.json.JSONObject)
   */
  @Override
  public SinIndexable fromJSON(JSONObject jsonObj)
  {
    final long id = validateAndGetIdKey(jsonObj);
    return new SinIndexableImpl(id, jsonObj.toString());
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinIndexableFactory#fromMap(java.util.Map)
   */
  @Override
  public SinIndexable fromMap(Map<String, Object> valMap)
  {
    JSONObject jsonObj = new JSONObject(valMap);
    return fromJSON(jsonObj);
  }

  private long validateAndGetIdKey(JSONObject jsonObj)
  {
    try
    {
      if(jsonObj.has(_storeConfig.getIdField()))
        return jsonObj.getLong(_storeConfig.getIdField());
    }
    catch (JSONException e)
    {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
    throw new IllegalArgumentException("Missing required ID field: " + _storeConfig.getIdField());
  }

}
