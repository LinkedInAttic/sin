/**
 * 
 */
package org.projectsin.client.impl;

import org.projectsin.client.api.SinIndexable;

/**
 * @author ruslan
 *
 */
public class SinIndexableImpl implements SinIndexable
{
  private final long    _id;
  private final String  _jsonString;
  
  public SinIndexableImpl(long id, String jsonString)
  {
    _id = id;
    _jsonString = jsonString;
  }
  
  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinIndexable#getId()
   */
  @Override
  public long getId()
  {
    return _id;
  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinIndexable#getAsJSONString()
   */
  @Override
  public String getAsJSONString()
  {
    return _jsonString;
  }

}
