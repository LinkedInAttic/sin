package org.projectsin.client.api;

import java.net.URL;

public class SinStoreConfig
{
  private String  _name;
  private String  _apiKey;
  private URL     _senseiUrl;
  
  private String  _idField = "id";

  public String getName()
  {
    return _name;
  }

  public SinStoreConfig setName(String name)
  {
    _name = name;
    return this;
  }

  public String getApiKey()
  {
    return _apiKey;
  }

  public SinStoreConfig setApiKey(String apiKey)
  {
    _apiKey = apiKey;
    return this;
  }

  public URL getSenseiUrl()
  {
    return _senseiUrl;
  }

  public SinStoreConfig setSenseiUrl(URL senseiUrl)
  {
    _senseiUrl = senseiUrl;
    return this;
  }

  public String getIdField()
  {
    return _idField;
  }

  public SinStoreConfig setIdField(String idField)
  {
    _idField = idField;
    return this;
  }  
  
}
