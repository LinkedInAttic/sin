/**
 * 
 */
package org.projectsin.client.api;


/**
 * @author ruslan
 *
 */
public interface SinClientFactory
{
  public SinClient createClient(SinConfig config);
}
