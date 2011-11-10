/**
 * 
 */
package org.projectsin.client.impl;

import org.projectsin.client.api.InvalidSinConfigurationException;
import org.projectsin.client.api.SinClient;
import org.projectsin.client.api.SinConfig;
import org.projectsin.client.api.SinStore;
import org.projectsin.client.api.SinStoreConfig;

/**
 * @author ruslan
 *
 */
public class SinClientImpl implements SinClient
{
  final SinConfig   _sinConfig;
  
  public SinClientImpl(SinConfig sincConfig)
  {
    _sinConfig = sincConfig;
  }
  
  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinClient#openStore(org.projectsin.client.api.SinStoreConfig)
   */
  @Override
  public SinStore openStore(SinStoreConfig storeConfig)
    throws InvalidSinConfigurationException
  {
    final SinStore sinStore = new SinStoreImpl(_sinConfig, storeConfig);
    return sinStore;
  }

}
