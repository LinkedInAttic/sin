/**
 * 
 */
package org.projectsin.client;

import org.projectsin.client.api.SinClient;
import org.projectsin.client.api.SinClientFactory;
import org.projectsin.client.api.SinConfig;

/**
 * @author ruslan
 *
 */
public class DefaultSinClientFactory implements SinClientFactory
{
  public static SinClientFactory INSTANCE = new DefaultSinClientFactory();
  
  public static SinClientFactory getInstance()
  {
    return INSTANCE;
  }
  
  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinClientFactory#createClient(org.projectsin.client.api.SinConfig)
   */
  @Override
  public SinClient createClient(SinConfig config)
  {
    // TODO Auto-generated method stub
    return null;
  }

}
