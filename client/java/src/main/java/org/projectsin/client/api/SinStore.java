package org.projectsin.client.api;

import java.util.Collection;

public interface SinStore
{
  public void submit(SinIndexable doc);
  
  public void submit(Collection<SinIndexable> docs);
  
  public void update(SinIndexable doc);
  
  public void remove(long id);
  public void remove(Collection<Long> ids);
  
  public SinSearchResult search(SinSearchQuery query);
}
