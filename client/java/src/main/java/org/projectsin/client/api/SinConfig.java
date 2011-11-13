/**
 * 
 */
package org.projectsin.client.api;

/**
 * @author ruslan
 *
 */
public class SinConfig
{
  private String    _host;
  private int       _port = 8666;
  
  public String getHost()
  {
    return _host;
  }
  
  public SinConfig setHost(String host)
  {
    _host = host;
    return this;
  }
  
  public int getPort()
  {
    return _port;
  }
  
  public SinConfig setPort(int port)
  {
    _port = port;
    return this;
  }
  
} /*SinConfig*/
