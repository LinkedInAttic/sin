/**
 * 
 */
package org.projectsin.client.api;

/**
 * @author ruslan
 *
 */
public interface SinClient
{
  /**
   * @param storeConfig
   * @return
   * @throws InvalidSinConfigurationException
   */
  public SinStore openStore(SinStoreConfig storeConfig)
      throws InvalidSinConfigurationException;
}
